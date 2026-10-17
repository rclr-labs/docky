"""
Example 3: Ingestar e depois buscar documentos
"""
import asyncio
from ingest.ingestors import DocumentIngestor
from api.search import SearchService
from api.config import settings


async def main():
    # Inicializar SearchService
    search_service = SearchService(
        qdrant_url=settings.QDRANT_URL,
        collection_name="documents",
    )
    
    # Garantir collection
    await search_service.ensure_collection()
    
    # Ingestar documento
    ingestor = DocumentIngestor(search_service)
    result = await ingestor.ingest("docs/guide.md")
    
    if result.status != "success":
        print(f"Erro ao ingestar: {result.error_message}")
        return
    
    print(f"✅ Ingestado: {result.file_name}")
    print(f"   Chunks: {result.chunks_indexed}")
    
    # Buscar informações relacionadas
    query = "Como usar o sistema?"
    
    print(f"\nBuscando: {query}")
    results = await search_service.search_with_reranking(
        query=query,
        top_k_initial=10,
        top_k_reranked=3,
    )
    
    # Mostrar resultados
    print(f"\nResultados ({len(results)}):")
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] Score: {result.score:.3f}")
        print(f"    Arquivo: {result.metadata.get('file_name')}")
        print(f"    Preview: {result.content[:200]}...")
    
    # Fechar
    await search_service.close()


if __name__ == "__main__":
    asyncio.run(main())
