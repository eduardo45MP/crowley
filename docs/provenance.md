# Provenance e rastreabilidade

## Objetivo

O projeto prioriza rastrear a origem de cada resultado e garantir que decisões sejam auditáveis.

## Padrão atual

Cada análise produz:

- um `*_analysis_run` com metadados da execução
- scores por cluster em `cluster_*_scores`
- `model_version`
- `calculated_at`
- `components` e `features`
- `source_analysis_ids` quando relevante

## Exemplos de rastreabilidade

### Opportunity Score

A saída final preserva:

- `source_analysis_ids`
- `source_model_versions`
- `components`
- `dimension_coverage`
- `evidence_coverage`
- `warnings`

### Eligibility

A avaliação preserva:

- `triggered_rules`
- `blocking_reasons`
- `review_reasons`
- `warnings`

### Deep Research

O dossier mantém a origem observável em:

- `competitor_profiles`
- `pricing_analysis`
- `review_analysis`
- `keyword_analysis`
- `product_structure_analysis`

## Regras de projeto

- dados brutos são imutáveis
- resultados derivados não sobem ao nível de fato sem evidência
- cada versão de modelo deve ser registrada
- cada cluster deve manter o vínculo para as dimensões que o alimentaram

## Limite de auditoria atual

O projeto ainda não implementa um sistema de outbox, event stream ou dashboard para revisar provas de forma centralizada. Mas a estrutura de banco e de modelos já preserva os elementos necessários para rastrear a origem dos principais resultados.
