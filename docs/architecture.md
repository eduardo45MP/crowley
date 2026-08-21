# Crowley Architecture

## 1. Purpose and scope

Crowley is a market-research and market-intelligence pipeline for discovering, evaluating, and ranking opportunities for niche digital products. Its first use case is identifying spreadsheets, calculators, and operational trackers/templates that can be sold in digital marketplaces.

The system turns marketplace listings and external demand signals into evidence-backed product-market opportunities:

```text
Sources
  -> crawler/connectors
  -> immutable raw data
  -> normalization
  -> enrichment
  -> clustering into product markets
  -> market analysis
  -> opportunity scoring
  -> API / dashboard / reports
```

Crowley does not treat a listing as an opportunity. Listings are observations; a cluster of comparable listings and external signals represents a candidate product market. Scores are comparative estimates built from evidence, not claims of sales or guaranteed revenue.

The initial product is a research report containing 100 ranked opportunities, a detailed Top 10, methodology, evidence, suggested pricing and positioning, keywords, and estimated build effort. A complementary spreadsheet exposes the ranking and its inputs for filtering and inspection.

## 2. Architectural decision: modular monolith first

Crowley should begin as a **modular monolith**, not as microservices.

The crawler, normalizer, enrichment pipeline, clustering engine, analyzers, scoring engine, and reporting layer should live in one deployable application with explicit module boundaries. Background workers may run as separate processes from the API, but they use the same codebase and versioned domain contracts.

This choice provides:

- simple local development and deployment;
- atomic database changes and easier reproducibility;
- low operational overhead while scoring assumptions change quickly;
- direct tracing of evidence from a report back to its source;
- module boundaries that permit later extraction when scale or team ownership justifies it.

Separate services are warranted only after measured pressure appears, such as independently scaling browser-heavy collection, isolating untrusted extraction workloads, assigning a component to a separate team, or meeting distinct availability requirements. Network boundaries must not be introduced merely to imitate the logical pipeline.

## 3. Architectural principles

1. **Evidence before generation.** Every conclusion and score must be traceable to collected observations or an explicitly identified estimate.
2. **Raw data is immutable.** Preserve source responses and collection context so normalization and scoring can be rerun without recrawling.
3. **Separate facts, derived features, and judgments.** Source observations, deterministic transformations, model-derived annotations, and editorial decisions have different provenance and confidence.
4. **Idempotent, resumable processing.** A job may be retried without duplicating logical records or corrupting downstream state.
5. **Version every material transformation.** Parsers, taxonomies, prompts/models, cluster assignments, feature definitions, and score formulas are versioned.
6. **Scores are explainable snapshots.** A ranked opportunity records its component scores, weights, evidence window, exclusions, and calculation version.
7. **Source adapters do not leak into the domain.** Marketplace-specific fields stop at the normalization boundary.
8. **Human review is a first-class stage.** Automated ranking narrows the research space; it does not remove editorial review, particularly for the Top 25 and Top 10.
9. **Compliance by design.** Collection respects applicable terms, robots policies, rate limits, privacy constraints, and source-specific retention rules.
10. **Start narrow and validate predictive value.** The first goal is to outperform ad hoc manual research, not to build a general web crawler or SaaS.

## 4. System context

```text
 Marketplace APIs/pages       External signals       Editorial inputs
 Etsy / Gumroad / ...     Search / trends / forums   niches / exclusions
          \                         |                         /
           +------------------------+------------------------+
                                    |
                              Crowley pipeline
                                    |
                +-------------------+-------------------+
                |                   |                   |
             REST API          Dashboard/admin     Report exports
                                                    PDF / XLSX / CSV
```

External sources answer different questions. Marketplace data indicates whether products are offered and how buyers appear to engage with them. Search and trend data indicate discovery demand. Community content reveals recurring problems and language. None is a direct substitute for verified sales data.

## 5. Components, responsibilities, and boundaries

### 5.1 Research catalog

Owns the controlled research universe:

