"""
Example 2: Ingestar múltiplos documentos em batch
"""
import asyncio
from pathlib import Path
from ingest.ingestors import DocumentIngestor
from api.search import SearchService
from api.config import settings


async def main():
    # Inicializar SearchService
    search_service = SearchService(
        qdrant_url=settings.QDRANT_URL,
        collection_name="documentation",
    )
    
    # Garantir que a collection existe
    await search_service.ensure_collection()
    
    # Inicializar DocumentIngestor
    ingestor = DocumentIngestor(search_service)
    
    # Encontrar todos os documentos em um diretório
    docs_dir = Path("docs")
    file_paths = list(docs_dir.glob("**/*.md")) + list(docs_dir.glob("**/*.json"))
    
    print(f"Encontrados {len(file_paths)} documentos")
    
    # Ingestar em batch
    results = await ingestor.ingest_batch(
        file_paths=[str(f) for f in file_paths],
        chunk_size=512,
        chunk_overlap=50,
    )
    
    # Resumo
    successful = sum(1 for r in results if r.status == "success")
    total_chunks = sum(r.chunks_indexed for r in results)
    
    print(f"\nResumo da ingestão:")
    print(f"  Sucesso: {successful}/{len(results)}")
    print(f"  Total de chunks: {total_chunks}")
    
    # Detalher falhas
    failures = [r for r in results if r.status == "error"]
    if failures:
        print(f"\nFalhas:")
        for r in failures:
            print(f"  - {r.file_name}: {r.error_message}")
    
    # Fechar conexão
    await search_service.close()


if __name__ == "__main__":
    asyncio.run(main())
