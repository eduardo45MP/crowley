# Crowley Architecture

## Visão geral

Crowley é um pipeline local de market intelligence para identificar oportunidades comerciais em nichos digitais. O código implementado hoje cobre coleta, normalização, clustering e análise de mercado em várias dimensões independentes antes da consolidação final em um Opportunity Score.

A arquitetura real do projeto é a seguinte:

```text
crawler
  -> raw listings
  -> normalization
  -> product clustering
  -> market intelligence dimensions
      -> demand
      -> competition
      -> purchase_intent
      -> build_ease
      -> differentiation
      -> opportunity score
      -> eligibility filters
      -> selection
      -> deep research
```

Este projeto não define, neste momento, uma API HTTP, dashboard, exportador de relatórios ou fila de jobs como parte do código executável. O que existe é um monólito modular com módulos bem separados e uma base relacional SQLite-first.

## Status da arquitetura

### Implementado

- `src/crawler`: coleta, normalização, clustering e persistência
- `src/market_intelligence/demand`: análise de demanda
- `src/market_intelligence/competition`: análise competitiva
- `src/market_intelligence/purchase_intent`: intenção de compra
- `src/market_intelligence/build_ease`: facilidade de produção
- `src/market_intelligence/differentiation`: diferenciação e potencial de nicho
- `src/market_intelligence/opportunity`: agregação final em 0-100
- `src/market_intelligence/eligibility`: filtro de elegibilidade para ranking
- `src/market_intelligence/selection`: seleção de portfólio final
- `src/market_intelligence/deep_research`: deep research determinístico e auditável

### Planejado / não implementado no código atual

- API REST ou GraphQL
- dashboard interno
- relatórios PDF/XLSX/CSV automatizados
- workers assíncronos independentes
- migrações Alembic
- LLM em deep research

Essas camadas podem ser evoluções futuras, mas não devem ser apresentadas como já existentes.

## Princípios da arquitetura

1. Evidência antes de geração.
2. Dados brutos são imutáveis.
3. Cada camada analítica trabalha sobre resultados da etapa anterior e não reescreve evidências anteriores.
4. Scores devem ser auditáveis e explicáveis.
5. O Opportunity Score não tenta descobrir novos fatos de mercado; ele apenas agrega dimensões independentes já produzidas.
6. Eligibility e selection são etapas separadas de ranking.
7. Deep research adiciona due diligence, mas não altera o score upstream.

## Camadas do sistema

### 1. Crawler

O crawler coleta listings em marketplaces e salva raw payloads e modelos canônicos. A interface principal é a CLI em `src/crawler/cli.py`.

Responsabilidades:

- buscar listings por query
- normalizar para o domínio canônico
- preservar payloads brutos em `raw_marketplace_products`
- persistir `products` canônicos
- agrupar itens em `product_clusters`

### 2. Clustering

A etapa de clustering converte produtos canônicos em mercados de produto. A lógica está em `src/crawler/clustering.py`, com taxonomia em `src/taxonomy`.

Os clusters são baseados em termos de nicho, problema, tipo de produto e palavras-chave, e persistidos no banco com `cluster_runs` e `product_clusters`.

### 3. Market Intelligence

A camadas de inteligência de mercado são independentes entre si. Cada uma produz um score e um contexto de confiança/coverage para um cluster.

Atualmente, as dimensões implementadas são:

- demand
- competition
- purchase_intent
- build_ease
- differentiation

Cada uma usa um `AnalysisRun` e um `Cluster...Score` persistidos no SQLAlchemy repository.

### 4. Opportunity Score

O Opportunity Score está em `src/market_intelligence/opportunity/` e combina as dimensões independentes com pesos fixos em configuração.

A regra de composição é:

```text
Opportunity Score =
  0.30 * demand
+ 0.20 * purchase_intent
+ 0.15 * competition
+ 0.15 * differentiation
+ 0.10 * build_ease
+ 0.10 * price_potential
```

A implementação atual também registra:

- `dimension_coverage`
- `evidence_coverage`
- `opportunity_confidence`
- `bottlenecks`
- `strongest_dimension`
- `weakest_dimension`
- `fatal_weaknesses`
- `ranking_eligible`

Importante: a camada de opportunity não faz nova investigação; ela apenas consolida os outputs das demais camadas.

### 5. Eligibility Filters

A elegibilidade está em `src/market_intelligence/eligibility/` e responde se a oportunidade é aceitável para entrar em ranking e potencial produção.

As regras cobrem:

