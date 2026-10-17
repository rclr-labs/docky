# Dockerfile simples e funcional para Docky
FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar arquivo de dependências
COPY pyproject.toml .

# Instalar apenas as dependências principais (sem desenvolvimento)
RUN pip install --upgrade pip setuptools wheel && \
    pip install fastapi uvicorn pydantic python-dotenv httpx \
    qdrant-client>=1.7.0 sentence-transformers python-docx PyPDF2 markdown \
    llama-index aiofiles

# Copiar código da aplicação
COPY . .

# Criar usuário não-root
RUN useradd -m -u 1000 docky && chown -R docky:docky /app
USER docky

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Iniciar aplicação
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
