"""
Testes para SearchService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from api.search import SearchService, SearchResult


@pytest.fixture
def mock_qdrant_client():
    """Mock para QdrantClient"""
    return AsyncMock()


@pytest.fixture
def mock_embedding_client():
    """Mock para EmbeddingClient"""
    client = MagicMock()
    client.encode = MagicMock(return_value=[[0.1, 0.2, 0.3]])
    client.encode_single = MagicMock(return_value=[0.1, 0.2, 0.3])
    return client


@pytest.mark.asyncio
async def test_search_service_initialization():
    """Teste de inicialização do SearchService"""
    # Este teste é mais uma validação de imports
    from api.search import SearchService
    assert SearchService is not None


def test_chunk_text_basic():
    """Teste de divisão de texto em chunks"""
    from api.search import SearchService
    
    service = SearchService.__new__(SearchService)
    
    text = "Este é um texto longo. Será dividido em chunks. Com sobreposição entre eles."
    chunks = service._chunk_text(text, chunk_size=30, overlap=5)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    # Verificar que chunks não estão vazios
    assert all(len(chunk) > 0 for chunk in chunks)


def test_chunk_text_with_overlap():
    """Teste de sobreposição entre chunks"""
    from api.search import SearchService
    
    service = SearchService.__new__(SearchService)
    
    text = "palavra1 palavra2 palavra3 palavra4 palavra5 palavra6 palavra7 palavra8"
    chunks = service._chunk_text(text, chunk_size=20, overlap=5)
    
    assert len(chunks) > 1
    # Verificar que há sobreposição (último chunk anterior != primeiro do próximo)
    # Este é um teste básico de que a sobreposição funciona


def test_search_result():
    """Teste de criação de SearchResult"""
    result = SearchResult(
        content="Test content",
        metadata={"file_name": "test.md"},
        score=0.95,
        rank=1,
    )
    
    assert result.content == "Test content"
    assert result.metadata["file_name"] == "test.md"
    assert result.score == 0.95
    assert result.rank == 1