- demanda mínima
- confiança mínima
- cobertura mínima de evidência
- risco de nicho regulado
- product types restritos
- sinais de fraude ou promessas irrealistas
- complexidade excessiva de build

A decisão final é `eligible`, `review_required`, `ineligible` ou `insufficient_data`.

### 6. Selection

A seleção está em `src/market_intelligence/selection/` e não é uma ordenação simples.

A lógica faz:

- filtra candidatos elegíveis
- aplica mínimo de oportunidade e confiança
- respeita quotas por buyer group
- limita por nicho e problema
- diversifica o portfólio

A saída final é um conjunto de oportunidades selecionadas com `selection_rank`, `quota_bucket` e utilidade de seleção.

### 7. Deep Research

A deep research está em `src/market_intelligence/deep_research/` e tem duas metas explícitas:

- executar due diligence para as oportunidades selecionadas
- produzir dossiers auditáveis e determinísticos

A V1 não usa LLM. Ela sintetiza:

- pricing analysis
- competitor profiles
- keyword analysis
- product structure analysis
- review themes
- market patterns
- confirmations, contradictions e warnings

A deep research não reescreve o score original; ela apenas adiciona contexto de pesquisa.

## Fluxo executado no código atual

```text
1. coleta de listings via crawler
2. normalização para Product
3. clustering por mercado
4. cálculo de demand
5. cálculo de competition
6. cálculo de purchase_intent
7. cálculo de build_ease
8. cálculo de differentiation
9. cálculo do opportunity_score
10. avaliação de eligibility
11. seleção do portfólio
12. deep_research para shortlisted clusters
```

## Persistência real

A base relacional persiste os resultados de cada camada, permitindo auditoria do pipeline completo. O repository em `src/crawler/repositories/sqlalchemy_repository.py` tem tabelas para as análises e scores finais, bem como para os resultados de elegibilidade e seleção.

Nenhuma camada de API ou job separado foi implementada para abstrair essa persistência.

## Limites explícitos

Este repositório não implementa ainda:

- GraphQL/REST API
- dashboard operatório
- serviço de exportação de relatórios
- filas ou workers
- migrações em Alembic
- publicação de snapshots para terceiros

Esses itens continuam no plano arquitetural do projeto, não como funcionalidade atual.

## Comandos reais do projeto

```bash
python -m crawler search "quebra de preço" --provider mock
python -m crawler cluster --limit 500
python -m market_intelligence demand calculate --limit 50
python -m market_intelligence competition calculate --limit 50
python -m market_intelligence purchase-intent calculate --limit 50
python -m market_intelligence build-ease calculate --limit 50
python -m market_intelligence differentiation calculate --limit 50
python -m market_intelligence opportunity calculate --limit 50
python -m market_intelligence eligibility evaluate --limit 50
python -m market_intelligence selection run --limit 200
python -m market_intelligence deep-research run --limit 25 --top 25
```

Essa é a superfície executável que o repositório entrega hoje.

## 9. Persistence

### Relational database

PostgreSQL is the recommended production system of record. SQLite is acceptable for a single-user local proof of concept. Store campaigns, canonical entities, observations, jobs, memberships, feature snapshots, scorecards, editorial decisions, and publication metadata relationally.

Use database constraints for idempotency keys, source identities, version uniqueness, and state transitions. Use JSON columns only for genuinely source-specific or versioned payloads; important queryable domain fields remain typed columns.

### Object storage

Use S3-compatible storage for raw HTML/JSON, permitted images/screenshots, large exports, and published report artifacts. Objects are content-addressed or carry a checksum. Database rows retain their URI, hash, media type, collection time, and retention policy.

### Search and vectors

For the MVP, PostgreSQL full-text search and `pgvector` are sufficient. Introduce a separate search or vector system only when corpus size, latency, or retrieval quality demonstrates the need.

### Cache

A cache is optional at first. If introduced, it accelerates external requests and read-heavy views but never becomes the system of record. Cache keys include source, normalized query, locale, and connector version.

### Retention and sensitive data

Store only data needed for research and auditability. Avoid unnecessary personal data, especially community usernames or profiles. Define source-specific retention and deletion procedures, encrypt credentials/secrets, and keep secrets out of raw payloads and logs.

## 10. Provenance and versioning

Every published claim should be traversable through this chain:

```text
report claim / rank
  -> scorecard and editorial annotation
  -> feature snapshot
  -> evidence records
  -> normalized observation or external signal
  -> immutable raw payload and collection metadata
```

