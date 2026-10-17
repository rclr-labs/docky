FROM python:3.11-slim

WORKDIR /app

# Copiar apenas código
COPY api ./api
COPY ingest ./ingest
COPY llm ./llm
COPY .env.example .env

# Instalar APENAS o essencial (rápido)
RUN pip install --no-cache-dir fastapi uvicorn pydantic python-dotenv httpx

# Expor porta
EXPOSE 8000

# Health check simples
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Rodar API
CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
