# Crowley

Crowley é um pipeline local, determinístico e auditável para descobrir e publicar oportunidades de produtos digitais. O MVP é um monólito modular: coleta evidência, normaliza, agrupa mercados, calcula dimensões independentes, aplica decisão de portfólio, aprofunda o Top 10 e publica um snapshot editorial em JSON, CSV, XLSX e PDF.

```text
Crawler -> Normalization -> Clustering -> Market Intelligence
-> Opportunity -> Eligibility -> Selection -> Deep Research
-> Top10 -> Opportunity Thesis -> Product Blueprint
-> Editorial Snapshot -> Reporting
```

Princípios centrais:

- evidência antes de geração;
- raw observations são imutáveis;
- cada estágio adiciona um artefato versionado;
- Opportunity Score, Eligibility, Selection e Deep Research são decisões separadas;
- Deep Research nunca altera retroativamente o Opportunity Score;
- dados ausentes permanecem ausentes;
- LLM não é dependência do pipeline.

## Setup

Requer Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

O banco padrão é SQLite:

```dotenv
DATABASE_URL=sqlite:///./data/products.db
```

## Demonstração offline completa

Este comando usa observações mock determinísticas, não usa rede e percorre todas as camadas até o relatório:

```bash
python -m market_intelligence pipeline demo --output-dir data/reports
```

Ele produz um diretório imutável `data/reports/<report-id>/` com:

```text
report.json
opportunities.csv
crowley-opportunities.xlsx
crowley-report.pdf
```

Escolha outro `--output-dir` para repetir a mesma fixture; snapshots existentes não são sobrescritos.

## Pipeline operacional

```bash
python -m crawler search "bakery pricing calculator" --provider mock
python -m crawler cluster --limit 500
python -m market_intelligence demand calculate --limit 50
python -m market_intelligence competition calculate --limit 50
python -m market_intelligence purchase-intent calculate --limit 50
python -m market_intelligence build-ease calculate --limit 50
python -m market_intelligence differentiation calculate --limit 50
python -m market_intelligence opportunity calculate --limit 50
python -m market_intelligence eligibility evaluate --limit 50
python -m market_intelligence selection run --limit 200
python -m market_intelligence deep-research run --selection-run <id> --top 25
python -m market_intelligence top10 select --selection-run <id> --top 10
python -m market_intelligence blueprint generate --selection-run <id> --top 10
python -m market_intelligence report build --selection-run <id> --top 100 --top10 10 \
  --output-dir data/reports --formats json,csv,xlsx,pdf
python -m market_intelligence report show --output-dir data/reports
```

Os comandos imprimem IDs, contagens e paths. `report build` exige uma execução de Selection persistida e informa de forma acionável quando o dado necessário não existe.

## Produto editorial

O ranking publicado vem da ordem diversity-aware de Selection e preserva `selection_rank`; não é recalculado com um sort por Opportunity Score. Se houver menos de 100 oportunidades selecionadas, o snapshot publica somente as disponíveis e registra o shortfall.

O Top 10 preserva `top10_rank` e incorpora, quando persistidos, Deep Research, Opportunity Thesis e Product Blueprint. Campos sem suporte permanecem `null`, vazios ou acompanhados de warning.

Pricing editorial preserva mínimo, mediana e máximo observados. A recomendação é uma heurística determinística: `110% da mediana`, limitada ao intervalo observado. Não representa willingness-to-pay.

Revenue Efficiency v1 usa:

```text
100 * opportunity_score / (opportunity_score + 2 * max(build_hours, 1))
```

É uma métrica comparativa 0-100, não previsão de receita.

## Persistência e rastreabilidade

O repository SQLAlchemy persiste runs e artefatos de todas as camadas, incluindo Selection, Deep Research, Top10, Thesis e Blueprint. O `ReportSnapshot` fixa versões, run IDs, contagens, schema assumido e janela de observação.

```text
report -> editorial opportunity -> selection/top10 -> opportunity score
-> component scores -> cluster -> normalized products -> raw observations
```

Consulte [docs/data-model.md](docs/data-model.md) e [docs/provenance.md](docs/provenance.md).

## Testes

```bash
pytest
```

A integração cobre banco temporário, análises persistidas, Selection, Deep Research, Top10, Thesis, Blueprint, snapshot e os quatro exportadores.

## Fora do escopo

O MVP não implementa API HTTP, dashboard, background workers, Kubernetes, SSO/auth, billing, SaaS público, automação de publicação em marketplaces, criação automática do produto vendido ou pesquisa dependente de LLM.
