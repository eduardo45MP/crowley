# Modelo de dados do Crowley

## Entidades observadas

- `RawMarketplaceProduct`: payload imutável, fonte, external ID, query e coleta.
- `Product`: representação canônica normalizada ligada ao raw mais recente.
- `ProductCluster`: mercado de produto com nicho, tipo, problema e keywords.
- `ProductClusterMembership`: vínculo auditável entre produto e cluster.

## Artefatos analíticos

Cada dimensão usa um `*_analysis_run` e um score por cluster. O padrão inclui run ID, cluster ID, score, confidence, evidence coverage, features/components, model version e timestamp.

Tabelas implementadas:

- `demand_analysis_runs` / `cluster_demand_scores`;
- `competition_analysis_runs` / `cluster_competition_scores`;
- `purchase_intent_analysis_runs` / `cluster_purchase_intent_scores`;
- `build_ease_analysis_runs` / `cluster_build_ease_scores`;
- `differentiation_analysis_runs` / `cluster_differentiation_scores`;
- `opportunity_analysis_runs` / `cluster_opportunity_scores`;
- `eligibility_evaluation_runs` / `cluster_eligibility_results`;
- `selection_runs` / `selected_opportunities`;
- `deep_research_runs` / `deep_research_dossiers`;
- `top10_selection_runs` / `top10_opportunities`;
- `opportunity_theses`;
- `product_blueprints`;
- `research_competitor_profiles` / `research_evidence`.

## Opportunity e decisão

`cluster_opportunity_scores` preserva `components`, `source_analysis_ids`, `source_model_versions`, coverage, confidence, bottlenecks, weaknesses e warnings. Eligibility adiciona status e regras disparadas. Selection adiciona `selection_rank`, buyer group, quota bucket e utility. Nenhuma dessas tabelas substitui outra.

## Deep Research, Top10, Thesis e Blueprint

O dossier contém pricing, competitor profiles, keyword/review/structure analysis, gaps, confirmations, contradictions, coverage e confidence. Top10 adiciona rank, verdict e utility. Thesis estrutura a narrativa evidenciada. Blueprint é a fonte única de `scope_level`, `build_complexity` e `estimated_build_hours`.

## Modelos editoriais não persistidos no banco

`PublishedOpportunity` é uma projeção de publicação; não recalcula scores. `ReportSnapshot` é serializado no diretório imutável do report e fixa:

- report ID e criação;
- application/schema/methodology versions;
- Selection, Deep Research e Top10 run IDs;
- model versions;
- contagens solicitadas e disponíveis;
- janela e quantidade de observações.

## Ausência de evidência

Campos sem fonte persistida ficam `null`, lista vazia ou warning. O relatório não cria preço, esforço, confidence, thesis ou blueprint ausentes.
