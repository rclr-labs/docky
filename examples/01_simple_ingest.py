"""
Example 1: Carregar e ingestar um documento único
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
    
    # Garantir que a collection existe
    await search_service.ensure_collection()
    
    # Inicializar DocumentIngestor
    ingestor = DocumentIngestor(search_service)
    
    # Ingestar um documento Markdown
    result = await ingestor.ingest(
        file_path="docs/README.md",
        chunk_size=512,
        chunk_overlap=50,
    )
    
    print(f"Status: {result.status}")
    print(f"Arquivo: {result.file_name}")
    print(f"Chunks indexados: {result.chunks_indexed}")
    
    if result.status == "error":
        print(f"Erro: {result.error_message}")
    
    # Fechar conexão
    await search_service.close()


if __name__ == "__main__":
    asyncio.run(main())