The following versions are recorded independently:

- application commit/build;
- database schema;
- connector and parser;
- canonical schema;
- taxonomy and query vocabulary;
- enrichment rule, model, and prompt;
- embedding model;
- clustering algorithm/configuration;
- feature definition and normalization curve;
- eligibility policy;
- scoring formula and ranking/diversity policy;
- editorial content and report template.

A published `ReportSnapshot` pins all applicable versions, the observation window, currency/date assumptions, and evidence IDs. Re-running newer logic produces a new snapshot and a diff; it never mutates an earlier edition.

## 11. Observability and data quality

### Operational telemetry

Use structured logs, metrics, and distributed traces with campaign, run, job, query, source, and entity correlation IDs. Do not log credentials or unrestricted raw content.

Key operational metrics include:

- crawl success/rate-limit/block rates by source;
- request latency, retry count, queue age, and dead-letter count;
- raw-to-normalized throughput and lag;
- parser yield and field completeness;
- enrichment latency, cost, and confidence;
- cluster size, unassigned rate, and membership-confidence distribution;
- report build duration and artifact failures.

### Data and model quality

Track schema drift, unexpected nulls, duplicate rates, price/currency anomalies, taxonomy coverage, cluster cohesion/separation, score distributions, feature freshness, evidence coverage, and manual-override rates. Alert on sudden source/parser changes and ranking shifts beyond configured tolerances.

Use small labeled evaluation sets for classification, entity resolution, and clustering. For scoring, monitor stability across reruns and, once outcomes exist, rank correlation, precision among top candidates, calibration by segment, and performance against random/manual baselines.

### Auditability

All manual overrides, exclusions, approvals, formula changes, and publication actions have actor, timestamp, before/after values, and rationale. Dashboards must show why an opportunity received its score and what evidence is missing or stale.

## 12. Security and compliance boundaries

- Prefer official APIs and licensed datasets; document the legal basis and terms for every connector.
- Enforce per-source throttles, crawl windows, user-agent/contact policy, and kill switches.
- Isolate browser/extraction execution from the main application when it processes untrusted content.
- Validate and sanitize fetched content; never execute scripts or follow arbitrary file references from a source payload.
- Store source and model credentials in a secret manager with least privilege and rotation.
- Apply role-based access for researchers, reviewers, and publishers.
- Treat LLM-retrieved content as untrusted; defend against prompt injection and require structured outputs with validation.
- Maintain deletion and retention workflows for raw content and generated artifacts.
- Label regulated, financial, medical, or legal-risk categories and require explicit review or exclusion.

## 13. Suggested modular monorepo

The exact language/framework is secondary to enforcing dependency direction. One suggested structure is:

```text
crowley/
├── architecture.md
├── README.md
├── pyproject.toml                 # or equivalent workspace manifest
├── apps/
│   ├── api/                       # HTTP entry point
│   ├── worker/                    # background-job entry point
│   ├── scheduler/                 # recurring campaign/job scheduling
│   └── dashboard/                 # internal research UI, when needed
├── src/crowley/
│   ├── research_catalog/          # taxonomy, seeds, query generation
│   ├── collection/                # connector interfaces and orchestration
│   │   └── connectors/            # one adapter package per source
│   ├── raw_store/                 # payload metadata and object storage
│   ├── normalization/             # canonical listing transformations
│   ├── identity/                  # deduplication/entity resolution
│   ├── enrichment/                # classifiers, extraction, embeddings
│   ├── clustering/                # product-market grouping
│   ├── analysis/                  # signals and feature snapshots
│   ├── eligibility/               # eliminatory policy rules
│   ├── scoring/                   # formulas and ranking policies
│   ├── editorial/                 # human review and content snapshots
│   ├── reporting/                 # PDF/XLSX/CSV/JSON generation
│   ├── outcomes/                  # launch metrics and calibration
│   ├── provenance/                # evidence/version/audit graph
│   ├── jobs/                      # job definitions, outbox, handlers
│   └── platform/                  # DB, storage, telemetry, config, security
├── migrations/
├── configs/
│   ├── taxonomies/
│   ├── scoring/
│   ├── policies/
│   └── sources/
├── templates/
│   └── reports/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── fixtures/
│   └── evaluation/                # labeled model/cluster datasets
├── scripts/                       # explicit backfills and admin utilities
└── docs/
    ├── adr/                       # architecture decision records
    ├── data-dictionary.md
    ├── methodology.md
    └── runbooks/
```

