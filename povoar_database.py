#!/usr/bin/env python3
"""
Script para povoar o banco de dados com movimentações realistas
para teste completo da ferramenta de estoque inteligente.
"""

import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta
from core.gerenciamento_estoque import carregar_produtos

def gerar_movimentacoes_realistas():
    """Gera movimentações realistas para todos os produtos."""
    
    # Conecta ao banco
    conn = sqlite3.connect('data/raw/estoque.db')
    
    # Carrega produtos existentes
    produtos_df = carregar_produtos()
    print(f"📦 Encontrados {len(produtos_df)} produtos para povoar")
    
    # Limpa movimentações antigas (mantém apenas as primeiras para histórico)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movimentacoes WHERE id_movimentacao > 2")
    conn.commit()
    
    # Configurações
    data_inicio = datetime.now() - timedelta(days=90)  # 90 dias atrás
    data_fim = datetime.now()
    
    movimentacoes = []
    id_movimentacao = 100  # Começa em 100 para não conflitar
    
    print("🎲 Gerando movimentações realistas...")
    
    for _, produto in produtos_df.iterrows():
        id_produto = produto['id_produto']
        nome = produto['nome']
        categoria = produto['categoria']
        vendidos_30_dias = produto['vendidos_ultimos_30_dias']
        
        print(f"  📍 {nome} (categoria: {categoria})")
        
        # Define padrão de vendas baseado na categoria
        if categoria == 'Bebidas':
            frequencia_base = 0.7  # 70% chance de venda por dia
            volume_medio = vendidos_30_dias / 20  # Concentra em alguns dias
        elif categoria == 'Salgados':
            frequencia_base = 0.5  # 50% chance
            volume_medio = vendidos_30_dias / 15
        elif categoria == 'Lanches':
            frequencia_base = 0.4  # 40% chance
            volume_medio = vendidos_30_dias / 12
        elif categoria == 'Sobremesas':
            frequencia_base = 0.3  # 30% chance
            volume_medio = vendidos_30_dias / 10
        else:
            frequencia_base = 0.3
            volume_medio = vendidos_30_dias / 10
        
        # Gera movimentações dia a dia
        data_atual = data_inicio
        while data_atual <= data_fim:
            
            # Fator fim de semana (mais vendas)
            fator_dia = 1.0
            if data_atual.weekday() >= 5:  # Sábado/Domingo
                fator_dia = 1.5
            elif data_atual.weekday() == 4:  # Sexta
                fator_dia = 1.3
            
            # Fator horário de almoço/jantar para alguns produtos
            if categoria in ['Salgados', 'Lanches']:
                if data_atual.hour in [12, 13, 19, 20]:
                    fator_dia *= 1.4
            
            # Decide se haverá venda neste dia
            chance_venda = frequencia_base * fator_dia
            if random.random() < chance_venda and volume_medio > 0:
                
                # Calcula quantidade vendida
                variacao = random.uniform(0.5, 2.0)
                quantidade = max(1, int(volume_medio * variacao))
                
                # Adiciona algumas vendas grandes ocasionais
                if random.random() < 0.1:  # 10% chance de venda grande
                    quantidade *= random.randint(2, 5)
                
                # Horário realista
                hora = random.choice([
                    "08:30", "09:15", "10:45", "11:30", "12:15", "12:45",
                    "13:30", "14:20", "15:45", "16:30", "17:15", "18:30",
                    "19:15", "19:45", "20:30"
                ])
                
                data_formatada = data_atual.strftime(f"%Y-%m-%d {hora}:00")
                
                # Observações variadas
                observacoes = [
                    "Venda balcão", "Venda delivery", "Promoção", 
                    "Cliente fidelidade", "Venda expressa", "Combo",
                    "Desconto", "Venda normal", ""
                ]
                observacao = random.choice(observacoes)
                
                movimentacoes.append({
                    'id_movimentacao': id_movimentacao,
                    'id_produto': id_produto,
                    'tipo': 'saida',
                    'quantidade': quantidade,
                    'data': data_formatada,
                    'usuario': 'Sistema',
                    'observacao': observacao,
                    'nome': nome,
                    'categoria': categoria
                })
                
                id_movimentacao += 1
            
            # Ocasionalmente adiciona entradas (reposição)
            if random.random() < 0.05:  # 5% chance de entrada
                quantidade_entrada = random.randint(10, 50)
                data_formatada = data_atual.strftime("%Y-%m-%d 09:00:00")
                
                movimentacoes.append({
                    'id_movimentacao': id_movimentacao,
                    'id_produto': id_produto,
                    'tipo': 'entrada',
                    'quantidade': quantidade_entrada,
                    'data': data_formatada,
                    'usuario': 'Sistema',
                    'observacao': 'Reposição estoque',
                    'nome': nome,
                    'categoria': categoria
                })
                
                id_movimentacao += 1
            
            data_atual += timedelta(days=1)
    
    # Insere no banco
    print(f"💾 Inserindo {len(movimentacoes)} movimentações no banco...")
    
    df_movimentacoes = pd.DataFrame(movimentacoes)
    df_movimentacoes.to_sql('movimentacoes', conn, if_exists='append', index=False)
    
    conn.close()
    
    print("✅ Database povoado com sucesso!")
    print(f"📊 Total de movimentações adicionadas: {len(movimentacoes)}")
    
    # Estatísticas
    saidas = df_movimentacoes[df_movimentacoes['tipo'] == 'saida']
    entradas = df_movimentacoes[df_movimentacoes['tipo'] == 'entrada']
    
    print(f"🔄 Saídas (vendas): {len(saidas)}")
    print(f"📥 Entradas (reposição): {len(entradas)}")
    print(f"💰 Volume total vendido: {saidas['quantidade'].sum()} unidades")
    
    print("\n🎯 Agora você pode:")
    print("  1. 🎓 Treinar IA - Todos os produtos terão dados suficientes")
    print("  2. 📊 Dashboard IA - Análises precisas com dados reais")  
    print("  3. 🔮 Análise IA - ML funcionando para todos")
    print("  4. 📈 Relatórios - Gráficos com dados interessantes")

