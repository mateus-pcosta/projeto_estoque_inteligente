import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.helpers import formatar_preco, formatar_nomes_colunas, formatar_colunas_historico
from core.gerenciamento_estoque import (
    carregar_produtos, adicionar_produto, editar_produto,
    remover_produto, buscar_produto, registrar_movimentacao,
    verificar_estoque_baixo, carregar_movimentacoes
)

st.set_page_config(
    page_title="Estoque Inteligente",
    page_icon="📦",
    layout="wide"
)

# Header principal
st.title("📦 Estoque Inteligente")
st.markdown("---")

# Dashboard Principal
def dashboard_principal():
    st.subheader("📊 Dashboard Principal")
    
    try:
        produtos = carregar_produtos()
        movimentacoes = carregar_movimentacoes()
        
        if produtos.empty:
            st.warning("📦 Nenhum produto cadastrado ainda!")
            return
        
        # Cards de métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_produtos = len(produtos)
            st.metric("📦 Total de Produtos", total_produtos)
        
        with col2:
            estoque_baixo = len(produtos[produtos["estoque_atual"] < 10])
            st.metric("⚠️ Estoque Baixo", estoque_baixo, delta=f"-{estoque_baixo}" if estoque_baixo > 0 else None)
        
        with col3:
            valor_total = (produtos["estoque_atual"] * produtos["preco_unitario"]).sum()
            st.metric("💰 Valor Total Estoque", f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        with col4:
            vendas_mes = produtos["vendidos_ultimos_30_dias"].sum()
            st.metric("📈 Vendas (30 dias)", vendas_mes)
        
        st.markdown("---")
        
        # Gráficos lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de estoque por categoria
            st.subheader("📊 Estoque por Categoria")
            estoque_categoria = produtos.groupby("categoria")["estoque_atual"].sum().reset_index()
            
            if not estoque_categoria.empty:
                fig_estoque = px.bar(
                    estoque_categoria, 
                    x="categoria", 
                    y="estoque_atual",
                    title="Distribuição do Estoque",
                    color="estoque_atual",
                    color_continuous_scale="Blues"
                )
                fig_estoque.update_layout(height=400)
                st.plotly_chart(fig_estoque, use_container_width=True)
        
        with col2:
            # Gráfico de vendas por categoria
            st.subheader("💰 Vendas por Categoria")
            vendas_categoria = produtos.groupby("categoria")["vendidos_ultimos_30_dias"].sum().reset_index()
            
            if not vendas_categoria.empty:
                fig_vendas = px.pie(
                    vendas_categoria,
                    values="vendidos_ultimos_30_dias",
                    names="categoria",
                    title="Vendas dos Últimos 30 Dias"
                )
                fig_vendas.update_layout(height=400)
                st.plotly_chart(fig_vendas, use_container_width=True)
        
        # Produtos com estoque baixo
        if estoque_baixo > 0:
            st.subheader("⚠️ Produtos com Estoque Baixo")
            produtos_baixo = produtos[produtos["estoque_atual"] < 10][["nome", "categoria", "estoque_atual", "vendidos_ultimos_30_dias"]]
            produtos_baixo = formatar_nomes_colunas(produtos_baixo)
            st.dataframe(produtos_baixo, use_container_width=True)
        
        # Top produtos mais vendidos
        st.subheader("🏆 Top 10 Produtos Mais Vendidos")
        top_vendidos = produtos.nlargest(10, "vendidos_ultimos_30_dias")[["nome", "categoria", "vendidos_ultimos_30_dias", "estoque_atual"]]
        
        if not top_vendidos.empty:
            fig_top = px.bar(
                top_vendidos,
                x="vendidos_ultimos_30_dias",
                y="nome",
                orientation="h",
                title="Produtos Mais Vendidos (30 dias)",
                color="vendidos_ultimos_30_dias",
                color_continuous_scale="Reds"
            )
            fig_top.update_layout(height=400)
            st.plotly_chart(fig_top, use_container_width=True)
        
        # Análise com Gemini IA
        st.markdown("---")
        st.subheader("🤖 Análise com Inteligência Artificial")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🚀 Executar Análise de Demanda com IA", type="primary", use_container_width=True):
                with st.spinner("🤖 IA analisando seus dados..."):
                    try:
                        from core.previsao_demanda import executar_analise_completa
                        resultado = executar_analise_completa()
                        
                        if resultado.get('sucesso'):
                            st.success("✅ Análise concluída com sucesso!")
                            
                            # Mostra resumo
                            resumo = resultado.get('resumo', {})
                            st.info(f"📊 {resumo.get('total_produtos', 0)} produtos analisados | ⚠️ {resumo.get('produtos_risco', 0)} em risco de ruptura")
                            
                            # Mostra insights da IA
                            analise = resultado.get('analise', {})
                            if 'resumo_geral' in analise:
                                recomendacoes = analise['resumo_geral'].get('recomendacoes_gerais', [])
                                if recomendacoes:
                                    st.markdown("**💡 Insights da IA:**")
                                    for rec in recomendacoes[:3]:
                                        st.markdown(f"• {rec}")
                        else:
                            st.error(f"❌ Erro na análise: {resultado.get('erro')}")
                            
                    except Exception as e:
                        st.error(f"❌ Erro ao executar análise IA: {str(e)}")
                        st.info("💡 Verifique se a API do Gemini está configurada em 'Configurações'")
        
        with col2:
            # Status da IA
            try:
                from utils.config import GEMINI_API_KEY
                if GEMINI_API_KEY and GEMINI_API_KEY != "sua_chave_api_do_gemini_aqui":
                    st.success("🤖 **IA Ativada**\nGemini configurado")
                else:
                    st.warning("⚠️ **IA Offline**\nConfigure Gemini em 'Configurações'")
            except:
                st.error("❌ **Erro de Config**\nVerifique configurações")
        
    except Exception as e:
        st.error(f"Erro no dashboard: {str(e)}")

def adicionar():
    st.subheader("➕ Adicionar Novo Produto")
    with st.form("form_adicionar"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome do Produto")
            categoria = st.selectbox("Categoria", ["Bebidas", "Salgados", "Lanches", "Porções", "Sobremesas", "Frutas"])
        
        with col2:
            preco = st.number_input("Preço Unitário", min_value=0.0, step=0.01)
            estoque = st.number_input("Estoque Atual", min_value=0)
        
        enviar = st.form_submit_button("Adicionar", type="primary")

    if enviar:
        if nome and categoria:
            novo_produto = {
                "nome": nome,
                "categoria": categoria,
                "preco_unitario": preco,
                "estoque_atual": estoque
            }
            adicionar_produto(novo_produto)
            st.success(f"Produto '{nome}' adicionado com sucesso!")
        else:
            st.error("Nome e categoria são obrigatórios!")

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

        # Filtros na sidebar
        st.sidebar.subheader("🔎 Filtros")
        
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

        # Formata colunas
        df_formatado = formatar_nomes_colunas(df_filtrado)
        df_formatado["Preço Unitário"] = df_formatado["Preço Unitário"].apply(formatar_preco)

        # Adiciona destaque para produtos com estoque baixo
        def highlight_baixo_estoque(val):
            if val < 10:
                return 'background-color: #ffcccc'
            return ''

        styled_df = df_formatado.style.applymap(highlight_baixo_estoque, subset=['Estoque Atual'])
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Legenda
        st.caption("🔴 Produtos com fundo vermelho têm estoque baixo (<10 unidades)")

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

    # Checkbox para venda 
    foi_venda = st.checkbox("🛒 Esta saída é uma VENDA? (importante para análises IA)", value=False)

    col_entrada, col_saida = st.columns(2)
    
    with col_entrada:
        if st.button("🔼 Registrar Entrada", help="Adiciona itens ao estoque", use_container_width=True):
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
        if st.button("🔽 Registrar Saída", help="Remove itens do estoque", use_container_width=True):
            try:
                resultado = registrar_movimentacao(
                    id_produto=id_produto,
                    tipo="saida",
                    quantidade=quantidade,
                    observacao=observacao,
                    venda=foi_venda
                )
                if resultado:
                    if foi_venda:
                        st.success("🛒 Venda registrada com sucesso!")
                    else:
                        st.success("✅ Saída registrada com sucesso!")
                else:
                    st.error("❌ Falha ao registrar saída")
            except Exception as e:
                st.error(f"Erro: {str(e)}")

def tela_historico():
    st.subheader("📜 Histórico de Movimentações")

    try:
        movimentacoes = carregar_movimentacoes()
        produtos = carregar_produtos()

        if not movimentacoes.empty:
            # Convertendo a coluna de data
            try:
                movimentacoes["data"] = pd.to_datetime(movimentacoes["data"], format='mixed')
            except:
                movimentacoes["data"] = pd.to_datetime(movimentacoes["data"], errors='coerce')

            movimentacoes = movimentacoes.dropna(subset=['data'])
            movimentacoes["data_formatada"] = movimentacoes["data"].dt.strftime("%d/%m/%Y %H:%M")

            # Junta o nome e categoria dos produtos
            produtos_reduzido = produtos[["id_produto", "nome", "categoria"]]
            movimentacoes = movimentacoes.merge(produtos_reduzido, on="id_produto", how="left")

            # Filtros na sidebar
            st.sidebar.subheader("🔍 Filtros - Histórico")

            tipos = list(movimentacoes["tipo"].dropna().unique())
            tipos_exibicao = ["Todos"] + sorted(tipos)
            tipo_filtro = st.sidebar.selectbox("Tipo de Movimentação", tipos_exibicao)

            produtos_opcoes = movimentacoes["nome"].dropna().unique()
            produto_filtro = st.sidebar.multiselect("Produto", produtos_opcoes, default=list(produtos_opcoes))

            df_filtrado = movimentacoes[
                ((movimentacoes["tipo"] == tipo_filtro) if tipo_filtro != "Todos" else True) &
                (movimentacoes["nome"].isin(produto_filtro))
            ]

            termo_busca = st.text_input("🔎 Buscar por Produto ou Categoria:")
            if termo_busca:
                termo = termo_busca.lower()
                df_filtrado = df_filtrado[
                    df_filtrado["nome"].str.lower().str.contains(termo) |
                    df_filtrado["categoria"].str.lower().str.contains(termo)
                ]

            df_filtrado = formatar_colunas_historico(df_filtrado)

            st.dataframe(
                df_filtrado.sort_values("Data", ascending=False).drop(columns="Data"),
                use_container_width=True
            )
        else:
            st.warning("Nenhuma movimentação registrada ainda")
    except Exception as e:
        st.error(f"Erro ao processar movimentações: {str(e)}")

def configuracoes():
    st.subheader("⚙️ Configurações do Sistema")
    
    # Teste da API Gemini
    st.markdown("#### 🤖 Configuração da IA (Gemini)")
    
    try:
        from utils.config import GEMINI_API_KEY
        
        if GEMINI_API_KEY and GEMINI_API_KEY != "sua_chave_api_do_gemini_aqui":
            st.success("✅ API Gemini configurada")
            
            if st.button("🧪 Testar Conexão com Gemini"):
                with st.spinner("Testando conexão..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=GEMINI_API_KEY)
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        
                        response = model.generate_content("Responda apenas: 'Conexão OK'")
                        
                        if response.text.strip():
                            st.success("✅ Conexão com Gemini funcionando!")
                            st.info(f"Resposta da IA: {response.text}")
                        else:
                            st.error("❌ Resposta vazia da API")
                            
                    except Exception as e:
                        st.error(f"❌ Erro na conexão: {str(e)}")
        else:
            st.warning("⚠️ API Gemini não configurada")
            st.markdown("""
            **Para configurar:**
            1. Acesse: https://makersuite.google.com/app/apikey
            2. Crie uma chave API gratuita
            3. Execute: `python setup_env.py`
            4. Cole sua chave quando solicitado
            """)
    
    except Exception as e:
        st.error(f"Erro ao verificar configuração: {str(e)}")
    
    st.markdown("---")
    
    # Informações do sistema
    st.markdown("#### 📊 Informações do Sistema")
    
    try:
        produtos = carregar_produtos()
        movimentacoes = carregar_movimentacoes()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📦 Total de Produtos", len(produtos))
            st.metric("📜 Total de Movimentações", len(movimentacoes))
        
        with col2:
            estoque_baixo = len(produtos[produtos["estoque_atual"] < 10]) if not produtos.empty else 0
            st.metric("⚠️ Produtos com Estoque Baixo", estoque_baixo)
            
            vendas_mes = produtos["vendidos_ultimos_30_dias"].sum() if not produtos.empty else 0
            st.metric("💰 Vendas (30 dias)", vendas_mes)
    
    except Exception as e:
        st.error(f"Erro ao carregar informações: {str(e)}")

# Menu principal
def main():
    # Menu de navegação na sidebar
    st.sidebar.title("🧭 Navegação")
    
    opcoes = [
        "📊 Dashboard",
        "📦 Visualizar Produtos", 
        "🔄 Movimentação",
        "📜 Histórico",
        "➕ Adicionar Produto",
        "✏️ Editar Produto", 
        "🗑️ Remover Produto",
        "⚙️ Configurações"
    ]
    
    opcao = st.sidebar.selectbox("Escolha uma opção:", opcoes)
    
    # Executa a função correspondente
    if opcao == "📊 Dashboard":
        dashboard_principal()
    elif opcao == "📦 Visualizar Produtos":
        st.sidebar.markdown("---")
        visualizar_produtos()
    elif opcao == "🔄 Movimentação":
        tela_movimentacao()
    elif opcao == "📜 Histórico":
        st.sidebar.markdown("---")
        tela_historico()
    elif opcao == "➕ Adicionar Produto":
        adicionar()
    elif opcao == "✏️ Editar Produto":
        editar()
    elif opcao == "🗑️ Remover Produto":
        remover()
    elif opcao == "⚙️ Configurações":
        configuracoes()

if __name__ == "__main__":
    main()