Domain modules expose application services and typed contracts; they do not import connector, web, or database implementation details directly. `platform` supplies adapters through dependency injection. Apps compose modules but contain little business logic. Cross-module writes occur through application services, and asynchronous reactions use the outbox/event contracts.

## 14. MVP delivery strategy

The MVP should answer one question: **Can Crowley identify commercially stronger opportunities than a person doing ad hoc manual research?**

### MVP scope

1. A curated catalog of roughly 500 niches/professions and a small problem/tool vocabulary.
2. A versioned query generator.
3. One marketplace connector, initially collecting at least title, price, review count, and URL.
4. PostgreSQL or SQLite plus immutable raw payload storage.
5. Basic deterministic normalization and deduplication.
6. Clustering into product markets, with a practical human review path.
7. The six component scores and versioned Opportunity Score.
8. Eligibility filters and a diversity-aware Top 100.
9. A reproducible report and spreadsheet export.

### Explicit non-goals

- a public SaaS or polished customer dashboard;
- many marketplace integrations;
- fully autonomous publishing;
- automatic product generation;
- real-time processing;
- microservices, Kubernetes, or separate data platforms;
- claims that reviews, trends, or scores equal sales or revenue.

### Recommended implementation sequence

**Milestone 1 — vertical slice:** run a small campaign through query generation, one connector, raw capture, normalization, database inspection, and CSV export.

**Milestone 2 — opportunity discovery:** enrich and cluster enough listings to produce recognizable product markets; establish a labeled review set and correct obvious grouping errors.

**Milestone 3 — explainable ranking:** compute feature snapshots, exclusions, scorecards, confidence, and a traceable Top 100. Validate with manual research and sensitivity analysis on weights.

**Milestone 4 — editorial product:** deepen the Top 25, produce Top 10 blueprints, freeze a snapshot, and generate the PDF and spreadsheet.

**Milestone 5 — market validation:** sell or otherwise test the report, build the top three products, ingest views/CTR/favorites/sales/conversion, and compare results with scores and random/manual selections.

Success progresses through three levels:

- **Research:** 100 convincing, evidence-backed opportunities.
- **Product:** buyers value the report.
- **Prediction:** products chosen by the scoring model outperform random or manually chosen baselines.

The third level is the strongest evidence that Crowley is becoming a predictive opportunity-discovery engine rather than only a research publishing workflow.

## 15. Evolution path

Evolution should follow evidence and workload, not a fixed platform roadmap.

### Near term

- add marketplace and external-signal connectors behind stable adapter contracts;
- schedule recurring editions and compare time-series snapshots;
- improve taxonomy, entity resolution, clustering evaluation, and evidence confidence;
- add internal review screens and score sensitivity/diff views;
- ingest product-launch outcomes and recalibrate feature curves and weights.

### Continuous discovery

- identify emerging queries, rapidly growing clusters, and new niche/problem combinations;
- expand the research vocabulary from observed terms with human approval;
- detect meaningful price, demand, competition, and ranking changes;
- create subscription editions and alerts from reproducible snapshots.

### Possible SaaS

A future customer interface may accept a target audience or product category and return analyzed markets, evidence, score breakdowns, build effort, price range, and research briefs. Multi-tenancy, quotas, billing, customer-specific campaigns, and stricter availability requirements should be designed only when this product direction is validated.

### Conditional service extraction

Keep the modular monolith until concrete thresholds justify extraction. Likely first candidates are collection/browser workers, embedding or LLM enrichment, report rendering, and high-volume search. Before extracting a module, require:

- measured independent scaling or isolation need;
- a stable, versioned contract;
- clear data ownership and failure semantics;
- observability and operational ownership;
- evidence that the added deployment and consistency cost is worthwhile.

The relational system of record, provenance model, and snapshot semantics should remain authoritative even if execution components are later distributed.

## 16. Key architecture decisions to record next

Create ADRs as implementation choices are made, beginning with:

1. language and application framework;
2. PostgreSQL versus SQLite for the first deployable version;
3. job queue and transactional outbox implementation;
4. object-storage provider and raw-data retention policy;
5. first marketplace/source and compliant collection method;
6. canonical listing and evidence schemas;
7. clustering baseline and evaluation dataset;
8. scoring missing-data/confidence policy;
9. report generation toolchain;
10. authentication, roles, and secrets management.

These decisions refine the implementation without changing the central architecture: a traceable, versioned, evidence-first pipeline delivered initially as a modular monolith.
