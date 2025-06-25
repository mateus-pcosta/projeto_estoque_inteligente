import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.helpers import formatar_preco, formatar_nomes_colunas, formatar_colunas_historico
from core.gerenciamento_estoque import (
    carregar_produtos, adicionar_produto, editar_produto,
    remover_produto, buscar_produto, registrar_movimentacao,
    verificar_estoque_baixo, carregar_movimentacoes, criar_tabelas_movimentacoes, 
    criar_tabelas_produtos
)

# Importações do módulo de IA
try:
    from core.previsao_demanda import (
        analisar_todos_produtos,
        classificar_urgencia_produto,
        gerar_lista_compras,
        treinar_todos_modelos,
        ML_DISPONIVEL
    )
except ImportError:
    ML_DISPONIVEL = False

# Importações do módulo de relatórios
try:
    from core.relatorios import (
        relatorio_vendas_periodo,
        relatorio_estoque_critico,
        relatorio_categorias,
        exportar_relatorio_excel,
        gerar_dashboard_resumo
    )
    RELATORIOS_DISPONIVEL = True
except ImportError:
    RELATORIOS_DISPONIVEL = False

st.set_page_config(page_title="Estoque Inteligente", layout="wide")
st.title("📦 Estoque Inteligente")

def adicionar():
    st.subheader("➕ Adicionar Novo Produto")
    with st.form("form_adicionar"):
        nome = st.text_input("Nome do Produto")
        categoria = st.text_input("Categoria")
        preco = st.number_input("Preço Unitário", min_value=0.0, step=0.01)
        estoque = st.number_input("Estoque Atual", min_value=0)
        enviar = st.form_submit_button("Adicionar")

    if enviar:
        novo_produto = {
            "nome": nome,
            "categoria": categoria,
            "preco_unitario": preco,
            "estoque_atual": estoque
        }
        adicionar_produto(novo_produto)
        st.success(f"Produto '{nome}' adicionado com sucesso!")

def editar():
    st.subheader("✏️ Editar Produto Existente")
    id_edit = st.number_input("ID do Produto a Editar", min_value=1, step=1)
    produto_encontrado = buscar_produto(int(id_edit))
    if not produto_encontrado.empty:
        with st.form("form_editar"):
            nome = st.text_input("Nome", produto_encontrado.iloc[0]["nome"])
            categoria = st.text_input("Categoria", produto_encontrado.iloc[0]["categoria"])
            preco = st.number_input("Preço", value=produto_encontrado.iloc[0]["preco_unitario"], step=0.01)
            estoque = st.number_input("Estoque", value=produto_encontrado.iloc[0]["estoque_atual"])
            enviar = st.form_submit_button("Salvar Alterações")

        if enviar:
            novos_dados = {
                "nome": nome,
                "categoria": categoria,
                "preco_unitario": preco,
                "estoque_atual": estoque
            }
            editar_produto(int(id_edit), novos_dados)
            st.success("Produto atualizado com sucesso!")
    else:
        st.warning("ID não encontrado.")

def remover():
    st.subheader("🗑️ Remover Produto")
    id_remover = st.number_input("ID do Produto a Remover", min_value=1, step=1)
    if st.button("Remover"):
        remover_produto(int(id_remover))
        st.success("Produto removido com sucesso!")

