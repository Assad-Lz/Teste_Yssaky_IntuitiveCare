import pandas as pd
from sqlalchemy import create_engine, text
import os
import sys

# LÓGICA DE CONEXÃO DINÂMICA:
# O script detecta se deve conectar via 'db' (dentro do Docker) ou 'localhost' (fora do Docker)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_URL = f"postgresql://user_intuitive:password123@{DB_HOST}:5432/intuitive_care"

def run_pipeline():
    print(f"🚀 Iniciando Pipeline ETL SQL em: {DB_HOST}")
    engine = create_engine(DB_URL)
    
    try:
        # --- PASSO 1: OPERADORAS (Carregamento e Limpeza) ---
        print("📥 Lendo e Processando Operadoras...")
        
        # Encoding UTF-8 para garantir acentuação correta
        try:
            df_ops = pd.read_csv('data/Relatorio_cadop.csv', sep=';', encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            print("⚠️ Erro de encoding UTF-8. Tentando 'latin1' como fallback...")
            df_ops = pd.read_csv('data/Relatorio_cadop.csv', sep=';', encoding='latin1', dtype=str)

        df_ops.columns = [c.replace('"', '').strip().upper() for c in df_ops.columns]
        
        rename_map = {}
        id_column_found = None

        for c in df_ops.columns:
            if 'DATA' in c: continue
            
            if ('REGISTRO' in c and 'OPERADORA' in c): 
                rename_map[c] = 'registro_ans'
                id_column_found = c
            elif ('REGISTRO' in c and 'ANS' in c) and not id_column_found:
                rename_map[c] = 'registro_ans'
                id_column_found = c
            elif ('RAZAO' in c): rename_map[c] = 'razao_social'
            elif ('CNPJ' in c): rename_map[c] = 'cnpj'
            elif ('UF' in c): rename_map[c] = 'uf'
            elif ('MODALIDADE' in c): rename_map[c] = 'modalidade'
        
        if not id_column_found:
            print(f"❌ Erro: Coluna de ID não encontrada.")
            return

        df_ops = df_ops.rename(columns=rename_map)
        df_ops = df_ops.loc[:, ~df_ops.columns.duplicated()]
        df_ops['registro_ans'] = df_ops['registro_ans'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        
        cols_to_keep = ['registro_ans', 'cnpj', 'razao_social', 'modalidade', 'uf']
        cols_to_keep = [c for c in cols_to_keep if c in df_ops.columns]
        df_ops = df_ops[cols_to_keep].drop_duplicates(subset=['registro_ans'])

        # Limpa o banco antes de inserir
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE despesas CASCADE;"))
            conn.execute(text("TRUNCATE TABLE operadoras CASCADE;"))
            conn.commit()
            
        df_ops.to_sql('operadoras', engine, if_exists='append', index=False)
        print(f"✅ {len(df_ops)} Operadoras carregadas.")

        # --- PASSO 2: DESPESAS (Inserção em Lotes) ---
        print("📥 Lendo Despesas...")
        df_exp = pd.read_csv('data/consolidado_despesas.csv', sep=';', dtype={'registroans': str})
        
        df_exp.columns = [c.strip().lower().replace(' ', '_') for c in df_exp.columns]
        df_exp = df_exp.rename(columns={'registroans': 'registro_ans', 'valordespesas': 'valor_despesa'})
        df_exp['registro_ans'] = df_exp['registro_ans'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        
        valid_ids = set(df_ops['registro_ans'])
        df_exp_valid = df_exp[df_exp['registro_ans'].isin(valid_ids)].copy()
        
        total_valid = len(df_exp_valid)
        if total_valid == 0:
            print("❌ ZERO registros compatíveis.")
            return

        cols = ['registro_ans', 'valor_despesa', 'trimestre', 'ano']
        if 'descricao' in df_exp_valid.columns: cols.append('descricao')
        
        print(f"⏳ Inserindo {total_valid} registros em lotes de 50.000...")
        chunk_size = 50000
        total_chunks = (total_valid // chunk_size) + 1
        
        for i in range(0, total_valid, chunk_size):
            chunk = df_exp_valid.iloc[i : i + chunk_size]
            chunk[cols].to_sql('despesas', engine, if_exists='append', index=False)
            current_chunk = (i // chunk_size) + 1
            percent = round((i + len(chunk)) / total_valid * 100, 1)
            print(f"   ... Lote {current_chunk}/{total_chunks} ({percent}%)")

        print("✅ Pipeline Finalizado com Sucesso Absoluto!")
        
    except Exception as e:
        print(f"❌ Falha no Pipeline: {e}")

if __name__ == "__main__":
    run_pipeline()