"""
Testes para configurações
"""
from api.config import settings


def test_settings_loaded():
    """Testar se as configurações foram carregadas"""
    assert settings.API_HOST == "0.0.0.0"
    assert settings.API_PORT == 8000
    assert settings.OLLAMA_MODEL == "mistral"
    assert settings.QDRANT_COLLECTION_NAME == "docky_documents"