- buyer segments, professions, niches, problems, and product types;
- seed terms and query templates;
- combinations such as `niche x problem x tool type`;
- source coverage plans, locale, language, and scheduling;
- legal, medical, financial, and other exclusion policies.

It produces versioned research campaigns and queries. It does not collect source data or rank opportunities.

### 5.2 Source connectors and crawler

Each connector translates a campaign query into source requests and captures the response with collection metadata. Depending on the source, it may use an official API, permitted HTTP extraction, browser automation, or manual import.

Responsibilities:

- source-specific authentication, pagination, throttling, and retry policy;
- robots/terms-aware collection and source-specific concurrency limits;
- capture of title, URL, marketplace, price, reviews, rating, seller, category, tags, summary, images, product type, and approximate listing age when available;
- content fingerprinting and deduplication;
- emission of a raw-observation event.

The crawler returns observations; it does not infer a canonical niche, calculate scores, or embed editorial rules. Connector failures must be isolated by source and query.

### 5.3 Raw data store

Stores immutable source payloads or snapshots plus request/response metadata:

- source, canonical URL or external ID, query, collection time, locale, and status;
- content hash, payload location, media references, and parser version intended for processing;
- consent, license, retention, or collection-policy metadata where applicable.

Large HTML/JSON/media payloads belong in object storage; searchable metadata belongs in the relational database. Raw records are append-only. Corrections create new records rather than overwriting source history.

### 5.4 Normalization

Maps source-specific observations into a canonical listing model. It handles currency and unit conversion, text cleanup, seller/source identities, URLs, timestamps, availability, and typed attributes.

Normalization is deterministic where possible. Unknown values remain unknown; missing data must not silently become zero. The normalized record retains a pointer to every raw input and the normalizer version.

### 5.5 Enrichment

Adds derived attributes needed for matching and analysis:

- language detection and optional translated search text;
- taxonomy classification for niche, problem, buyer segment, and product type;
- keyword and feature extraction;
- price normalization to a reporting currency using a dated exchange rate;
- text/image embeddings;
- quality, relevance, and confidence signals;
- complaint, missing-feature, and purchase-intent cues from reviews or community content.

Rules and statistical/LLM outputs are stored separately from normalized facts. Model name, model/prompt version, input hash, output, confidence, cost, and execution time are retained. Low-confidence results enter a review queue.

### 5.6 Entity resolution and deduplication

Identifies repeated observations of the same listing and probable cross-marketplace duplicates. Exact source IDs and canonical URLs are preferred; fuzzy title, seller, image, and embedding matches provide candidates.

Matches above an automatic threshold are linked, ambiguous matches await review, and non-matches remain separate. Original records are never destroyed by deduplication.

### 5.7 Clustering engine

Groups comparable listings into candidate product markets, for example bakery pricing calculators or Airbnb ROI calculators. Clustering combines taxonomy constraints, keywords, embeddings, and deterministic business rules.

The engine owns cluster membership and cluster summaries, not opportunity scores. Each clustering run is an immutable snapshot containing algorithm/configuration versions, feature set, input window, membership confidence, and representative terms. Human merge, split, and exclusion decisions are recorded as auditable overrides.

### 5.8 Market analyzer

Aggregates listing, source, search, trend, community, and editorial signals for a cluster and a defined observation window. It creates versioned feature snapshots for six initial dimensions:

- **Demand:** listing activity, accumulated reviews, leader reviews, seller diversity, cross-marketplace presence, search/trend signals, content volume, and community questions.
- **Competition favorability:** competitor count and quality, review concentration, price distribution, visual/product depth, and signs of imperfect competition. A high score means favorable competition, not more competition.
- **Purchase intent:** financial impact, frequency, urgency, cost of error, and perceived value.
- **Build ease:** estimated formula/logic complexity, tabs or screens, external data/API needs, design burden, maintenance burden, and estimated hours.
- **Differentiation:** missing features, complaints, UX/visual quality gaps, automation, documentation, customization, and localization potential.
- **Price potential:** observed minimum/median/maximum, comparable depth, and plausible Basic/Pro/Bundle positioning.

