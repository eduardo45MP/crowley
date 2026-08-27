# Arquitetura do Crowley

## Forma do sistema

Crowley é um monólito modular local. A CLI compõe serviços de domínio e um repository SQLAlchemy SQLite-first; não há serviços distribuídos, API HTTP ou workers.

```text
crawler
  -> raw observations
  -> canonical products
  -> product clusters
market_intelligence
  -> demand / competition / purchase_intent / build_ease / differentiation
  -> opportunity
  -> eligibility
  -> selection
  -> deep_research
  -> top10
  -> opportunity thesis
  -> product blueprint
editorial
  -> ReportSnapshot + PublishedOpportunity
reporting
  -> JSON -> CSV/XLSX/PDF
```

## Dependency direction

Collection adapters só capturam raw payloads. Normalizers convertem fontes para `Product`. Clustering cria mercados. Dimensões analíticas leem clusters e adicionam scores independentes. Opportunity agrega esses scores; Eligibility aceita ou rejeita; Selection monta o portfólio diversity-aware; Deep Research adiciona due diligence; Top10, Thesis e Blueprint refinam somente os selecionados.

`market_intelligence.editorial` consome artefatos persistidos. Ele não importa feature extractors nem scorers e não recalcula dimensões. `market_intelligence.reporting` serializa exclusivamente o modelo editorial canônico.

## Invariantes

1. Raw observations são append-only.
2. Um estágio não sobrescreve semanticamente seu predecessor.
3. Opportunity Score nunca incorpora resultado posterior de Deep Research.
4. Eligibility e Selection são decisões separadas do score.
5. Selection preserva quotas e diversidade; o relatório preserva `selection_rank`.
6. Top10 preserva seu próprio `top10_rank`.
7. Valores ausentes não recebem defaults comerciais silenciosos.
8. Cada artefato registra model versions e IDs rastreáveis.
9. Uma nova publicação cria um novo diretório; snapshots existentes não são sobrescritos.

## Camadas editoriais

`PublishedOpportunity` reúne identidade do cluster, scores já existentes, ranks, research, pricing, keywords, positioning e esforço. `ReportSnapshot` fixa application version, schema assumido, run IDs, model versions, contagens e metadados das observações.

Pricing observado e preço recomendado são campos diferentes. Revenue Efficiency é calculado somente quando Opportunity Score e horas do Blueprint existem. O Blueprint continua sendo a única implementação da estimativa de esforço.

## Exportadores

`report.json` é a representação canônica. CSV, XLSX e PDF usam o mesmo `PublishedReport`. XLSX usa `openpyxl`, sem macros; PDF usa ReportLab com paginação estável.

## Persistência

`SqlAlchemyProductRepository` cria o schema com `Base.metadata.create_all()`. O projeto ainda não possui migrations Alembic; bancos existentes que antecedam novas tabelas devem ser recriados ou migrados manualmente antes de uso em produção.

## Não implementado

- API REST/GraphQL;
- dashboard ou frontend;
- jobs/background workers;
- microservices, Kubernetes ou event bus;
- SSO/auth, billing ou multi-tenancy;
- publicação automática em marketplaces;
- criação automática do produto final;
- pesquisa obrigatoriamente dependente de LLM.
