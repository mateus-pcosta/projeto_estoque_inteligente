#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os

def relatorio_vendas_periodo(movimentacoes_df: pd.DataFrame, dias: int = 30) -> Dict:
    """
    Gera relatorio de vendas para um periodo especifico.
    
    Args:
        movimentacoes_df: DataFrame com as movimentacoes
        dias: Numero de dias para analisar (padrao: 30)
    
    Returns:
        Dict com dados do relatorio de vendas
    """
    try:
        # Converte datas para garantir formato correto
        movimentacoes_df = movimentacoes_df.copy()
        movimentacoes_df['data'] = pd.to_datetime(movimentacoes_df['data'], format='mixed', errors='coerce')
        
        # Remove linhas com datas invalidas
        movimentacoes_df = movimentacoes_df.dropna(subset=['data'])
        
        # Filtra apenas saidas (vendas) no periodo
        data_limite = datetime.now() - timedelta(days=dias)
        vendas = movimentacoes_df[
            (movimentacoes_df['tipo'] == 'saida') & 
            (movimentacoes_df['data'] >= data_limite)
        ].copy()
        
        if vendas.empty:
            return {
                'sucesso': True,
                'periodo_dias': dias,
                'total_vendas': 0,
                'quantidade_total': 0,
                'produtos_vendidos': 0,
                'vendas_por_dia': [],
                'vendas_por_produto': [],
                'vendas_por_categoria': [],
                'mensagem': 'Nenhuma venda encontrada no periodo'
            }
        
        # Calcula totais
        quantidade_total = int(vendas['quantidade'].sum())
        produtos_vendidos = int(vendas['id_produto'].nunique())
        
        # Vendas por dia
        vendas['data_str'] = vendas['data'].dt.strftime('%Y-%m-%d')
        vendas_por_dia = vendas.groupby('data_str')['quantidade'].sum().reset_index()
        vendas_por_dia = vendas_por_dia.sort_values('data_str')
        
        vendas_dia_list = []
        for _, row in vendas_por_dia.iterrows():
            vendas_dia_list.append({
                'data': row['data_str'],
                'quantidade': int(row['quantidade'])
            })
        
        # Vendas por produto
        vendas_por_produto = vendas.groupby(['id_produto', 'nome'])['quantidade'].sum().reset_index()
        vendas_por_produto = vendas_por_produto.sort_values('quantidade', ascending=False)
        
        vendas_produto_list = []
        for _, row in vendas_por_produto.iterrows():
            vendas_produto_list.append({
                'produto': row['nome'] if pd.notna(row['nome']) else f"Produto ID {row['id_produto']}",
                'quantidade': int(row['quantidade'])
            })
        
        # Vendas por categoria
        vendas_categoria = vendas.groupby('categoria')['quantidade'].sum().reset_index()
        vendas_categoria = vendas_categoria.sort_values('quantidade', ascending=False)
        
        vendas_categoria_list = []
        for _, row in vendas_categoria.iterrows():
            categoria = row['categoria'] if pd.notna(row['categoria']) else 'Sem categoria'
            vendas_categoria_list.append({
                'categoria': categoria,
                'quantidade': int(row['quantidade'])
            })
        
        return {
            'sucesso': True,
            'periodo_dias': dias,
            'total_vendas': len(vendas),
            'quantidade_total': quantidade_total,
            'produtos_vendidos': produtos_vendidos,
            'media_diaria': round(quantidade_total / dias, 2),
            'vendas_por_dia': vendas_dia_list,
            'vendas_por_produto': vendas_produto_list,
            'vendas_por_categoria': vendas_categoria_list
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'mensagem': 'Erro ao gerar relatorio de vendas'
        }


