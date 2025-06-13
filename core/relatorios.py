import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import json
import os

def carregar_previsoes():
    """Carrega as últimas previsões salvas"""
    caminho = "data/processed/previsoes_demanda.json"
    
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def criar_grafico_produtos_risco():
    """Cria gráfico de produtos em risco de ruptura"""
    previsoes = carregar_previsoes()
    
    if not previsoes or 'analises' not in previsoes:
        return None
    
    # Filtra produtos em risco
    produtos_risco = [
        p for p in previsoes['analises'] 
        if p.get('sugerir_reposicao', False)
    ]
    
    if not produtos_risco:
        return None
    
    # Prepara dados
    nomes = [p['nome'] for p in produtos_risco]
    dias_ruptura = [p.get('dias_ate_ruptura', 0) for p in produtos_risco]
    
    # Cores baseadas na urgência
    cores = ['red' if d < 7 else 'orange' if d < 14 else 'yellow' for d in dias_ruptura]
    
    fig = go.Figure(data=[
        go.Bar(
            x=nomes,
            y=dias_ruptura,
            marker_color=cores,
            text=[f"{d} dias" for d in dias_ruptura],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="⚠️ Produtos em Risco de Ruptura",
        xaxis_title="Produtos",
        yaxis_title="Dias até Ruptura",
        template="plotly_white",
        height=400
    )
    
    return fig

def criar_grafico_classificacao_produtos():
    """Cria gráfico de pizza com classificação dos produtos"""
    previsoes = carregar_previsoes()
    
    if not previsoes or 'analises' not in previsoes:
        return None
    
    # Conta classificações
    classificacoes = {}
    for produto in previsoes['analises']:
        classificacao = produto.get('classificacao_saida', 'Não classificado')
        classificacoes[classificacao] = classificacoes.get(classificacao, 0) + 1
    
    if not classificacoes:
        return None
    
    # Cores para cada classificação
    cores = {
        'Alta saída': '#ff6b6b',
        'Média saída': '#ffd93d',
        'Baixa saída': '#6bcf7f',
        'Sazonal': '#4ecdc4'
    }
    
    labels = list(classificacoes.keys())
    values = list(classificacoes.values())
    colors = [cores.get(label, '#gray') for label in labels]
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo='label+percent',
            hole=0.3
        )
    ])
    
    fig.update_layout(
        title="📊 Classificação de Produtos por Saída",
        template="plotly_white",
        height=400
    )
    
    return fig

def criar_grafico_previsao_demanda():
    """Cria gráfico de barras com previsão de demanda"""
    previsoes = carregar_previsoes()
    
    if not previsoes or 'analises' not in previsoes:
        return None
    
    # Prepara dados
    produtos = []
    demanda_7d = []
    demanda_30d = []
    
    for produto in previsoes['analises']:
        produtos.append(produto['nome'][:20])  # Limita nome para visualização
        demanda_7d.append(produto.get('previsao_demanda_7_dias', 0))
        demanda_30d.append(produto.get('previsao_demanda_30_dias', 0))
    
    # Ordena por demanda de 30 dias (decrescente)
    dados = list(zip(produtos, demanda_7d, demanda_30d))
    dados.sort(key=lambda x: x[2], reverse=True)
    produtos, demanda_7d, demanda_30d = zip(*dados)
    
    # Pega os top 10 para não poluir o gráfico
    produtos = produtos[:10]
    demanda_7d = demanda_7d[:10]
    demanda_30d = demanda_30d[:10]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='7 dias',
        x=produtos,
        y=demanda_7d,
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='30 dias',
        x=produtos,
        y=demanda_30d,
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title="📈 Previsão de Demanda - Top 10 Produtos",
        xaxis_title="Produtos",
        yaxis_title="Quantidade Prevista",
        barmode='group',
        template="plotly_white",
        height=500,
        xaxis_tickangle=-45
    )
    
    return fig

def criar_tabela_alertas():
    """Cria tabela formatada com alertas"""
    previsoes = carregar_previsoes()
    
    if not previsoes or 'analises' not in previsoes:
        return pd.DataFrame()
    
    alertas_data = []
    
    for produto in previsoes['analises']:
        if produto.get('sugerir_reposicao', False):
            prioridade = "🔴 ALTA" if produto.get('dias_ate_ruptura', 99) < 7 else "🟡 MÉDIA"
            
            alertas_data.append({
                'Produto': produto['nome'],
                'Categoria': produto.get('categoria', 'N/A'),
                'Dias até Ruptura': produto.get('dias_ate_ruptura', 'N/A'),
                'Estoque Atual': produto.get('estoque_atual', 0),
                'Repor (sugestão)': produto.get('quantidade_reposicao_sugerida', 'N/A'),
                'Prioridade': prioridade,
                'Classificação': produto.get('classificacao_saida', 'N/A')
            })
    
    if not alertas_data:
        return pd.DataFrame({'Mensagem': ['✅ Nenhum produto em risco de ruptura!']})
    
    df = pd.DataFrame(alertas_data)
    return df.sort_values('Dias até Ruptura')