def visualizar_produtos():
    st.subheader("📦 Produtos em Estoque")

    try:
        produtos = carregar_produtos()

        if produtos.empty:
            st.warning("Nenhum produto encontrado.")
            return

        estoque_baixo = verificar_estoque_baixo()
        if not estoque_baixo.empty:
            st.warning("⚠️ Produtos com estoque baixo:")
            st.dataframe(estoque_baixo[["nome", "estoque_atual"]])

        categorias = produtos["categoria"].dropna().unique()
        categoria_filtro = st.sidebar.multiselect("Categoria", categorias, default=list(categorias))

        preco_min = float(produtos["preco_unitario"].min())
        preco_max = float(produtos["preco_unitario"].max())
        faixa_preco = st.sidebar.slider("Faixa de Preço (R$)", min_value=preco_min, max_value=preco_max, value=(preco_min, preco_max))

        estoque_min = int(produtos["estoque_atual"].min())
        estoque_max = int(produtos["estoque_atual"].max())
        faixa_estoque = st.sidebar.slider("Estoque Atual", min_value=estoque_min, max_value=estoque_max, value=(estoque_min, estoque_max))

        df_filtrado = produtos[
            (produtos["categoria"].isin(categoria_filtro)) &
            (produtos["preco_unitario"] >= faixa_preco[0]) &
            (produtos["preco_unitario"] <= faixa_preco[1]) &
            (produtos["estoque_atual"] >= faixa_estoque[0]) &
            (produtos["estoque_atual"] <= faixa_estoque[1])
        ]

        termo_busca = st.text_input("🔎 Buscar por Nome ou Categoria:")
        if termo_busca:
            termo = termo_busca.lower()
            df_filtrado = df_filtrado[
                df_filtrado["nome"].str.lower().str.contains(termo) |
                df_filtrado["categoria"].str.lower().str.contains(termo)
            ]

        df_formatado = formatar_nomes_colunas(df_filtrado)
        df_formatado["Preço Unitário"] = df_formatado["Preço Unitário"].apply(formatar_preco)

        st.dataframe(df_formatado.sort_values("ID Produto"))

        st.markdown("---")
        st.subheader("🏆 Ranking de Categorias Mais Lucrativas")

        if "vendidos_ultimos_30_dias" in produtos.columns:
            produtos["lucro_total"] = produtos["preco_unitario"] * produtos["vendidos_ultimos_30_dias"]
            ranking_df = produtos.groupby("categoria")["lucro_total"].sum().reset_index()
            ranking_df.columns = ["Categoria", "Lucro Total"]

            fig = px.bar(
                ranking_df.sort_values("Lucro Total", ascending=False),
                x="Categoria",
                y="Lucro Total",
                text=ranking_df["Lucro Total"].apply(formatar_preco),
                labels={"Lucro Total": "Lucro Total (R$)"},
                title="Ranking de Categorias Mais Lucrativas"
            )

            fig.update_traces(textposition="outside")
            fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=".2f")

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Coluna 'vendidos_ultimos_30_dias' não encontrada para calcular o ranking.")


    except Exception as e:
        st.error(f"Erro ao carregar produtos: {str(e)}")


def tela_movimentacao():
    st.subheader("🔄 Movimentação de Estoque")
    produtos = carregar_produtos()

    col1, col2 = st.columns(2)
    with col1:
        produto_nome = st.selectbox(
            "Selecione o Produto:",
            options=produtos["nome"],
            format_func=lambda x: f"{x} (Estoque: {produtos[produtos['nome'] == x]['estoque_atual'].values[0]})"
        )
        id_produto = produtos[produtos["nome"] == produto_nome]["id_produto"].values[0]

    with col2:
        quantidade = st.number_input("Quantidade:", min_value=1, value=1)
        observacao = st.text_input("Observação/Motivo:")

    foi_venda = st.checkbox("Essa saída foi uma venda?", value=False)

    col_entrada, col_saida, _ = st.columns([1, 1, 2])
    
    with col_entrada:
        if st.button("🔼 Registrar Entrada", help="Adiciona itens ao estoque"):
            try:
                resultado = registrar_movimentacao(
                    id_produto=id_produto,
                    tipo="entrada",
                    quantidade=quantidade,
                    observacao=observacao
                )
                if resultado:
                    st.success("✅ Entrada registrada com sucesso!")
                else:
                    st.error("❌ Falha ao registrar entrada")
            except Exception as e:
                st.error(f"Erro: {str(e)}")

    with col_saida:
        if st.button("🔽 Registrar Saída", help="Remove itens do estoque"):
            try:
                resultado = registrar_movimentacao(
                    id_produto=id_produto,
                    tipo="saida",
                    quantidade=quantidade,
                    observacao=observacao,
                    venda=foi_venda
                )
                if resultado:
                    st.success("✅ Saída registrada com sucesso!")
                else:
                    st.error("❌ Falha ao registrar saída")
            except Exception as e:
                st.error(f"Erro: {str(e)}")

