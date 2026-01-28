import pandas as pd

def debug_match():
    print("🔍 DIAGNOSTICO DE IDs (ANS)...")
    
    # 1. Carregar Operadoras
    df_ops = pd.read_csv('data/Relatorio_cadop.csv', sep=';', encoding='latin1', dtype=str)
    # Limpa colunas
    df_ops.columns = [c.replace('"', '').strip().upper() for c in df_ops.columns]
    # Acha a coluna de ID
    col_op = next(c for c in df_ops.columns if 'REGISTRO' in c and 'ANS' in c)
    # Limpa valores
    ops_ids = df_ops[col_op].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).unique()
    
    # 2. Carregar Despesas
    df_exp = pd.read_csv('data/consolidado_despesas.csv', sep=';', dtype=str)
    # Acha coluna ID (pode variar o nome)
    col_exp = next(c for c in df_exp.columns if 'registro' in c.lower())
    # Limpa valores
    exp_ids = df_exp[col_exp].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).unique()
    
    # 3. MOSTRAR A VERDADE
    print(f"\n--- AMOSTRA OPERADORAS ({len(ops_ids)} total) ---")
    print(ops_ids[:5]) # Mostra os 5 primeiros
    
    print(f"\n--- AMOSTRA DESPESAS ({len(exp_ids)} total) ---")
    print(exp_ids[:5]) # Mostra os 5 primeiros
    
    # 4. Tenta achar interseção
    comum = set(ops_ids).intersection(set(exp_ids))
    print(f"\n--- IDS EM COMUM: {len(comum)} ---")
    
    if len(comum) == 0:
        print("❌ PROBLEMA CONFIRMADO: Os formatos estão diferentes!")
        print("Compare as duas listas acima. Um tem zeros na frente? Pontos?")

if __name__ == "__main__":
    debug_match()