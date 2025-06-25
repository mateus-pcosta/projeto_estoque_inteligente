import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os
import warnings
warnings.filterwarnings('ignore')

# Machine Learning
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_DISPONIVEL = True
except ImportError:
    ML_DISPONIVEL = False
    print("⚠️ Scikit-learn não instalado. Execute: pip install scikit-learn joblib")


def criar_dados_sinteticos(vendidos_30_dias: int, id_produto: int) -> pd.DataFrame:
    """Cria dados sintéticos baseados no campo vendidos_ultimos_30_dias."""
    if vendidos_30_dias <= 0:
        return pd.DataFrame()
    
    # Cria 30 dias de dados sintéticos
    from datetime import datetime, timedelta
    datas = [datetime.now() - timedelta(days=i) for i in range(29, -1, -1)]
    
    # Distribui as vendas de forma realística
    vendas_diarias = []
    media_diaria = vendidos_30_dias / 30
    
    for i, data in enumerate(datas):
        # Simula padrão: mais vendas em fins de semana e meio/fim do mês
        fator = 1.0
        if data.weekday() >= 5:  # Fim de semana
            fator = 1.3
        if data.day > 20:  # Final do mês
            fator *= 1.2
        
        # Adiciona variação aleatória
        import random
        variacao = random.uniform(0.7, 1.3)
        vendas = max(0, int(media_diaria * fator * variacao))
        vendas_diarias.append(vendas)
    
    # Ajusta para somar exatamente vendidos_30_dias
    diferenca = vendidos_30_dias - sum(vendas_diarias)
    if diferenca != 0:
        # Distribui a diferença nos últimos dias
        for i in range(min(5, len(vendas_diarias))):
            if diferenca > 0:
                vendas_diarias[-(i+1)] += 1
                diferenca -= 1
            elif diferenca < 0 and vendas_diarias[-(i+1)] > 0:
                vendas_diarias[-(i+1)] -= 1
                diferenca += 1
    
    df = pd.DataFrame({
        'data': datas,
        'vendas': vendas_diarias
    })
    
    return df


def preparar_dados_vendas(movimentacoes_df: pd.DataFrame, id_produto: int) -> pd.DataFrame:
    """Prepara dados de vendas de um produto para análise."""
    # Filtra apenas saídas do produto
    vendas = movimentacoes_df[
        (movimentacoes_df['id_produto'] == id_produto) & 
        (movimentacoes_df['tipo'] == 'saida')
    ].copy()
    
    if vendas.empty:
        return pd.DataFrame()
    
    # Converte datas (suporta formatos mistos) e agrupa por dia
    vendas['data'] = pd.to_datetime(vendas['data'], format='mixed', errors='coerce')
    
    # Remove linhas com datas inválidas
    vendas = vendas.dropna(subset=['data'])
    
    if vendas.empty:
        return pd.DataFrame()
    
    vendas_diarias = vendas.groupby(vendas['data'].dt.date)['quantidade'].sum().reset_index()
    vendas_diarias.columns = ['data', 'vendas']
    vendas_diarias['data'] = pd.to_datetime(vendas_diarias['data'])
    
    # Preenche dias sem vendas com 0
    data_range = pd.date_range(
        start=vendas_diarias['data'].min(),
        end=vendas_diarias['data'].max(),
        freq='D'
    )
    
    df_completo = pd.DataFrame({'data': data_range})
    df_completo = df_completo.merge(vendas_diarias, on='data', how='left')
    df_completo['vendas'] = df_completo['vendas'].fillna(0)
    
    return df_completo


