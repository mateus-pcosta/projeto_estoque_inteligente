def formatar_preco(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_nomes_colunas(df):
    df = df.copy()
    nomes_personalizados = {
        "id_produto": "ID Produto",
        "nome": "Nome",
        "categoria": "Categoria",
        "preco_unitario": "Preço Unitário",
        "estoque_atual": "Estoque Atual",
        "vendidos_ultimos_30_dias": "Vendidos dos últimos 30 dias"
    }
    df.rename(columns=nomes_personalizados, inplace=True)
    return df

def formatar_colunas_historico(df):
    df = df.copy()
    nomes_personalizados = {
        "id_movimentacao": "ID Movimentação",
        "id_produto": "ID Produto",
        "tipo": "Tipo",
        "quantidade": "Quantidade",
        "data": "Data",
        "data_formatada": "Data/Hora",
        "usuario": "Usuário",
        "observacao": "Observação"
    }
    df.rename(columns=nomes_personalizados, inplace=True)
    return df