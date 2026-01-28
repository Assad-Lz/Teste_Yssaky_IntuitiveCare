import pandas as pd
import glob
import os
import zipfile

def process_data():
    print("[ETL] Starting Processing Phase...")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
    OUTPUT_FILE = os.path.join(DATA_DIR, 'consolidado_despesas.csv')
    
    all_files = glob.glob(os.path.join(DATA_DIR, '*202*.csv'))
    
    df_list = []
    
    for filename in all_files:
        if "consolidado" in filename or "Relatorio" in filename:
            continue
            
        print(f"Reading file: {os.path.basename(filename)}")
        try:
            # TENTATIVA 1: UTF-8 (Novo padrão da ANS)
            try:
                df = pd.read_csv(filename, sep=';', encoding='utf-8', dtype=str)
            except UnicodeDecodeError:
                # TENTATIVA 2: Latin-1 (Fallback para arquivos antigos)
                print(f"UTF-8 failed for {filename}, trying Latin-1...")
                df = pd.read_csv(filename, sep=';', encoding='latin1', dtype=str)
            
            # Limpeza de colunas
            df.columns = [c.replace('"', '').strip() for c in df.columns]
            
            # Extrair data do nome do arquivo
            base_name = os.path.basename(filename)
            if 'T' in base_name:
                trimestre = base_name.split('T')[0] + 'T'
                ano = base_name.split('T')[1].split('.')[0]
                df['Trimestre'] = trimestre
                df['Ano'] = ano
            
            # Normalizar nome da coluna de valor
            if 'VL_SALDO_FINAL' in df.columns:
                df.rename(columns={'VL_SALDO_FINAL': 'ValorDespesas'}, inplace=True)
            elif 'Valor' in df.columns:
                df.rename(columns={'Valor': 'ValorDespesas'}, inplace=True)
                
            # Converter valor monetário (BR para US)
            if 'ValorDespesas' in df.columns:
                df['ValorDespesas'] = df['ValorDespesas'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce')
            
            # Renomear colunas
            rename_map = {
                'REG_ANS': 'RegistroANS',
                'CD_CONTA_CONTABIL': 'ContaContabil',
                'DESCRICAO': 'Descricao'
            }
            df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
            
            df_list.append(df)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    if df_list:
        full_df = pd.concat(df_list, ignore_index=True)
        
        # Salvar em UTF-8 PURO
        full_df.to_csv(OUTPUT_FILE, index=False, sep=';', encoding='utf-8')
        print(f"Consolidated CSV saved to: {OUTPUT_FILE} (UTF-8)")
        
        # Gerar ZIP
        with zipfile.ZipFile(OUTPUT_FILE.replace('.csv', '.zip'), 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(OUTPUT_FILE, arcname='consolidado_despesas.csv')
            
    else:
        print("No data found.")

if __name__ == "__main__":
    process_data()