import sqlite3
import pandas as pd
import os
from datetime import datetime

CSV_PATH = "data/raw/produtos.csv"
MOVIMENTACOES_PATH = "data/raw/movimentacoes.csv"

def carregar_produtos():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        if "vendidos_ultimos_30_dias" not in df.columns:
            df["vendidos_ultimos_30_dias"] = 0
        return df
    return pd.DataFrame(columns=["id_produto", "nome", "categoria", "preco_unitario", "estoque_atual", "vendidos_ultimos_30_dias"])

def salvar_produtos(df):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    df.to_csv(CSV_PATH, index=False)

def carregar_movimentacoes():
    if os.path.exists(MOVIMENTACOES_PATH):
        return pd.read_csv(MOVIMENTACOES_PATH)
    return pd.DataFrame(columns=["id_movimentacao", "id_produto", "nome", "categoria", "tipo", "quantidade", "data", "usuario", "observacao"])

def salvar_movimentacoes(df):
    os.makedirs(os.path.dirname(MOVIMENTACOES_PATH), exist_ok=True)
    df.to_csv(MOVIMENTACOES_PATH, index=False)

def registrar_movimentacao(id_produto, tipo, quantidade, usuario="Sistema", observacao="", venda=False):
    try:
        produtos = carregar_produtos()
        movimentacoes = carregar_movimentacoes()
        
        if id_produto not in produtos["id_produto"].values:
            raise ValueError("ID de produto inválido")
        
        if tipo == "saida":
            estoque_atual = produtos.loc[produtos["id_produto"] == id_produto, "estoque_atual"].values[0]
            if estoque_atual < quantidade:
                raise ValueError("Quantidade indisponível em estoque")
        
        nova_id = movimentacoes["id_movimentacao"].max() + 1 if not movimentacoes.empty else 1
        produto_info = produtos[produtos["id_produto"] == id_produto].iloc[0]
        nova_mov = pd.DataFrame([{
            "id_movimentacao": nova_id,
            "id_produto": id_produto,
            "nome": produto_info["nome"],
            "categoria": produto_info["categoria"],
            "tipo": tipo,
            "quantidade": quantidade,
            "data": datetime.now().isoformat(sep=' ', timespec='seconds'),
            "usuario": usuario,
            "observacao": observacao
        }])

        if tipo == "entrada":
            produtos.loc[produtos["id_produto"] == id_produto, "estoque_atual"] += quantidade
        else:
            produtos.loc[produtos["id_produto"] == id_produto, "estoque_atual"] -= quantidade

            # Se for uma venda, atualiza a coluna vendidos_ultimos_30_dias
            if venda:
                produtos.loc[produtos["id_produto"] == id_produto, "vendidos_ultimos_30_dias"] += quantidade

        movimentacoes = pd.concat([movimentacoes, nova_mov], ignore_index=True)
        salvar_movimentacoes(movimentacoes)
        salvar_produtos(produtos)
        return True
    except Exception as e:
        print(f"Erro ao registrar movimentação: {str(e)}")
        return False

def adicionar_produto(produto):
    df = carregar_produtos()
    novo_id = df["id_produto"].max() + 1 if not df.empty else 1
    produto["id_produto"] = novo_id
    produto["estoque_atual"] = produto.get("estoque_atual", 0)
    produto["vendidos_ultimos_30_dias"] = 0
    df = pd.concat([df, pd.DataFrame([produto])], ignore_index=True)
    salvar_produtos(df)
    return novo_id

def editar_produto(id_produto, novos_dados):
    df = carregar_produtos()
    if id_produto not in df["id_produto"].values:
        raise ValueError("ID de produto não encontrado")
    
    for chave, valor in novos_dados.items():
        if chave in df.columns:
            df.loc[df["id_produto"] == id_produto, chave] = valor
    
    salvar_produtos(df)
    return True

def remover_produto(id_produto):
    df = carregar_produtos()
    if id_produto not in df["id_produto"].values:
        raise ValueError("ID de produto não encontrado")
    df = df[df["id_produto"] != id_produto]
    salvar_produtos(df)
    return True

def buscar_produto(termo):
    df = carregar_produtos()
    if isinstance(termo, int):
        resultado = df[df["id_produto"] == termo]
    else:
        termo = termo.lower()
        mask = (
            df["nome"].str.lower().str.contains(termo) |
            df["categoria"].str.lower().str.contains(termo)
        )
        resultado = df[mask]
    return resultado

def verificar_estoque_baixo(limite=10):
    df = carregar_produtos()
    return df[df['estoque_atual'] < limite]

def criar_tabelas_movimentacoes():
    con = sqlite3.connect('data/raw/movimentacoes.db')

    cur = con.cursor()

    cur.execute(
    """CREATE TABLE if not exists movimentacoes(
    id_movimentacao INT PRIMARY KEY,
    id_produto INT NOT NULL,
    tipo VARCHAR(10) CHECK (tipo IN ('entrada', 'saida')),
    quantidade INT NOT NULL,
    data TIMESTAMP NOT NULL,
    usuario VARCHAR(50),
    observacao TEXT,
    nome VARCHAR(100),
    categoria VARCHAR(100)
    );""")

    con.close()

def criar_tabelas_produtos():
    con = sqlite3.connect('data/raw/estoque.db')

    cur = con.cursor()

    cur.execute(
    """CREATE TABLE if not exists produtos(
    id_produto INT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    categoria VARCHAR(50),
    preco_unitario DECIMAL(10, 2) NOT NULL,
    estoque_atual INT NOT NULL,
    vendidos_ultimos_30_dias INT DEFAULT 0
    );"""
    )

    con.close()
