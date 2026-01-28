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
    version="2.1.0"
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
        # FIX ENCODING: Try UTF-8 first (Modern ANS standard), then Latin1 fallback
        try:
            df_ops = pd.read_csv(CADASTRO_FILE, sep=';', encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            df_ops = pd.read_csv(CADASTRO_FILE, sep=';', encoding='latin1', dtype=str)
        except:
             # Fallback for comma separator
            df_ops = pd.read_csv(CADASTRO_FILE, sep=',', encoding='utf-8', dtype=str)
            
        # Normalize Column Names
        df_ops.columns = [c.upper().strip() for c in df_ops.columns]
        
        rename_map = {}
        for col in df_ops.columns:
            # FIX COLUMN MAPPING: Explicitly look for REGISTRO_OPERADORA
            if col == 'REGISTRO_OPERADORA': 
                rename_map[col] = 'RegistroANS'
            elif 'REGISTRO' in col and 'ANS' in col and 'DATA' not in col: 
                rename_map[col] = 'RegistroANS'
            elif 'CNPJ' in col: 
                rename_map[col] = 'CNPJ'
            elif 'RAZAO' in col: 
                rename_map[col] = 'RazaoSocial'
            elif 'UF' in col: 
                rename_map[col] = 'UF'
            elif 'MODALIDADE' in col:
                rename_map[col] = 'Modalidade'
            
        df_ops.rename(columns=rename_map, inplace=True)
        
        # Verify if critical column exists
        if 'RegistroANS' not in df_ops.columns:
            print(f"CRITICAL: 'RegistroANS' not found in operators. Columns: {df_ops.columns}")

        # 2. Load Expenses
        # Expenses usually come from our ETL which saves as UTF-8
        df_exp = pd.read_csv(EXPENSES_FILE, sep=';', encoding='utf-8')
        
        # Ensure ID columns are strings for matching
        if 'RegistroANS' in df_ops.columns:
            df_ops['RegistroANS'] = df_ops['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)
            
        if 'RegistroANS' in df_exp.columns:
            df_exp['RegistroANS'] = df_exp['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)

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
    
    # FIX: .fillna("") prevents JSON serialization errors
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
    # Robust CNPJ cleanup
    clean_cnpj = str(cnpj).replace('.', '').replace('/', '').replace('-', '').strip()
    
    # Ensure column is string and clean
    df_operators['CNPJ_Clean'] = df_operators['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
    
    match = df_operators[df_operators['CNPJ_Clean'] == clean_cnpj]
    
    if match.empty:
        raise HTTPException(status_code=404, detail="Operadora not found")
    
    # Return first match
    return match.iloc[0].fillna("").to_dict()

@app.get("/api/operadoras/{cnpj}/despesas")
def get_operadora_expenses(cnpj: str):
    clean_cnpj = str(cnpj).replace('.', '').replace('/', '').replace('-', '').strip()
    
    # 1. Find Operator ID
    df_operators['CNPJ_Clean'] = df_operators['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
    op_match = df_operators[df_operators['CNPJ_Clean'] == clean_cnpj]
    
    if op_match.empty:
        raise HTTPException(status_code=404, detail="Operadora not found")
        
    registro_ans = str(op_match.iloc[0]['RegistroANS'])
    
    # 2. Filter Expenses
    expenses_match = df_expenses[df_expenses['RegistroANS'] == registro_ans]
    
    # Sort by date (Ano/Trimestre) descending
    if not expenses_match.empty:
        expenses_match = expenses_match.sort_values(by=['Ano', 'Trimestre'], ascending=False)

    return expenses_match.fillna("").to_dict(orient="records")

@app.get("/api/estatisticas")
def get_statistics():
    try:
        # Group by Operator and Sum Expenses
        agg = df_expenses.groupby('RegistroANS')['ValorDespesas'].sum().reset_index()
        
        # Join to get Names and UF
        # Use inner join to ensure we only show operators that exist in both
        merged = pd.merge(agg, df_operators[['RegistroANS', 'RazaoSocial', 'UF']], on='RegistroANS', how='inner')
        
        # Top 5 Operators
        top_5 = merged.sort_values(by='ValorDespesas', ascending=False).head(5)
        
        # Expenses by UF
        by_uf = merged.groupby('UF')['ValorDespesas'].sum().reset_index().sort_values(by='ValorDespesas', ascending=False)
        
        return {
            "top_5_operadoras": top_5.fillna("").to_dict(orient="records"),
            "despesas_por_uf": by_uf.head(5).fillna("").to_dict(orient="records")
        }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {"top_5_operadoras": [], "despesas_por_uf": []}