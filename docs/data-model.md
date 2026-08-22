# Modelo de dados do Crowley

## Visão geral

O modelo de dados do projeto se baseia em entidades canônicas e em registros de análise por execução. O padrão dominante é: entidade principal + run + score por cluster.

## Entidades principais

### Product

Representa o produto canônico normalizado.

Campos principais:

- `id`
- `identity_key`
- `marketplace`
- `external_id`
- `product_name`
- `niche`
- `product_type`
- `price`
- `currency`
- `review_count`
- `rating`
- `seller`
- `url`
- `keywords`
- `description`
- `image_urls`
- `category`
- `listing_date`
- `listing_age_days`
- `query`
- `collected_at`
- `raw_product_id`

### RawMarketplaceProduct

Representa a observação bruta capturada do marketplace.

Campos principais:

- `id`
- `marketplace`
- `external_id`
- `query`
- `raw_payload`
- `collected_at`
- `created_at`

### ProductCluster

Representa um mercado de produto agrupado.

Campos principais:

- `id`
- `run_id`
- `name`
- `slug`
- `niche`
- `product_type`
- `primary_problem`
- `secondary_problems`
- `keywords`
- `product_count`
- `confidence`
- `created_at`
- `updated_at`

### ProductClusterMembership

Relaciona um `Product` ao cluster ao qual pertence.

Campos:

- `cluster_id`
- `product_id`
- `membership_score`
- `created_at`

## Execuções de análise

Para cada camada de market intelligence, o projeto persiste:

- uma tabela `*_analysis_runs` para a execução da análise
- uma tabela `cluster_*_scores` para o score por cluster

Exemplos:

- `demand_analysis_runs` + `cluster_demand_scores`
- `competition_analysis_runs` + `cluster_competition_scores`
- `purchase_intent_analysis_runs` + `cluster_purchase_intent_scores`
- `build_ease_analysis_runs` + `cluster_build_ease_scores`
- `differentiation_analysis_runs` + `cluster_differentiation_scores`
- `opportunity_analysis_runs` + `cluster_opportunity_scores`
- `eligibility_evaluation_runs` + `cluster_eligibility_results`
- `selection_runs` + `selected_opportunities`
- `deep_research_runs` + `deep_research_dossiers`

## Estrutura de score por cluster

A maioria das tabelas de score inclui:

- `run_id`
- `cluster_id`
- `score`
- `confidence`
- `evidence_coverage`
- `features`
- `components`
- `model_version`
- `calculated_at`

Os nomes podem variar por camada, mas o padrão é consistente.

## Opportunity Score

O resultado final é persistido em `cluster_opportunity_scores`.

Campos relevantes:

- `opportunity_score`
- `status`
- `qualification`
- `opportunity_confidence`
- `dimension_coverage`
- `evidence_coverage`
- `ranking_eligible`
- `source_analysis_ids`
- `source_model_versions`
- `bottlenecks`
- `strongest_dimension`
- `weakest_dimension`
- `fatal_weaknesses`
- `warnings`

## Eligibility result

Persistido em `cluster_eligibility_results`.

Campos relevantes:

- `status`
- `ranking_eligible`
- `triggered_rules`
- `blocking_reasons`
- `review_reasons`
- `warnings`
- `source_analysis_ids`
- `evaluated_at`

## Selection

Persistido em `selection_runs` e `selected_opportunities`.

Campos relevantes:

- `candidate_count`
- `eligible_count`
- `selected_count`
- `buyer_group`
- `quota_bucket`
- `selection_utility`
- `selection_reasons`

## Deep research dossier

Persistido em `deep_research_dossiers`.

Campos relevantes:

- `cluster_id`
- `cluster_name`
- `research_rank`
- `pricing_analysis`
- `competitor_profiles`
- `feature_matrix`
- `review_analysis`
- `keyword_analysis`
- `product_structure_analysis`
- `market_patterns`
- `confirmations`
- `contradictions`
- `warnings`
- `research_coverage`
- `research_confidence`
- `status`

## Validação de integridade

A aplicação usa a persistência relacional para preservar rastreabilidade e permitir reexecução dos módulos.

A regra prática foi: cada score, avaliação e dossier deve guardar a origem dos dados e a versão de modelo utilizada. Isso permite reprocessar ou depurar sem perder o contexto histórico.
