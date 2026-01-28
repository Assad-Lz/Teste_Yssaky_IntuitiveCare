"""
Project: Intuitive Care Technical Assessment
Module: Backend API
Author: Yssaky Assad Luz
Description: RESTful API built with FastAPI. Serves operator data and expense metrics
             using the generated CSV files as a lightweight data source.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

# --- Configuration ---
app = FastAPI(
    title="Intuitive Care Assessment API",
    description="API to query Operator Expenses and Metrics",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
CADASTRO_FILE = os.path.join(DATA_DIR, 'Relatorio_cadop.csv')
EXPENSES_FILE = os.path.join(DATA_DIR, 'consolidado_despesas.csv')

print("Loading datasets into memory...")

def load_data():
    """Helper to load and normalize CSV data"""
    try:
        # 1. Load Operators
        try:
            df_ops = pd.read_csv(CADASTRO_FILE, sep=';', encoding='latin1', dtype=str)
        except:
            df_ops = pd.read_csv(CADASTRO_FILE, sep=',', encoding='utf-8', dtype=str)
            
        # Normalize Column Names
        df_ops.columns = [c.upper().strip() for c in df_ops.columns]
        
        rename_map = {}
        for col in df_ops.columns:
            if 'CNPJ' in col: rename_map[col] = 'CNPJ'
            elif 'RAZAO' in col: rename_map[col] = 'RazaoSocial'
            elif 'REGISTRO' in col and 'ANS' in col and 'DATA' not in col: rename_map[col] = 'RegistroANS'
            elif 'UF' in col: rename_map[col] = 'UF'
            
        df_ops.rename(columns=rename_map, inplace=True)
        
        # 2. Load Expenses
        df_exp = pd.read_csv(EXPENSES_FILE, sep=';', encoding='utf-8')
        
        return df_ops, df_exp
    
    except Exception as e:
        print(f"CRITICAL: Error loading data. Ensure ETL has run. Details: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Global Dataframes
df_operators, df_expenses = load_data()

# --- Routes ---

@app.get("/")
def health_check():
    return {"status": "online", "operators_loaded": len(df_operators)}

@app.get("/api/operadoras")
def list_operadoras(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search by Razao Social")
):
    filtered_df = df_operators.copy()
    
    if search:
        mask = filtered_df['RazaoSocial'].str.contains(search, case=False, na=False)
        filtered_df = filtered_df[mask]

    total = len(filtered_df)
    start = (page - 1) * limit
    end = start + limit
    
    subset = filtered_df.iloc[start:end]
    
    # FIX: .fillna("") prevents JSON serialization errors with NaN values
    data = subset.fillna("").to_dict(orient="records")
    
    return {
        "data": data,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    }

@app.get("/api/operadoras/{cnpj}")
def get_operadora_details(cnpj: str):
    clean_cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '')
    
    # Robust search removing punctuation from DF column on the fly
    match = df_operators[df_operators['CNPJ'].str.replace(r'\D', '', regex=True) == clean_cnpj]
    
    if match.empty:
        raise HTTPException(status_code=404, detail="Operadora not found")
    
    # FIX: .fillna("")
    return match.iloc[0].fillna("").to_dict()

@app.get("/api/operadoras/{cnpj}/despesas")
def get_operadora_expenses(cnpj: str):
    clean_cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '')
    op_match = df_operators[df_operators['CNPJ'].str.replace(r'\D', '', regex=True) == clean_cnpj]
    
    if op_match.empty:
        raise HTTPException(status_code=404, detail="Operadora not found")
        
    registro_ans = str(op_match.iloc[0]['RegistroANS'])
    
    expenses_match = df_expenses[df_expenses['RegistroANS'].astype(str) == registro_ans]
    
    # FIX: .fillna("")
    return expenses_match.fillna("").to_dict(orient="records")

@app.get("/api/estatisticas")
def get_statistics():
    # Ensure types match
    df_expenses['RegistroANS'] = df_expenses['RegistroANS'].astype(str)
    df_operators['RegistroANS'] = df_operators['RegistroANS'].astype(str)
    
    # Aggregate
    agg = df_expenses.groupby('RegistroANS')['ValorDespesas'].sum().reset_index()
    merged = pd.merge(agg, df_operators[['RegistroANS', 'RazaoSocial', 'UF']], on='RegistroANS', how='left')
    
    top_5 = merged.sort_values(by='ValorDespesas', ascending=False).head(5)
    by_uf = merged.groupby('UF')['ValorDespesas'].sum().reset_index().sort_values(by='ValorDespesas', ascending=False)
    
    # FIX: .fillna("")
    return {
        "top_5_operadoras": top_5.fillna("").to_dict(orient="records"),
        "despesas_por_uf": by_uf.fillna("").to_dict(orient="records")
    }