import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import formatar_preco, formatar_nomes_colunas, formatar_colunas_historico
from core.gerenciamento_estoque import (
    carregar_produtos, adicionar_produto, editar_produto,
    remover_produto, buscar_produto, registrar_movimentacao,
    verificar_estoque_baixo, carregar_movimentacoes
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
    st.subheader("📋 Lista de Produtos")

    produtos = carregar_produtos()
    produtos_raw = produtos.copy()

    # Filtros na barra lateral
    categorias = produtos_raw["categoria"].dropna().unique()
    categoria_selecionada = st.sidebar.selectbox("Categoria:", options=["Todas"] + list(categorias))

    preco_min = float(produtos_raw["preco_unitario"].min())
    preco_max = float(produtos_raw["preco_unitario"].max())
    faixa_preco = st.sidebar.slider(
        "Faixa de Preço (R$):", min_value=preco_min, max_value=preco_max,
        value=(preco_min, preco_max), step=0.01
    )

    estoque_min = int(produtos_raw["estoque_atual"].min())
    estoque_max = int(produtos_raw["estoque_atual"].max())
    faixa_estoque = st.sidebar.slider(
        "Estoque Atual:", min_value=estoque_min, max_value=estoque_max,
        value=(estoque_min, estoque_max), step=1
    )

    termo = st.text_input("🔍 Buscar por nome, categoria ou ID:")

    produtos_filtrados = produtos_raw.copy()

    if categoria_selecionada != "Todas":
        produtos_filtrados = produtos_filtrados[produtos_filtrados["categoria"] == categoria_selecionada]

    produtos_filtrados = produtos_filtrados[
        (produtos_filtrados["preco_unitario"] >= faixa_preco[0]) &
        (produtos_filtrados["preco_unitario"] <= faixa_preco[1]) &
        (produtos_filtrados["estoque_atual"] >= faixa_estoque[0]) &
        (produtos_filtrados["estoque_atual"] <= faixa_estoque[1])
    ]

    if termo:
        termo_lower = termo.lower()
        try:
            termo_int = int(termo)
            produtos_filtrados = produtos_filtrados[produtos_filtrados["id_produto"] == termo_int]
        except ValueError:
            produtos_filtrados = produtos_filtrados[
                produtos_filtrados["nome"].str.lower().str.contains(termo_lower) |
                produtos_filtrados["categoria"].str.lower().str.contains(termo_lower)
            ]

    produtos_filtrados["preco_unitario"] = produtos_filtrados["preco_unitario"].apply(formatar_preco)
    produtos_filtrados = formatar_nomes_colunas(produtos_filtrados)

    estoque_baixo = verificar_estoque_baixo()
    if not estoque_baixo.empty:
        st.warning(f"⚠️ {len(estoque_baixo)} produto(s) com estoque baixo:")
        estoque_baixo = formatar_nomes_colunas(estoque_baixo)
        st.dataframe(estoque_baixo[["Id do produto", "Nome", "Estoque Atual"]])

    st.dataframe(produtos_filtrados)

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

    col_entrada, col_saida, _ = st.columns([1, 1, 2])
    with col_entrada:
        if st.button("🔼 Registrar Entrada", help="Adiciona itens ao estoque"):
            if registrar_movimentacao(id_produto, "entrada", quantidade, observacao=observacao):
                st.success("Entrada registrada com sucesso!")

    with col_saida:
        if st.button("🔽 Registrar Saída", help="Remove itens do estoque"):
            if registrar_movimentacao(id_produto, "saida", quantidade, observacao=observacao):
                st.success("Saída registrada com sucesso!")

def tela_historico():
    st.subheader("📜 Histórico de Movimentações")

    try:
        movimentacoes = carregar_movimentacoes()
        if not movimentacoes.empty:
            try:
                movimentacoes["data"] = pd.to_datetime(movimentacoes["data"], format='mixed')
            except:
                movimentacoes["data"] = pd.to_datetime(movimentacoes["data"], errors='coerce')

            movimentacoes = movimentacoes.dropna(subset=['data'])
            movimentacoes["data_formatada"] = movimentacoes["data"].dt.strftime("%d/%m/%Y %H:%M")
            movimentacoes = formatar_colunas_historico(movimentacoes)

            st.dataframe(
                movimentacoes.sort_values("Data", ascending=False).drop(columns="Data"),
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
    main()
