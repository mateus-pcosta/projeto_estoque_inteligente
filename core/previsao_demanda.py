import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configuração de logging para ambiente acadêmico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GeminiAPIClient:
    """Cliente para API do Google Gemini com gestão inteligente de quota"""
    
    def __init__(self):
        self.model = None
        self.api_available = False
        self.quota_exhausted = False  # Flag para evitar chamadas desnecessárias
        self.last_error_time = None
        self._initialize_api()
    
    def _initialize_api(self) -> bool:
        """Inicializa a API do Gemini com tratamento de erros"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key or api_key == "sua_chave_api_do_gemini_aqui":
                logger.info("Chave API do Gemini não configurada - usando análise local exclusiva")
                return False
            
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.api_available = True
            logger.info("API Gemini configurada (verificação de quota pendente)")
            return True
            
        except ImportError:
            logger.warning("Biblioteca google-generativeai não instalada - análise local ativa")
            return False
        except Exception as e:
            logger.warning(f"Erro ao inicializar Gemini: {str(e)} - análise local ativa")
            return False
    
    def is_quota_available(self) -> bool:
        """Verifica se a quota está disponível sem fazer chamadas desnecessárias"""
        if not self.api_available or self.quota_exhausted:
            return False
        
        # Se teve erro de quota há menos de 1 hora, não tenta novamente
        if self.last_error_time:
            from datetime import datetime, timedelta
            if datetime.now() - self.last_error_time < timedelta(hours=1):
                return False
        
        return True
    
    def generate_analysis(self, prompt: str) -> Optional[str]:
        """Gera análise usando Gemini apenas se quota disponível"""
        if not self.is_quota_available():
            logger.info("Quota Gemini indisponível - usando análise local")
            return None
        
        try:
            # Faz uma chamada mínima para testar quota
            test_response = self.model.generate_content(".")  # Prompt mínimo
            if not test_response.text:
                raise Exception("Resposta vazia do Gemini")
            
            logger.info("Quota Gemini disponível - executando análise IA")
            # Se chegou aqui, quota está OK - faz a análise real
            response = self.model.generate_content(prompt)
            logger.info("Análise Gemini executada com sucesso")
            return response.text.strip()
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                self.quota_exhausted = True
                self.last_error_time = datetime.now()
                logger.info("Quota Gemini esgotada - análise local ativada automaticamente")
            else:
                logger.warning(f"Erro temporário no Gemini: {error_msg[:50]}... - usando análise local")
            return None

class DemandAnalyzer:
    """Analisador de demanda com múltiplas estratégias"""
    
    def __init__(self):
        self.gemini_client = GeminiAPIClient()
        
    def classify_product_movement(self, sales_30d: int, sales_history: List[int]) -> Tuple[str, float]:
        """
        Classifica o movimento do produto com base em vendas
        
        Args:
            sales_30d: Vendas dos últimos 30 dias
            sales_history: Histórico de vendas
            
        Returns:
            Tuple[classificação, confiança]
        """
        
        # Análise estatística do histórico
        if len(sales_history) > 1:
            cv = np.std(sales_history) / (np.mean(sales_history) + 1e-6)  # Coeficiente de variação
            trend = self._calculate_trend(sales_history)
        else:
            cv = 0
            trend = 0
        
        # Classificação baseada em múltiplos critérios
        if sales_30d >= 40:
            classification = "Alta saída"
            confidence = 0.95 if cv < 0.3 else 0.85  # Menor variabilidade = maior confiança
        elif sales_30d >= 25:
            classification = "Média-Alta saída"
            confidence = 0.85 if trend > 0 else 0.75  # Tendência crescente = maior confiança
        elif sales_30d >= 15:
            classification = "Média saída"
            confidence = 0.75
        elif sales_30d >= 5:
            classification = "Baixa saída"
            confidence = 0.65
        else:
            classification = "Muito baixa saída"
            confidence = 0.55
        
        # Ajuste para produtos sazonais
        if cv > 0.5 and len(sales_history) >= 4:
            classification = "Sazonal"
            confidence = min(confidence + 0.1, 0.95)
        
        return classification, confidence
    
    def _calculate_trend(self, sales_history: List[int]) -> float:
        """Calcula tendência usando regressão linear simples"""
        if len(sales_history) < 2:
            return 0
        
        x = np.arange(len(sales_history))
        y = np.array(sales_history)
        
        # Regressão linear: y = ax + b
        if len(x) > 1:
            slope = np.corrcoef(x, y)[0, 1] if np.std(x) > 0 and np.std(y) > 0 else 0
            return slope
        return 0
    
    def predict_demand(self, product_data: Dict, days_ahead: int = 30) -> Dict:
        """
        Prediz demanda futura usando múltiplos métodos
        
        Args:
            product_data: Dados do produto
            days_ahead: Dias para previsão
            
        Returns:
            Dicionário com previsões
        """
        sales_30d = product_data.get('vendidos_ultimos_30_dias', 0)
        current_stock = product_data.get('estoque_atual', 0)
        
        # Método 1: Média móvel ponderada
        daily_avg = sales_30d / 30
        
        # Método 2: Ajuste por tendência sazonal
        sales_history = [s.get('quantidade', 0) for s in product_data.get('historico_vendas', [])]
        
        if len(sales_history) > 1:
            # Fator de sazonalidade baseado em variação histórica
            seasonal_factor = self._calculate_seasonal_factor(sales_history)
            daily_adjusted = daily_avg * seasonal_factor
        else:
            seasonal_factor = 1.0
            daily_adjusted = daily_avg
        
        # Método 3: Suavização exponencial simples
        alpha = 0.3  # Parâmetro de suavização
        if len(sales_history) >= 2:
            exponential_avg = self._exponential_smoothing(sales_history, alpha)
            daily_adjusted = (daily_adjusted + exponential_avg / 30) / 2
        
        # Previsão final
        demand_prediction = daily_adjusted * days_ahead
        
        # Cálculo de ruptura
        if daily_adjusted > 0:
            days_to_stockout = int(current_stock / daily_adjusted)
        else:
            days_to_stockout = 999
        
        # Sugestão de reposição
        suggest_reorder = days_to_stockout < 14 and sales_30d > 0
        
        if suggest_reorder:
            # Fórmula: demanda prevista + estoque de segurança
            safety_factor = 1.5 if daily_adjusted > 2 else 1.3
            reorder_quantity = int(demand_prediction * safety_factor)
        else:
            reorder_quantity = None
        
        return {
            'previsao_demanda': round(demand_prediction, 2),
            'demanda_diaria': round(daily_adjusted, 2),
            'dias_ate_ruptura': days_to_stockout if days_to_stockout < 999 else None,
            'sugerir_reposicao': suggest_reorder,
            'quantidade_reposicao': reorder_quantity,
            'fator_sazonal': round(seasonal_factor, 2),
            'metodo_usado': 'Média móvel ponderada + Suavização exponencial'
        }
    
    def _calculate_seasonal_factor(self, sales_history: List[int]) -> float:
        """Calcula fator de sazonalidade"""
        if len(sales_history) < 4:
            return 1.0
        
        # Últimas vendas vs média histórica
        recent_avg = np.mean(sales_history[-3:])
        total_avg = np.mean(sales_history)
        
        if total_avg > 0:
            factor = recent_avg / total_avg
            # Limita o fator entre 0.5 e 2.0 para evitar extremos
            return max(0.5, min(2.0, factor))
        return 1.0
    
    def _exponential_smoothing(self, data: List[int], alpha: float) -> float:
        """Aplica suavização exponencial"""
        if not data:
            return 0
        
        result = data[0]
        for value in data[1:]:
            result = alpha * value + (1 - alpha) * result
        
        return result

class LocalAnalysisEngine:
    """Motor de análise local avançado"""
    
    def __init__(self):
        self.analyzer = DemandAnalyzer()
    
    def analyze_products(self, products_data: List[Dict]) -> Dict:
        """Executa análise local completa"""
        
        logger.info(f"Iniciando análise local de {len(products_data)} produtos")
        
        analyses = []
        risk_products = 0
        category_performance = {}
        
        for product in products_data:
            # Análise individual do produto
            analysis = self._analyze_single_product(product)
            analyses.append(analysis)
            
            # Contabiliza produtos em risco
            if analysis.get('sugerir_reposicao', False):
                risk_products += 1
            
            # Performance por categoria
            category = product.get('categoria', 'Outros')
            if category not in category_performance:
                category_performance[category] = {
                    'total_sales': 0,
                    'total_revenue': 0,
                    'product_count': 0
                }
            
            category_performance[category]['total_sales'] += product.get('vendidos_ultimos_30_dias', 0)
            category_performance[category]['total_revenue'] += (
                product.get('vendidos_ultimos_30_dias', 0) * product.get('preco_unitario', 0)
            )
            category_performance[category]['product_count'] += 1
        
        # Encontra categoria de melhor performance
        best_category = max(
            category_performance.items(),
            key=lambda x: x[1]['total_revenue']
        )[0] if category_performance else "N/A"
        
        # Gera recomendações inteligentes
        recommendations = self._generate_recommendations(analyses, category_performance, risk_products)
        
        return {
            "analises": analyses,
            "resumo_geral": {
                "produtos_risco_ruptura": risk_products,
                "categoria_maior_demanda": best_category,
                "recomendacoes_gerais": recommendations,
                "metodo_analise": "Análise Local Avançada (Matemática + Estatística)",
                "precisao_estimada": "Alta (baseada em dados históricos reais)",
                "algoritmos_usados": [
                    "Média móvel ponderada",
                    "Suavização exponencial",
                    "Análise de tendência (regressão linear)",
                    "Detecção de sazonalidade",
                    "Coeficiente de variação"
                ],
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _analyze_single_product(self, product: Dict) -> Dict:
        """Analisa um produto individual"""
        
        sales_30d = product.get('vendidos_ultimos_30_dias', 0)
        sales_history = [s.get('quantidade', 0) for s in product.get('historico_vendas', [])]
        
        # Classificação
        classification, confidence = self.analyzer.classify_product_movement(sales_30d, sales_history)
        
        # Previsões
        prediction_7d = self.analyzer.predict_demand(product, 7)
        prediction_30d = self.analyzer.predict_demand(product, 30)
        
        # Insights personalizados
        insights = self._generate_product_insights(product, classification, prediction_30d)
        
        # Alertas
        alerts = self._generate_product_alerts(product, prediction_30d)
        
        return {
            "id_produto": product.get('id_produto'),
            "nome": product.get('nome'),
            "categoria": product.get('categoria'),
            "previsao_demanda_7_dias": prediction_7d.get('previsao_demanda'),
            "previsao_demanda_30_dias": prediction_30d.get('previsao_demanda'),
            "classificacao_saida": classification,
            "dias_ate_ruptura": prediction_30d.get('dias_ate_ruptura'),
            "sugerir_reposicao": prediction_30d.get('sugerir_reposicao'),
            "quantidade_reposicao_sugerida": prediction_30d.get('quantidade_reposicao'),
            "confianca_previsao": confidence,
            "insights": insights,
            "alertas": alerts,
            "metricas_detalhadas": {
                "demanda_diaria": prediction_30d.get('demanda_diaria'),
                "fator_sazonal": prediction_30d.get('fator_sazonal'),
                "metodo_calculo": prediction_30d.get('metodo_usado'),
                "vendas_historicas": len(product.get('historico_vendas', [])),
                "estoque_atual": product.get('estoque_atual', 0),
                "valor_unitario": product.get('preco_unitario', 0)
            }
        }
    
    def _generate_product_insights(self, product: Dict, classification: str, prediction: Dict) -> str:
        """Gera insights personalizados para o produto"""
        insights = []
        
        sales_30d = product.get('vendidos_ultimos_30_dias', 0)
        price = product.get('preco_unitario', 0)
        stock = product.get('estoque_atual', 0)
        
        # Insights baseados em classificação
        if "Alta" in classification:
            insights.append("🌟 Produto estrela - alta demanda consistente")
        elif "Média" in classification:
            insights.append("📈 Produto popular - demanda estável")
        elif "Baixa" in classification:
            insights.append("📉 Baixo giro - considere estratégias de promoção")
        elif "Sazonal" in classification:
            insights.append("🔄 Padrão sazonal detectado - ajuste estoque conforme época")
        
        # Insights financeiros
        revenue_30d = sales_30d * price
        if revenue_30d > 500:
            insights.append(f"💰 Alto faturamento: R$ {revenue_30d:.2f} nos últimos 30 dias")
        
        # Insights de estoque
        days_supply = prediction.get('dias_ate_ruptura', 0)
        if days_supply and days_supply < 7:
            insights.append("🚨 CRÍTICO: Reposição urgente necessária")
        elif days_supply and days_supply < 14:
            insights.append("⚠️ ATENÇÃO: Programar reposição em breve")
        elif stock > sales_30d * 2:
            insights.append("📦 Estoque elevado em relação à demanda atual")
        
        return " | ".join(insights) if insights else "Produto com padrão de vendas normal"
    
    def _generate_product_alerts(self, product: Dict, prediction: Dict) -> List[str]:
        """Gera alertas específicos para o produto"""
        alerts = []
        
        days_to_stockout = prediction.get('dias_ate_ruptura')
        
        if days_to_stockout:
            if days_to_stockout < 3:
                alerts.append("🔴 CRÍTICO: Ruptura iminente (< 3 dias)")
            elif days_to_stockout < 7:
                alerts.append("🟠 URGENTE: Ruptura em menos de 7 dias")
            elif days_to_stockout < 14:
                alerts.append("🟡 ATENÇÃO: Ruptura em menos de 14 dias")
        
        # Alertas de performance
        sales_30d = product.get('vendidos_ultimos_30_dias', 0)
        if sales_30d == 0:
            alerts.append("📊 INFO: Produto sem vendas nos últimos 30 dias")
        
        return alerts
    
    def _generate_recommendations(self, analyses: List[Dict], category_performance: Dict, risk_products: int) -> List[str]:
        """Gera recomendações gerais do sistema"""
        recommendations = []
        
        # Recomendações baseadas em risco
        if risk_products > 0:
            recommendations.append(f"🚨 PRIORIDADE: {risk_products} produtos precisam de reposição urgente")
        
        # Produtos de alta performance
        high_performers = [a for a in analyses if "Alta" in a.get('classificacao_saida', '')]
        if high_performers:
            recommendations.append(f"⭐ Focar nos {len(high_performers)} produtos de alta saída para maximizar vendas")
        
        # Produtos de baixa performance
        low_performers = [a for a in analyses if "Baixa" in a.get('classificacao_saida', '')]
        if len(low_performers) > 3:
            recommendations.append(f"📉 Avaliar estratégias para {len(low_performers)} produtos de baixo giro")
        
        # Categoria performance
        if category_performance:
            best_revenue = max(category_performance.values(), key=lambda x: x['total_revenue'])
            best_category = [k for k, v in category_performance.items() if v == best_revenue][0]
            recommendations.append(f"💎 Categoria '{best_category}' é a mais rentável - manter estoque adequado")
        
        # Recomendação geral
        recommendations.append("📊 Execute análises semanais para manter insights atualizados")
        
        return recommendations

class HybridIntelligenceEngine:
    """Motor principal de inteligência híbrida"""
    
    def __init__(self):
        self.local_engine = LocalAnalysisEngine()
        self.gemini_client = GeminiAPIClient()
    
    def execute_complete_analysis(self, products_df: pd.DataFrame, movements_df: pd.DataFrame) -> Dict:
        """
        Executa análise completa com IA híbrida
        
        Returns:
            Dict com resultados da análise
        """
        
        logger.info("Iniciando análise híbrida de demanda")
        
        # Prepara dados para análise
        prepared_data = self._prepare_analysis_data(products_df, movements_df)
        
        # Executa análise local (sempre disponível)
        local_results = self.local_engine.analyze_products(prepared_data)
        
        # Tenta enriquecer com insights do Gemini
        gemini_insights = self._attempt_gemini_enhancement(prepared_data)
        
        if gemini_insights:
            # Combina resultados
            enhanced_results = self._merge_ai_insights(local_results, gemini_insights)
            enhanced_results['resumo_geral']['metodo_analise'] = "Análise Híbrida (Local + Gemini AI)"
            logger.info("Análise híbrida concluída com sucesso")
            return enhanced_results
        else:
            logger.info("Análise local concluída (Gemini indisponível)")
            return local_results
    
    def _prepare_analysis_data(self, products_df: pd.DataFrame, movements_df: pd.DataFrame) -> List[Dict]:
        """Prepara dados para análise"""
        
        prepared_data = []
        
        for _, product in products_df.iterrows():
            # Histórico de vendas do produto
            product_movements = movements_df[
                (movements_df['id_produto'] == product['id_produto']) &
                (movements_df['tipo'] == 'saida')
            ]
            
            # Converte para formato de análise
            sales_history = []
            for _, movement in product_movements.iterrows():
                try:
                    date = pd.to_datetime(movement['data']).strftime('%Y-%m-%d')
                    sales_history.append({
                        'data': date,
                        'quantidade': movement['quantidade'],
                        'observacao': movement.get('observacao', '')
                    })
                except:
                    continue
            
            product_data = {
                'id_produto': int(product['id_produto']),
                'nome': product['nome'],
                'categoria': product['categoria'],
                'preco_unitario': float(product['preco_unitario']),
                'estoque_atual': int(product['estoque_atual']),
                'vendidos_ultimos_30_dias': int(product.get('vendidos_ultimos_30_dias', 0)),
                'historico_vendas': sales_history
            }
            
            prepared_data.append(product_data)
        
        return prepared_data
    
    def _attempt_gemini_enhancement(self, products_data: List[Dict]) -> Optional[Dict]:
        """Tenta enriquecer análise com Gemini de forma inteligente"""
        
        # Verifica se vale a pena tentar usar Gemini
        if not self.gemini_client.is_quota_available():
            logger.info("Gemini indisponível - análise local será suficiente")
            return None
        
        # Só usa Gemini para produtos realmente prioritários
        priority_products = [
            p for p in products_data 
            if p.get('vendidos_ultimos_30_dias', 0) > 30  # Apenas produtos de alta rotatividade
        ][:2]  # Máximo 2 produtos para economizar quota
        
        if not priority_products:
            logger.info("Nenhum produto de alta prioridade para análise IA")
            return None
        
        # Prompt super otimizado para economizar tokens
        prompt = f"""