def relatorio_estoque_critico(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame) -> Dict:
    """
    Gera relatorio de produtos com estoque critico.
    
    Args:
        produtos_df: DataFrame com dados dos produtos
        movimentacoes_df: DataFrame com movimentacoes
    
    Returns:
        Dict com produtos criticos e estatisticas
    """
    try:
        from core.previsao_demanda import classificar_urgencia_produto
        
        produtos_criticos = []
        produtos_atencao = []
        produtos_normais = []
        
        for _, produto in produtos_df.iterrows():
            analise = classificar_urgencia_produto(produtos_df, movimentacoes_df, produto['id_produto'])
            
            if analise['sucesso']:
                produto_info = {
                    'id': produto['id_produto'],  
                    'nome': produto['nome'],
                    'categoria': produto['categoria'],
                    'estoque_atual': produto['estoque_atual'],
                    'preco_unitario': produto['preco_unitario'],
                    'urgencia': analise['urgencia'],
                    'dias_ate_fim': analise['dias_ate_fim'],
                    'quantidade_repor': analise['quantidade_repor'],
                    'investimento': analise['investimento']
                }
                
                if analise['urgencia'] == 'CRITICO':
                    produtos_criticos.append(produto_info)
                elif analise['urgencia'] == 'ATENCAO':
                    produtos_atencao.append(produto_info)
                else:
                    produtos_normais.append(produto_info)
        
        # Ordena por urgencia
        produtos_criticos.sort(key=lambda x: x['dias_ate_fim'])
        produtos_atencao.sort(key=lambda x: x['dias_ate_fim'])
        
        # Calcula investimentos
        investimento_critico = sum(p['investimento'] for p in produtos_criticos)
        investimento_atencao = sum(p['investimento'] for p in produtos_atencao)
        investimento_total = investimento_critico + investimento_atencao
        
        return {
            'sucesso': True,
            'total_produtos': len(produtos_df),
            'produtos_criticos': len(produtos_criticos),
            'produtos_atencao': len(produtos_atencao),
            'produtos_normais': len(produtos_normais),
            'investimento_critico': round(investimento_critico, 2),
            'investimento_atencao': round(investimento_atencao, 2),
            'investimento_total': round(investimento_total, 2),
            'lista_criticos': produtos_criticos,
            'lista_atencao': produtos_atencao,
            'resumo_categorias': _resumo_por_categoria(produtos_criticos + produtos_atencao)
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'mensagem': 'Erro ao gerar relatorio de estoque critico'
        }


def relatorio_categorias(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame) -> Dict:
    """
    Gera relatorio de analise por categorias.
    
    Args:
        produtos_df: DataFrame com dados dos produtos
        movimentacoes_df: DataFrame com movimentacoes
    
    Returns:
        Dict com analise por categorias
    """
    try:
        # Converte datas
        movimentacoes_df = movimentacoes_df.copy()
        movimentacoes_df['data'] = pd.to_datetime(movimentacoes_df['data'], format='mixed', errors='coerce')
        movimentacoes_df = movimentacoes_df.dropna(subset=['data'])
        
        # Ultimos 30 dias
        data_limite = datetime.now() - timedelta(days=30)
        vendas_recentes = movimentacoes_df[
            (movimentacoes_df['tipo'] == 'saida') & 
            (movimentacoes_df['data'] >= data_limite)
        ]
        
        categorias_info = []
        
        # Agrupa produtos por categoria
        for categoria, produtos_cat in produtos_df.groupby('categoria'):
            categoria_nome = categoria if pd.notna(categoria) else 'Sem categoria'
            
            # Estatisticas basicas
            total_produtos = len(produtos_cat)
            estoque_total = int(produtos_cat['estoque_atual'].sum())
            valor_estoque = float((produtos_cat['estoque_atual'] * produtos_cat['preco_unitario']).sum())
            
            # Vendas da categoria
            ids_categoria = produtos_cat['id_produto'].tolist()
            vendas_categoria = vendas_recentes[vendas_recentes['id_produto'].isin(ids_categoria)]
            
            total_vendido = int(vendas_categoria['quantidade'].sum()) if not vendas_categoria.empty else 0
            
            # Produtos com problema de estoque
            produtos_criticos = 0
            produtos_zerados = 0
            
            for _, produto in produtos_cat.iterrows():
                if produto['estoque_atual'] == 0:
                    produtos_zerados += 1
                elif produto['estoque_atual'] <= 5:  # Criterio simples para critico
                    produtos_criticos += 1
            
            # Produto mais vendido da categoria
            produto_top = None
            if not vendas_categoria.empty:
                vendas_por_produto = vendas_categoria.groupby('id_produto')['quantidade'].sum()
                if not vendas_por_produto.empty:
                    id_top = vendas_por_produto.idxmax()
                    produto_info = produtos_cat[produtos_cat['id_produto'] == id_top]
                    if not produto_info.empty:
                        produto_top = {
                            'nome': produto_info['nome'].iloc[0],
                            'vendas': int(vendas_por_produto.max())
                        }
            
            categorias_info.append({
                'categoria': categoria_nome,
                'total_produtos': total_produtos,
                'estoque_total': estoque_total,
                'valor_estoque': round(valor_estoque, 2),
                'total_vendido_30d': total_vendido,
                'produtos_criticos': produtos_criticos,
                'produtos_zerados': produtos_zerados,
                'produto_mais_vendido': produto_top,
                'giro_categoria': round(total_vendido / max(estoque_total, 1), 2)
            })
        
        # Ordena por valor do estoque
        categorias_info.sort(key=lambda x: x['valor_estoque'], reverse=True)
        
        # Estatisticas gerais
        total_valor_estoque = sum(cat['valor_estoque'] for cat in categorias_info)
        total_vendas_30d = sum(cat['total_vendido_30d'] for cat in categorias_info)
        
        return {
            'sucesso': True,
            'total_categorias': len(categorias_info),
            'valor_total_estoque': round(total_valor_estoque, 2),
            'total_vendas_30d': total_vendas_30d,
            'categorias': categorias_info,
            'categoria_maior_estoque': categorias_info[0]['categoria'] if categorias_info else None,
            'categoria_mais_vendas': max(categorias_info, key=lambda x: x['total_vendido_30d'])['categoria'] if categorias_info else None
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'mensagem': 'Erro ao gerar relatorio de categorias'
        }


