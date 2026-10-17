# Multi-stage build para otimizar tamanho da imagem
FROM python:3.11-slim as builder

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema necessárias para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Criar e usar diretório virtual Python
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar requirements (sera gerado pelo pyproject.toml)
WORKDIR /build
COPY pyproject.toml .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e .

# ============================================================================
# Estágio final - imagem de desenvolvimento
# ============================================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Instalar apenas dependências em runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar venv do builder
COPY --from=builder /opt/venv /opt/venv

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 docky

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY --chown=docky:docky . .

# Trocar para usuário não-root
USER docky

# Expor porta padrão
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão para iniciar a aplicação
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
