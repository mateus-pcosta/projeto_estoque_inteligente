#!/usr/bin/env python3
"""
Script para corrigir o campo vendidos_ultimos_30_dias baseado nas movimentações reais.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def corrigir_vendidos_30_dias():
    """Atualiza o campo vendidos_ultimos_30_dias baseado nas movimentações reais."""
    
    # Conecta ao banco
    conn = sqlite3.connect('data/raw/estoque.db')
    
    # Carrega movimentações
    movimentacoes_df = pd.read_sql_query("SELECT * FROM movimentacoes", conn)
    produtos_df = pd.read_sql_query("SELECT * FROM produtos", conn)
    
    print("🔧 Corrigindo campo vendidos_ultimos_30_dias...")
    
    # Converte datas
    movimentacoes_df['data_convertida'] = pd.to_datetime(movimentacoes_df['data'], format='mixed', errors='coerce')
    data_limite = datetime.now() - timedelta(days=30)
    
    cursor = conn.cursor()
    
    for _, produto in produtos_df.iterrows():
        id_produto = produto['id_produto']
        nome = produto['nome']
        
        # Calcula vendas reais dos últimos 30 dias
        vendas_30_dias = movimentacoes_df[
            (movimentacoes_df['id_produto'] == id_produto) & 
            (movimentacoes_df['tipo'] == 'saida') &
            (movimentacoes_df['data_convertida'] >= data_limite)
        ]['quantidade'].sum()
        
        valor_antigo = produto['vendidos_ultimos_30_dias']
        
        # Atualiza no banco
        cursor.execute(
            "UPDATE produtos SET vendidos_ultimos_30_dias = ? WHERE id_produto = ?",
            (int(vendas_30_dias), id_produto)
        )
        
        print(f"  📦 {nome}: {valor_antigo} → {vendas_30_dias}")
    
    conn.commit()
    conn.close()
    
    print("✅ Campo vendidos_ultimos_30_dias corrigido!")

if __name__ == "__main__":
    corrigir_vendidos_30_dias()