Analise estes produtos TOP de vendas:
{json.dumps(priority_products, ensure_ascii=False)}

JSON conciso:
{{
  "insights": [
    {{"produto": "nome", "dica": "estratégia em 10 palavras"}}
  ],
  "oportunidade": "principal insight em uma frase"
}}
"""
        
        response = self.gemini_client.generate_analysis(prompt)
        
        if response:
            try:
                # Parse mais tolerante
                clean_response = response.strip()
                if clean_response.startswith('```'):
                    clean_response = clean_response.split('\n', 1)[1]
                if clean_response.endswith('```'):
                    clean_response = clean_response.rsplit('\n', 1)[0]
                
                return json.loads(clean_response)
            except json.JSONDecodeError:
                logger.info("Resposta Gemini não é JSON válido - continuando com análise local")
                return None
        
        return None
    
    def _create_gemini_prompt(self, products_data: List[Dict]) -> str:
        """Cria prompt otimizado para Gemini"""
        
        prompt = f"""
Você é um especialista em análise de negócios. Analise estes produtos de alta prioridade e forneça insights estratégicos.

DADOS PRIORITÁRIOS:
{json.dumps(products_data, indent=2, ensure_ascii=False)}

Responda APENAS em JSON válido:
{{
  "insights_estrategicos": [
    {{"produto": "nome", "estrategia": "recomendação específica"}}
  ],
  "tendencias_mercado": "análise geral do portfólio",
  "oportunidades": ["lista de oportunidades identificadas"],
  "riscos_detectados": ["lista de riscos do negócio"]
}}

