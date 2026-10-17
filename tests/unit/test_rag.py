"""
Testes para RAGService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from api.rag import RAGService, RAGResponse
from api.search import SearchResult


@pytest.fixture
def mock_search_service():
    """Mock para SearchService"""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_llm_client():
    """Mock para OllamaClient"""
    client = AsyncMock()
    # Mock response
    from llm.client import LLMResponse
    client.generate = AsyncMock(
        return_value=LLMResponse(
            text="This is a test response about RAG.",
            model="test-model",
            tokens_used=50,
        )
    )
    return client


@pytest.mark.asyncio
async def test_rag_service_initialization(mock_search_service, mock_llm_client):
    """Teste de inicialização do RAGService"""
    service = RAGService(
        search_service=mock_search_service,
        llm_client=mock_llm_client,
    )
    
    assert service.search_service == mock_search_service
    assert service.llm_client == mock_llm_client


def test_compress_context():
    """Teste de compressão de contexto"""
    from api.search import SearchService
    
    mock_search = MagicMock()
    mock_llm = MagicMock()
    
    service = RAGService(
        search_service=mock_search,
        llm_client=mock_llm,
        max_chunk_length=100,
    )
    
    # Criar resultados de busca
    results = [
        SearchResult(
            content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 2,
            metadata={"file_name": "doc1.md"},
            score=0.95,
            rank=1,
        ),
        SearchResult(
            content="Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            metadata={"file_name": "doc2.md"},
            score=0.85,
            rank=2,
        ),
    ]
    
    compressed = service._compress_context(results)
    
    assert isinstance(compressed, str)
    assert len(compressed) > 0
    assert "doc1.md" in compressed
    assert "doc2.md" in compressed


def test_build_prompt():
    """Teste de construção de prompt"""
    from api.search import SearchService
    
    mock_search = MagicMock()
    mock_llm = MagicMock()
    
    service = RAGService(
        search_service=mock_search,
        llm_client=mock_llm,
    )
    
    query = "What is RAG?"
    context = "[Fonte 1: doc.md]\nRAG is Retrieval-Augmented Generation."
    
    prompt = service._build_prompt(query, context)
    
    assert isinstance(prompt, str)
    assert query in prompt
    assert context in prompt
    assert "Pergunta" in prompt
    assert "Resposta" in prompt


def test_rag_response():
    """Teste de criação de RAGResponse"""
    response = RAGResponse(
        answer="This is a test answer.",
        source_documents=[
            {
                "rank": 1,
                "file_name": "test.md",
                "relevance_score": 0.95,
            }
        ],
        confidence=0.95,
        tokens_used=100,
        retrieval_time_ms=150.5,
        generation_time_ms=250.3,
    )
    
    assert response.answer == "This is a test answer."
    assert len(response.source_documents) == 1
    assert response.confidence == 0.95
    assert response.tokens_used == 100
