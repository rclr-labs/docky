"""
Configurações da aplicação Docky
"""
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação baseadas em variáveis de ambiente"""
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_SECRET_KEY: str = "your-secret-key-change-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "docky_documents"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_TEMPERATURE: float = 0.7
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_DEVICE: str = "cpu"
    
    # Ingest
    INGEST_SOURCE_DIR: str = "./data/raw"
    INGEST_PROCESSED_DIR: str = "./data/processed"
    INGEST_FILE_EXTENSIONS: list[str] = [".pdf", ".docx", ".md", ".txt"]
    INGEST_MAX_FILE_SIZE_MB: int = 50
    
    # Retrieval/RAG
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.5
    ENABLE_RERANKING: bool = True
    
    # Cache
    ENABLE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600
    
    # Database
    DATABASE_URL: str = "sqlite:///./docky.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global de configurações
settings = Settings()
