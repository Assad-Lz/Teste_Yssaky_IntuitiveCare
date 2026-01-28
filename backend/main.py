from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import os

app = FastAPI()

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexão SQL
DB_URL = "postgresql://user_intuitive:password123@db:5432/intuitive_care"
engine = create_engine(DB_URL)

@app.get("/")
def read_root():
    return {"message": "API Intuitive Care Running (SQL Version) 🚀"}

@app.get("/api/operadoras")
def list_operadoras(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None)
):
    offset = (page - 1) * limit
    
    with engine.connect() as conn:
        # Query Dinâmica
        query_base = "SELECT * FROM operadoras"
        count_base = "SELECT COUNT(*) FROM operadoras"
        params = {"limit": limit, "offset": offset}
        
        if search:
            # Busca insensível a maiúsculas/minúsculas (ILIKE)
            filter_clause = " WHERE razao_social ILIKE :search"
            query_base += filter_clause
            count_base += filter_clause
            params["search"] = f"%{search}%"
            
        query_final = text(query_base + " ORDER BY registro_ans LIMIT :limit OFFSET :offset")
        
        # Executa
        result = conn.execute(query_final, params).mappings().all()
        total = conn.execute(text(count_base), params).scalar()
        
    return {
        "data": result,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit
        }
    }

# --- ROTA NOVA PARA DETALHES DAS DESPESAS ---
@app.get("/api/operadoras/{registro_ans}/despesas")
def get_operadora_despesas(registro_ans: str):
    """
    Busca todas as despesas vinculadas a um ID específico.
    """
    query = text("""
        SELECT * FROM despesas 
        WHERE registro_ans = :id 
        ORDER BY ano DESC, trimestre DESC
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"id": registro_ans}).mappings().all()
        
    # Retorna lista vazia se não achar nada, em vez de erro
    return result
# ---------------------------------------------

@app.get("/api/estatisticas")
def get_estatisticas():
    query = text("""
        SELECT 
            o.uf, 
            SUM(d.valor_despesa) as total 
        FROM despesas d
        JOIN operadoras o ON d.registro_ans = o.registro_ans
        GROUP BY o.uf
        ORDER BY total DESC
        LIMIT 5
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query).mappings().all()
        
    return {"despesas_por_uf": result}