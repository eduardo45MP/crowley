# Pipeline do Crowley

## Sequência executável

```text
Crawler -> Normalization -> Clustering -> Market Intelligence
-> Opportunity -> Eligibility -> Selection -> Deep Research
-> Top10 -> Opportunity Thesis -> Product Blueprint
-> Editorial Snapshot -> Reporting
```

Cada seta representa consumo de um artefato anterior e criação de um novo artefato.

## 1. Crawler e Normalization

Providers produzem `RawMarketplaceProduct`; normalizers produzem `Product`. O raw payload e o timestamp de observação são preservados. O provider `mock` permite execução offline determinística.

## 2. Clustering

Produtos canônicos são agrupados em `ProductCluster`, com memberships, nicho, problema, tipo e termos canônicos. Ao recarregar um cluster, o repository também recarrega seus membros para que análises posteriores usem evidência real.

## 3. Market Intelligence

Demand, Competition, Purchase Intent, Build Ease e Differentiation são independentes e versionados. Cada execução persiste um run e scores por cluster.

## 4. Opportunity

Agrega dimensões já calculadas, registra componentes, coverage, confidence, source analysis IDs e source model versions. Price Potential continua opcional; sua ausência torna o score provisional conforme a política existente.

## 5. Eligibility

Aplica gates de risco, cobertura, demanda, diferenciação e escopo. Produz `eligible`, `review_required`, `ineligible` ou `insufficient_data` sem alterar o score.

## 6. Selection

Monta o portfólio com quotas de buyer group e diversidade por nicho/problema. Persiste `SelectionRun` e `SelectedOpportunity`. O `selection_rank` é a ordem editorial Top 100.

## 7. Deep Research

Analisa pricing, concorrentes, keywords, reviews, estruturas e gaps dos selecionados. Persiste runs e dossiers. Confirmações ou contradições não reescrevem Opportunity Score.

## 8. Top10, Thesis e Blueprint

Top10Selector usa Opportunity Score, qualidade da evidência, clareza e contradições para uma decisão separada. Opportunity Thesis estrutura comprador, problema, evidência e vantagem. Product Blueprint define escopo, features e `estimated_build_hours`.

## 9. Editorial Snapshot

`EditorialReportService` carrega Selection como fonte primária, limita em até 100 e acrescenta dados disponíveis. Não fabrica candidatos. Keywords vêm somente de análise do dossier, termos do cluster e keywords observadas em concorrentes.

## 10. Reporting

O snapshot gera `report.json`, `opportunities.csv`, `crowley-opportunities.xlsx` e `crowley-report.pdf`. O JSON contém `metadata`, `methodology`, `summary`, `top10`, `ranking` e `provenance`.

## Execução offline completa

```bash
python -m market_intelligence pipeline demo --output-dir data/reports
```

Para dados persistidos reais, execute os comandos sequenciais documentados no README e finalize com:

```bash
python -m market_intelligence report build --selection-run <id> --top 100 --top10 10
```