def criar_relatorio_vendas_categoria(produtos_df):
    """Cria relatório de vendas por categoria"""
    if produtos_df.empty:
        return None
    
    vendas_categoria = produtos_df.groupby('categoria').agg({
        'vendidos_ultimos_30_dias': 'sum',
        'preco_unitario': 'mean',
        'estoque_atual': 'sum'
    }).reset_index()
    
    # Calcula receita estimada
    vendas_categoria['receita_estimada'] = (
        vendas_categoria['vendidos_ultimos_30_dias'] * 
        vendas_categoria['preco_unitario']
    )
    
    vendas_categoria = vendas_categoria.sort_values('receita_estimada', ascending=False)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=vendas_categoria['categoria'],
        y=vendas_categoria['receita_estimada'],
        name='Receita (R$)',
        marker_color='green',
        yaxis='y'
    ))
    
    fig.add_trace(go.Scatter(
        x=vendas_categoria['categoria'],
        y=vendas_categoria['vendidos_ultimos_30_dias'],
        mode='lines+markers',
        name='Unidades Vendidas',
        line=dict(color='orange', width=3),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="💰 Performance por Categoria (Últimos 30 dias)",
        xaxis_title="Categorias",
        yaxis=dict(title="Receita (R$)", side="left"),
        yaxis2=dict(title="Unidades Vendidas", side="right", overlaying="y"),
        template="plotly_white",
        height=400
    )
    
    return fig

def exibir_painel_principal():
    """Exibe o painel principal de relatórios no Streamlit"""
    st.subheader("📊 Dashboard de Análise Inteligente")
    
    # Verifica se há previsões
    previsoes = carregar_previsoes()
    
    if not previsoes:
        st.warning("⚠️ Nenhuma análise de demanda encontrada. Execute a análise primeiro.")
        
        if st.button("🚀 Executar Análise de Demanda"):
            with st.spinner("Analisando produtos com IA..."):
                from core.previsao_demanda import executar_analise_completa
                resultado = executar_analise_completa()
                
                if resultado.get('sucesso'):
                    st.success("✅ Análise concluída!")
                    st.rerun()
                else:
                    st.error(f"❌ Erro: {resultado.get('erro')}")
        return
    
    # Mostra informações da última análise
    timestamp = previsoes.get('timestamp_analise', 'N/A')
    if timestamp != 'N/A':
        timestamp = datetime.fromisoformat(timestamp).strftime("%d/%m/%Y %H:%M")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📦 Produtos Analisados", 
            previsoes.get('total_produtos_analisados', 0)
        )
    
    with col2:
        produtos_risco = previsoes.get('resumo_geral', {}).get('produtos_risco_ruptura', 0)
        st.metric(
            "⚠️ Em Risco de Ruptura", 
            produtos_risco,
            delta=f"-{produtos_risco}" if produtos_risco > 0 else "0"
        )
    
    with col3:
        st.metric(
            "🕐 Última Análise", 
            timestamp
        )
    
    # Gráficos principais
    st.markdown("---")
    
    # Alertas de reposição
    st.subheader("🚨 Alertas de Reposição")
    tabela_alertas = criar_tabela_alertas()
    
    if not tabela_alertas.empty and 'Produto' in tabela_alertas.columns:
        st.dataframe(tabela_alertas, use_container_width=True)
    else:
        st.success("✅ Todos os produtos com estoque adequado!")
    
    # Gráficos em colunas
    col1, col2 = st.columns(2)
    
    with col1:
        grafico_risco = criar_grafico_produtos_risco()
        if grafico_risco:
            st.plotly_chart(grafico_risco, use_container_width=True)
    
    with col2:
        grafico_classificacao = criar_grafico_classificacao_produtos()
        if grafico_classificacao:
            st.plotly_chart(grafico_classificacao, use_container_width=True)
    
    # Gráfico de previsão de demanda
    st.markdown("---")
    grafico_demanda = criar_grafico_previsao_demanda()
    if grafico_demanda:
        st.plotly_chart(grafico_demanda, use_container_width=True)
    
    # Performance por categoria
    from core.gerenciamento_estoque import carregar_produtos
    produtos_df = carregar_produtos()
    
    if not produtos_df.empty:
        st.markdown("---")
        grafico_categoria = criar_relatorio_vendas_categoria(produtos_df)
        if grafico_categoria:
            st.plotly_chart(grafico_categoria, use_container_width=True)
    
    # Insights da IA
    if 'resumo_geral' in previsoes:
        resumo = previsoes['resumo_geral']
        
        if 'recomendacoes_gerais' in resumo and resumo['recomendacoes_gerais']:
            st.markdown("---")
            st.subheader("💡 Recomendações da IA")
            
            for recomendacao in resumo['recomendacoes_gerais']:
                st.info(f"🔍 {recomendacao}")
    
    # Botão para nova análise
    st.markdown("---")
    if st.button("🔄 Executar Nova Análise"):
        with st.spinner("Analisando dados..."):
            from core.previsao_demanda import executar_analise_completa
            resultado = executar_analise_completa()
            
            if resultado.get('sucesso'):
                st.success("✅ Nova análise concluída!")
                st.rerun()
            else:
                st.error(f"❌ Erro: {resultado.get('erro')}")

def gerar_relatorio_pdf():
    """Gera relatório em PDF (implementação futura)"""
    st.info("📄 Geração de PDF será implementada em versão futura")
    pass

if __name__ == "__main__":
    # Teste das funções
    print("Testando módulo de relatórios...")
    previsoes = carregar_previsoes()
    print(f"Previsões carregadas: {previsoes is not None}")