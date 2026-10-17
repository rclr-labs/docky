#!/bin/bash

# Script para rodar Docky localmente sem Docker

echo "🚀 Docky - Setup e Execução"
echo "════════════════════════════════════════════"
echo ""

# Instalar dependências
echo "📦 Instalando dependências..."
python3 -m pip install --quiet fastapi uvicorn pydantic pydantic-settings python-dotenv httpx qdrant-client sentence-transformers markdown python-docx PyPDF2 llama-index aiofiles 2>/dev/null

echo "✅ Dependências instaladas"
echo ""

# Iniciar servidor
echo "🚀 Iniciando servidor FastAPI..."
echo "📍 Acesse: http://localhost:8000/health"
echo "📍 RAG: POST http://localhost:8000/ask"
echo ""
echo "════════════════════════════════════════════"
echo ""

# Rodar API
cd /Users/rafaelnc/apps/docky
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