Foque em insights de negócio, não apenas estatísticas.
"""
        return prompt
    
    def _merge_ai_insights(self, local_results: Dict, gemini_insights: Dict) -> Dict:
        """Combina resultados local e Gemini"""
        
        # Adiciona insights do Gemini de forma mais simples
        if 'insights' in gemini_insights:
            local_results['resumo_geral']['insights_ia'] = gemini_insights['insights']
        
        if 'oportunidade' in gemini_insights:
            local_results['resumo_geral']['oportunidade_principal'] = gemini_insights['oportunidade']
        
        local_results['resumo_geral']['ia_utilizada'] = True
        
        return local_results

# Funções de interface para compatibilidade

def preparar_dados_para_analise(produtos_df: pd.DataFrame, movimentacoes_df: pd.DataFrame) -> List[Dict]:
    """Função de compatibilidade"""
    engine = HybridIntelligenceEngine()
    return engine._prepare_analysis_data(produtos_df, movimentacoes_df)

def executar_analise_completa() -> Dict:
    """Função principal de execução"""
    try:
        from core.gerenciamento_estoque import carregar_produtos, carregar_movimentacoes
        
        # Carrega dados
        produtos_df = carregar_produtos()
        movimentacoes_df = carregar_movimentacoes()
        
        if produtos_df.empty:
            return {"sucesso": False, "erro": "Nenhum produto encontrado"}
        
        # Executa análise híbrida
        engine = HybridIntelligenceEngine()
        resultado = engine.execute_complete_analysis(produtos_df, movimentacoes_df)
        
        # Salva resultados
        salvar_previsoes(resultado)
        
        # Preparar resumo para interface
        resumo = {
            "total_produtos": len(resultado.get('analises', [])),
            "produtos_risco": resultado.get('resumo_geral', {}).get('produtos_risco_ruptura', 0),
            "usando_gemini": "insights_ia" in resultado.get('resumo_geral', {})
        }
        
        return {
            "sucesso": True,
            "analise": resultado,
            "resumo": resumo
        }
        
    except Exception as e:
        logger.error(f"Erro na análise completa: {str(e)}")
        return {"sucesso": False, "erro": str(e)}

def salvar_previsoes(resultado_analise: Dict, caminho: str = "data/processed/previsoes_demanda.json"):
    """Salva resultados da análise"""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(resultado_analise, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Análise salva em: {caminho}")

if __name__ == "__main__":
    # Teste acadêmico do módulo
    print("🎓 TESTE ACADÊMICO - MÓDULO DE IA HÍBRIDA")
    print("=" * 60)
    
    resultado = executar_analise_completa()
    
    if resultado.get('sucesso'):
        resumo = resultado.get('resumo', {})
        print(f"✅ Análise concluída com sucesso!")
        print(f"📊 Produtos analisados: {resumo.get('total_produtos', 0)}")
        print(f"⚠️ Produtos em risco: {resumo.get('produtos_risco', 0)}")
        print(f"🤖 IA Gemini ativa: {resumo.get('usando_gemini', False)}")
        
        analise = resultado.get('analise', {})
        if 'resumo_geral' in analise:
            metodo = analise['resumo_geral'].get('metodo_analise', 'N/A')
            print(f"🔬 Método utilizado: {metodo}")
    else:
        print(f"❌ Erro na análise: {resultado.get('erro')}")