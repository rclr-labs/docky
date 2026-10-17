"""
API principal do Docky - Chatbot RAG para Documentação
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.config import settings
from api.health import health_router


# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Models para requisições/respostas
class QueryRequest(BaseModel):
    """Request model para query ao chatbot"""
    query: str
    top_k: Optional[int] = 5
    threshold: Optional[float] = 0.5


class QueryResponse(BaseModel):
    """Response model para query ao chatbot"""
    answer: str
    sources: list[dict]
    confidence: float


# Lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar inicialização e shutdown da aplicação"""
    # Startup
    logger.info("🚀 Inicializando Docky API...")
    logger.info(f"🔌 Qdrant: {settings.QDRANT_URL}")
    logger.info(f"🧠 Ollama: {settings.OLLAMA_BASE_URL}")
    logger.info(f"🎯 Modelo: {settings.OLLAMA_MODEL}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Desligando Docky API...")


# Criar aplicação FastAPI
app = FastAPI(
    title="Docky",
    description="Chatbot RAG para Documentação",
    version="0.1.0",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(health_router, tags=["Health"])


@app.post("/query", response_model=QueryResponse, tags=["Chat"])
async def query(request: QueryRequest) -> QueryResponse:
    """
    Enviar uma query ao RAG.
    
    Args:
        request: Requisição com query e parâmetros opcionais
        
    Returns:
        QueryResponse com resposta e fontes
    """
    logger.info(f"📝 Query recebida: {request.query}")
    
    try:
        # TODO: Implementar lógica de RAG
        # 1. Recuperar documentos relevantes
        # 2. Processar com LLM
        # 3. Retornar resposta e fontes
        
        # Resposta placeholder
        return QueryResponse(
            answer="Funcionalidade de RAG ainda será implementada.",
            sources=[],
            confidence=0.0
        )
    except Exception as e:
        logger.error(f"❌ Erro ao processar query: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao processar query")


@app.get("/")
async def root():
    """Root endpoint com informações da API"""
    return {
        "name": "Docky",
        "version": "0.1.0",
        "description": "Chatbot RAG para Documentação",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
