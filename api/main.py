"""
API principal do Docky - Chatbot RAG para Documentação
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.config import settings
from api.health import health_router
from api.search import SearchService
from api.rag import RAGService, RAGResponse
from llm.client import OllamaClient


# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Models para requisições/respostas
class QueryRequest(BaseModel):
    """Request model para query ao chatbot"""
    query: str = Field(..., description="Pergunta do usuário")
    top_k: Optional[int] = Field(default=5, description="Número de documentos a recuperar")
    threshold: Optional[float] = Field(default=0.5, description="Threshold de similaridade")


class SearchRequest(BaseModel):
    """Request model para busca vetorial"""
    query: str = Field(..., description="Texto da busca")
    top_k_initial: Optional[int] = Field(default=15, description="Candidatos iniciais")
    top_k_reranked: Optional[int] = Field(default=5, description="Resultados finais após re-ranking")
    similarity_threshold: Optional[float] = Field(default=0.5, description="Threshold de similaridade")


class SearchResultItem(BaseModel):
    """Item de resultado de busca"""
    rank: int
    file_name: str
    content: str
    score: float
    chunk_index: int


class SearchResponse(BaseModel):
    """Response model para busca"""
    query: str
    results_count: int
    results: list[SearchResultItem]
    retrieval_time_ms: Optional[float] = None


class RAGRequestModel(BaseModel):
    """Request model para RAG"""
    query: str = Field(..., description="Pergunta do usuário")
    top_k_initial: Optional[int] = Field(default=15, description="Candidatos iniciais")
    top_k_reranked: Optional[int] = Field(default=5, description="Resultados finais após re-ranking")
    similarity_threshold: Optional[float] = Field(default=0.5, description="Threshold de similaridade")
    temperature: Optional[float] = Field(default=None, description="Temperatura do LLM")


class QueryResponse(BaseModel):
    """Response model para RAG"""
    answer: str
    sources: list[dict]
    confidence: float
    retrieval_time_ms: Optional[float] = None
    generation_time_ms: Optional[float] = None


# Instâncias de serviços (inicializadas no lifespan)
search_service: Optional[SearchService] = None
rag_service: Optional[RAGService] = None
ollama_client: Optional[OllamaClient] = None


# Lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar inicialização e shutdown da aplicação"""
    global search_service, rag_service, ollama_client
    
    # Startup
    logger.info("🚀 Inicializando Docky API...")
    logger.info(f"🔌 Qdrant: {settings.QDRANT_URL}")
    logger.info(f"🧠 Ollama: {settings.OLLAMA_BASE_URL}")
    logger.info(f"🎯 Modelo: {settings.OLLAMA_MODEL}")
    
    # Inicializar serviços
    try:
        # SearchService
        search_service = SearchService(
            qdrant_url=settings.QDRANT_URL,
            qdrant_api_key=settings.QDRANT_API_KEY,
            collection_name=settings.QDRANT_COLLECTION_NAME,
        )
        
        # Garantir que a collection existe
        await search_service.ensure_collection()
        
        # OllamaClient
        ollama_client = OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.OLLAMA_TEMPERATURE,
        )
        
        # RAGService
        rag_service = RAGService(
            search_service=search_service,
            llm_client=ollama_client,
        )
        
        logger.info("✅ Todos os serviços inicializados com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar serviços: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Desligando Docky API...")
    if search_service:
        await search_service.close()
    if ollama_client:
        await ollama_client.close()


# Criar aplicação FastAPI
app = FastAPI(
    title="Docky",
    description="Chatbot RAG para Documentação",
    version="0.2.0",
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


@app.get("/")
async def root():
    """Root endpoint com informações da API"""
    return {
        "name": "Docky",
        "version": "0.2.0",
        "description": "Chatbot RAG para Documentação",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "ask": "/ask",
            "docs": "/docs",
        }
    }


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest) -> SearchResponse:
    """
    Buscar documentos com re-ranking.
    
    Args:
        request: Query e parâmetros de busca
        
    Returns:
        SearchResponse com resultados re-ranked
    """
    if not search_service:
        raise HTTPException(status_code=500, detail="SearchService não inicializado")
    
    logger.info(f"\n🔍 POST /search - Query: {request.query}")
    
    try:
        results = await search_service.search_with_reranking(
            query=request.query,
            top_k_initial=request.top_k_initial or 15,
            top_k_reranked=request.top_k_reranked or 5,
            similarity_threshold=request.similarity_threshold or 0.5,
        )
        
        if not results:
            return SearchResponse(
                query=request.query,
                results_count=0,
                results=[],
            )
        
        # Converter para response items
        result_items = [
            SearchResultItem(
                rank=r.rank,
                file_name=r.metadata.get("file_name", "unknown"),
                content=r.content,
                score=r.score,
                chunk_index=r.metadata.get("chunk_index", 0),
            )
            for r in results
        ]
        
        logger.info(f"✅ {len(result_items)} resultados retornados")
        
        return SearchResponse(
            query=request.query,
            results_count=len(result_items),
            results=result_items,
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar: {str(e)}")


@app.post("/ask", response_model=QueryResponse, tags=["RAG"])
async def ask(request: RAGRequestModel) -> QueryResponse:
    """
    Processar uma pergunta através do pipeline RAG completo.
    
    Etapas:
    1. Busca vetorial com Qdrant (top-k inicial)
    2. Re-ranking com bge-reranker-base (top-k final)
    3. Compressão extrativa do contexto
    4. Construção de prompt compacto
    5. Geração com LLM local (Phi/Qwen)
    
    Args:
        request: Pergunta e parâmetros
        
    Returns:
        QueryResponse com resposta, confiança e fontes
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="RAGService não inicializado")
    
    logger.info(f"\n📚 POST /ask - Query: {request.query}")
    
    try:
        rag_response = await rag_service.ask(
            query=request.query,
            top_k_initial=request.top_k_initial or 15,
            top_k_reranked=request.top_k_reranked or 5,
            similarity_threshold=request.similarity_threshold or 0.5,
            temperature=request.temperature,
        )
        
        return QueryResponse(
            answer=rag_response.answer,
            sources=rag_response.source_documents,
            confidence=rag_response.confidence,
            retrieval_time_ms=rag_response.retrieval_time_ms,
            generation_time_ms=rag_response.generation_time_ms,
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar query RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar query: {str(e)}")


@app.post("/query", response_model=QueryResponse, tags=["Chat (Deprecated)"])
async def query(request: QueryRequest) -> QueryResponse:
    """
    ⚠️ DEPRECATED: Use /ask em vez disso.
    
    Enviar uma query ao RAG.
    """
    logger.warning("⚠️ POST /query é deprecated, use /ask")
    
    # Redirecionar para /ask
    return await ask(
        RAGRequestModel(
            query=request.query,
            top_k_reranked=request.top_k,
            similarity_threshold=request.threshold,
        )
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
