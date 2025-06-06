import pandas as pd
import os

CSV_PATH = "data/raw/produtos.csv"

def carregar_produtos():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    else:
        print("Arquivo de produtos não encontrado.")
        return pd.DataFrame()

def salvar_produtos(df):
    df.to_csv(CSV_PATH, index=False)

def adicionar_produto(produto):
    df = carregar_produtos()
    novo_id = df["id_produto"].max() + 1 if not df.empty else 1
    produto["id_produto"] = novo_id
    df = pd.concat([df, pd.DataFrame([produto])], ignore_index=True)
    salvar_produtos(df)
    print(f"Produto '{produto['nome']}' adicionado com ID {novo_id}.")

def editar_produto(id_produto, novos_dados):
    df = carregar_produtos()
    if id_produto in df["id_produto"].values:
        df.loc[df["id_produto"] == id_produto, novos_dados.keys()] = list(novos_dados.values())
        salvar_produtos(df)
        print(f"Produto ID {id_produto} atualizado.")
    else:
        print(f"Produto ID {id_produto} não encontrado.")

def remover_produto(id_produto):
    df = carregar_produtos()
    if id_produto in df["id_produto"].values:
        df = df[df["id_produto"] != id_produto]
        salvar_produtos(df)
        print(f"Produto ID {id_produto} removido.")
    else:
        print(f"Produto ID {id_produto} não encontrado.")

def buscar_produto(pesquisa):
    df = carregar_produtos()
    if isinstance(pesquisa, int):
        return df[df["id_produto"] == pesquisa]
    else:
        return df[df["nome"].str.contains(pesquisa, case=False) | df["categoria"].str.contains(pesquisa, case=False)]