def tela_historico():
    st.subheader("📜 Histórico de Movimentações")
    
    try:
        movimentacoes = carregar_movimentacoes()
        
        if not movimentacoes.empty:
            movimentacoes["data"] = pd.to_datetime(movimentacoes["data"], format='mixed', errors='coerce')
            movimentacoes = movimentacoes.dropna(subset=['data'])
            movimentacoes["data_formatada"] = movimentacoes["data"].dt.strftime("%d/%m/%Y %H:%M")

            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 Filtros - Histórico")

            tipos = movimentacoes["tipo"].unique()
            tipo_filtro = st.sidebar.selectbox("Tipo de Movimentação", options=["Todos"] + list(tipos))

            produtos_opcoes = movimentacoes["nome"].unique()
            produto_filtro = st.sidebar.multiselect("Produto", options=produtos_opcoes, default=list(produtos_opcoes))

            categorias = movimentacoes["categoria"].unique()
            categoria_filtro = st.sidebar.multiselect("Categoria", options=categorias, default=list(categorias))

            data_min = movimentacoes["data"].min().date()
            data_max = movimentacoes["data"].max().date()
            data_inicio, data_fim = st.sidebar.date_input("Período", value=(data_min, data_max))

            qtd_min = int(movimentacoes["quantidade"].min())
            qtd_max = int(movimentacoes["quantidade"].max())
            qtd_range = st.sidebar.slider("Quantidade", min_value=qtd_min, max_value=qtd_max, value=(qtd_min, qtd_max))

            df_filtrado = movimentacoes[
                ((movimentacoes["tipo"] == tipo_filtro) if tipo_filtro != "Todos" else True) &
                (movimentacoes["nome"].isin(produto_filtro)) &
                (movimentacoes["categoria"].isin(categoria_filtro)) &
                (movimentacoes["data"].dt.date >= data_inicio) &
                (movimentacoes["data"].dt.date <= data_fim) &
                (movimentacoes["quantidade"] >= qtd_range[0]) &
                (movimentacoes["quantidade"] <= qtd_range[1])
            ]

            termo_busca = st.text_input("🔍 Buscar por Produto ou Categoria:")
            if termo_busca:
                termo = termo_busca.lower()
                df_filtrado = df_filtrado[
                    df_filtrado["nome"].str.lower().str.contains(termo) |
                    df_filtrado["categoria"].str.lower().str.contains(termo)
                ]

            df_filtrado = formatar_colunas_historico(df_filtrado)

            st.dataframe(
                df_filtrado.sort_values("Data", ascending=False).drop(columns="Data"),
                column_config={"Data/Hora": "Data/Hora"}
            )

            st.markdown("### 📈 Evolução das Movimentações por Produto")

            df_filtrado["Data"] = pd.to_datetime(df_filtrado["Data"], errors="coerce")

            # Abas para visualizações diferentes
            tab1, tab2, tab3 = st.tabs(["📈 Vendas por Produto", "📊 Entradas vs Saídas", "📅 Resumo por Período"])
            
            with tab1:
                # Filtro de produtos para o gráfico
                produtos_disponiveis = df_filtrado[df_filtrado["Tipo"] == "saida"]["Nome"].unique()
                
                if len(produtos_disponiveis) > 0:
                    # Filtro para selecionar produtos específicos
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        produtos_selecionados = st.multiselect(
                            "🎯 Selecione produtos para visualizar (máximo 6 para melhor legibilidade):",
                            produtos_disponiveis,
                            default=list(produtos_disponiveis[:6]) if len(produtos_disponiveis) <= 6 else list(produtos_disponiveis[:4])
                        )
                    with col2:
                        mostrar_todos = st.button("📊 Mostrar Todos", help="Mostra todos os produtos (pode ficar confuso)")
                    
                    if mostrar_todos:
                        produtos_selecionados = list(produtos_disponiveis)
                    
                    if produtos_selecionados:
                        # Filtra apenas produtos selecionados
                        vendas = df_filtrado[
                            (df_filtrado["Tipo"] == "saida") & 
                            (df_filtrado["Nome"].isin(produtos_selecionados))
                        ].copy()
                        
                        if not vendas.empty:
                            # Agrupa vendas por data e produto
                            vendas_agrupadas = vendas.groupby(["Data", "Nome"])["Quantidade"].sum().reset_index()
                            vendas_agrupadas.rename(columns={"Nome": "Produto"}, inplace=True)
                            
                            # Cores personalizadas para melhor distinção
                            cores_personalizadas = [
                                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
                                '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
                                '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA'
                            ]
                            
                            fig_vendas = px.line(
                                vendas_agrupadas,
                                x="Data",
                                y="Quantidade",
                                color="Produto",
                                markers=True,
                                title="📊 Evolução das Vendas por Produto",
                                labels={"Quantidade": "Unidades Vendidas", "Data": "Data"},
                                color_discrete_sequence=cores_personalizadas
                            )
                            
                            # Layout melhorado
                            fig_vendas.update_layout(
                                xaxis_title="Data",
                                yaxis_title="Unidades Vendidas",
                                hovermode='x unified',
                                height=500,
                                # Legenda posicionada à direita, fora do gráfico
                                legend=dict(
                                    orientation="v",
                                    yanchor="top",
                                    y=1,
                                    xanchor="left",
                                    x=1.02,
                                    bgcolor="rgba(255,255,255,0.8)",
                                    bordercolor="rgba(0,0,0,0.2)",
                                    borderwidth=1
                                ),
                                # Mais espaço para a legenda
                                margin=dict(r=200)
                            )
                            
                            # Linhas mais grossas e marcadores maiores
                            fig_vendas.update_traces(
                                line=dict(width=4), 
                                marker=dict(size=8),
                                connectgaps=True
                            )
                            
                            # Grid sutil
                            fig_vendas.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                            fig_vendas.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                            
                            st.plotly_chart(fig_vendas, use_container_width=True)
                            
                            # Estatísticas dos produtos selecionados
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Top produtos mais vendidos no período (dos selecionados)
                                top_vendas = vendas.groupby("Nome")["Quantidade"].sum().sort_values(ascending=False)
                                st.markdown("#### 🏆 Ranking dos Produtos Selecionados")
                                for i, (produto, qtd) in enumerate(top_vendas.items(), 1):
                                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
                                    st.write(f"{emoji} **{produto}**: {qtd} unidades")
                            
                            with col2:
                                # Resumo estatístico
                                st.markdown("#### 📈 Resumo Estatístico")
                                total_vendido = vendas["Quantidade"].sum()
                                dias_com_vendas = len(vendas_agrupadas["Data"].unique())
                                media_diaria = total_vendido / max(dias_com_vendas, 1)
                                
                                st.metric("📦 Total Vendido", f"{total_vendido} un")
                                st.metric("📅 Dias Ativos", f"{dias_com_vendas} dias")
                                st.metric("📊 Média/Dia", f"{media_diaria:.1f} un")
                        else:
                            st.info("📊 Nenhuma venda dos produtos selecionados no período")
                    else:
                        st.warning("⚠️ Selecione pelo menos um produto para visualizar o gráfico")
                else:
                    st.info("📊 Nenhuma venda registrada no período selecionado")
            
            with tab2:
                # Comparação entre entradas e saídas
                movimentacao_por_tipo = df_filtrado.groupby(["Data", "Tipo"])["Quantidade"].sum().reset_index()
                
                if not movimentacao_por_tipo.empty:
                    fig_comparacao = px.bar(
                        movimentacao_por_tipo,
                        x="Data",
                        y="Quantidade",
                        color="Tipo",
                        title="📦 Entradas vs Saídas ao Longo do Tempo",
                        labels={"Quantidade": "Quantidade", "Tipo": "Tipo de Movimentação"},
                        color_discrete_map={"entrada": "#2E8B57", "saida": "#FF4444"}
                    )
                    fig_comparacao.update_layout(
                        xaxis_title="Data",
                        yaxis_title="Quantidade",
                        barmode='group'
                    )
                    st.plotly_chart(fig_comparacao, use_container_width=True)
                    
                    # Resumo numérico
                    col1, col2, col3 = st.columns(3)
                    total_entradas = df_filtrado[df_filtrado["Tipo"] == "entrada"]["Quantidade"].sum()
                    total_saidas = df_filtrado[df_filtrado["Tipo"] == "saida"]["Quantidade"].sum()
                    saldo = total_entradas - total_saidas
                    
                    with col1:
                        st.metric("📥 Total Entradas", f"{total_entradas} un")
                    with col2:
                        st.metric("📤 Total Saídas", f"{total_saidas} un")
                    with col3:
                        st.metric("⚖️ Saldo", f"{saldo} un")
                else:
                    st.info("📊 Nenhuma movimentação no período")
            
            with tab3:
                # Resumo estatístico
                if not df_filtrado.empty:
                    st.markdown("#### 📊 Estatísticas do Período")
                    
                    # Métricas gerais
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_movimentacoes = len(df_filtrado)
                        st.metric("📋 Total Movimentações", total_movimentacoes)
                    
                    with col2:
                        produtos_unicos = df_filtrado["Nome"].nunique()
                        st.metric("📦 Produtos Movimentados", produtos_unicos)
                    
                    with col3:
                        dias_periodo = (df_filtrado["Data"].max() - df_filtrado["Data"].min()).days + 1
                        st.metric("📅 Dias no Período", dias_periodo)
                    
                    with col4:
                        media_diaria = total_movimentacoes / max(dias_periodo, 1)
                        st.metric("📈 Média Mov./Dia", f"{media_diaria:.1f}")
                    
                    # Produto mais ativo
                    produto_mais_ativo = df_filtrado["Nome"].value_counts().head(1)
                    if not produto_mais_ativo.empty:
                        st.success(f"🎯 **Produto mais ativo**: {produto_mais_ativo.index[0]} ({produto_mais_ativo.iloc[0]} movimentações)")
                
                else:
                    st.info("📊 Nenhum dado para análise")


        else:
            st.warning("Nenhuma movimentação registrada ainda")
            
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {str(e)}")


