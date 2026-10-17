"""
Example 4: Ingestar múltiplos formatos
"""
import asyncio
from ingest.ingestors import DocumentIngestor
from api.search import SearchService
from api.config import settings


async def main():
    # Inicializar
    search_service = SearchService(
        qdrant_url=settings.QDRANT_URL,
        collection_name="all_documents",
    )
    await search_service.ensure_collection()
    
    ingestor = DocumentIngestor(search_service)
    
    # Mostrar formatos suportados
    formats = ingestor.get_supported_formats()
    print(f"Formatos suportados: {', '.join(formats)}")
    
    # Documentos de diferentes tipos
    documents = [
        "README.txt",              # Texto simples
        "docs/guide.md",           # Markdown
        "api/openapi.json",        # OpenAPI JSON
        "api/swagger.yaml",        # OpenAPI YAML
    ]
    
    # Ingestar
    for doc_path in documents:
        print(f"\nIngestando: {doc_path}")
        result = await ingestor.ingest(doc_path)
        
        if result.status == "success":
            print(f"  ✅ {result.chunks_indexed} chunks")
        else:
            print(f"  ❌ {result.error_message}")
    
    await search_service.close()


if __name__ == "__main__":
    asyncio.run(main())