def exportar_relatorio_excel(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame, 
                           arquivo: str = None) -> Dict:
    """
    Exporta relatorios completos para arquivo Excel.
    
    Args:
        produtos_df: DataFrame com dados dos produtos
        movimentacoes_df: DataFrame com movimentacoes
        arquivo: Nome do arquivo (opcional)
    
    Returns:
        Dict com resultado da exportacao
    """
    try:
        # Define nome do arquivo
        if not arquivo:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            arquivo = f'relatorio_estoque_{timestamp}.xlsx'
        
        # Garante que o diretorio existe
        os.makedirs('relatorios', exist_ok=True)
        caminho_completo = os.path.join('relatorios', arquivo)
        
        # Gera todos os relatorios
        rel_vendas = relatorio_vendas_periodo(movimentacoes_df, 30)
        rel_critico = relatorio_estoque_critico(produtos_df, movimentacoes_df)
        rel_categorias = relatorio_categorias(produtos_df, movimentacoes_df)
        
        # Cria o arquivo Excel
        with pd.ExcelWriter(caminho_completo, engine='openpyxl') as writer:
            
            # Aba 1: Produtos
            produtos_df.to_excel(writer, sheet_name='Produtos', index=False)
            
            # Aba 2: Movimentacoes recentes (ultimos 30 dias)
            movimentacoes_df_temp = movimentacoes_df.copy()
            movimentacoes_df_temp['data'] = pd.to_datetime(movimentacoes_df_temp['data'], format='mixed', errors='coerce')
            movimentacoes_recentes = movimentacoes_df_temp[
                movimentacoes_df_temp['data'] >= (datetime.now() - timedelta(days=30))
            ].sort_values('data', ascending=False)
            movimentacoes_recentes.to_excel(writer, sheet_name='Movimentacoes_30d', index=False)
            
            # Aba 3: Estoque Critico
            if rel_critico['sucesso'] and (rel_critico['lista_criticos'] or rel_critico['lista_atencao']):
                criticos_df = pd.DataFrame(rel_critico['lista_criticos'] + rel_critico['lista_atencao'])
                criticos_df.to_excel(writer, sheet_name='Estoque_Critico', index=False)
            
            # Aba 4: Vendas por Produto
            if rel_vendas['sucesso'] and rel_vendas['vendas_por_produto']:
                vendas_produto_df = pd.DataFrame(rel_vendas['vendas_por_produto'])
                vendas_produto_df.to_excel(writer, sheet_name='Vendas_Produto', index=False)
            
            # Aba 5: Analise por Categoria
            if rel_categorias['sucesso'] and rel_categorias['categorias']:
                categorias_df = pd.DataFrame(rel_categorias['categorias'])
                categorias_df.to_excel(writer, sheet_name='Analise_Categorias', index=False)
            
            # Aba 6: Resumo Executivo
            resumo_data = []
            
            # Dados gerais
            resumo_data.append(['=== RESUMO EXECUTIVO ===', ''])
            resumo_data.append(['Data do Relatorio', datetime.now().strftime('%d/%m/%Y %H:%M')])
            resumo_data.append(['', ''])
            
            # Produtos
            resumo_data.append(['=== PRODUTOS ===', ''])
            resumo_data.append(['Total de Produtos', len(produtos_df)])
            resumo_data.append(['Valor Total em Estoque', f"R$ {rel_categorias.get('valor_total_estoque', 0):,.2f}"])
            resumo_data.append(['', ''])
            
            # Estoque Critico
            if rel_critico['sucesso']:
                resumo_data.append(['=== ESTOQUE CRITICO ===', ''])
                resumo_data.append(['Produtos Criticos', rel_critico['produtos_criticos']])
                resumo_data.append(['Produtos Atencao', rel_critico['produtos_atencao']])
                resumo_data.append(['Investimento Necessario', f"R$ {rel_critico['investimento_total']:,.2f}"])
                resumo_data.append(['', ''])
            
            # Vendas
            if rel_vendas['sucesso']:
                resumo_data.append(['=== VENDAS (30 DIAS) ===', ''])
                resumo_data.append(['Total de Vendas', rel_vendas['total_vendas']])
                resumo_data.append(['Quantidade Vendida', rel_vendas['quantidade_total']])
                resumo_data.append(['Media Diaria', rel_vendas.get('media_diaria', 0)])
                resumo_data.append(['Produtos Vendidos', rel_vendas['produtos_vendidos']])
            
            resumo_df = pd.DataFrame(resumo_data, columns=['Metrica', 'Valor'])
            resumo_df.to_excel(writer, sheet_name='Resumo_Executivo', index=False)
        
        return {
            'sucesso': True,
            'arquivo': caminho_completo,
            'tamanho_kb': round(os.path.getsize(caminho_completo) / 1024, 2),
            'abas_criadas': ['Produtos', 'Movimentacoes_30d', 'Estoque_Critico', 
                           'Vendas_Produto', 'Analise_Categorias', 'Resumo_Executivo'],
            'mensagem': f'Relatorio exportado com sucesso para {caminho_completo}'
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'mensagem': 'Erro ao exportar relatorio para Excel'
        }


