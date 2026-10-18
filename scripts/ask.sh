#!/bin/bash
# Pergunte ao Docky: ./ask.sh "sua pergunta"  (sem pergunta = modo interativo)
cd "$(dirname "$0")/.." 2>/dev/null || true
exec docker exec -i docky-api-1 python3 /app/scripts/ask.py "$@"
