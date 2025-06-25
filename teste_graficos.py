#!/usr/bin/env python3
"""
Script para testar os gráficos melhorados
"""

import sys
sys.path.append('.')

from core.gerenciamento_estoque import carregar_produtos, carregar_movimentacoes
import pandas as pd

def main():
    print("🎨 TESTE DOS GRÁFICOS MELHORADOS")
    print("=" * 50)
    
    # Carrega dados
    produtos_df = carregar_produtos()
    movimentacoes_df = carregar_movimentacoes()
    
    print(f"📊 Dados carregados:")
    print(f"  • {len(produtos_df)} produtos")
    print(f"  • {len(movimentacoes_df)} movimentações")
    
    # Analisa vendas por produto
    vendas = movimentacoes_df[movimentacoes_df['tipo'] == 'saida']
    print(f"\n📈 Vendas por produto:")
    
    produtos_com_vendas = vendas.groupby('nome')['quantidade'].sum().sort_values(ascending=False)
    
    for i, (produto, qtd) in enumerate(produtos_com_vendas.head(6).items(), 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
        print(f"  {emoji} {produto}: {qtd} unidades")
    
    print(f"\n🎯 MELHORIAS IMPLEMENTADAS:")
    print("  ✅ Filtro para selecionar produtos específicos")
    print("  ✅ Legenda posicionada fora do gráfico")
    print("  ✅ Cores personalizadas e distintas")
    print("  ✅ Ranking automático dos produtos")
    print("  ✅ Estatísticas contextualizadas")
    print("  ✅ Grid sutil para melhor leitura")
    
    print(f"\n🚀 Para testar, execute:")
    print("  streamlit run app.py")
    print("  Vá em 'Histórico de Movimentações' > aba 'Vendas por Produto'")
    print("  Ou 'Análise IA' > selecione um produto > aba 'Evolução de Vendas'")

if __name__ == "__main__":
    main()