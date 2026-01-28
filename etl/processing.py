"""
Project: ANS Data ETL Pipeline
Author: Yssaky Assad Luz
Module: Data Processing & Consolidation
Description: 
    Reads raw CSV files, filters for 'Despesas com Eventos/Sinistros',
    standardizes columns, handles inconsistencies, and generates the final 
    consolidated dataset.
"""

import pandas as pd
import os
import glob
import zipfile

# --- Configuration ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_CSV = "consolidado_despesas.csv"
OUTPUT_ZIP = "consolidado_despesas.zip"

def standardize_columns(df):
    """
    Maps varying column names from ANS files to a standard schema.
    ANS files often change column headers (e.g., 'CD_OPERADORA' vs 'REG_ANS').
    """
    # Map common variations to our target names
    # Target structure: REG_ANS, Data, Descricao, Valor
    column_map = {
        'CD_OPERADORA': 'RegistroANS',
        'REG_ANS': 'RegistroANS',
        'DATA': 'Data',
        'DT_REFERENCIA': 'Data',
        'CD_CONTA_CONTABIL': 'CodigoConta',
        'DESCRICAO': 'Descricao',
        'VL_SALDO_FINAL': 'ValorDespesas',
        'VL_SALDO_INICIAL': 'ValorInicial' # Optional, kept for context
    }
    
    # Normalize current dataframe columns to uppercase for matching
    df.columns = [c.upper().strip() for c in df.columns]
    
    # Rename using the map
    df.rename(columns=column_map, inplace=True)
    return df

def process_data():
    print(f"[{__author__}] Starting ETL Process - Transformation Phase...")
    
    # 1. List all CSV files in the data directory
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    if not csv_files:
        print("CRITICAL: No CSV files found in /data. Run extraction first.")
        return

    all_data = []

    for file_path in csv_files:
        print(f"Reading file: {os.path.basename(file_path)}")
        
        try:
            # Trade-off: Using 'latin1' encoding and ';' separator 
            # standard for Brazilian government open data.
            # 'thousands' parameter handles '1.000,00' formatting if needed, 
            # but usually ANS uses ',' as decimal.
            df = pd.read_csv(
                file_path, 
                sep=';', 
                encoding='latin1', 
                decimal=',',
                on_bad_lines='skip' # Robustness: skip corrupted lines
            )
            
            # Standardize column names
            df = standardize_columns(df)
            
            # 2. FILTERING STRATEGY (The "Intelligent" part) 
            # We need "Despesas com Eventos/Sinistros". 
            # Usually Account Group 4 in accounting plans (4.1.1...)
            # We filter by Description containing specific keywords.
            
            # Ensure 'Descricao' exists before filtering
            if 'Descricao' in df.columns:
                # Filter for "EVENTOS" or "SINISTROS" (Case insensitive)
                mask = df['Descricao'].str.contains('EVENTOS|SINISTRO', case=False, na=False)
                df_filtered = df[mask].copy()
                
                # If file had data, extract Quarter/Year from filename or Date column
                if not df_filtered.empty:
                    # Enriching with Year/Quarter (Assuming file name has 1T2025 format or similar)
                    filename = os.path.basename(file_path)
                    
                    # Basic extraction logic (Robustness for 2025 files)
                    if '2025' in filename:
                        df_filtered['Ano'] = 2025
                    else:
                        df_filtered['Ano'] = 2023 # Fallback
                        
                    # Derive 'Trimestre' from filename if possible
                    if '1T' in filename: df_filtered['Trimestre'] = '1T'
                    elif '2T' in filename: df_filtered['Trimestre'] = '2T'
                    elif '3T' in filename: df_filtered['Trimestre'] = '3T'
                    elif '4T' in filename: df_filtered['Trimestre'] = '4T'
                    else: df_filtered['Trimestre'] = 'UNK'

                    all_data.append(df_filtered)
            else:
                print(f"WARNING: File {file_path} lacks 'Descricao' column. Skipping.")

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # 3. CONSOLIDATION [cite: 41]
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        
        # 4. INCONSISTENCY HANDLING [cite: 43]
        print("Handling inconsistencies...")
        
        # A. Remove duplicates
        initial_count = len(full_df)
        full_df.drop_duplicates(inplace=True)
        print(f"Removed {initial_count - len(full_df)} duplicates.")
        
        # B. Handle Negative/Zero Values [cite: 48]
        # Strategy: Accounting usually has negatives for reversals. We keep them but flag if needed.
        # Requirement says "Document how you treated". We filter out exact zeros as they add no value.
        full_df = full_df[full_df['ValorDespesas'] != 0]
        
        # C. Missing CNPJ/Razao Social check
        # As expected, these files likely only have 'RegistroANS'.
        # We will add placeholders to match the requested output format.
        if 'CNPJ' not in full_df.columns:
            full_df['CNPJ'] = 'Unavailable (See Step 2.2)' 
        if 'RazaoSocial' not in full_df.columns:
            full_df['RazaoSocial'] = 'Unavailable (See Step 2.2)'

        # Select final columns as requested 
        # Note: We prioritize RegistroANS as the real ID available
        final_columns = ['RegistroANS', 'CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas', 'Descricao']
        
        # Keep only available columns from the list
        cols_to_keep = [c for c in final_columns if c in full_df.columns]
        full_df = full_df[cols_to_keep]

        # 5. SAVE & COMPRESS 
        output_path = os.path.join(DATA_DIR, OUTPUT_CSV)
        full_df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
        print(f"Consolidated CSV saved to: {output_path}")

        zip_path = os.path.join(DATA_DIR, OUTPUT_ZIP)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_path, arcname=OUTPUT_CSV)
        print(f"Compressed file created: {zip_path}")
        
    else:
        print("No matching data found to consolidate.")

if __name__ == "__main__":
    # Defining author variable for the print statement
    __author__ = "Yssaky [Seu Sobrenome]"
    process_data()