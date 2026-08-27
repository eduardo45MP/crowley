# Desenvolvimento do Crowley

## Setup e testes

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Dependências de runtime: SQLAlchemy, openpyxl e ReportLab. Pytest é dependência de desenvolvimento declarada em `requirements.txt`.

## Organização

- `src/crawler`: providers, normalização, clustering e repository;
- `src/market_intelligence/<dimension>`: dimensões independentes;
- `opportunity`, `eligibility`, `selection`: score e decisões separadas;
- `deep_research`, `top10`, `product_blueprint`: due diligence e produto;
- `editorial`: projeção de publicação e métricas editoriais;
- `reporting`: JSON/CSV/XLSX/PDF;
- `demo.py`: fixture offline end-to-end.

## Regras para mudanças

- não recalcular dimensão upstream dentro de editorial/reporting;
- não modificar raw observations;
- persistir run, model version e origem;
- manter `None` quando a evidência não existe;
- não introduzir LLM obrigatório;
- preservar `selection_rank` e `top10_rank`;
- criar novo snapshot em vez de sobrescrever um existente.

## Testes editoriais

Cobrem pricing, positioning, Revenue Efficiency, keywords, mapping, ranking, serialização determinística e integração com banco temporário até os quatro arquivos. Ao alterar XLSX ou PDF, também faça inspeção estrutural e renderização visual.

## Qualidade antes de merge

```bash
python -m compileall -q src tests
pytest
python -m market_intelligence pipeline demo --output-dir /tmp/crowley-reports
```

Abra o XLSX com `openpyxl`, valide o JSON/CSV, use `pdfinfo` e renderize o PDF com `pdftoppm` para detectar clipping.
