#!/bin/bash

if [ -z "$1" ]; then
  echo "Uso: ./ingest_folder.sh <pasta>"
  exit 1
fi

FOLDER="$1"

if [ ! -d "$FOLDER" ]; then
  echo "Erro: Pasta nao encontrada: $FOLDER"
  exit 1
fi

echo "Ingestao de pasta: $FOLDER"
echo "=================================================="

python3 << 'PYTHON_EOF'
import os
import sys
from pathlib import Path
from ingest.ingestors import DocumentIngestor
from api.search import SearchService

folder = "$FOLDER"
ingestor = DocumentIngestor(SearchService())

ext_map = {
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml"
}

files = []
for ext, doc_type in ext_map.items():
    for f in Path(folder).rglob(f"*{ext}"):
        if f.is_file():
            files.append((str(f), doc_type))

if not files:
    print("Nenhum arquivo encontrado")
    sys.exit(1)

print(f"\nIngerindo {len(files)} documentos...")
print()

try:
    results = ingestor.ingest_batch(files)
    print()
    print("================================================")
    print(f"OK: {len(results)} documentos ingeridos!")
    print("================================================")
    print()
    for i, (file_path, doc_type) in enumerate(files, 1):
        print(f"  {i}. {file_path}")
    print()
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()

PYTHON_EOF

