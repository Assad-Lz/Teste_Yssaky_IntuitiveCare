from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Garante que o Python encontre a pasta root do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app

client = TestClient(app)

def test_read_root():
    """Valida se a rota raiz responde com 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

@patch("backend.main.engine.connect")
def test_list_operadoras(mock_connect):
    """Testa a listagem de operadoras com Mocks."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {"registro_ans": "123", "razao_social": "Teste", "uf": "SP"}
    ]
    mock_conn.execute.side_effect = [mock_result, MagicMock(scalar=lambda: 1)]

    response = client.get("/api/operadoras")
    assert response.status_code == 200
    assert response.json()["data"][0]["registro_ans"] == "123"

@patch("backend.main.engine.connect")
def test_list_operadoras_search(mock_connect):
    """Testa a busca de operadoras."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = []
    mock_conn.execute.side_effect = [mock_result, MagicMock(scalar=lambda: 0)]

    response = client.get("/api/operadoras?search=Inexistente")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 0

@patch("backend.main.engine.connect")
def test_get_despesas(mock_connect):
    """Testa a rota de despesas."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [{"valor": 100}]
    mock_conn.execute.return_value = mock_result

    response = client.get("/api/operadoras/123/despesas")
    assert response.status_code == 200
    assert len(response.json()) == 1