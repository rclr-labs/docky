#!/bin/bash

# Script para ingerir uma pasta inteira com documentos

if [ -z "$1" ]; then
  echo "Uso: ./ingest_folder.sh <pasta>"
  echo "Exemplo: ./ingest_folder.sh docs/"
  exit 1
fi

FOLDER="$1"

if [ ! -d "$FOLDER" ]; then
  echo "Erro: Pasta nao encontrada: $FOLDER"
  exit 1
fi

echo "Ingestao de pasta: $FOLDER"
echo "=================================================="
echo ""

# Contar arquivos
COUNT=$(find "$FOLDER" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) | wc -l)
echo "Documentos encontrados: $COUNT"
echo ""

# Executar ingestao em batch
python3 << 'PYTHON_EOF'
import os
from pathlib import Path
from ingest.ingestors import DocumentIngestor
from api.search import SearchService

folder = "$FOLDER"
ingestor = DocumentIngestor(SearchService())

# Mapear extensoes
ext_map = {
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml"
}

# Encontrar arquivos
files = []
for ext, doc_type in ext_map.items():
    files.extend([(str(f), doc_type) for f in Path(folder).rglob(f"*{ext}")])

if not files:
    print("Nenhum arquivo encontrado")
    exit(1)

# Ingerir em batch
print(f"Ingerindo {len(files)} documentos...")
print()

results = ingestor.ingest_batch(files)

print()
print("================================================")
print(f"OK: {len(results)} documentos ingeridos")
print("================================================")

# Resumo
for i, (file_path, doc_type) in enumerate(files, 1):
    print(f"  {i}. {file_path}")

PYTHON_EOF

echo ""
echo "Pronto! Faca uma pergunta:"
echo "curl -X POST http://localhost:8000/ask \\"
echo "  -H "Content-Type: application/json" \\"
echo "  -d '{"query": "Sua pergunta"}'"
