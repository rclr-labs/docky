#!/bin/bash
echo "Docky - Ingestao de Documentos"
FILE="$1"
if [ -z "$FILE" ]; then
  echo "Uso: ./ingest.sh <arquivo>"
  exit 1
fi
python3 << 'PYTHON_EOF'
import asyncio
from ingest.ingestors import DocumentIngestor
from api.search import SearchService

async def main():
    search = SearchService()
    ingestor = DocumentIngestor(search)
    doc_id = ingestor.ingest("$FILE", "markdown")
    print(f"OK: {doc_id}")

asyncio.run(main())
PYTHON_EOF
