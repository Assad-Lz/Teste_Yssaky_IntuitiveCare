from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure the backend module can be imported relative to the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Initialize the TestClient with our FastAPI app
client = TestClient(app)

def test_read_root_not_found():
    """
    Sanity Check: Ensures the app is running.
    Since we didn't define a root route ('/'), it should return 404.
    """
    response = client.get("/")
    assert response.status_code == 404

@patch("backend.main.engine.connect")
def test_list_operadoras_success(mock_connect):
    """
    Test GET /api/operadoras with MOCKED database.
    We simulate the SQL response without actually hitting PostgreSQL.
    """
    # 1. Setup the Mock Connection (Context Manager)
    # This simulates 'with engine.connect() as conn:'
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    # 2. Define the fake data we expect the DB to return
    fake_operators = [
        {"registro_ans": "123456", "razao_social": "MOCK OPERADORA 1", "cnpj": "000", "uf": "SP", "modalidade": "Medica"},
        {"registro_ans": "654321", "razao_social": "MOCK OPERADORA 2", "cnpj": "111", "uf": "RJ", "modalidade": "Odonto"}
    ]
    fake_total = 150 # Simulate that there are 150 records in total
    
    # 3. Configure the 'execute' method side effects
    # The API calls execute() twice: 
    #   1st time: Fetch data list -> returns a ResultProxy with .mappings().all()
    #   2nd time: Fetch count -> returns a ResultProxy with .scalar()
    
    # Mock for the first query (Data)
    mock_result_data = MagicMock()
    mock_result_data.mappings.return_value.all.return_value = fake_operators
    
    # Mock for the second query (Count)
    mock_result_count = MagicMock()
    mock_result_count.scalar.return_value = fake_total
    
    # Apply side_effect: First call returns data, Second call returns count
    mock_conn.execute.side_effect = [mock_result_data, mock_result_count]
    
    # 4. Run the request
    response = client.get("/api/operadoras?page=1&limit=10")
    
    # 5. Assertions
    assert response.status_code == 200
    json_resp = response.json()
    
    # Check structure
    assert "data" in json_resp
    assert "meta" in json_resp
    
    # Check content matches our fake data
    assert len(json_resp["data"]) == 2
    assert json_resp["data"][0]["razao_social"] == "MOCK OPERADORA 1"
    assert json_resp["meta"]["total"] == 150
    assert json_resp["meta"]["page"] == 1

@patch("backend.main.engine.connect")
def test_search_operadoras(mock_connect):
    """
    Test GET /api/operadoras with a search term.
    """
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    # Mock return (only 1 result found for search)
    fake_search_result = [{"registro_ans": "999999", "razao_social": "SEARCHED OPS", "cnpj": "999", "uf": "MG"}]
    
    mock_result_data = MagicMock()
    mock_result_data.mappings.return_value.all.return_value = fake_search_result
    
    mock_result_count = MagicMock()
    mock_result_count.scalar.return_value = 1
    
    mock_conn.execute.side_effect = [mock_result_data, mock_result_count]
    
    # Call with search parameter
    response = client.get("/api/operadoras?search=SEARCHED")
    
    assert response.status_code == 200
    assert response.json()["data"][0]["razao_social"] == "SEARCHED OPS"

@patch("backend.main.engine.connect")
def test_get_estatisticas_success(mock_connect):
    """
    Test GET /api/estatisticas (Analytical Query).
    """
    # 1. Setup Mock
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    # 2. Fake Aggregated Data (SUM by UF)
    fake_stats = [
        {"uf": "SP", "total": 500000.50},
        {"uf": "RJ", "total": 250000.00},
        {"uf": "MG", "total": 100000.00}
    ]
    
    # 3. Configure execute return
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = fake_stats
    mock_conn.execute.return_value = mock_result
    
    # 4. Run Request
    response = client.get("/api/estatisticas")
    
    # 5. Assertions
    assert response.status_code == 200
    json_resp = response.json()
    
    assert "despesas_por_uf" in json_resp
    assert len(json_resp["despesas_por_uf"]) == 3
    assert json_resp["despesas_por_uf"][0]["uf"] == "SP"
    assert json_resp["despesas_por_uf"][0]["total"] == 500000.50