The analyzer keeps raw measurements and their confidence alongside normalized 0-100 dimension scores. Review counts, trends, and other proxies are explicitly labeled as proxies.

### 5.9 Policy and eligibility engine

Applies eliminatory filters before ranking. Initial exclusions include high legal or regulated-advice risk, medical advice, misleading financial claims, unverifiable demand, dependence on inaccessible paid data, extreme competition, trivial products, and no credible differentiation path.

Rules return structured reason codes and supporting evidence. Exclusion does not delete an opportunity; it changes eligibility for a specific ranking run. Manual exceptions require an author, rationale, and timestamp.

### 5.10 Scoring and ranking engine

Calculates an explainable score from a feature snapshot. An initial formula is:

```text
Opportunity Score =
    0.30 * demand
  + 0.20 * purchase_intent
  + 0.15 * competition_favorability
  + 0.15 * differentiation
  + 0.10 * build_ease
  + 0.10 * price_potential
```

Weights are configuration, not source code constants. Every score stores the exact formula version, component values, weights, missing-data policy, confidence, input snapshot, and calculation time.

Ranking occurs after eligibility checks. Top 100 selection may apply explicit diversity constraints across segments; therefore final rank is not always a pure descending sort. The engine records whether a candidate moved because of a diversity rule.

A separate **Revenue Efficiency Score** may compare opportunity to build effort. It is a prioritization aid, not a revenue forecast, and should not be folded into the core score until validation supports it.

### 5.11 Research and editorial workflow

Automated analysis produces the Top 100 candidate set. The Top 25 receive deeper competitor, pricing, review, keyword, screenshot, and feature research. The Top 10 receive an opportunity thesis, product blueprint, formulas/features, positioning, proposed price tiers, build estimate, and supporting evidence.

Editorial annotations and approvals are separate domain records. Generated prose must cite evidence IDs and distinguish observed facts from estimates. Publication requires a reproducible ranking snapshot and an editorial approval state.

### 5.12 API and dashboard

The API exposes campaigns, jobs, listings, clusters, evidence, scores, rankings, reviews, and report artifacts. The initial dashboard is an internal research/admin interface for:

- monitoring collection and processing;
- inspecting provenance and failures;
- reviewing uncertain classifications and duplicate/cluster suggestions;
- comparing score components and formula versions;
- applying auditable overrides;
- approving a ranking/report snapshot.

Public SaaS functionality is outside the MVP. API contracts should be designed around resources and snapshots rather than internal database tables.

### 5.13 Reporting and export

Builds artifacts from an approved, frozen ranking snapshot:

- PDF report with executive summary, methodology, Top 10, ranks 11-100, category views, validation/pricing guidance, and appendix;
- XLSX/CSV with rank, product, niche, sources, component scores, prices, build effort, final score, confidence, keywords, and evidence references;
- charts for ranking, niche distribution, prices, difficulty, demand, and competition;
- optional machine-readable JSON export.

Report generation is deterministic for a given content snapshot and template version. Artifacts store hashes and links to all inputs used.

## 6. End-to-end data flow

1. A researcher creates a campaign from a versioned niche/problem/tool vocabulary.
2. The query generator expands seeds into source-specific search queries.
3. The scheduler creates rate-limited collection jobs.
4. Connectors fetch or import observations and append raw payloads.
5. Normalization maps new observations to canonical listings.
6. Entity resolution links duplicates without destroying source history.
7. Enrichment classifies listings, extracts features, and creates embeddings.
8. A clustering run groups listings into product-market candidates.
9. Signal collectors and the market analyzer compute a time-bounded feature snapshot per cluster.
10. The eligibility engine records exclusions and warnings.
11. The scoring engine calculates component and overall scores.
12. The ranking engine selects an ordered, diversity-aware Top 100.
13. Researchers deepen and approve the Top 25 and Top 10 analyses.
14. Reporting freezes the approved snapshot and creates PDF/spreadsheet/API artifacts.
15. When products are launched, outcome metrics are linked back to the prediction for calibration.

