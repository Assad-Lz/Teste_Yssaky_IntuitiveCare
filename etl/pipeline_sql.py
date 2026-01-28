import pandas as pd
from sqlalchemy import create_engine, text
import sys

# Conexão com o Banco de Dados
DB_URL = "postgresql://user_intuitive:password123@localhost:5432/intuitive_care"

def run_pipeline():
    print("🚀 Iniciando Pipeline ETL SQL (Correção de Acentos)...")
    engine = create_engine(DB_URL)
    
    try:
        # --- PASSO 1: OPERADORAS (Carregamento e Limpeza) ---
        print("📥 Lendo e Processando Operadoras...")
        
        # CORREÇÃO AQUI: Mudado de 'latin1' para 'utf-8' para corrigir acentos
        try:
            df_ops = pd.read_csv('data/Relatorio_cadop.csv', sep=';', encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            print("⚠️ Erro de encoding UTF-8. Tentando 'latin1' como fallback...")
            df_ops = pd.read_csv('data/Relatorio_cadop.csv', sep=';', encoding='latin1', dtype=str)

        # Padroniza nomes das colunas
        df_ops.columns = [c.replace('"', '').strip().upper() for c in df_ops.columns]
        
        # Lógica de Mapeamento Inteligente
        rename_map = {}
        id_column_found = None

        for c in df_ops.columns:
            if 'DATA' in c: continue # Pula colunas de data
            
            # Prioridade de busca para o ID
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
            print(f"❌ Erro: Coluna de ID não encontrada nas colunas: {df_ops.columns.tolist()}")
            return

        print(f"✅ Coluna ID identificada: '{id_column_found}' -> 'registro_ans'")
        
        df_ops = df_ops.rename(columns=rename_map)
        df_ops = df_ops.loc[:, ~df_ops.columns.duplicated()] # Remove colunas duplicadas
        
        # Limpeza do ID (remove .0 e espaços)
        df_ops['registro_ans'] = df_ops['registro_ans'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        
        # Seleciona apenas as colunas que existem no banco
        cols_to_keep = ['registro_ans', 'cnpj', 'razao_social', 'modalidade', 'uf']
        cols_to_keep = [c for c in cols_to_keep if c in df_ops.columns]
        
        # Remove duplicatas baseadas no ID
        df_ops = df_ops[cols_to_keep].drop_duplicates(subset=['registro_ans'])

        # Limpa o banco antes de inserir novos dados
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE despesas CASCADE;"))
            conn.execute(text("TRUNCATE TABLE operadoras CASCADE;"))
            conn.commit()
            
        df_ops.to_sql('operadoras', engine, if_exists='append', index=False)
        print(f"✅ {len(df_ops)} Operadoras carregadas com sucesso.")

        # --- PASSO 2: DESPESAS (Inserção em Lotes) ---
        print("📥 Lendo Despesas (Isso pode levar alguns segundos)...")
        df_exp = pd.read_csv('data/consolidado_despesas.csv', sep=';', dtype={'registroans': str})
        
        df_exp.columns = [c.strip().lower().replace(' ', '_') for c in df_exp.columns]
        df_exp = df_exp.rename(columns={'registroans': 'registro_ans', 'valordespesas': 'valor_despesa'})
        
        # Limpeza ID das despesas
        df_exp['registro_ans'] = df_exp['registro_ans'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        
        # Filtro de Integridade (Só insere despesas se a operadora existir)
        valid_ids = set(df_ops['registro_ans'])
        df_exp_valid = df_exp[df_exp['registro_ans'].isin(valid_ids)].copy()
        
        total_valid = len(df_exp_valid)
        print(f"📊 Relatório de Integridade: {total_valid} registros válidos prontos para inserção.")
        
        if total_valid == 0:
            print("❌ ZERO registros compatíveis. Verifique os IDs.")
            return

        # Preparação das colunas finais
        cols = ['registro_ans', 'valor_despesa', 'trimestre', 'ano']
        if 'descricao' in df_exp_valid.columns: cols.append('descricao')
        
        # --- INSERÇÃO FRAGMENTADA (CHUNKS) ---
        print("⏳ Iniciando inserção fragmentada (Lotes de 50.000)...")
        
        chunk_size = 50000
        total_chunks = (total_valid // chunk_size) + 1
        
        for i in range(0, total_valid, chunk_size):
            chunk = df_exp_valid.iloc[i : i + chunk_size]
            chunk[cols].to_sql('despesas', engine, if_exists='append', index=False)
            
            # Barra de progresso visual
            current_chunk = (i // chunk_size) + 1
            percent = round((i + len(chunk)) / total_valid * 100, 1)
            print(f"   ... Lote {current_chunk}/{total_chunks} inserido ({percent}%)")

        print("✅ Pipeline Finalizado com Sucesso Absoluto!")
        
    except Exception as e:
        print(f"❌ Falha no Pipeline: {e}")

if __name__ == "__main__":
    run_pipeline()