# tests/test_main.py
from fastapi.testclient import TestClient
from backend.main import app

# Create a test client that simulates real requests
client = TestClient(app)

def test_health_check():
    """Checks if the API is online"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_list_operadoras_pagination():
    """Checks if pagination is returning data and metadata"""
    response = client.get("/api/operadoras?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert len(data["data"]) == 5

def test_search_operadora_success():
    """Checks if searching by text works"""
    # Search for something generic that probably exists
    response = client.get("/api/operadoras?search=SAUDE")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)

def test_get_operadora_not_found():
    """Checks if returns 404 for non-existent CNPJ"""
    response = client.get("/api/operadoras/00000000000000")
    assert response.status_code == 404

def test_statistics_structure():
    """Checks if the statistics endpoint returns the correct keys for the chart"""
    response = client.get("/api/estatisticas")
    assert response.status_code == 200
    data = response.json()
    assert "top_5_operadoras" in data
    assert "despesas_por_uf" in data