# NOVAS FUNÇÕES DE IA

def dashboard_ia():
    """Dashboard com análise inteligente."""
    st.subheader("🤖 Dashboard Inteligente")
    
    if not ML_DISPONIVEL:
        st.warning("⚠️ Para usar IA, instale: pip install scikit-learn joblib")
    
    # Analisa todos produtos
    produtos = carregar_produtos()
    movimentacoes = carregar_movimentacoes()
    
    if produtos.empty:
        st.warning("Nenhum produto cadastrado")
        return
    
    with st.spinner("Analisando..."):
        analise = analisar_todos_produtos(produtos, movimentacoes)
    
    # Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔴 Críticos", analise['produtos_criticos'])
    with col2:
        st.metric("🟡 Atenção", analise['produtos_atencao'])
    with col3:
        st.metric("💰 Investimento", formatar_preco(analise['investimento_urgente']))
    with col4:
        st.metric("🤖 Com ML", f"{analise['produtos_ml']}/{analise['total_produtos']}")
    
    # Produtos críticos
    if analise['produtos_criticos'] > 0:
        st.markdown("---")
        st.markdown("### 🚨 Produtos Críticos")
        
        for prod in analise['lista_criticos'][:5]:
            with st.expander(f"{prod['produto']} - {prod['dias_ate_fim']} dias"):
                st.write(f"**Comprar:** {prod['quantidade_repor']} unidades")
                st.write(f"**Investimento:** {formatar_preco(prod['investimento'])}")
                for insight in prod['insights']:
                    st.info(insight)
    
    # Lista de compras
    st.markdown("---")
    st.markdown("### 📋 Lista de Compras")
    
    lista = gerar_lista_compras(produtos, movimentacoes)
    if not lista.empty:
        lista['Investimento'] = lista['Investimento'].apply(formatar_preco)
        st.dataframe(lista)
        
        csv = lista.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar", csv, "lista_compras.csv", "text/csv")


