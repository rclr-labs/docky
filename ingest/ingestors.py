"""
Document Ingestor: integra loaders com pipeline RAG
Carrega documentos em múltiplos formatos e indexa no Qdrant
"""
import logging
import uuid
from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass

from ingest.loader import DocumentLoaderFactory, Document

if TYPE_CHECKING:
    from api.search import SearchService


logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Resultado de uma ingestão"""
    doc_id: str
    file_name: str
    file_path: str
    format: str
    chunks_indexed: int
    total_size: int
    status: str  # "success" | "error"
    error_message: Optional[str] = None


class DocumentIngestor:
    """Ingesta documentos em múltiplos formatos para o Qdrant"""
    
    def __init__(self, search_service: "SearchService"):
        """
        Inicializar DocumentIngestor
        
        Args:
            search_service: Instância de SearchService para indexação
        """
        self.search_service = search_service
        logger.info("✅ DocumentIngestor inicializado")
    
    async def ingest(
        self,
        file_path: str,
        doc_id: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> IngestResult:
        """
        Ingestar documento único
        
        Args:
            file_path: Caminho para o arquivo
            doc_id: ID único (gerado se não fornecido)
            chunk_size: Tamanho do chunk em tokens
            chunk_overlap: Sobreposição entre chunks
            
        Returns:
            IngestResult com status da ingestão
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        logger.info(f"Ingestando: {file_path}")
        
        try:
            # Carregar documento
            doc = await DocumentLoaderFactory.load_document(file_path)
            
            if doc is None:
                error_msg = f"Formato não suportado ou arquivo inválido: {file_path}"
                logger.error(error_msg)
                return IngestResult(
                    doc_id=doc_id,
                    file_name=file_path.split("/")[-1],
                    file_path=file_path,
                    format="unknown",
                    chunks_indexed=0,
                    total_size=0,
                    status="error",
                    error_message=error_msg,
                )
            
            # Preparar metadados
            metadata = {
                "file_name": doc.metadata.file_name,
                "file_path": str(doc.metadata.file_path),
                "file_type": doc.metadata.file_type,
                "file_size": doc.metadata.file_size,
            }
            
            # Adicionar metadados específicos do formato
            if hasattr(doc.metadata, 'api_title'):
                metadata['api_title'] = doc.metadata.api_title
            if hasattr(doc.metadata, 'api_version'):
                metadata['api_version'] = doc.metadata.api_version
            if hasattr(doc.metadata, 'chunk_count'):
                metadata['loader_chunk_count'] = doc.metadata.chunk_count
            
            logger.info(f"  Documento: {doc.metadata.file_name}")
            logger.info(f"  Formato: {doc.metadata.file_type}")
            logger.info(f"  Tamanho: {doc.metadata.file_size} bytes")
            
            # Se o documento já tem chunks (Markdown, OpenAPI), tentar usar direto
            if doc.chunks and len(doc.chunks) > 1:
                logger.info(f"  Usando {len(doc.chunks)} chunks pré-processados")
                chunks_indexed = await self._index_chunks(
                    doc_id=doc_id,
                    chunks=doc.chunks,
                    metadata=metadata,
                )
                
                # Se fallback para chunking genérico caso falhe
                if chunks_indexed == 0:
                    logger.info(f"  Fallback para chunking genérico")
                    chunks_indexed = await self.search_service.index_document(
                        doc_id=doc_id,
                        content=doc.content,
                        metadata=metadata,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    )
            else:
                # Usar SearchService para chunking genérico
                logger.info(f"  Usando chunking genérico")
                chunks_indexed = await self.search_service.index_document(
                    doc_id=doc_id,
                    content=doc.content,
                    metadata=metadata,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            
            return IngestResult(
                doc_id=doc_id,
                file_name=doc.metadata.file_name,
                file_path=str(doc.metadata.file_path),
                format=doc.metadata.file_type,
                chunks_indexed=chunks_indexed,
                total_size=doc.metadata.file_size,
                status="success" if chunks_indexed > 0 else "error",
                error_message=None if chunks_indexed > 0 else "Nenhum chunk foi indexado",
            )
        
        except Exception as e:
            error_msg = f"Erro ao ingestar: {str(e)}"
            logger.error(error_msg)
            return IngestResult(
                doc_id=doc_id,
                file_name=file_path.split("/")[-1],
                file_path=file_path,
                format="unknown",
                chunks_indexed=0,
                total_size=0,
                status="error",
                error_message=error_msg,
            )
    
    async def ingest_batch(
        self,
        file_paths: List[str],
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> List[IngestResult]:
        """
        Ingestar múltiplos documentos
        
        Args:
            file_paths: Lista de caminhos de arquivos
            chunk_size: Tamanho do chunk em tokens
            chunk_overlap: Sobreposição entre chunks
            
        Returns:
            Lista de IngestResult
        """
        logger.info(f"Ingestando {len(file_paths)} documentos em batch")
        
        results = []
        total_chunks = 0
        successful = 0
        
        for file_path in file_paths:
            result = await self.ingest(
                file_path=file_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            results.append(result)
            
            if result.status == "success":
                successful += 1
                total_chunks += result.chunks_indexed
                logger.info(f"  ✅ {result.file_name} ({result.chunks_indexed} chunks)")
            else:
                logger.warning(f"  ❌ {result.file_name}: {result.error_message}")
        
        logger.info(f"\nResumo da ingestão:")
        logger.info(f"  Total: {len(file_paths)} arquivos")
        logger.info(f"  Sucesso: {successful}")
        logger.info(f"  Chunks: {total_chunks}")
        
        return results
    
    async def _index_chunks(
        self,
        doc_id: str,
        chunks: List[str],
        metadata: dict,
    ) -> int:
        """
        Indexar chunks pré-processados
        
        Args:
            doc_id: ID do documento
            chunks: Lista de chunks já processados
            metadata: Metadados do documento
            
        Returns:
            Número de chunks indexados
        """
        logger.info(f"Indexando {len(chunks)} chunks pré-processados")
        
        try:
            from qdrant_client.models import PointStruct
            
            # Gerar embeddings
            embeddings = self.search_service.embedding_client.encode(chunks)
            
            # Preparar points
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
                        id=hash(f"{doc_id}_{i}") & 0x7fffffff,
                        vector=embedding,
                        payload=point_metadata,
                    )
                )
            
            # Upsert no Qdrant
            await self.search_service.qdrant_client.upsert(
                collection_name=self.search_service.collection_name,
                points=points,
            )
            
            logger.info(f"✅ {len(points)} chunks indexados")
            return len(points)
        
        except ImportError:
            logger.error("qdrant-client não instalado - usando fallback")
            return 0
        except Exception as e:
            logger.error(f"Erro ao indexar chunks: {str(e)}")
            return 0
    
    async def ensure_ready(self) -> bool:
        """
        Garantir que sistema está pronto para ingestão
        
        Returns:
            True se tudo está configurado
        """
        logger.info("Verificando pré-requisitos...")
        
        # Verificar collection no Qdrant
        collection_ok = await self.search_service.ensure_collection()
        
        if collection_ok:
            logger.info("✅ Sistema pronto para ingestão")
            return True
        else:
            logger.error("❌ Falha ao preparar sistema")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Obter formatos suportados"""
        return DocumentLoaderFactory.get_supported_formats()