Each step consumes an immutable or versioned input and publishes a new output. Reprocessing creates a new version; it does not rewrite a published historical result.

## 7. Conceptual data model

| Entity | Purpose | Key relationships |
|---|---|---|
| `ResearchCampaign` | Scope, locale, sources, window, and goal of a research run | has queries and runs |
| `TaxonomyTerm` | Versioned segment, niche, problem, product type, or keyword | used by queries and classifications |
| `SearchQuery` | Generated or curated source query | belongs to campaign; has collection jobs |
| `CollectionJob` | One resumable source/query/page task | creates raw observations |
| `RawObservation` | Immutable source response and metadata | points to payload; produces normalized observations |
| `Listing` | Stable logical source listing identity | has observation versions and enrichments |
| `ListingObservation` | Canonical listing facts at a collection time | derived from raw observation |
| `Enrichment` | Versioned classifications, extracted features, or embeddings | belongs to listing/observation |
| `ProductMarket` | Stable editorial identity for a candidate market | has cluster snapshots and analyses |
| `ClusterRun` | Versioned clustering execution | contains cluster memberships |
| `ClusterMembership` | Listing-to-market assignment with confidence | links listing and product market |
| `Evidence` | Addressable fact/proxy with source, time, and confidence | supports features, scores, and claims |
| `FeatureSnapshot` | Time-bounded measurements for a product market | input to eligibility and scoring |
| `EligibilityDecision` | Pass/exclude/warn with rule reasons | applies to feature snapshot/ranking run |
| `Scorecard` | Component scores, weights, result, and confidence | belongs to formula and feature snapshot |
| `RankingRun` | Ordered eligible set plus diversity policy | contains ranked opportunities |
| `EditorialReview` | Human decision, rationale, and annotations | targets market, scorecard, or report item |
| `ReportSnapshot` | Frozen approved content and evidence graph | produces report artifacts |
| `ReportArtifact` | PDF, XLSX, CSV, or JSON output | belongs to report snapshot |
| `OutcomeObservation` | Views, CTR, favorites, sales, conversion, price, revenue | links a built product to a prior scorecard |
| `ModelVersion` | Parser, taxonomy, prompt/model, algorithm, or formula identity | referenced by all derived records |

Stable identities (`Listing`, `ProductMarket`) are distinct from time/version-specific observations and snapshots. This supports historical comparison and second editions without erasing past conclusions.

## 8. Jobs and domain events

The MVP can use a database-backed job queue or a small message broker. Delivery is at least once; consumers must be idempotent. A durable outbox written in the same transaction as domain state prevents lost event publication.

Representative jobs:

- `generate_queries(campaign_id)`
- `collect_source(query_id, cursor)`
- `normalize_observation(raw_observation_id)`
- `resolve_listing_identity(listing_observation_id)`
- `enrich_listing(listing_id, enrichment_profile)`
- `build_clusters(campaign_id, clustering_version)`
- `collect_external_signals(product_market_id)`
- `compute_features(product_market_id, window, feature_version)`
- `evaluate_eligibility(feature_snapshot_id, policy_version)`
- `score_opportunity(feature_snapshot_id, formula_version)`
- `build_ranking(campaign_id, ranking_policy_version)`
- `generate_report(report_snapshot_id, template_version)`
- `ingest_outcomes(product_id, period)`
- `evaluate_calibration(model_version, cohort)`

Representative events:

```text
campaign.created
query.generated
raw_observation.captured
listing.normalized
listing.enriched
cluster_run.completed
feature_snapshot.created
opportunity.excluded
opportunity.scored
ranking.completed
editorial_review.completed
report.published
outcome.observed
scoring_calibration.completed
```

Event envelopes include `event_id`, `event_type`, `schema_version`, `occurred_at`, `correlation_id`, `causation_id`, producer version, entity ID, and payload. Failed jobs use bounded retries with exponential backoff and a dead-letter/review queue. Backfills run under an explicit run ID and must not silently update published reports.

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
