#Visualização rápida e local dos dados (produtos, alertas, top vendidos)

import pandas as pd

CSV_PATH = "data/raw/produtos.csv"

def carregar_dados():
    try:
        df = pd.read_csv(CSV_PATH)
        return df
    except FileNotFoundError:
        print("Arquivo CSV não encontrado.")
        return pd.DataFrame()

def mostrar_produtos(df):
    print("\n Lista de Produtos:\n")
    print(df[["id_produto", "nome", "categoria", "preco_unitario", "estoque_atual"]])

def alerta_estoque_baixo(df, limite=10):
    print(f"\n Produtos com estoque abaixo de {limite}:\n")
    print(df[df["estoque_atual"] < limite][["nome", "estoque_atual"]])

def top_vendidos(df, top_n=5):
    print(f"\n Top {top_n} produtos mais vendidos (últimos 30 dias):\n")
    print(df.sort_values("vendidos_ultimos_30_dias", ascending=False).head(top_n)[["nome", "vendidos_ultimos_30_dias"]])

def vendas_por_categoria(df):
    print("\n Vendas por Categoria:\n")
    print(df.groupby("categoria")["vendidos_ultimos_30_dias"].sum())
    
# Menu de opções
def menu():
    df = carregar_dados()
    if df.empty:
        return

    while True:
        print("\n=== Menu ===")
        print("1. Mostrar todos os produtos")
        print("2. Alertas de estoque baixo")
        print("3. Top produtos mais vendidos")
        print("4. Vendas por categoria")
        print("5. Sair")

        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            mostrar_produtos(df)
        elif escolha == "2":
            alerta_estoque_baixo(df)
        elif escolha == "3":
            top_vendidos(df)
        elif escolha == "4":
            vendas_por_categoria(df)
        elif escolha == "5":
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    menu()
