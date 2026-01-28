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
    version="2.2.0"
)

# Enable CORS (Cross-Origin Resource Sharing)
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
    """
    Helper to load and normalize CSV data with Robust Encoding strategies.
    Handles 'Mojibake' (bad encoding) by trying UTF-8 first, then Latin-1.
    """
    
    # --- 1. Load Operators (Cadastro) ---
    try:
        try:
            # First try: Modern UTF-8 (Standard for current Data Pipelines)
            df_ops = pd.read_csv(CADASTRO_FILE, sep=';', encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            # Fallback: Latin-1 (Common in older government legacy files)
            df_ops = pd.read_csv(CADASTRO_FILE, sep=';', encoding='latin1', dtype=str)
        except Exception:
            # Last resort fallback
            df_ops = pd.read_csv(CADASTRO_FILE, sep=',', encoding='utf-8', dtype=str)
            
        # Normalize Column Names (Upper case and stripped)
        df_ops.columns = [c.upper().strip() for c in df_ops.columns]
        
        rename_map = {}
        for col in df_ops.columns:
            if col == 'REGISTRO_OPERADORA': rename_map[col] = 'RegistroANS'
            elif 'REGISTRO' in col and 'ANS' in col and 'DATA' not in col: rename_map[col] = 'RegistroANS'
            elif 'CNPJ' in col: rename_map[col] = 'CNPJ'
            elif 'RAZAO' in col: rename_map[col] = 'RazaoSocial'
            elif 'UF' in col: rename_map[col] = 'UF'
            elif 'MODALIDADE' in col: rename_map[col] = 'Modalidade'
            
        df_ops.rename(columns=rename_map, inplace=True)
    except Exception as e:
        print(f"CRITICAL: Error loading Operators. Details: {e}")
        df_ops = pd.DataFrame()

    # --- 2. Load Expenses (Despesas) ---
    try:
        try:
            # Try UTF-8 first (Our ETL output format)
            # low_memory=False prevents DtypeWarning on mixed types columns
            df_exp = pd.read_csv(EXPENSES_FILE, sep=';', encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            print("Warning: Expenses file is not UTF-8. Falling back to Latin-1.")
            df_exp = pd.read_csv(EXPENSES_FILE, sep=';', encoding='latin1', low_memory=False)
            
    except Exception as e:
        print(f"CRITICAL: Error loading Expenses. Ensure ETL has run. Details: {e}")
        df_exp = pd.DataFrame()

    # --- Data Cleaning & Joining Prep ---
    # Ensure Join Keys are strings and clean of floating point artifacts (e.g. "12345.0" -> "12345")
    if not df_ops.empty and 'RegistroANS' in df_ops.columns:
        df_ops['RegistroANS'] = df_ops['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)
        
    if not df_exp.empty and 'RegistroANS' in df_exp.columns:
        df_exp['RegistroANS'] = df_exp['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)

    return df_ops, df_exp

# Initialize Global Dataframes
df_operators, df_expenses = load_data()

# --- Routes ---

@app.get("/")
def health_check():
    """Simple health check to verify API is running and data is loaded."""
    return {
        "status": "online", 
        "operators_loaded": len(df_operators), 
        "expenses_loaded": len(df_expenses)
    }

@app.get("/api/operadoras")
def list_operadoras(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search by Razao Social")
):
    """
    Lists all operators with pagination and optional text search.
    """
    filtered_df = df_operators.copy()
    
    if search:
        # Case-insensitive search
        mask = filtered_df['RazaoSocial'].str.contains(search, case=False, na=False)
        filtered_df = filtered_df[mask]

    # Pagination Logic
    total = len(filtered_df)
    start = (page - 1) * limit
    end = start + limit
    
    subset = filtered_df.iloc[start:end]
    
    # Return formatted JSON (fillna handles NaN values safely)
    return {
        "data": subset.fillna("").to_dict(orient="records"),
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    }

@app.get("/api/operadoras/{cnpj}")
def get_operadora_details(cnpj: str):
    """
    Returns registration details for a specific operator by CNPJ.
    """
    # Clean up input CNPJ (remove . / -)
    clean_cnpj = str(cnpj).replace('.', '').replace('/', '').replace('-', '').strip()
    
    # Create temp column for matching
    df_operators['CNPJ_Clean'] = df_operators['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
    
    match = df_operators[df_operators['CNPJ_Clean'] == clean_cnpj]
    
    if match.empty:
        raise HTTPException(status_code=404, detail="Operadora not found")
    
    return match.iloc[0].fillna("").to_dict()

@app.get("/api/operadoras/{cnpj}/despesas")
def get_operadora_expenses(cnpj: str):
    """
    Returns historical expenses for a specific operator.
    Joins Operators and Expenses via RegistroANS.
    """
    clean_cnpj = str(cnpj).replace('.', '').replace('/', '').replace('-', '').strip()
    
    # 1. Find Operator ID (RegistroANS)
    df_operators['CNPJ_Clean'] = df_operators['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
    op_match = df_operators[df_operators['CNPJ_Clean'] == clean_cnpj]
    
    if op_match.empty:
        raise HTTPException(status_code=404, detail="Operadora not found")
        
    registro_ans = str(op_match.iloc[0]['RegistroANS'])
    
    # 2. Filter Expenses by this ID
    expenses_match = df_expenses[df_expenses['RegistroANS'] == registro_ans]
    
    # Sort by date (Year/Quarter) descending
    if not expenses_match.empty:
        expenses_match = expenses_match.sort_values(by=['Ano', 'Trimestre'], ascending=False)

    return expenses_match.fillna("").to_dict(orient="records")

@app.get("/api/estatisticas")
def get_statistics():
    """
    Returns aggregated statistics for the Dashboard chart.
    """
    try:
        # Group by Operator and Sum Expenses
        agg = df_expenses.groupby('RegistroANS')['ValorDespesas'].sum().reset_index()
        
        # Inner join to ensure we only count operators that exist in both tables
        merged = pd.merge(agg, df_operators[['RegistroANS', 'RazaoSocial', 'UF']], on='RegistroANS', how='inner')
        
        # Top 5 Operators by Expense
        top_5 = merged.sort_values(by='ValorDespesas', ascending=False).head(5)
        
        # Total Expenses by State (UF) - Used for Chart
        by_uf = merged.groupby('UF')['ValorDespesas'].sum().reset_index().sort_values(by='ValorDespesas', ascending=False)
        
        return {
            "top_5_operadoras": top_5.fillna("").to_dict(orient="records"),
            "despesas_por_uf": by_uf.head(5).fillna("").to_dict(orient="records")
        }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {"top_5_operadoras": [], "despesas_por_uf": []}