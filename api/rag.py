"""
Serviço RAG completo: busca → re-rank → compress → prompt → LLM
"""
import logging
from typing import Optional

from api.search import SearchService, SearchResult
from llm.client import OllamaClient


logger = logging.getLogger(__name__)


class RAGResponse:
    """Resposta do pipeline RAG"""
    
    def __init__(
        self,
        answer: str,
        source_documents: list[dict],
        confidence: float,
        tokens_used: Optional[int] = None,
        retrieval_time_ms: Optional[float] = None,
        generation_time_ms: Optional[float] = None,
    ):
        self.answer = answer
        self.source_documents = source_documents
        self.confidence = confidence
        self.tokens_used = tokens_used
        self.retrieval_time_ms = retrieval_time_ms
        self.generation_time_ms = generation_time_ms


class RAGService:
    """Serviço RAG completo"""
    
    def __init__(
        self,
        search_service: SearchService,
        llm_client: OllamaClient,
        max_chunk_length: int = 300,
        max_context_tokens: int = 2000,
    ):
        """
        Inicializar RAGService
        
        Args:
            search_service: Instância de SearchService
            llm_client: Instância de OllamaClient
            max_chunk_length: Tamanho máximo de chunk na resposta
            max_context_tokens: Limite de tokens do contexto
        """
        self.search_service = search_service
        self.llm_client = llm_client
        self.max_chunk_length = max_chunk_length
        self.max_context_tokens = max_context_tokens
        
        logger.info("✅ RAGService inicializado")
    
    async def ask(
        self,
        query: str,
        top_k_initial: int = 15,
        top_k_reranked: int = 5,
        similarity_threshold: float = 0.5,
        temperature: Optional[float] = None,
    ) -> RAGResponse:
        """
        Processar uma pergunta através do pipeline RAG completo
        
        Args:
            query: Pergunta do usuário
            top_k_initial: Candidatos iniciais da busca vetorial
            top_k_reranked: Número final após re-ranking
            similarity_threshold: Threshold de similaridade
            temperature: Temperatura do LLM
            
        Returns:
            RAGResponse com resposta e metadados
        """
        import time
        
        logger.info(f"\n🔍 Query: {query}")
        logger.info(f"   Top-k: {top_k_initial} → {top_k_reranked}")
        
        retrieval_start = time.time()
        
        # 1. BUSCA VETORIAL + RE-RANKING
        logger.info("\n📍 Etapa 1: Busca Vetorial + Re-ranking")
        search_results = await self.search_service.search_with_reranking(
            query=query,
            top_k_initial=top_k_initial,
            top_k_reranked=top_k_reranked,
            similarity_threshold=similarity_threshold,
        )
        
        if not search_results:
            logger.warning("⚠️  Nenhum documento relevante encontrado")
            return RAGResponse(
                answer="Desculpe, não consegui encontrar informações relevantes sobre isso na documentação.",
                source_documents=[],
                confidence=0.0,
                retrieval_time_ms=(time.time() - retrieval_start) * 1000,
            )
        
        retrieval_time = (time.time() - retrieval_start) * 1000
        logger.info(f"   ✅ {len(search_results)} documentos relevantes (tempo: {retrieval_time:.1f}ms)")
        
        # 2. COMPRESSÃO EXTRATIVA
        logger.info("\n🗜️  Etapa 2: Compressão Extrativa")
        compressed_context = self._compress_context(search_results)
        
        # Estimativa de tokens (aproximado: 1 token ≈ 4 caracteres)
        context_tokens = len(compressed_context) // 4
        logger.info(f"   Context: {len(compressed_context)} chars (~{context_tokens} tokens)")
        
        # 3. CONSTRUIR PROMPT
        logger.info("\n📝 Etapa 3: Construção de Prompt")
        prompt = self._build_prompt(query, compressed_context)
        logger.info(f"   Prompt size: {len(prompt)} chars (~{len(prompt)//4} tokens)")
        
        # 4. GERAR RESPOSTA COM LLM
        logger.info("\n🧠 Etapa 4: Geração com LLM")
        generation_start = time.time()
        
        try:
            llm_response = await self.llm_client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=512,
            )
            answer = llm_response.text.strip()
            generation_time = (time.time() - generation_start) * 1000
            
            logger.info(f"   ✅ Resposta gerada (tempo: {generation_time:.1f}ms)")
            logger.info(f"   Resposta: {answer[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta: {str(e)}")
            return RAGResponse(
                answer="Desculpe, ocorreu um erro ao gerar a resposta.",
                source_documents=[],
                confidence=0.0,
                retrieval_time_ms=retrieval_time,
            )
        
        # 5. PREPARAR RESPOSTA FINAL
        logger.info("\n✅ Etapa 5: Preparação de Resposta")
        source_docs = [
            {
                "rank": r.rank,
                "file_name": r.metadata.get("file_name", "unknown"),
                "file_path": r.metadata.get("file_path", ""),
                "chunk_index": r.metadata.get("chunk_index", 0),
                "relevance_score": round(r.score, 3),
                "preview": r.content[:100] + "..." if len(r.content) > 100 else r.content,
            }
            for r in search_results
        ]
        
        # Calcular confiança baseado nos scores de re-ranking
        confidence = float(search_results[0].score) if search_results else 0.0
        
        logger.info(f"   Confiança: {confidence:.1%}")
        logger.info(f"   Fontes: {len(source_docs)} documentos")
        
        return RAGResponse(
            answer=answer,
            source_documents=source_docs,
            confidence=confidence,
            tokens_used=None,  # Será preenchido pelo LLM se disponível
            retrieval_time_ms=retrieval_time,
            generation_time_ms=generation_time,
        )
    
    def _compress_context(self, search_results: list[SearchResult]) -> str:
        """
        Comprimir contexto extraindo trechos mais relevantes
        
        Args:
            search_results: Lista de resultados de busca
            
        Returns:
            Contexto comprimido em formato estruturado
        """
        context_parts = []
        total_tokens = 0
        
        for i, result in enumerate(search_results):
            # Extrair trecho relevante (limitado)
            chunk = result.content
            if len(chunk) > self.max_chunk_length:
                # Tentar encontrar limite de parágrafo
                truncated = chunk[:self.max_chunk_length]
                last_period = truncated.rfind(".")
                if last_period > self.max_chunk_length * 0.7:
                    chunk = truncated[:last_period + 1]
                else:
                    chunk = truncated + "..."
            
            # Adicionar com metadados
            source_line = f"[Fonte {i+1}: {result.metadata.get('file_name', 'doc')}]"
            context_parts.append(f"{source_line}\n{chunk}\n")
            
            total_tokens += len(chunk) // 4
            
            # Parar se exceder limite de tokens
            if total_tokens > self.max_context_tokens:
                logger.warning(f"⚠️  Contexto truncado em {len(context_parts)} chunks para respeitar limite de tokens")
                break
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """
        Construir prompt compacto com query e contexto
        
        Args:
            query: Pergunta do usuário
            context: Contexto recuperado
            
        Returns:
            Prompt formatado
        """
        prompt = f"""Responda a pergunta com base na documentação fornecida.

## Pergunta
{query}

## Documentação
{context}

## Resposta
Forneça uma resposta concisa e relevante baseada na documentação acima. Se a resposta não estiver na documentação, diga que não encontrou as informações."""
        
        return prompt