def analise_ia():
    """Análise individual com IA e relatórios detalhados."""
    st.subheader("🔮 Análise Preditiva Inteligente")
    
    produtos = carregar_produtos()
    movimentacoes = carregar_movimentacoes()
    
    if produtos.empty:
        st.warning("Nenhum produto cadastrado")
        return
    
    # Seleção do produto
    col1, col2 = st.columns([3, 1])
    with col1:
        produto_nome = st.selectbox("📦 Selecione o produto:", produtos['nome'].tolist())
    with col2:
        analisar = st.button("🔍 Analisar", type="primary")
    
    if analisar:
        id_produto = produtos[produtos['nome'] == produto_nome]['id_produto'].values[0]
        produto_info = produtos[produtos['id_produto'] == id_produto].iloc[0]
        
        with st.spinner("🤖 Processando análise com IA..."):
            resultado = classificar_urgencia_produto(produtos, movimentacoes, id_produto)
        
        if resultado['sucesso']:
            # Header com informações básicas do produto
            st.markdown("### 📊 Informações do Produto")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 Preço", formatar_preco(produto_info['preco_unitario']))
            with col2:
                st.metric("📦 Estoque", f"{produto_info['estoque_atual']} un")
            with col3:
                st.metric("📈 Vendas 30d", f"{produto_info['vendidos_ultimos_30_dias']} un")
            with col4:
                st.metric("🏷️ Categoria", produto_info['categoria'])
            
            st.markdown("---")
            
            # Análise de urgência
            st.markdown("### 🎯 Análise de Urgência")
            col1, col2, col3, col4 = st.columns(4)
            
            # Define cores baseado na urgência
            if resultado['urgencia'] == 'CRITICO':
                urgencia_color = "🚨"
            elif resultado['urgencia'] == 'ATENCAO':
                urgencia_color = "⚠️"
            else:
                urgencia_color = "✅"
            
            with col1:
                st.metric(f"{urgencia_color} Status", resultado['urgencia'])
            with col2:
                st.metric("⏰ Dias restantes", f"{resultado['dias_ate_fim']} dias")
            with col3:
                st.metric("📦 Repor", f"{resultado['quantidade_repor']} un")
            with col4:
                st.metric("💵 Investimento", formatar_preco(resultado['investimento']))
            
            st.markdown("---")
            
            # Insights da IA
            st.markdown("### 🧠 Insights da Inteligência Artificial")
            for insight in resultado['insights']:
                if "CRÍTICO" in insight:
                    st.error(insight)
                elif "ATENÇÃO" in insight:
                    st.warning(insight)
                else:
                    st.info(insight)
            
            # Status do modelo
            col1, col2 = st.columns(2)
            with col1:
                if resultado.get('modelo_ml'):
                    st.success("✅ Usando Machine Learning Avançado")
                else:
                    st.warning("⚠️ Usando análise estatística simples")
            
            with col2:
                # Confiabilidade baseada na quantidade de dados
                if produto_info['vendidos_ultimos_30_dias'] > 50:
                    confiabilidade = "Alta"
                    cor = "success"
                elif produto_info['vendidos_ultimos_30_dias'] > 20:
                    confiabilidade = "Média"
                    cor = "warning"
                else:
                    confiabilidade = "Baixa"
                    cor = "error"
                
                if cor == "success":
                    st.success(f"🎯 Confiabilidade: {confiabilidade}")
                elif cor == "warning":
                    st.warning(f"🎯 Confiabilidade: {confiabilidade}")
                else:
                    st.error(f"🎯 Confiabilidade: {confiabilidade}")
            
            st.markdown("---")
            
            # Relatórios e gráficos
            st.markdown("### 📈 Relatórios Detalhados")
            
            # Filtra movimentações do produto
            movs_produto = movimentacoes[movimentacoes['id_produto'] == id_produto].copy()
            
            if not movs_produto.empty:
                # Converte datas
                movs_produto['data_convertida'] = pd.to_datetime(movs_produto['data'], format='mixed', errors='coerce')
                movs_produto = movs_produto.dropna(subset=['data_convertida'])
                
                if len(movs_produto) > 0:
                    # Abas para diferentes relatórios
                    tab1, tab2, tab3 = st.tabs(["📊 Evolução de Vendas", "📅 Padrão Semanal", "💰 Resumo Financeiro"])
                    
                    with tab1:
                        # Gráfico de vendas ao longo do tempo (melhorado)
                        vendas_diarias = movs_produto[movs_produto['tipo'] == 'saida'].copy()
                        if not vendas_diarias.empty:
                            # Agrupa por data
                            vendas_por_dia = vendas_diarias.groupby(vendas_diarias['data_convertida'].dt.date)['quantidade'].sum().reset_index()
                            vendas_por_dia.columns = ['Data', 'Quantidade_Vendida']
                            
                            import plotly.express as px
                            
                            # Gráfico principal de linha
                            fig = px.line(
                                vendas_por_dia, 
                                x='Data', 
                                y='Quantidade_Vendida',
                                title=f"📈 Evolução das Vendas - {produto_nome}",
                                labels={'Quantidade_Vendida': 'Unidades Vendidas', 'Data': 'Data'},
                                markers=True
                            )
                            
                            # Layout profissional
                            fig.update_layout(
                                xaxis_title="Data",
                                yaxis_title="Unidades Vendidas",
                                hovermode='x unified',
                                height=400,
                                showlegend=False,
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(size=12)
                            )
                            
                            # Estilo da linha e marcadores
                            fig.update_traces(
                                line=dict(color='#2E86AB', width=4),
                                marker=dict(size=10, color='#2E86AB', line=dict(width=2, color='white')),
                                fill='tonexty' if len(vendas_por_dia) > 1 else None,
                                fillcolor='rgba(46, 134, 171, 0.1)'
                            )
                            
                            # Grid sutil
                            fig.update_xaxes(
                                showgrid=True, 
                                gridwidth=1, 
                                gridcolor='rgba(128,128,128,0.2)',
                                tickformat='%d/%m'
                            )
                            fig.update_yaxes(
                                showgrid=True, 
                                gridwidth=1, 
                                gridcolor='rgba(128,128,128,0.2)'
                            )
                            
                            # Adiciona linha de média
                            media_vendas = vendas_por_dia['Quantidade_Vendida'].mean()
                            fig.add_hline(
                                y=media_vendas, 
                                line_dash="dash", 
                                line_color="rgba(255, 107, 107, 0.6)",
                                annotation_text=f"Média: {media_vendas:.1f} un/dia",
                                annotation_position="top right"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Estatísticas das vendas
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📊 Total Vendido", f"{vendas_diarias['quantidade'].sum()} un")
                            with col2:
                                st.metric("📅 Dias com Vendas", f"{len(vendas_por_dia)} dias")
                            with col3:
                                media_vendas = vendas_diarias['quantidade'].mean()
                                st.metric("📈 Média por Venda", f"{media_vendas:.1f} un")
                        else:
                            st.info("📊 Nenhuma venda registrada para este produto")
                    
                    with tab2:
                        # Análise por dia da semana
                        if not vendas_diarias.empty:
                            vendas_diarias['dia_semana'] = vendas_diarias['data_convertida'].dt.day_name()
                            vendas_por_dia_semana = vendas_diarias.groupby('dia_semana')['quantidade'].sum().reset_index()
                            
                            # Traduz dias para português
                            dias_pt = {
                                'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                                'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                            }
                            vendas_por_dia_semana['dia_semana_pt'] = vendas_por_dia_semana['dia_semana'].map(dias_pt)
                            
                            # Ordena pelos dias da semana
                            ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                            vendas_por_dia_semana['ordem'] = vendas_por_dia_semana['dia_semana_pt'].apply(lambda x: ordem_dias.index(x) if x in ordem_dias else 99)
                            vendas_por_dia_semana = vendas_por_dia_semana.sort_values('ordem')
                            
                            fig2 = px.bar(
                                vendas_por_dia_semana,
                                x='dia_semana_pt',
                                y='quantidade',
                                title=f"Vendas por Dia da Semana - {produto_nome}",
                                labels={'quantidade': 'Unidades Vendidas', 'dia_semana_pt': 'Dia da Semana'},
                                color='quantidade',
                                color_continuous_scale='Viridis'
                            )
                            fig2.update_layout(showlegend=False)
                            st.plotly_chart(fig2, use_container_width=True)
                            
                            # Melhor dia
                            melhor_dia = vendas_por_dia_semana.loc[vendas_por_dia_semana['quantidade'].idxmax()]
                            st.success(f"🏆 Melhor dia: {melhor_dia['dia_semana_pt']} ({melhor_dia['quantidade']} unidades)")
                        else:
                            st.info("📅 Dados insuficientes para análise semanal")
                    
                    with tab3:
                        # Resumo financeiro
                        st.markdown("#### 💰 Análise Financeira")
                        
                        preco = produto_info['preco_unitario']
                        total_vendido = movs_produto[movs_produto['tipo'] == 'saida']['quantidade'].sum()
                        receita_total = total_vendido * preco
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("💵 Receita Total", formatar_preco(receita_total))
                        with col2:
                            st.metric("📦 Unidades Vendidas", f"{total_vendido} un")
                        with col3:
                            if produto_info['vendidos_ultimos_30_dias'] > 0:
                                receita_30d = produto_info['vendidos_ultimos_30_dias'] * preco
                                st.metric("💰 Receita 30 dias", formatar_preco(receita_30d))
                            else:
                                st.metric("💰 Receita 30 dias", formatar_preco(0))
                        
                        # Projeção se repor estoque
                        if resultado['quantidade_repor'] > 0:
                            st.markdown("#### 📊 Projeção de Investimento")
                            st.info(f"💡 **Recomendação**: Investir {formatar_preco(resultado['investimento'])} para repor {resultado['quantidade_repor']} unidades")
                            
                            # Calcula ROI potencial
                            if resultado['demanda_prevista'] > 0:
                                receita_prevista = resultado['demanda_prevista'] * preco
                                roi = ((receita_prevista - resultado['investimento']) / resultado['investimento']) * 100
                                st.metric("📈 ROI Previsto (14 dias)", f"{roi:.1f}%")
            else:
                st.info("📊 Nenhuma movimentação encontrada para este produto")


def treinar_ia():
    """Tela para treinar modelos."""
    st.subheader("🎓 Treinar Modelos de IA")
    
    if not ML_DISPONIVEL:
        st.error("Instale scikit-learn primeiro!")
        return
    
    st.info("Treina modelos de Machine Learning para melhorar as previsões")
    
    if st.button("Iniciar Treinamento"):
        produtos = carregar_produtos()
        movimentacoes = carregar_movimentacoes()
        
        with st.spinner("Treinando modelos..."):
            resultado = treinar_todos_modelos(produtos, movimentacoes)
        
        if resultado['sucesso'] > 0:
            st.success(f"✅ {resultado['sucesso']} modelos treinados!")
        
        if resultado['falha'] > 0:
            st.warning(f"⚠️ {resultado['falha']} sem dados suficientes")
        
        with st.expander("Detalhes"):
            for detalhe in resultado['detalhes']:
                if detalhe['status'] == 'OK':
                    st.write(f"✅ {detalhe['produto']}")
                else:
                    st.write(f"❌ {detalhe['produto']}: {detalhe['motivo']}")


def relatorios():
    """Tela de relatórios e análises."""
    st.subheader("📈 Relatórios e Análises")
    
    if not RELATORIOS_DISPONIVEL:
        st.error("Módulo de relatórios não disponível!")
        return
    
    # Carrega dados
    produtos = carregar_produtos()
    movimentacoes = carregar_movimentacoes()
    
    if produtos.empty:
        st.warning("Nenhum produto cadastrado!")
        return
        
    # Tabs para diferentes tipos de relatórios
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Vendas", "🚨 Estoque Crítico", "📋 Categorias", "📁 Exportar"])
    
    with tab1:
        st.subheader("Relatório de Vendas")
        
        # Seletor de período
        periodo = st.selectbox("Período:", [7, 15, 30, 60], index=2)
        
        if st.button("Gerar Relatório de Vendas"):
            with st.spinner("Gerando relatório..."):
                resultado = relatorio_vendas_periodo(movimentacoes, periodo)
            
            if resultado['sucesso']:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Vendas", resultado['total_vendas'])
                with col2:
                    st.metric("Quantidade Vendida", resultado['quantidade_total'])
                with col3:
                    st.metric("Média Diária", f"{resultado.get('media_diaria', 0):.1f}")
                
                # Vendas por produto
                if resultado['vendas_por_produto']:
                    st.subheader("Top Produtos Vendidos")
                    vendas_df = pd.DataFrame(resultado['vendas_por_produto'])
                    st.dataframe(vendas_df.head(10), use_container_width=True)
                    
                    # Gráfico
                    fig = px.bar(vendas_df.head(10), x='produto', y='quantidade', 
                               title=f"Top 10 Produtos - Últimos {periodo} dias")
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Vendas por categoria
                if resultado['vendas_por_categoria']:
                    st.subheader("Vendas por Categoria")
                    cat_df = pd.DataFrame(resultado['vendas_por_categoria'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(cat_df, use_container_width=True)
                    with col2:
                        fig = px.pie(cat_df, values='quantidade', names='categoria',
                                   title="Distribuição por Categoria")
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"Erro: {resultado.get('mensagem', 'Erro desconhecido')}")
    
    with tab2:
        st.subheader("Estoque Crítico")
        
        if st.button("Analisar Estoque"):
            with st.spinner("Analisando estoque..."):
                resultado = relatorio_estoque_critico(produtos, movimentacoes)
            
            if resultado['sucesso']:
                # Métricas principais
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🚨 Produtos Críticos", resultado['produtos_criticos'])
                with col2:
                    st.metric("⚠️ Produtos Atenção", resultado['produtos_atencao'])  
                with col3:
                    st.metric("💰 Investimento Crítico", f"R$ {resultado['investimento_critico']:.2f}")
                with col4:
                    st.metric("💸 Investimento Total", f"R$ {resultado['investimento_total']:.2f}")
                
                # Lista de produtos críticos
                if resultado['lista_criticos']:
                    st.subheader("🚨 Produtos Críticos")
                    criticos_df = pd.DataFrame(resultado['lista_criticos'])
                    st.dataframe(criticos_df[['nome', 'categoria', 'estoque_atual', 'dias_ate_fim', 'quantidade_repor', 'investimento']], 
                               use_container_width=True)
                
                # Lista de produtos em atenção
                if resultado['lista_atencao']:
                    st.subheader("⚠️ Produtos em Atenção")
                    atencao_df = pd.DataFrame(resultado['lista_atencao'])
                    st.dataframe(atencao_df[['nome', 'categoria', 'estoque_atual', 'dias_ate_fim', 'quantidade_repor', 'investimento']], 
                               use_container_width=True)
            else:
                st.error(f"Erro: {resultado.get('mensagem', 'Erro desconhecido')}")
    
    with tab3:
        st.subheader("Análise por Categorias")
        
        if st.button("Analisar Categorias"):
            with st.spinner("Analisando categorias..."):
                resultado = relatorio_categorias(produtos, movimentacoes)
            
            if resultado['sucesso']:
                # Métricas gerais
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Categorias", resultado['total_categorias'])
                with col2:
                    st.metric("Valor Total Estoque", f"R$ {resultado['valor_total_estoque']:.2f}")
                with col3:
                    st.metric("Vendas 30d", resultado['total_vendas_30d'])
                
                # Tabela de categorias
                if resultado['categorias']:
                    st.subheader("Detalhes por Categoria")
                    cat_df = pd.DataFrame(resultado['categorias'])
                    st.dataframe(cat_df, use_container_width=True)
                    
                    # Gráfico de valor por categoria
                    fig = px.bar(cat_df, x='categoria', y='valor_estoque',
                               title="Valor em Estoque por Categoria")
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"Erro: {resultado.get('mensagem', 'Erro desconhecido')}")
    
    with tab4:
        st.subheader("Exportar Relatórios")
        st.info("Exporta todos os relatórios para um arquivo Excel completo")
        
        nome_arquivo = st.text_input("Nome do arquivo (opcional):", placeholder="relatorio_estoque.xlsx")
        
        if st.button("📁 Exportar para Excel"):
            with st.spinner("Exportando relatórios..."):
                arquivo = nome_arquivo if nome_arquivo else None
                resultado = exportar_relatorio_excel(produtos, movimentacoes, arquivo)
            
            if resultado['sucesso']:
                st.success(f"✅ {resultado['mensagem']}")
                st.info(f"Arquivo: {resultado['arquivo']}")
                st.info(f"Tamanho: {resultado['tamanho_kb']} KB")
                st.info(f"Abas criadas: {', '.join(resultado['abas_criadas'])}")
            else:
                st.error(f"Erro: {resultado.get('mensagem', 'Erro desconhecido')}")


# Dicionário de opções do menu
opcoes_menu = {
    "📦 Visualizar Produtos": visualizar_produtos,
    "🔄 Movimentação de Estoque": tela_movimentacao,
    "📜 Histórico de Movimentações": tela_historico,
    "➕ Adicionar Produto": adicionar,
    "✏️ Editar Produto": editar,
    "🗑️ Remover Produto": remover,
    "📊 Dashboard IA": dashboard_ia,
    "🔮 Análise IA": analise_ia,
    "🎓 Treinar IA": treinar_ia,
    "📈 Relatórios": relatorios
}

def main():
    
    st.sidebar.title("Menu")
    opcao_selecionada = st.sidebar.selectbox("Escolha uma ação:", list(opcoes_menu.keys()))

    if opcao_selecionada == "📦 Visualizar Produtos":
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔎 Filtros")  # Aparece só nessa aba

    opcoes_menu[opcao_selecionada]()

if __name__ == "__main__":
    criar_tabelas_movimentacoes()
    criar_tabelas_produtos()
    main()