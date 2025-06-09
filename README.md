# Estoque Inteligente — Sistema de Controle de Estoque com I.A.
Sistema de controle de estoque simples e inteligente para pequenos comércios. Desenvolvido em Python com Streamlit e IA para prever demanda, registrar movimentações e exibir gráficos interativos. Projeto de extensão universitária com foco em acessibilidade e baixo custo.

---

## ✅ Principais Funcionalidades do Sistema de Controle de Estoque Inteligente

### 1. **Gestão de Produtos**

* [ ] Visualizar todos os produtos do estoque.
* [ ] Buscar produtos por nome, categoria ou ID.
* [ ] Adicionar, editar ou remover produtos (em versão final, com banco).
* [ ] Alertar quando estoque estiver baixo (ex: abaixo de 10 unidades).

### 2. **Relatórios de Vendas e Estoque**

* [ ] Mostrar os produtos mais vendidos nos últimos 30 dias.
* [ ] Ranking de categorias mais lucrativas.
* [ ] Relatório de estoque atual (para tomada de decisão de compra).
* [ ] Gráficos de movimentação do estoque.

### 3. **Previsão de Demanda com IA**

* [ ] Usar dados históricos de vendas para prever demanda futura.
* [ ] Sugerir reposições automáticas com base na previsão.
* [ ] Classificar produtos como: “Alta saída”, “Baixa saída”, “Sazonais”, etc.

### 4. **Sistema de Alerta e Reposição Inteligente**

* [ ] Avisar quando o estoque está acabando, com base na previsão.
* [ ] Priorizar reposição de produtos com alta demanda.

### 5. **Painel Interativo (futuro com Streamlit)**

* [ ] Interface amigável com filtros, busca e gráficos.
* [ ] Visualização dos dados em tempo real.

---

## 🏗️ Estrutura do Projeto

```bash
projeto_estoque_inteligente/
│
├── core/                          # Módulos principais do sistema
│   ├── gerenciamento_estoque.py  # Controle de estoque (CRUD, alertas, manipulação dos dados dos produtos)
│   ├── previsao_demanda.py       # Modelos de IA para previsão de demanda e comportamento do estoque
│   ├── relatorios.py             # Geração de gráficos, relatórios e visualizações para análise
│   ├── __init__.py               # Inicializador do pacote core (pode ficar vazio)
│   └── __pycache__/              # Cache dos arquivos compilados Python (gerado automaticamente)
│
├── data/                         # Gestão e armazenamento dos dados
│   ├── processed/                # Dados processados, resultados de previsões, arquivos intermediários
│   └── raw/                     # Dados originais, nunca alterados manualmente
│       └── produtos.csv          # Base de dados inicial dos produtos em CSV
│
├── tests/                        # Testes automatizados para garantir qualidade e funcionamento
│   ├── integracao/               # Testes de integração entre módulos do sistema
│   └── unitarios/                # Testes unitários focados em funções específicas
│       └── visualizacao_simples.py  # Teste da visualização básica dos dados CSV
│
├── utils/                        # Código compartilhado e funções auxiliares reutilizáveis
│   ├── config.py                 # Configurações globais e constantes do sistema
│   ├── helpers.py                # Funções auxiliares e utilitárias para o projeto
│   └── __init__.py               # Inicializador do pacote utils (pode ficar vazio)
│
├── app.py                       # Aplicação principal do Streamlit (interface web do sistema)
├── .gitignore                   # Arquivos/pastas ignorados pelo Git (ex: __pycache__, .env)
├── README.md                    # Documentação básica do projeto
├── requirements.txt             # Dependências Python para o ambiente do projeto

