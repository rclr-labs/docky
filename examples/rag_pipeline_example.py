"""
Exemplo de uso do pipeline RAG completo
"""
import asyncio
import logging

from api.config import settings
from api.search import SearchService
from api.rag import RAGService
from llm.client import OllamaClient, EmbeddingClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Exemplo de pipeline RAG"""
    
    logger.info("🚀 Inicializando Docky RAG Pipeline")
    
    # 1. Inicializar SearchService
    search_service = SearchService(
        qdrant_url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )
    
    # Garantir que a collection existe
    await search_service.ensure_collection()
    
    # 2. Indexar um documento de exemplo
    example_doc = """
    RAG (Retrieval-Augmented Generation) é uma abordagem inovadora que combina a 
    potência de modelos de linguagem grande com a capacidade de recuperar informações 
    relevantes de um banco de dados de documentos.
    
    O pipeline funciona em três etapas:
    1. Recuperação: Buscar documentos relevantes usando similaridade vetorial
    2. Ranking: Re-ordenar documentos por relevância usando um modelo de re-ranking
    3. Geração: Usar o modelo LLM com os documentos relevantes para gerar uma resposta
    """
    
    chunks_indexed = await search_service.index_document(
        doc_id="example_rag_doc",
        content=example_doc,
        metadata={
            "file_name": "rag_guide.md",
            "file_path": "docs/rag_guide.md",
            "source_url": "https://example.com/docs/rag",
        }
    )
    logger.info(f"✅ Indexados {chunks_indexed} chunks")
    
    # 3. Inicializar OllamaClient
    ollama_client = OllamaClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.3,
    )
    
    # 4. Inicializar RAGService
    rag_service = RAGService(
        search_service=search_service,
        llm_client=ollama_client,
    )
    
    # 5. Processar uma pergunta
    queries = [
        "O que é RAG?",
        "Quais são as etapas do pipeline de RAG?",
        "Como RAG funciona?",
    ]
    
    for query in queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Query: {query}")
        logger.info('='*60)
        
        response = await rag_service.ask(
            query=query,
            top_k_initial=15,
            top_k_reranked=5,
            temperature=0.3,
        )
        
        logger.info(f"\n✅ Resposta:\n{response.answer}")
        logger.info(f"\nConfiança: {response.confidence:.1%}")
        logger.info(f"Tempo de recuperação: {response.retrieval_time_ms:.1f}ms")
        logger.info(f"Tempo de geração: {response.generation_time_ms:.1f}ms")
        
        if response.source_documents:
            logger.info(f"\nFontes ({len(response.source_documents)}):")
            for doc in response.source_documents:
                logger.info(
                    f"  [{doc['rank']}] {doc['file_name']} "
                    f"(score: {doc['relevance_score']:.3f})"
                )
    
    # 6. Cleanup
    await search_service.close()
    await ollama_client.close()
    
    logger.info("\n✅ Pipeline finalizado com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
