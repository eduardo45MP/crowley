# Operações e execução do Crowley

## Requisitos

- Python 3.11+
- venv local
- SQLite por padrão
- pacote do projeto instalado em modo editável

## Setup inicial

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Variáveis de ambiente

O repositório suporta configuração básica de crawler e banco:

```dotenv
DATABASE_URL=sqlite:///./data/products.db
ETSY_API_KEY=your_keystring
ETSY_API_SECRET=your_shared_secret
```

## Fluxo operacional típico

### 1. Coletar dados

```bash
python -m crawler search "bakery pricing calculator" --provider mock
```

### 2. Agrupar em clusters

```bash
python -m crawler cluster --limit 500
```

### 3. Calcular dimensões

```bash
python -m market_intelligence demand calculate --limit 50
python -m market_intelligence competition calculate --limit 50
python -m market_intelligence purchase-intent calculate --limit 50
python -m market_intelligence build-ease calculate --limit 50
python -m market_intelligence differentiation calculate --limit 50
```

### 4. Consolidar opportunity score

```bash
python -m market_intelligence opportunity calculate --limit 50
```

### 5. Avaliar elegibilidade

```bash
python -m market_intelligence eligibility evaluate --limit 50
```

### 6. Selecionar portfólio

```bash
python -m market_intelligence selection run --limit 200
```

### 7. Deep research

```bash
python -m market_intelligence deep-research run --limit 25 --top 25
```

## Observações de execução

- Usa `SQLAlchemy.metadata.create_all()` para bootstrap inicial.
- Não há workers independentes em execução no código atual.
- Os resultados são persistidos no banco e podem ser consultados/reatualizados em várias execuções.
- A execução é local e determinística, sem dependência de serviço externo para os valores principais.

## Boas práticas

- sempre preservar a sequência de etapas
- nunca reescrever resultados brutos
- usar o `cluster_id` para rastrear a origem de cada score
- tratar `eligibility`, `selection` e `deep_research` como etapas diferenciadas

## Limites operacionais conhecidos

- sem fila de background
- sem API de consulta em tempo real
- sem exportação de PDF/XLSX
- sem migração de schema automatizada

Esses limites são explícitos e não devem ser tratados como implementados no código atual.
