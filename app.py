import streamlit as st
import pandas as pd
from core.gerenciamento_estoque import (
    carregar_produtos, adicionar_produto,
    editar_produto, remover_produto, buscar_produto
)

st.set_page_config(page_title="Estoque Inteligente", layout="wide")
st.title("📦 Estoque Inteligente — Gestão de Produtos")

df = carregar_produtos()

def visualizar_produtos(df):
    st.subheader("📋 Lista de Produtos no Estoque")
    st.dataframe(df)

def buscar():
    st.subheader("🔍 Buscar Produto")
    termo = st.text_input("Digite nome, categoria ou ID:")
    if termo:
        try:
            termo = int(termo)
        except ValueError:
            pass
        resultado = buscar_produto(termo)
        st.dataframe(resultado)

def adicionar():
    st.subheader("➕ Adicionar Novo Produto")
    with st.form("form_adicionar"):
        nome = st.text_input("Nome do Produto")
        categoria = st.text_input("Categoria")
        preco = st.number_input("Preço Unitário", min_value=0.0, step=0.01)
        estoque = st.number_input("Estoque Atual", min_value=0)
        vendidos = st.number_input("Vendidos nos Últimos 30 Dias", min_value=0)
        enviar = st.form_submit_button("Adicionar")

    if enviar:
        novo_produto = {
            "nome": nome,
            "categoria": categoria,
            "preco_unitario": preco,
            "estoque_atual": estoque,
            "vendidos_ultimos_30_dias": vendidos
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
            vendidos = st.number_input("Vendidos", value=produto_encontrado.iloc[0]["vendidos_ultimos_30_dias"])
            enviar = st.form_submit_button("Salvar Alterações")

        if enviar:
            novos_dados = {
                "nome": nome,
                "categoria": categoria,
                "preco_unitario": preco,
                "estoque_atual": estoque,
                "vendidos_ultimos_30_dias": vendidos
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

# Menu lateral

st.sidebar.title("Menu")
opcao = st.sidebar.selectbox("Escolha uma ação:", [
    "Visualizar Produtos",
    "Buscar Produto",
    "Adicionar Produto",
    "Editar Produto",
    "Remover Produto"
])

if opcao == "Visualizar Produtos":
    visualizar_produtos(df)
elif opcao == "Buscar Produto":
    buscar()
elif opcao == "Adicionar Produto":
    adicionar()
elif opcao == "Editar Produto":
    editar()
elif opcao == "Remover Produto":
    remover()
