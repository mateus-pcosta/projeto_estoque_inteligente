# 📦 Sistema de Controle de Estoque Inteligente

## 🎯 O que é este sistema?

Este é um sistema completo de controle de estoque com **Inteligência Artificial** que ajuda pequenos comerciantes a:

- 📊 Controlar produtos e movimentações
- 🤖 Prever demanda futura usando Machine Learning
- ⚠️ Receber alertas de produtos críticos
- 📈 Gerar relatórios automáticos
- 💰 Otimizar compras e reduzir perdas

---

## 🚀 Como começar

### 1. Instalação

```bash
# Clone ou baixe o projeto
cd projeto_estoque_inteligente

# Instale as dependências
pip install -r requirements.txt

# Execute o sistema
streamlit run app.py
```

### 2. Primeiro Acesso

1. Abra seu navegador em: `http://localhost:8501`
2. O sistema já vem com dados de exemplo
3. Comece explorando as abas do menu lateral

---

## 📋 Como usar cada funcionalidade

### 🏠 **Dashboard Principal**
- **Visão geral** do seu estoque
- **Alertas importantes** em destaque
- **Métricas principais** (produtos críticos, vendas, etc.)
- **Gráficos** de vendas e categorias

### 📦 **Gerenciar Produtos**

#### Adicionar Produto
1. Vá em "Gerenciar Produtos"
2. Preencha: Nome, Categoria, Preço, Estoque inicial
3. Clique em "Adicionar Produto"

#### Visualizar Produtos
- Lista todos os produtos
- Use os **filtros** para encontrar produtos específicos
- Veja estoque atual e informações detalhadas

### 📊 **Movimentação de Estoque**

#### Registrar Entrada (Compras)
1. Vá em "Movimentação de Estoque"
2. Selecione "Entrada"
3. Escolha o produto e quantidade
4. Adicione observações se necessário

#### Registrar Saída (Vendas)
1. Selecione "Saída"
2. Escolha produto e quantidade vendida
3. O sistema atualiza automaticamente o estoque

### 🤖 **Previsão de Demanda (IA)**

#### Como funciona
- O sistema analisa seu **histórico de vendas**
- Usa **Machine Learning** para prever vendas futuras
- Considera padrões: dias da semana, sazonalidade, tendências

#### Usar a IA
1. Vá em "Previsão de Demanda"
2. Selecione um produto
3. Escolha quantos dias prever (padrão: 14 dias)
4. Veja as previsões e insights

#### Dicas importantes
- ⚠️ **Mínimo 14 dias** de histórico para IA funcionar
- 📈 Mais dados = previsões mais precisas
- 🔄 Sistema aprende automaticamente com novas vendas

### 📈 **Relatórios**

#### Relatório de Vendas
- Vendas por período (7, 15, 30 dias)
- Produtos mais vendidos
- Análise por categoria
- Tendências de vendas

#### Estoque Crítico
- 🚨 **Crítico**: produtos acabando em ≤ 3 dias
- ⚠️ **Atenção**: produtos acabando em ≤ 7 dias
- 💰 Valor necessário para reposição
- Lista de compras otimizada

#### Exportar para Excel
1. Vá em "Relatórios"
2. Clique em "Exportar Relatório Excel"
3. Arquivo será salvo na pasta `relatorios/`
4. Contém todas as análises em abas separadas

---

## 🎨 Entendendo os Alertas

### Cores dos Produtos
- 🔴 **Vermelho**: CRÍTICO (≤ 3 dias de estoque)
- 🟡 **Amarelo**: ATENÇÃO (≤ 7 dias de estoque)
- 🟢 **Verde**: NORMAL (estoque OK)
- 🔵 **Azul**: EXCESSO (muito estoque)

### Símbolos
- 🤖 = Previsão com IA ativa
- 📊 = Dados suficientes para análise
- ⚠️ = Requer atenção
- 🚨 = Urgente

---

## 💡 Dicas para Melhores Resultados

### Para a IA funcionar melhor:
1. **Registre todas as vendas** diariamente
2. **Mantenha dados atualizados** (preços, categorias)
3. **Use pelo menos 30 dias** de histórico
4. **Seja consistente** nos registros

### Gestão de Estoque:
1. **Confira alertas** diariamente
2. **Use relatórios** para planejar compras
3. **Monitore produtos críticos** semanalmente
4. **Analise categorias** mensalmente

### Organização:
1. **Categorize produtos** corretamente
2. **Use nomes descritivos** para produtos
3. **Adicione observações** nas movimentações
4. **Faça backup** dos dados regularmente

---

## 🔧 Solução de Problemas

### Problemas Comuns:

#### "Dados insuficientes para IA"
- **Causa**: Menos de 14 dias de vendas
- **Solução**: Continue registrando vendas, a IA ativará automaticamente

#### "Erro ao carregar dados"
- **Causa**: Arquivo CSV corrompido
- **Solução**: Verifique os arquivos na pasta `data/raw/`

#### Previsões estranhas
- **Causa**: Dados inconsistentes ou poucos
- **Solução**: Revise histórico de vendas, remova outliers

#### Sistema lento
- **Causa**: Muitos dados ou modelos ML
- **Solução**: Limpe cache, reinicie o Streamlit

---

## 📊 Estrutura dos Dados

### Produtos (produtos.csv)
```
id_produto,nome,categoria,preco_unitario,estoque_atual,vendidos_ultimos_30_dias
1,Coca-Cola 2L,Bebidas,8.50,29,54
```

### Movimentações (movimentacoes.csv)
```
id_movimentacao,id_produto,tipo,quantidade,data,usuario,observacao,nome,categoria
1,1,entrada,50,2023-11-01,Sistema,Compra inicial,Coca-Cola 2L,Bebidas
```

---

## 🆘 Suporte

### Para dúvidas:
1. Leia este manual completo
2. Verifique os exemplos no sistema
3. Consulte os logs de erro (se houver)

### Backup dos Dados:
- **Produtos**: `data/raw/produtos.csv`
- **Movimentações**: `data/raw/movimentacoes.csv`
- **Banco**: `data/raw/estoque.db`
- **Modelos IA**: pasta `models/`

---

## 🎓 Conceitos Importantes

### **Giro de Estoque**
- Quantas vezes o produto "gira" no período
- Alto giro = produto popular
- Baixo giro = produto parado

### **Previsão de Demanda**
- Estimativa de vendas futuras
- Baseada em histórico e padrões
- Ajuda a planejar compras

### **Estoque de Segurança**
- Quantidade extra para emergências
- Sistema sugere +20% sobre demanda prevista
- Evita rupturas inesperadas

### **Sazonalidade**
- Variações por época do ano
- Sistema detecta padrões automaticamente
- Importante para planejamento

---

## ✅ Checklist Diário

Para usar o sistema eficientemente:

- [ ] Registrar todas as vendas do dia
- [ ] Verificar alertas de produtos críticos
- [ ] Confirmar recebimento de mercadorias (entradas)
- [ ] Revisar previsões da IA
- [ ] Planejar compras baseado nos relatórios

---

**🎉 Pronto! Agora você tem um sistema profissional de controle de estoque com Inteligência Artificial!**

*Sistema desenvolvido para pequenos comerciantes - Simples, poderoso e eficiente.*