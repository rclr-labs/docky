FROM python:3.11-slim

WORKDIR /app

# Instalar TODAS as dependências
RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings python-dotenv httpx qdrant-client sentence-transformers markdown python-docx python-pptx PyPDF2 llama-index aiofiles

# Copiar código
COPY api ./api
COPY ingest ./ingest
COPY llm ./llm
COPY .env.example .env

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

