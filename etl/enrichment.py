"""
Project: ANS Data ETL Pipeline
Author: Yssaky Assad Luz
Module: Data Enrichment & Validation
Date: January 2026

Description: 
    This module performs Step 2 of the assessment:
    1. Downloads operator registration data (Cadastrais).
    2. Enriches financial data by joining with registration data.
    3. Validates data integrity (CNPJ, positive values).
    4. Aggregates metrics (Mean, Std Dev) for final reporting.
"""

import pandas as pd
import numpy as np
import os
import requests
import re

# --- Configuration ---
__author__ = "Yssaky [Seu Sobrenome]"

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
INPUT_FINANCIAL_CSV = "consolidado_despesas.csv"
OUTPUT_AGGREGATED = "despesas_agregadas.csv"
CADASTRO_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"

def download_cadastrais():
    print(f"[{__author__}] Downloading Operator Registry (Cadastrais)...")
    target_path = os.path.join(DATA_DIR, "Relatorio_cadop.csv")
    
    if os.path.exists(target_path):
         print(f"Registry file already exists at: {target_path}")
         return target_path

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Data Pipeline)'}
        response = requests.get(CADASTRO_URL, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(target_path, 'wb') as f:
                f.write(response.content)
            print(f"Registry file saved to: {target_path}")
            return target_path
        else:
            print(f"Failed to download registry. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Network error downloading registry: {e}")
        return None

def validate_cnpj(cnpj):
    if pd.isna(cnpj): return False
    clean_cnpj = re.sub(r'\D', '', str(cnpj))
    return len(clean_cnpj) == 14

def normalize_columns(df, source_name="Unknown"):
    """
    Robust column normalization.
    """
    print(f"DEBUG [{source_name}] Original columns: {list(df.columns)}")
    
    # 1. Clean format
    df.columns = [
        str(c).strip().upper().replace(' ', '_').replace('.', '').replace('Ç', 'C').replace('Ã', 'A') 
        for c in df.columns
    ]
    
    # 2. Map known variations
    rename_map = {}
    
    for col in df.columns:
        # CORREÇÃO: Prioriza 'REGISTRO_OPERADORA' (Nome padrão ANS)
        if col == 'REGISTRO_OPERADORA':
            rename_map[col] = 'RegistroANS'
        # Fallback seguro: Evita pegar DATA_REGISTRO_ANS
        elif 'REGISTRO' in col and 'ANS' in col and 'DATA' not in col:
            rename_map[col] = 'RegistroANS'
        elif 'CNPJ' in col:
            rename_map[col] = 'CNPJ_Cad'
        elif 'RAZAO' in col:
            rename_map[col] = 'RazaoSocial_Cad'
        elif 'MODALIDADE' in col:
            rename_map[col] = 'Modalidade'
        elif col == 'UF':
            rename_map[col] = 'UF'
            
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
        print(f"DEBUG [{source_name}] Renamed columns: {rename_map}")
    
    return df

def run_enrichment_pipeline():
    print(f"[{__author__}] Starting Step 2: Enrichment and Validation...")
    
    # 1. Load Financial Data
    fin_path = os.path.join(DATA_DIR, INPUT_FINANCIAL_CSV)
    if not os.path.exists(fin_path):
        print("CRITICAL: Consolidated financial data not found.")
        return

    df_fin = pd.read_csv(fin_path, sep=';', encoding='utf-8')
    print(f"Loaded {len(df_fin)} financial records.")

    # 2. Load Registry Data
    cad_path = download_cadastrais()
    if not cad_path: return

    try:
        df_cad = pd.read_csv(cad_path, sep=';', encoding='latin1', on_bad_lines='skip')
    except:
        df_cad = pd.read_csv(cad_path, sep=',', encoding='utf-8', on_bad_lines='skip')

    # Apply Normalization
    df_cad = normalize_columns(df_cad, source_name="Cadastro")
    
    if 'RegistroANS' not in df_cad.columns:
        print(f"CRITICAL ERROR: Could not find 'RegistroANS' column in Cadastral file. Columns: {list(df_cad.columns)}")
        return

    # Ensure keys are numeric
    df_fin['RegistroANS'] = pd.to_numeric(df_fin['RegistroANS'], errors='coerce')
    df_cad['RegistroANS'] = pd.to_numeric(df_cad['RegistroANS'], errors='coerce')

    # 3. ENRICHMENT (JOIN)
    print("Merging financial data with registry...")
    
    cols_to_use = ['RegistroANS', 'CNPJ_Cad', 'RazaoSocial_Cad', 'Modalidade', 'UF']
    cols_to_use = [c for c in cols_to_use if c in df_cad.columns]
    
    df_merged = pd.merge(df_fin, df_cad[cols_to_use], on='RegistroANS', how='left')

    # 4. VALIDATION
    print("Applying validation rules...")
    
    if 'RazaoSocial_Cad' in df_merged.columns:
        df_merged['RazaoSocial'] = df_merged['RazaoSocial_Cad'].fillna('Desconhecido')
    if 'CNPJ_Cad' in df_merged.columns:
        df_merged['CNPJ'] = df_merged['CNPJ_Cad'].fillna('00000000000000')
    
    df_merged['CNPJ_Valido'] = df_merged['CNPJ'].apply(validate_cnpj)
    
    # Filter Positive Expenses
    df_clean = df_merged[df_merged['ValorDespesas'] > 0].copy()
    
    # 5. AGGREGATION
    print("Calculating statistics...")
    
    agg_rules = {'ValorDespesas': ['sum', 'mean', 'std', 'count']}
    
    df_grouped = df_clean.groupby(['RazaoSocial', 'UF']).agg(agg_rules).reset_index()
    
    df_grouped.columns = ['RazaoSocial', 'UF', 'Despesa_Total', 'Despesa_Media_Trimestral', 'Despesa_Desvio_Padrao', 'Qtd_Registros']
    df_grouped['Despesa_Desvio_Padrao'] = df_grouped['Despesa_Desvio_Padrao'].fillna(0)
    
    df_grouped.sort_values(by='Despesa_Total', ascending=False, inplace=True)
    
    # 6. SAVE
    output_path = os.path.join(DATA_DIR, OUTPUT_AGGREGATED)
    df_grouped.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"Success! Aggregated data saved to: {output_path}")

if __name__ == "__main__":
    run_enrichment_pipeline()