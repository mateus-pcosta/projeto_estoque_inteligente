import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import formatar_preco, formatar_nomes_colunas, formatar_colunas_historico
from core.gerenciamento_estoque import (
    carregar_produtos, adicionar_produto, editar_produto,
    remover_produto, buscar_produto, registrar_movimentacao,
    verificar_estoque_baixo, carregar_movimentacoes, criar_tabelas_movimentacoes, 
    criar_tabelas_produtos
)

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

        st.dataframe(df_formatado.sort_values("ID Produto"))

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
            tipo_filtro = st.sidebar.selectbox(
                "Tipo de Movimentação",
                options=["Todos"] + list(tipos)
            )

            produtos_opcoes = movimentacoes["nome"].unique()
            produto_filtro = st.sidebar.multiselect(
                "Produto",
                options=produtos_opcoes,
                default=list(produtos_opcoes)
            )

            categorias = movimentacoes["categoria"].unique()
            categoria_filtro = st.sidebar.multiselect(
                "Categoria",
                options=categorias,
                default=list(categorias)
            )

            data_min = movimentacoes["data"].min().date()
            data_max = movimentacoes["data"].max().date()
            data_inicio, data_fim = st.sidebar.date_input(
                "Período",
                value=(data_min, data_max)
            )
            
            qtd_min = int(movimentacoes["quantidade"].min())
            qtd_max = int(movimentacoes["quantidade"].max())
            qtd_range = st.sidebar.slider(
                "Quantidade",
                min_value=qtd_min,
                max_value=qtd_max,
                value=(qtd_min, qtd_max)
            )

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
            
        else:
            st.warning("Nenhuma movimentação registrada ainda")
            
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {str(e)}")
        
opcoes_menu = {
    "Visualizar Produtos": visualizar_produtos,
    "Movimentação de Estoque": tela_movimentacao,
    "Histórico de Movimentações": tela_historico,
    "Adicionar Produto": adicionar,
    "Editar Produto": editar,
    "Remover Produto": remover
}

def main():
    
    st.sidebar.title("Menu")
    opcao_selecionada = st.sidebar.selectbox("Escolha uma ação:", list(opcoes_menu.keys()))

    if opcao_selecionada == "Visualizar Produtos":
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔎 Filtros")  # Aparece só nessa aba

    opcoes_menu[opcao_selecionada]()

if __name__ == "__main__":
    criar_tabelas_movimentacoes()
    criar_tabelas_produtos()
    main()