def _resumo_por_categoria(produtos_lista: List[Dict]) -> List[Dict]:
    """
    Funcao auxiliar para resumir produtos por categoria.
    """
    if not produtos_lista:
        return []
    
    categorias = {}
    for produto in produtos_lista:
        categoria = produto.get('categoria', 'Sem categoria')
        if categoria not in categorias:
            categorias[categoria] = {
                'categoria': categoria,
                'quantidade': 0,
                'investimento': 0
            }
        categorias[categoria]['quantidade'] += 1
        categorias[categoria]['investimento'] += produto.get('investimento', 0)
    
    return list(categorias.values())


def gerar_dashboard_resumo(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame) -> Dict:
    """
    Gera um resumo executivo para dashboard.
    
    Args:
        produtos_df: DataFrame com dados dos produtos
        movimentacoes_df: DataFrame com movimentacoes
    
    Returns:
        Dict com metricas principais para dashboard
    """
    try:
        # Gera relatorios
        rel_vendas = relatorio_vendas_periodo(movimentacoes_df, 30)
        rel_critico = relatorio_estoque_critico(produtos_df, movimentacoes_df)
        rel_categorias = relatorio_categorias(produtos_df, movimentacoes_df)
        
        # Metricas principais
        metricas = {
            'total_produtos': len(produtos_df),
            'valor_estoque': rel_categorias.get('valor_total_estoque', 0),
            'produtos_criticos': rel_critico.get('produtos_criticos', 0),
            'produtos_atencao': rel_critico.get('produtos_atencao', 0),
            'vendas_30d': rel_vendas.get('quantidade_total', 0),
            'investimento_necessario': rel_critico.get('investimento_total', 0),
            'categorias_total': rel_categorias.get('total_categorias', 0)
        }
        
        # Alertas
        alertas = []
        if metricas['produtos_criticos'] > 0:
            alertas.append(f"🚨 {metricas['produtos_criticos']} produtos com estoque critico!")
        
        if metricas['produtos_atencao'] > 0:
            alertas.append(f"⚠️ {metricas['produtos_atencao']} produtos precisam de atencao")
        
        if metricas['investimento_necessario'] > 0:
            alertas.append(f"💰 R$ {metricas['investimento_necessario']:,.2f} necessarios para reposicao")
        
        # Top produtos criticos
        top_criticos = []
        if rel_critico['sucesso'] and rel_critico['lista_criticos']:
            top_criticos = rel_critico['lista_criticos'][:5]  # Top 5
        
        return {
            'sucesso': True,
            'metricas': metricas,
            'alertas': alertas,
            'top_criticos': top_criticos,
            'categoria_mais_vendas': rel_categorias.get('categoria_mais_vendas'),
            'categoria_maior_estoque': rel_categorias.get('categoria_maior_estoque')
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'mensagem': 'Erro ao gerar dashboard resumo'
        }