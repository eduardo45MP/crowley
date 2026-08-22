# Pipeline do Crowley

## Visão geral

O pipeline atual do Crowley segue uma sequência linear e auditável, com cada etapa gerando um artefato persistido e cada etapa seguinte consumindo apenas o que foi produzido antes.

```text
crawler
  -> raw collection
  -> normalization
  -> clustering
  -> market intelligence
      -> demand
      -> competition
      -> purchase_intent
      -> build_ease
      -> differentiation
      -> opportunity_score
      -> eligibility
      -> selection
      -> deep_research
```

Este fluxo reflete o que está implementado no código e no repositório de persistência.

## 1. Coleta

A entrada do pipeline é a camada de crawler. Ela usa `MarketplaceProvider` e `ProductNormalizer` para captar listings, extrair campos e persistir os dados brutos.

Artefatos:

- `raw_marketplace_products`
- `products`
- `Product` canonizado

A coleta preserva o payload bruto e nunca sobrescreve o histórico de observações.

## 2. Normalização

A normalização converte dados de fontes específicas para um mesmo domínio canônico.

Funções principais:

- padronização de moeda e preço
- limpeza de texto e keywords
- normalização de URL, seller, categoria, review/rating
- geração de identidade canônica do produto

A normalização é determinística e separada do provider.

## 3. Clustering

O clustering agrega produtos canônicos em mercados de produto. Ele usa termos de nicho, problema e product type para construir clusters com `slug`, `confidence`, `keywords`, `product_count` e membros.

Artefatos:

- `cluster_runs`
- `product_clusters`
- `product_cluster_memberships`

## 4. Market intelligence por dimensão

Cada análise de dimensão é uma etapa independente e persistida.

### 4.1 Demand

Calcula um score da demanda a partir do sinal do cluster. Persiste `cluster_demand_scores` e `demand_analysis_runs`.

### 4.2 Competition

Analisa o ambiente competitivo e calcula um score favorável à oportunidade, não uma quantidade absoluta de competição. Persistido em `cluster_competition_scores`.

### 4.3 Purchase intent

Captura probabilidade de compra e valor percebido. Persistido em `cluster_purchase_intent_scores`.

### 4.4 Build ease

Anota a dificuldade de construir o produto. Persistido em `cluster_build_ease_scores`.

### 4.5 Differentiation

Avalia lacunas, diferenciação, uyx e oportunidades de posicionamento. Persistido em `cluster_differentiation_scores`.

## 5. Opportunity score

A camada de `opportunity` consolida resultados das dimensões independentes em um único score de 0 a 100.

Ela calcula:

- `opportunity_score`
- `opportunity_confidence`
- `dimension_coverage`
- `evidence_coverage`
- `strongest_dimension`
- `weakest_dimension`
- `fatal_weaknesses`
- `ranking_eligible`

A regra de composição é definida em configuração e registrada em `opportunity_analysis_runs` e `cluster_opportunity_scores`.

## 6. Eligibility

Eligibility responde se a oportunidade deve prosseguir para ranking ou produção. Ele usa `EligibilityContext` e regras separadas.

Resultados:

- `eligible`
- `review_required`
- `ineligible`
- `insufficient_data`

Persistência:

- `eligibility_evaluation_runs`
- `cluster_eligibility_results`

## 7. Selection

Selection usa o conjunto de oportunidades elegíveis para montar um portfólio final com diversificação, quotas por buyer group e limites por nicho ou problema.

Persistência:

- `selection_runs`
- `selected_opportunities`

## 8. Deep Research

Deep research atua sobre o portfólio selecionado e produz dossiers mais detalhados, sem alterar o score original.

O output inclui:

- pricing analysis
- competitor profiles
- keyword analysis
- product structure analysis
- market patterns
- confirmations and contradictions
- research coverage/confidence

Persistência:

- `deep_research_runs`
- `deep_research_dossiers`

## 9. Regra de separação

Uma regra importante do projeto é a seguinte:

- deep research não inventa fatos novos que alterem o Opportunity Score
- eligibility não reescreve a dimensão original
- selection não é um sort simples
- cada etapa cria um resultado adicional, em vez de substituir a etapa anterior

## 10. Limites do pipeline atual

O código executável hoje não inclui:

- API para servir dados
- dashboard para revisão humana
- execução de jobs em background
- exportação adequada de relatórios
- LLM ou evidência externa não estruturada

O que existe é um pipeline determinístico, rastreável e orientado a evidência para pesquisa local de oportunidades digitais.
