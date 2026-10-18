#!/bin/bash
# Valida a ingestão do Docky rodando dentro do container da API.
# Uso: ./validate.sh [--ask] [--top-k N] [--cases caminho.yml]
cd "$(dirname "$0")/.." 2>/dev/null || true
exec docker exec -i docky-api-1 python3 /app/scripts/validate_ingestion.py "$@"
