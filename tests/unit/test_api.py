"""
Testes para API principal
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Fixture para cliente de teste"""
    return TestClient(app)


def test_root(client):
    """Testar endpoint raiz"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Docky"


def test_health_check(client):
    """Testar health check"""
    response = client.get("/health")
    # Pode ser 200 ou 503 dependendo dos serviços
    assert response.status_code in [200, 503]


def test_query_endpoint(client):
    """Testar endpoint de query"""
    response = client.post(
        "/query",
        json={"query": "Test query"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()