def criar_features_ml(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features para os modelos de ML."""
    df = df.copy()
    
    # Features temporais
    df['dia_semana'] = df['data'].dt.dayofweek
    df['dia_mes'] = df['data'].dt.day
    df['mes'] = df['data'].dt.month
    df['fim_semana'] = (df['dia_semana'] >= 5).astype(int)
    
    # Features cíclicas (captura padrões circulares)
    df['dia_semana_sin'] = np.sin(2 * np.pi * df['dia_semana'] / 7)
    df['dia_semana_cos'] = np.cos(2 * np.pi * df['dia_semana'] / 7)
    
    # Lags (valores passados)
    for lag in [1, 3, 7, 14]:
        df[f'vendas_lag_{lag}'] = df['vendas'].shift(lag)
    
    # Médias móveis
    for janela in [3, 7, 14]:
        df[f'media_movel_{janela}'] = df['vendas'].rolling(window=janela, min_periods=1).mean()
    
    # Remove linhas com NaN nas features críticas
    df = df.dropna()
    
    return df


def treinar_modelo_produto(movimentacoes_df: pd.DataFrame, id_produto: int, produtos_df: pd.DataFrame = None) -> Dict:
    """Treina modelo de ML para um produto específico."""
    if not ML_DISPONIVEL:
        return {'sucesso': False, 'mensagem': 'ML não disponível'}
    
    # Prepara dados reais
    df = preparar_dados_vendas(movimentacoes_df, id_produto)
    usar_dados_sinteticos = False
    
    # Se não há dados suficientes, tenta usar dados sintéticos
    if len(df) < 7 or len(df[df['vendas'] > 0]) < 3:
        if produtos_df is not None:
            produto = produtos_df[produtos_df['id_produto'] == id_produto]
            if not produto.empty:
                vendidos_30_dias = int(produto['vendidos_ultimos_30_dias'].values[0])
                if vendidos_30_dias > 0:
                    df = criar_dados_sinteticos(vendidos_30_dias, id_produto)
                    usar_dados_sinteticos = True
    
    # Validações finais
    if len(df) < 7:
        return {'sucesso': False, 'mensagem': 'Dados insuficientes (mínimo 7 dias)'}
    
    dias_com_vendas = len(df[df['vendas'] > 0])
    if dias_com_vendas < 3:
        return {'sucesso': False, 'mensagem': f'Muito poucas vendas ({dias_com_vendas} dias com vendas)'}
    
    # Cria features
    df = criar_features_ml(df)
    
    # Define features e target
    feature_cols = [col for col in df.columns if col not in ['data', 'vendas']]
    X = df[feature_cols]
    y = df['vendas']
    
    # Divide dados (80/20)
    split_point = int(len(X) * 0.8)
    X_train, X_test = X[:split_point], X[split_point:]
    y_train, y_test = y[:split_point], y[split_point:]
    
    # Treina modelo
    modelo = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    modelo.fit(X_train, y_train)
    
    # Avalia
    y_pred = modelo.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Salva modelo
    os.makedirs('models', exist_ok=True)
    joblib.dump(modelo, f'models/modelo_produto_{id_produto}.pkl')
    joblib.dump(feature_cols, f'models/features_produto_{id_produto}.pkl')
    
    return {
        'sucesso': True,
        'mae': mae,
        'r2': r2,
        'features': feature_cols,
        'dados_treino': len(X_train),
        'dados_teste': len(X_test),
        'dados_sinteticos': usar_dados_sinteticos
    }


def prever_demanda(movimentacoes_df: pd.DataFrame, id_produto: int, dias: int = 14, produtos_df: pd.DataFrame = None) -> Dict:
    """Prevê demanda futura usando modelo treinado."""
    if not ML_DISPONIVEL:
        return {'sucesso': False, 'mensagem': 'ML não disponível'}
    
    # Verifica se existe modelo treinado
    modelo_path = f'models/modelo_produto_{id_produto}.pkl'
    features_path = f'models/features_produto_{id_produto}.pkl'
    
    if not os.path.exists(modelo_path):
        # Tenta treinar (incluindo dados sintéticos se necessário)
        resultado = treinar_modelo_produto(movimentacoes_df, id_produto, produtos_df)
        if not resultado['sucesso']:
            return resultado
    
    # Carrega modelo
    try:
        modelo = joblib.load(modelo_path)
        feature_cols = joblib.load(features_path)
    except:
        return {'sucesso': False, 'mensagem': 'Erro ao carregar modelo'}
    
    # Prepara dados históricos (usa sintéticos se necessário)
    df = preparar_dados_vendas(movimentacoes_df, id_produto)
    if df.empty and produtos_df is not None:
        # Tenta usar dados sintéticos
        produto = produtos_df[produtos_df['id_produto'] == id_produto]
        if not produto.empty:
            vendidos_30_dias = int(produto['vendidos_ultimos_30_dias'].values[0])
            if vendidos_30_dias > 0:
                df = criar_dados_sinteticos(vendidos_30_dias, id_produto)
    
    if df.empty:
        return {'sucesso': False, 'mensagem': 'Sem dados históricos'}
    
    df = criar_features_ml(df)
    
    # Gera previsões dia a dia
    previsoes = []
    ultima_data = df['data'].max()
    
    for i in range(dias):
        # Data da previsão
        data_prev = ultima_data + timedelta(days=i+1)
        
        # Cria features para o dia
        features = {
            'dia_semana': data_prev.weekday(),
            'dia_mes': data_prev.day,
            'mes': data_prev.month,
            'fim_semana': int(data_prev.weekday() >= 5),
            'dia_semana_sin': np.sin(2 * np.pi * data_prev.weekday() / 7),
            'dia_semana_cos': np.cos(2 * np.pi * data_prev.weekday() / 7)
        }
        
        # Adiciona lags e médias móveis baseadas no histórico
        vendas_historico = list(df['vendas'].tail(14)) + previsoes
        
        for lag in [1, 3, 7, 14]:
            if len(vendas_historico) >= lag:
                features[f'vendas_lag_{lag}'] = vendas_historico[-(lag)]
            else:
                features[f'vendas_lag_{lag}'] = df['vendas'].mean()
        
        for janela in [3, 7, 14]:
            if len(vendas_historico) >= janela:
                features[f'media_movel_{janela}'] = np.mean(vendas_historico[-janela:])
            else:
                features[f'media_movel_{janela}'] = df['vendas'].mean()
        
        # Organiza features na ordem correta
        X_pred = pd.DataFrame([features])[feature_cols]
        
        # Faz previsão
        previsao = max(0, modelo.predict(X_pred)[0])
        previsoes.append(previsao)
    
    return {
        'sucesso': True,
        'previsoes': previsoes,
        'total_previsto': sum(previsoes),
        'media_diaria': np.mean(previsoes)
    }


def classificar_urgencia_produto(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame, 
                                id_produto: int) -> Dict:
    """Classifica a urgência de reposição de um produto."""
    # Busca produto
    produto = produtos_df[produtos_df['id_produto'] == id_produto]
    if produto.empty:
        return {'sucesso': False, 'mensagem': 'Produto não encontrado'}
    
    estoque_atual = int(produto['estoque_atual'].values[0])
    nome_produto = produto['nome'].values[0]
    preco = float(produto['preco_unitario'].values[0])
    
    # Obter custo unitário (fallback para 65% do preço se não existir)
    if 'custo_unitario' in produto.columns and not pd.isna(produto['custo_unitario'].values[0]):
        custo = float(produto['custo_unitario'].values[0])
    else:
        custo = preco * 0.65  # fallback: assume margem de 35%
    
    # Tenta prever com ML
    previsao_ml = prever_demanda(movimentacoes_df, id_produto, 14, produtos_df)
    
    if previsao_ml['sucesso'] and previsao_ml['total_previsto'] > 0:
        # Usa previsão ML apenas se prevê demanda > 0
        demanda_prevista = previsao_ml['previsoes']
        demanda_total = previsao_ml['total_previsto']
    else:
        # Fallback melhorado: usa dados reais dos últimos 30 dias
        # Converte datas e filtra últimos 30 dias
        movimentacoes_produto = movimentacoes_df[
            (movimentacoes_df['id_produto'] == id_produto) & 
            (movimentacoes_df['tipo'] == 'saida')
        ].copy()
        
        if not movimentacoes_produto.empty:
            # Converte datas
            movimentacoes_produto['data_convertida'] = pd.to_datetime(
                movimentacoes_produto['data'], format='mixed', errors='coerce'
            )
            movimentacoes_produto = movimentacoes_produto.dropna(subset=['data_convertida'])
            
            # Filtra últimos 30 dias
            data_limite = datetime.now() - timedelta(days=30)
            vendas_recentes = movimentacoes_produto[
                movimentacoes_produto['data_convertida'] >= data_limite
            ]
            
            if not vendas_recentes.empty:
                # Usa vendas dos últimos 30 dias
                vendas_30_dias = vendas_recentes['quantidade'].sum()
                media_diaria = vendas_30_dias / 30
            else:
                # Se não há vendas recentes, usa campo vendidos_ultimos_30_dias do produto
                vendidos_30_dias = int(produto['vendidos_ultimos_30_dias'].values[0])
                media_diaria = vendidos_30_dias / 30
        else:
            # Se não há histórico de vendas, usa campo vendidos_ultimos_30_dias
            vendidos_30_dias = int(produto['vendidos_ultimos_30_dias'].values[0])
            media_diaria = vendidos_30_dias / 30
        
        demanda_prevista = [media_diaria] * 14
        demanda_total = media_diaria * 14
    
    # Calcula dias até acabar - corrigido para não limitar a 14 dias
    if demanda_total <= 0:
        # Sem demanda prevista - classifica por estoque absoluto
        dias_ate_fim = 999  # Valor alto para indicar sem urgência imediata
    else:
        # Calcula quantos dias o estoque durará
        media_diaria = demanda_total / 14
        if media_diaria > 0:
            dias_ate_fim = int(estoque_atual / media_diaria)
        else:
            dias_ate_fim = 999
    
    # Classifica urgência - lógica melhorada
    if estoque_atual == 0:
        urgencia = 'CRITICO'
    elif estoque_atual <= 8:  # Produtos com estoque muito baixo
        urgencia = 'CRITICO'
    elif demanda_total > 0 and dias_ate_fim <= 3:
        urgencia = 'CRITICO'
    elif demanda_total > 0 and dias_ate_fim <= 7:
        urgencia = 'ATENCAO'
    elif estoque_atual <= 12:  # Produtos com estoque baixo mesmo sem demanda alta
        urgencia = 'ATENCAO'
    elif demanda_total > 0 and dias_ate_fim <= 21:
        urgencia = 'NORMAL'
    elif estoque_atual <= 18:  # Alerta preventivo para estoques médio-baixos
        urgencia = 'NORMAL'
    else:
        urgencia = 'EXCESSO'
    
    # Calcula quantidade para repor - lógica melhorada
    if demanda_total > 0:
        # Com demanda prevista: cobertura de 21 dias + 20% segurança
        cobertura_dias = 21
        demanda_21_dias = (demanda_total / 14) * cobertura_dias
        quantidade_ideal = demanda_21_dias * 1.2
    else:
        # Sem demanda: repor até estoque mínimo baseado no histórico de vendas
        vendidos_30_dias = int(produto['vendidos_ultimos_30_dias'].values[0])
        if vendidos_30_dias > 0:
            # Estoque mínimo = vendas de 15 dias baseado no histórico
            quantidade_ideal = (vendidos_30_dias / 30) * 15
        else:
            # Produto sem vendas: manter estoque mínimo de 20 unidades
            quantidade_ideal = 20
    
    quantidade_repor = max(0, int(quantidade_ideal - estoque_atual))
    
    # Gera insights melhorados
    insights = []
    
    # Insight sobre fonte de dados
    if previsao_ml['sucesso']:
        insights.append(f"📊 ML prevê demanda de {demanda_total:.1f} unidades/14 dias")
    else:
        vendidos_30_dias = int(produto['vendidos_ultimos_30_dias'].values[0])
        insights.append(f"📈 Baseado em histórico: {vendidos_30_dias} vendidos/30 dias")
    
    # Insight sobre urgência
    if urgencia == 'CRITICO':
        if estoque_atual <= 8:
            insights.append(f"🚨 CRÍTICO: Estoque muito baixo ({estoque_atual} unidades)")
        elif dias_ate_fim <= 3:
            insights.append(f"🚨 CRÍTICO: Acabará em {dias_ate_fim} dias")
        else:
            insights.append(f"🚨 CRÍTICO: Reposição urgente necessária")
    elif urgencia == 'ATENCAO':
        if estoque_atual <= 12:
            insights.append(f"⚠️ ATENÇÃO: Estoque baixo ({estoque_atual} unidades)")
        else:
            insights.append(f"⚠️ ATENÇÃO: Estoque para {dias_ate_fim} dias")
    elif urgencia == 'NORMAL':
        if estoque_atual <= 18:
            insights.append(f"📋 Estoque adequado mas monitore ({estoque_atual} unidades)")
        else:
            insights.append(f"📋 Estoque normal para {dias_ate_fim} dias")
    elif urgencia == 'EXCESSO':
        insights.append(f"📦 Possível excesso: estoque para {dias_ate_fim}+ dias")
    
    # Detecta padrões
    vendas_por_dia = movimentacoes_df[
        (movimentacoes_df['id_produto'] == id_produto) & 
        (movimentacoes_df['tipo'] == 'saida')
    ].copy()
    
    if not vendas_por_dia.empty:
        vendas_por_dia['data_convertida'] = pd.to_datetime(vendas_por_dia['data'], format='mixed', errors='coerce')
        vendas_por_dia = vendas_por_dia.dropna(subset=['data_convertida'])
        
        if not vendas_por_dia.empty:
            vendas_por_dia['dia_semana'] = vendas_por_dia['data_convertida'].dt.day_name()
            dia_mais_vendas = vendas_por_dia.groupby('dia_semana')['quantidade'].sum().idxmax()
            dias_pt = {
                'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            insights.append(f"📅 Maior venda: {dias_pt.get(dia_mais_vendas, dia_mais_vendas)}")
    
    return {
        'sucesso': True,
        'produto': nome_produto,
        'urgencia': urgencia,
        'dias_ate_fim': dias_ate_fim,
        'estoque_atual': estoque_atual,
        'demanda_prevista': demanda_total,
        'quantidade_repor': quantidade_repor,
        'investimento': quantidade_repor * custo,
        'insights': insights,
        'modelo_ml': previsao_ml['sucesso']
    }


def analisar_todos_produtos(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame) -> Dict:
    """Analisa todos os produtos e gera dashboard executivo."""
    resultados = []
    
    for _, produto in produtos_df.iterrows():
        analise = classificar_urgencia_produto(produtos_df, movimentacoes_df, produto['id_produto'])
        if analise['sucesso']:
            resultados.append(analise)
    
    # Separa por urgência
    criticos = [r for r in resultados if r['urgencia'] == 'CRITICO']
    atencao = [r for r in resultados if r['urgencia'] == 'ATENCAO']
    normais = [r for r in resultados if r['urgencia'] == 'NORMAL']
    excesso = [r for r in resultados if r['urgencia'] == 'EXCESSO']
    
    # Calcula totais
    investimento_urgente = sum(r['investimento'] for r in criticos)
    investimento_total = sum(r['investimento'] for r in criticos + atencao)
    
    # Ordena por urgência
    criticos.sort(key=lambda x: x['dias_ate_fim'])
    atencao.sort(key=lambda x: x['dias_ate_fim'])
    
    return {
        'total_produtos': len(produtos_df),
        'produtos_criticos': len(criticos),
        'produtos_atencao': len(atencao),
        'produtos_normais': len(normais),
        'produtos_excesso': len(excesso),
        'investimento_urgente': investimento_urgente,
        'investimento_total': investimento_total,
        'lista_criticos': criticos,
        'lista_atencao': atencao,
        'produtos_ml': sum(1 for r in resultados if r.get('modelo_ml', False))
    }


def gerar_lista_compras(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame) -> pd.DataFrame:
    """Gera lista de compras otimizada."""
    analise = analisar_todos_produtos(produtos_df, movimentacoes_df)
    
    lista = []
    for produto in analise['lista_criticos'] + analise['lista_atencao']:
        if produto['quantidade_repor'] > 0:
            lista.append({
                'Produto': produto['produto'],
                'Quantidade': produto['quantidade_repor'],
                'Urgência': produto['urgencia'],
                'Dias Restantes': produto['dias_ate_fim'],
                'Investimento': produto['investimento']
            })
    
    if lista:
        return pd.DataFrame(lista).sort_values('Dias Restantes')
    return pd.DataFrame()


def treinar_todos_modelos(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame) -> Dict:
    """Treina modelos para todos os produtos possíveis."""
    if not ML_DISPONIVEL:
        return {'sucesso': False, 'mensagem': 'ML não disponível'}
    
    resultados = {
        'sucesso': 0,
        'falha': 0,
        'detalhes': []
    }
    
    for _, produto in produtos_df.iterrows():
        id_produto = produto['id_produto']
        nome = produto['nome']
        
        resultado = treinar_modelo_produto(movimentacoes_df, id_produto, produtos_df)
        
        if resultado['sucesso']:
            resultados['sucesso'] += 1
            status_texto = 'OK (sintético)' if resultado.get('dados_sinteticos', False) else 'OK'
            resultados['detalhes'].append({
                'produto': nome,
                'status': status_texto,
                'r2': resultado.get('r2', 0),
                'mae': resultado.get('mae', 0)
            })
        else:
            resultados['falha'] += 1
            resultados['detalhes'].append({
                'produto': nome,
                'status': 'FALHA',
                'motivo': resultado.get('mensagem', 'Erro')
            })
    
    return resultados