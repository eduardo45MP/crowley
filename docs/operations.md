# Operações do Crowley

## Configuração

```dotenv
DATABASE_URL=sqlite:///./data/products.db
ETSY_API_KEY=optional
ETSY_API_SECRET=optional
```

O provider `mock` e o pipeline editorial não precisam de rede, credenciais ou LLM.

## Smoke test completo

```bash
python -m market_intelligence pipeline demo --output-dir data/reports
```

O comando persiste uma fixture offline com raw observations, produtos, clusters, análises, eligibility, selection, research, Top10, theses e blueprints; depois publica os quatro formatos.

## Execução com dados coletados

Siga a sequência do README. Anote o `Run ID` impresso por Selection e reutilize-o:

```bash
python -m market_intelligence deep-research run --selection-run 12 --top 25
python -m market_intelligence top10 select --selection-run 12 --top 10
python -m market_intelligence blueprint generate --selection-run 12 --top 10
python -m market_intelligence report build --selection-run 12 \
  --top 100 --top10 10 --output-dir data/reports \
  --formats json,csv,xlsx,pdf
```

## Inspeção

```bash
python -m market_intelligence report show --output-dir data/reports
python -m market_intelligence report show --report-id <report-id> --output-dir data/reports
```

Validação operacional:

```bash
python -m json.tool data/reports/<report-id>/report.json >/dev/null
python -c "from openpyxl import load_workbook; print(load_workbook('data/reports/<report-id>/crowley-opportunities.xlsx').sheetnames)"
pdfinfo data/reports/<report-id>/crowley-report.pdf
```

## Erros comuns

- `Nenhuma execução de Selection persistida`: execute `selection run`.
- Selection sem oportunidades: confira Eligibility e os mínimos da policy; não fabrique candidatos.
- Snapshot já existe: use outro diretório/edição; publicação é imutável.
- Erro de XLSX/PDF: reinstale dependências com `pip install -r requirements.txt`.

## Limites

Não há scheduler, workers, API, dashboard, SSO, billing, SaaS, marketplace publishing ou criação automática de produtos. O operador executa comandos locais e preserva banco e diretórios de reports como registros de auditoria.
