# Crowley

Crowley é um pipeline determinístico de market intelligence local para identificar oportunidades de produtos digitais em nichos específicos. O código atual implementa coleta, normalização, clustering, análise de demanda, competição, compra, build ease, diferenciação, oportunidade, elegibilidade, seleção e deep research.

A documentação de arquitetura e a disciplina do projeto estão em [docs/architecture.md](docs/architecture.md) e [docs/pipeline.md](docs/pipeline.md).

## Status da implementação

A implementação atual cobre esta sequência:

```text
Crawler
  -> normalização
  -> clustering
  -> market intelligence
      -> demand
      -> competition
      -> purchase_intent
      -> build_ease
      -> differentiation
      -> opportunity score
      -> eligibility
      -> selection
      -> deep_research
```

O repositório ainda não inclui uma API HTTP, dashboard, jobs assíncronos, exportação de relatórios em PDF/XLSX, ou migrações Alembic. Esses itens continuam como arquitetura futura ou planejamento explícito, não como serviços implementados.

## Setup

Requer Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

A configuração principal usa SQLAlchemy 2 e um banco SQLite padrão:

```dotenv
DATABASE_URL=sqlite:///./data/products.db
```

## Como rodar o pipeline

### 1) Coleta + normalização

```bash
python -m crawler search "bakery pricing calculator" --provider mock
```

Opções úteis:

```bash
python -m crawler search "bakery pricing calculator" \
  --provider mock \
  --limit 100 \
  --output data/raw
```

`--output` aceita um diretório base ou um arquivo JSON final. O provider padrão é `mock`, o que mantém a execução funcional e determinística sem rede nem credenciais externas.

### 2) Clustering

```bash
python -m crawler cluster --limit 500
python -m crawler clusters --limit 20
python -m crawler cluster-show 1
```

### 3) Market intelligence por dimensão

Cada camada calcula uma dimensão independente e persiste resultados por cluster.

```bash
a) demand
python -m market_intelligence demand calculate --limit 50

b) competition
python -m market_intelligence competition calculate --limit 50

c) purchase-intent
python -m market_intelligence purchase-intent calculate --limit 50

d) build-ease
python -m market_intelligence build-ease calculate --limit 50

e) differentiation
python -m market_intelligence differentiation calculate --limit 50
```

### 4) Opportunity score

O Opportunity Score não inventa novas evidências. Ele combina os resultados das camadas independentes já calculadas.

```bash
python -m market_intelligence opportunity calculate --limit 50
```

### 5) Eligibility Filters

A camada de elegibilidade responde: “esta oportunidade é aceitável para seguir para ranking e possível produção?”

```bash
python -m market_intelligence eligibility evaluate --limit 50
```

### 6) Selection

A seleção não é um simples `ORDER BY score DESC LIMIT 100`; ela aplica quotas, diversificação e regra de portfólio.

```bash
python -m market_intelligence selection run --limit 200
```

### 7) Deep Research / Due Diligence

A camada de deep research é separada e determinística, com foco em evidência e auditoria, sem uso de LLM na V1.

```bash
python -m market_intelligence deep-research run --limit 25 --top 25
```

## Estrutura do código

```text
src/
  crawler/
    cli.py
    config.py
    models.py
    clustering.py
    normalization.py
    normalizers/
    providers/
    repositories/
    services/
    storage/

  market_intelligence/
    __main__.py
    cli.py
    demand/
    competition/
    purchase_intent/
    build_ease/
    differentiation/
    opportunity/
    eligibility/
    selection/
    deep_research/
    taxonomy/
```

Os módulos principais refletem o que existe hoje:

- `crawler`: coleta, normalização, deduplicação, clustering e persistência.
- `market_intelligence/demand`: sinais de demanda e volume de procura.
- `market_intelligence/competition`: estrutura competitiva e ambiente de mercado.
- `market_intelligence/purchase_intent`: intenção de compra e valor percebido.
- `market_intelligence/build_ease`: complexidade e esforço de produção.
- `market_intelligence/differentiation`: diferenciação, lacunas, e proposições.
- `market_intelligence/opportunity`: agregação final em 0-100.
- `market_intelligence/eligibility`: filtros de aceitabilidade para ranking.
- `market_intelligence/selection`: seleção final do portfólio.
- `market_intelligence/deep_research`: due diligence explicita e auditável.

## Providers e normalização

### `mock`

Operacional e determinístico; usa payloads locais representativos.

### `etsy`

Implementado como adapter oficial da Etsy Open API v3; requer credenciais aprovadas e usa `ETSY_API_KEY` e `ETSY_API_SECRET`.

O projeto trata source adapters como fronteiras de coleta. Os providers não inferem decisões de oportunidade; eles apenas capturam raw payloads e deixam a normalização transformar em domínio canônico.

## Persistência e schema

O repositório de persistência em [src/crawler/repositories/sqlalchemy_repository.py](src/crawler/repositories/sqlalchemy_repository.py) cria as tabelas com `SQLAlchemy.metadata.create_all()`. A estrutura atual inclui:

- `raw_marketplace_products`
- `products`
- `cluster_runs`
- `product_clusters`
- `product_cluster_memberships`
- `demand_analysis_runs`
- `cluster_demand_scores`
- `competition_analysis_runs`
- `cluster_competition_scores`
- `purchase_intent_analysis_runs`
- `cluster_purchase_intent_scores`
- `build_ease_analysis_runs`
- `cluster_build_ease_scores`
- `differentiation_analysis_runs`
- `cluster_differentiation_scores`
- `eligibility_evaluation_runs`
- `cluster_eligibility_results`
- `opportunity_analysis_runs`
- `cluster_opportunity_scores`
- `selection_runs`
- `selected_opportunities`
- `deep_research_runs`
- `deep_research_dossiers`

A persistência é SQLite-first, mas o modelo SQLAlchemy é compatível com outros dialetos com ajustes discretos de driver e migração.

## O que não existe nesta V1

Como parte do código atual, não há:

- API HTTP com FastAPI/Flask
- dashboard interno
- workers/jobs assíncronos independentes
- outbox/event bus de produção
- Alembic ou migrations
- exportações PDF/XLSX automatizadas
- SSO ou autenticação do usuário
- LLM no deep research

Esses itens podem ser parte de uma arquitetura futura, mas não devem ser documentados como presentes no código atual.

## Testes

```bash
pytest
```

Os testes existentes validam a coleta e a determinismo de deep research, sem depender de marketplace real.

## Arquivos de documentação

- [docs/architecture.md](docs/architecture.md): visão arquitetural e separação de responsabilidades.
- [docs/pipeline.md](docs/pipeline.md): fluxo do pipeline e ordem de execução.
- [docs/data-model.md](docs/data-model.md): entidades de domínio e classes persistidas.

## Observação de projeto

A arquitetura do Crowley prioriza evidência, rastreabilidade e separação clara de camadas. A regra central do código é simples: cada camada produz resultados independentes e o próximo estágio apenas consome esses resultados, em vez de reinventar ou ocultar evidências.