def resetar_estoques():
    """Ajusta estoques para níveis mais realistas após povoar."""
    print("\n🔧 Ajustando estoques para níveis realistas...")
    
    conn = sqlite3.connect('data/raw/estoque.db')
    cursor = conn.cursor()
    
    # Consulta movimentações para calcular estoques
    cursor.execute("""
        SELECT id_produto, 
               SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE 0 END) as entradas,
               SUM(CASE WHEN tipo = 'saida' THEN quantidade ELSE 0 END) as saidas
        FROM movimentacoes 
        GROUP BY id_produto
    """)
    
    movimentacoes = cursor.fetchall()
    
    for id_produto, entradas, saidas in movimentacoes:
        # Calcula estoque baseado em movimentações + estoque inicial
        cursor.execute("SELECT estoque_atual FROM produtos WHERE id_produto = ?", (id_produto,))
        estoque_inicial = cursor.fetchone()[0]
        
        # Estoque = inicial + entradas - saídas + margem de segurança
        novo_estoque = max(5, estoque_inicial + entradas - saidas + random.randint(10, 30))
        
        cursor.execute(
            "UPDATE produtos SET estoque_atual = ? WHERE id_produto = ?",
            (novo_estoque, id_produto)
        )
    
    conn.commit()
    conn.close()
    
    print("✅ Estoques ajustados!")

if __name__ == "__main__":
    print("🚀 Povoando Database - Sistema de Estoque Inteligente")
    print("=" * 60)
    
    try:
        # Gera movimentações
        gerar_movimentacoes_realistas()
        
        # Ajusta estoques
        resetar_estoques()
        
        print("\n🎉 SUCESSO! Database completamente povoado!")
        print("🏁 Sua ferramenta está pronta para uso completo!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("Verifique se o banco de dados existe em data/raw/estoque.db")