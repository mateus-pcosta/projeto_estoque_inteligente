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
    """Adiciona um novo produto ao estoque."""
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
    """Edita um produto existente no estoque."""
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
    """Remove um produto do estoque."""
    st.subheader("🗑️ Remover Produto")
    id_remover = st.number_input("ID do Produto a Remover", min_value=1, step=1)
    if st.button("Remover"):
        remover_produto(int(id_remover))
        st.success("Produto removido com sucesso!")

def visualizar_produtos():
    """Visualiza todos os produtos em estoque com filtros e ranking."""
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
    """Tela para registrar movimentações de estoque (entrada/saída)."""
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
    """Tela para visualizar o histórico de movimentações com filtros e gráficos."""
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
                # Certifique-se de que a coluna existe antes de tentar acessá-la
                if 'vendidos_ultimos_30_dias' in produto_info:
                    st.metric("📈 Vendas 30d", f"{produto_info['vendidos_ultimos_30_dias']} un")
                else:
                    st.metric("📈 Vendas 30d", "N/A")
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
                if 'vendidos_ultimos_30_dias' in produto_info:
                    if produto_info['vendidos_ultimos_30_dias'] > 50:
                        confiabilidade = "Alta"
                        cor = "success"
                    elif produto_info['vendidos_ultimos_30_dias'] > 20:
                        confiabilidade = "Média"
                        cor = "warning"
                    else:
                        confiabilidade = "Baixa"
                        cor = "error"
                else:
                    confiabilidade = "Indisponível"
                    cor = "info" # Use info for N/A cases

                if cor == "success":
                    st.success(f"🎯 Confiabilidade: {confiabilidade}")
                elif cor == "warning":
                    st.warning(f"🎯 Confiabilidade: {confiabilidade}")
                elif cor == "error":
                    st.error(f"🎯 Confiabilidade: {confiabilidade}")
                else: # For 'info' or other cases
                    st.info(f"🎯 Confiabilidade: {confiabilidade}")


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

                            st.plotly_chart(fig, use_container_width=True)

                            # Métricas de vendas
                            st.markdown("##### Resumo de Vendas")
                            col1, col2, col3 = st.columns(3)
                            total_vendido = vendas_diarias['quantidade'].sum()
                            media_diaria = vendas_diarias.groupby(vendas_diarias['data_convertida'].dt.date)['quantidade'].sum().mean()
                            dias_com_venda = vendas_diarias['data_convertida'].dt.date.nunique()

                            with col1:
                                st.metric("Total Vendido", f"{total_vendido} un")
                            with col2:
                                st.metric("Média Diária", f"{media_diaria:.1f} un")
                            with col3:
                                st.metric("Dias com Venda", f"{dias_com_venda} dias")

                        else:
                            st.info("Não há dados de vendas para este produto no período.")

                    with tab2:
                        # Análise de Padrão Semanal
                        vendas_semanais = movs_produto[movs_produto['tipo'] == 'saida'].copy()
                        if not vendas_semanais.empty:
                            vendas_semanais['dia_semana'] = vendas_semanais['data_convertida'].dt.day_name(locale='pt_BR')
                            ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
                            vendas_por_dia_semana = vendas_semanais.groupby('dia_semana')['quantidade'].sum().reindex(ordem_dias).fillna(0).reset_index()
                            vendas_por_dia_semana.columns = ['Dia da Semana', 'Quantidade Vendida']

                            fig_semanal = px.bar(
                                vendas_por_dia_semana,
                                x='Dia da Semana',
                                y='Quantidade Vendida',
                                title=f"📅 Padrão de Vendas Semanal - {produto_nome}",
                                labels={'Quantidade Vendida': 'Unidades Vendidas'},
                                color_discrete_sequence=px.colors.qualitative.Pastel
                            )
                            st.plotly_chart(fig_semanal, use_container_width=True)

                            st.markdown("##### Análise do Padrão Semanal")
                            dia_pico = vendas_por_dia_semana.loc[vendas_por_dia_semana['Quantidade Vendida'].idxmax()]
                            st.info(f"O dia de pico de vendas para **{produto_nome}** é **{dia_pico['Dia da Semana']}** com **{int(dia_pico['Quantidade Vendida'])} unidades**.")
                        else:
                            st.info("Não há dados de vendas para analisar o padrão semanal.")


                    with tab3:
                        # Resumo Financeiro
                        if not movs_produto.empty:
                            movs_produto['custo_total_mov'] = movs_produto['quantidade'] * produto_info['preco_unitario']

                            total_entradas_valor = movs_produto[movs_produto['tipo'] == 'entrada']['custo_total_mov'].sum()
                            total_saidas_valor = movs_produto[movs_produto['tipo'] == 'saida']['custo_total_mov'].sum()

                            st.markdown("##### Resumo Financeiro do Produto")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Valor Entradas", formatar_preco(total_entradas_valor))
                            with col2:
                                st.metric("Valor Saídas (Vendas)", formatar_preco(total_saidas_valor))
                            with col3:
                                st.metric("Diferença de Valor", formatar_preco(total_saidas_valor - total_entradas_valor)) # Lucro/Perda baseando-se nas saídas como vendas

                            st.warning("Nota: O 'Valor Saídas (Vendas)' representa o valor de venda. O lucro real dependeria do custo de aquisição do produto.")
                        else:
                            st.info("Não há dados de movimentação para gerar o resumo financeiro.")

                else:
                    st.info("Não há movimentações suficientes para gerar gráficos detalhados para este produto.")
            else:
                st.info("Não há movimentações registradas para este produto.")
        else:
            st.error(f"❌ Erro ao analisar o produto: {resultado['mensagem']}")

# Cria as tabelas ao iniciar o aplicativo (se não existirem)
criar_tabelas_produtos()
criar_tabelas_movimentacoes()

# Sidebar para navegação
st.sidebar.title("Navegação")
opcao = st.sidebar.radio(
    "Escolha uma opção:",
    ["Visualizar Produtos", "Adicionar Produto", "Editar Produto", "Remover Produto", "Movimentação de Estoque", "Histórico de Movimentações", "Dashboard Inteligente (IA)", "Análise Preditiva (IA)"]
)

# Renderiza a função selecionada
if opcao == "Visualizar Produtos":
    visualizar_produtos()
elif opcao == "Adicionar Produto":
    adicionar()
elif opcao == "Editar Produto":
    editar()
elif opcao == "Remover Produto":
    remover()
elif opcao == "Movimentação de Estoque":
    tela_movimentacao()
elif opcao == "Histórico de Movimentações":
    tela_historico()
elif opcao == "Dashboard Inteligente (IA)":
    dashboard_ia()
elif opcao == "Análise Preditiva (IA)":
    analise_ia()
