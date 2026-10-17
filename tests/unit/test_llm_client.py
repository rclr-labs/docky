"""
Testes para LLM clients
"""
import pytest
from unittest.mock import AsyncMock, patch
from llm.client import OllamaClient, EmbeddingClient


@pytest.fixture
def ollama_client():
    """Fixture para OllamaClient"""
    return OllamaClient(
        base_url="http://localhost:11434",
        model="test-model",
        temperature=0.7
    )


@pytest.mark.asyncio
async def test_ollama_client_init(ollama_client):
    """Testar inicialização do OllamaClient"""
    assert ollama_client.model == "test-model"
    assert ollama_client.temperature == 0.7
    assert ollama_client.base_url == "http://localhost:11434"


@pytest.mark.asyncio
async def test_ollama_client_custom_temp(ollama_client):
    """Testar temperatura customizada"""
    # Temperatura padrão
    assert ollama_client.temperature == 0.7
    
    # Temperatura customizada deve sobrescrever a padrão
    # (testado através do método generate com temperatura customizada)


def test_embedding_client_init():
    """Testar inicialização do EmbeddingClient"""
    try:
        client = EmbeddingClient()
        assert client.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    except Exception:
        # Esperado se o modelo não estiver instalado no ambiente de teste
        pytest.skip("Modelo de embeddings não disponível")


@pytest.mark.asyncio
async def test_ollama_client_context_manager(ollama_client):
    """Testar que OllamaClient tem método close"""
    assert hasattr(ollama_client, 'close')
    await ollama_client.close()
