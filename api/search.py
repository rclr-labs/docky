"""
Serviço de busca vetorial e re-ranking com Qdrant
"""
import logging
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import CrossEncoder

from api.config import settings
from llm.client import EmbeddingClient


logger = logging.getLogger(__name__)


class SearchResult:
    """Resultado de uma busca"""
    
    def __init__(
        self,
        content: str,
        metadata: dict,
        score: float,
        rank: int,
    ):
        self.content = content
        self.metadata = metadata
        self.score = score
        self.rank = rank


class SearchService:
    """Serviço de busca vetorial com Qdrant e re-ranking"""
    
    def __init__(
        self,
        qdrant_url: str = settings.QDRANT_URL,
        qdrant_api_key: Optional[str] = settings.QDRANT_API_KEY,
        collection_name: str = settings.QDRANT_COLLECTION_NAME,
        embedding_model: str = settings.EMBEDDING_MODEL,
        embedding_dim: int = settings.EMBEDDING_DIMENSION,
    ):
        """Inicializar SearchService"""
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        # Clientes
        self.qdrant_client = AsyncQdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
        )
        self.embedding_client = EmbeddingClient(embedding_model)
        
        # Re-ranker (CrossEncoder de bge-reranker-base)
        logger.info("Carregando modelo de re-ranking: BAAI/bge-reranker-base")
        self.reranker = CrossEncoder("BAAI/bge-reranker-base", max_length=512)
        
        logger.info(f"✅ SearchService inicializado")
        logger.info(f"   Qdrant: {qdrant_url}")
        logger.info(f"   Collection: {collection_name}")
        logger.info(f"   Embedding dim: {embedding_dim}")
    
    async def ensure_collection(self) -> bool:
        """Garantir que a collection existe no Qdrant"""
        try:
            # Tentar obter informações da collection
            collection_info = await self.qdrant_client.get_collection(
                self.collection_name
            )
            logger.info(f"Collection '{self.collection_name}' existe")
            return True
        except Exception:
            # Collection não existe, criar
            logger.info(f"Criando collection '{self.collection_name}'...")
            try:
                await self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"✅ Collection '{self.collection_name}' criada")
                return True
            except Exception as e:
                logger.error(f"❌ Erro ao criar collection: {str(e)}")
                return False
    
    async def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: dict,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> int:
        """
        Indexar documento no Qdrant
        
        Args:
            doc_id: ID único do documento
            content: Conteúdo do documento
            metadata: Metadados (file_name, file_path, source_url, etc)
            chunk_size: Tamanho máximo de cada chunk
            chunk_overlap: Sobreposição entre chunks
            
        Returns:
            Número de chunks indexados
        """
        logger.info(f"Indexando documento: {metadata.get('file_name', doc_id)}")
        
        # Dividir conteúdo em chunks
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)
        logger.info(f"  Dividido em {len(chunks)} chunks")
        
        # Gerar embeddings para todos os chunks
        embeddings = self.embedding_client.encode(chunks)
        
        # Preparar points para Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_metadata = {
                **metadata,
                "chunk_index": i,
                "chunk_text": chunk,
                "doc_id": doc_id,
            }
            
            points.append(
                PointStruct(
                    id=hash(f"{doc_id}_{i}") & 0x7fffffff,  # ID positivo
                    vector=embedding,
                    payload=point_metadata,
                )
            )
        
        # Upsert points no Qdrant
        try:
            await self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(f"✅ {len(points)} chunks indexados")
            return len(points)
        except Exception as e:
            logger.error(f"❌ Erro ao indexar: {str(e)}")
            return 0
    
    async def search(
        self,
        query: str,
        top_k: int = 15,
        similarity_threshold: float = 0.5,
        filter_metadata: Optional[dict] = None,
    ) -> list[SearchResult]:
        """
        Buscar documentos por similaridade
        
        Args:
            query: Texto da query
            top_k: Número de resultados a retornar antes do re-ranking
            similarity_threshold: Threshold mínimo de similaridade
            filter_metadata: Filtros de metadados (opcional)
            
        Returns:
            Lista de SearchResult ordenados por score
        """
        logger.info(f"Buscando: {query}")
        
        # Gerar embedding da query
        query_embedding = self.embedding_client.encode_single(query)
        
        # Buscar no Qdrant (top_k documentos candidatos)
        try:
            query_response = await self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                score_threshold=similarity_threshold,
            )
            search_result = query_response.points
        except Exception as e:
            logger.error(f"❌ Erro ao buscar no Qdrant: {str(e)}")
            return []
        
        if not search_result:
            logger.info("  ⚠️ Nenhum resultado encontrado")
            return []
        
        logger.info(f"  📍 {len(search_result)} candidatos iniciais")
        
        # Converter resultados para SearchResult
        results = []
        for rank, point in enumerate(search_result):
            result = SearchResult(
                content=point.payload.get("chunk_text", ""),
                metadata={
                    k: v for k, v in point.payload.items()
                    if k not in ["chunk_text"]
                },
                score=point.score,
                rank=rank + 1,
            )
            results.append(result)
        
        return results
    
    async def search_with_reranking(
        self,
        query: str,
        top_k_initial: int = 15,
        top_k_reranked: int = 5,
        similarity_threshold: float = 0.5,
    ) -> list[SearchResult]:
        """
        Buscar com re-ranking
        
        Args:
            query: Texto da query
            top_k_initial: Candidatos iniciais da busca vetorial
            top_k_reranked: Número final de resultados após re-ranking
            similarity_threshold: Threshold de similaridade
            
        Returns:
            Lista de SearchResult re-ranked (top-k)
        """
        logger.info(f"Busca com re-ranking: {query}")
        logger.info(f"  Initial candidates: {top_k_initial}, Final: {top_k_reranked}")
        
        # Busca vetorial inicial
        candidates = await self.search(
            query=query,
            top_k=top_k_initial,
            similarity_threshold=similarity_threshold,
        )
        
        if not candidates:
            logger.info("  ⚠️ Nenhum candidato para re-ranking")
            return []
        
        # Re-ranking com CrossEncoder
        logger.info(f"  🔄 Re-ranking {len(candidates)} candidatos...")
        
        query_text_pairs = [
            [query, result.content] for result in candidates
        ]
        
        # Scores de re-ranking (0-1)
        rerank_scores = self.reranker.predict(query_text_pairs)
        
        # Atualizar scores e ordenar
        for result, score in zip(candidates, rerank_scores):
            result.score = float(score)
        
        # Ordenar por score descendente e pegar top-k
        candidates.sort(key=lambda x: x.score, reverse=True)
        reranked = candidates[:top_k_reranked]
        
        # Atualizar ranks
        for i, result in enumerate(reranked):
            result.rank = i + 1
        
        logger.info(f"  ✅ {len(reranked)} resultados após re-ranking")
        for i, r in enumerate(reranked):
            logger.debug(f"     [{i+1}] {r.metadata.get('file_name')} - score: {r.score:.3f}")
        
        return reranked
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> list[str]:
        """
        Dividir texto em chunks com sobreposição
        
        Args:
            text: Texto a dividir
            chunk_size: Tamanho máximo do chunk em caracteres
            overlap: Sobreposição entre chunks
            
        Returns:
            Lista de chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            # Definir fim do chunk
            end = min(start + chunk_size, len(text))
            
            # Se não é o último chunk, tentar quebrar em espaço/newline
            if end < len(text):
                # Procurar último espaço antes de 'end'
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space + 1
            
            chunk = text[start:end].strip()
            if chunk:  # Apenas adicionar chunks não-vazios
                chunks.append(chunk)
            
            # Mover start considerando overlap
            start = end - overlap if end < len(text) else len(text)
        
        return chunks
    
    async def close(self):
        """Fechar conexões"""
        await self.qdrant_client.close()
