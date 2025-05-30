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
├── core/               # Módulos principais do sistema
│   ├── gerenciamento_estoque.py  # Controle de estoque (CRUD, alertas)
│   ├── previsao_demanda.py       # Modelos de IA para previsão
│   └── relatorios.py             # Geração de gráficos/relatórios
│
├── data/               # Gestão de dados
│   ├── processed/      # Dados processados (ex: previsões geradas)
│   └── raw/           # Dados originais (nunca alterados manualmente)
│       └── produtos.csv  # Base de produtos inicial
│
├── tests/              # Testes automatizados
│   ├── integracao/     # Testes de integração entre módulos
│   └── unitarios/      # Testes unitários
│       └── visualizacao_simples.py  # Teste da visualização básica
│
└── utils/              # Código compartilhado
    ├── config.py       # Configurações globais
    └── helpers.py      # Funções auxiliares reutilizáveis
