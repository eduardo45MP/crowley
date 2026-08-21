# Crowley

Crowley é um pipeline local de inteligência de mercado. Esta V1 pesquisa produtos
em um marketplace, normaliza os resultados e preserva uma saída JSON estruturada.
A arquitetura mais ampla do projeto está em [`docs/architecture.md`](docs/architecture.md).

## Setup

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

O runtime usa SQLAlchemy 2 para persistência relacional. O arquivo de requirements
instala o pacote em modo editável e o pytest para desenvolvimento.

## Execução

O provider mock permite validar todo o pipeline sem rede nem credenciais:

```bash
python -m crawler search "bakery pricing calculator" --provider mock
```

Opções disponíveis:

```bash
python -m crawler search "3d printing cost calculator" \
  --provider mock \
  --limit 100 \
  --output data/raw
```

`--output` aceita um diretório base (a hierarquia é criada automaticamente) ou
o caminho exato de um arquivo terminado em `.json`. O provider padrão é `mock`,
para que uma instalação nova tenha comportamento funcional e determinístico.

Por padrão, cada execução preserva observações raw e faz upsert dos produtos
canônicos no banco configurado por:

```dotenv
DATABASE_URL=sqlite:///./data/products.db
```

Para executar somente coleta/normalização e exportar o JSON, sem banco:

```bash
python -m crawler search "bakery pricing calculator" --provider mock --no-db
```

Para inspecionar os 20 produtos canônicos atualizados mais recentemente:

```bash
python -m crawler products
```

## Testes

```bash
pytest
```

Os testes não acessam marketplaces reais.

## Providers disponíveis

### `mock` — operacional

Retorna payloads raw locais representativos, incluindo preços em USD/EUR e reviews
com sufixo `k`. Eles passam pelo mesmo registry e pipeline de normalização real.

### `etsy` — implementado, requer credenciais aprovadas

O adapter usa exclusivamente a Etsy Open API v3 oficial:

```text
GET https://api.etsy.com/v3/application/listings/active
```

Ele envia `keywords`, pagina com `limit`/`offset` e ordena por relevância. Cada
requisição V3 exige o header `x-api-key` no formato `keystring:shared_secret`.
Configure as duas partes no `.env`:

```dotenv
ETSY_API_KEY=your_keystring
ETSY_API_SECRET=your_shared_secret
```

Depois execute:

```bash
python -m crawler search "bakery pricing calculator" --provider etsy
```

É necessário registrar uma Seller App ou Personal App no portal de developers da
Etsy e aguardar a aprovação da chave. O endpoint público de busca exige a chave,
mas não exige OAuth; endpoints privados ou de escrita exigem também OAuth 2.0 e
os scopes correspondentes. Commercial Access é necessário para operar uma
aplicação para outros vendedores em escala mais ampla, sujeito à aprovação da
Etsy. A aplicação deve cumprir os termos, limites e política de cache aplicáveis.

Esta V1 não faz scraping, não tenta contornar CAPTCHA, autenticação ou rate limits.
O endpoint de busca de listings não fornece contagem agregada de reviews/rating;
o normalizer preserva esses campos como `null` quando ausentes. Seller e categoria
seguem a mesma regra.

Referências oficiais:

- [Etsy Open API v3](https://developers.etsy.com/)
- [Referência de endpoints](https://developers.etsy.com/documentation/reference)
- [Autenticação](https://developers.etsy.com/documentation/essentials/authentication/)
- [Rate limits](https://developers.etsy.com/documentation/essentials/rate-limits/)

## Configuração de resiliência

Os valores ficam centralizados em `CrawlerConfig` e podem ser sobrescritos no
`.env`:

```dotenv
CRAWLER_REQUESTS_PER_SECOND=2
CRAWLER_DELAY_BETWEEN_REQUESTS=0.5
CRAWLER_MAX_RETRIES=3
CRAWLER_TIMEOUT=15
```

O adapter Etsy limita a cadência, usa timeout, respeita `Retry-After` quando
recebe HTTP 429 e aplica backoff exponencial moderado a erros transitórios.

## Estrutura

```text
src/crawler/
  models.py                         # raw e modelos canônicos
  normalization.py                  # parsers reutilizáveis
  providers/                        # coleta e payload raw
  normalizers/                      # adapter de normalização por marketplace
  repositories/                     # contrato e adapter SQLAlchemy
  services/ingestion_service.py     # collect -> raw -> normalize -> upsert
  storage/                          # exportação JSON canônica
  cli.py
```

O fluxo é:

```text
MarketplaceProvider -> RawMarketplaceProduct -> ProductNormalizer
                    -> Product -> ProductRepository
```

Providers não criam `Product`, normalizers não fazem SQL e a CLI apenas coordena
os componentes. Novos providers implementam `MarketplaceProvider.search` e
registram um normalizer próprio. Destinos relacionais implementam
`ProductRepository`, sem alterar o domínio.

### Identidade e histórico

Cada coleta sempre insere uma linha em `raw_marketplace_products`. O registro em
`products` é identificado primeiro por `marketplace + external_id` e, sem ID,
por `marketplace + canonical_url`. Uma nova observação atualiza preço, reviews e
demais campos do produto canônico, mas nunca remove o payload raw anterior.

`raw_product_id` aponta do estado canônico atual para a observação que o produziu.
Isso permite reprocessar todos os payloads com uma versão futura do normalizer sem
consultar novamente o marketplace.

### Schema e migrações

Na V1, o repository executa `SQLAlchemy.metadata.create_all()` como bootstrap
simples. Alembic não foi incluído porque ainda há apenas o schema inicial. Antes
de alterar um banco com dados persistentes, deve-se adicionar migrações Alembic.

O domínio e o serviço não dependem de SQLite. Uma URL PostgreSQL pode ser usada
sem reescrevê-los, após instalar o driver PostgreSQL adequado e criar uma migração
de produção. Os campos multivalorados e payloads usam o tipo SQLAlchemy `JSON`,
compatível conceitualmente com JSON/JSONB conforme o dialeto.

### Mudança interna da V1

`MarketplaceProvider.search()` agora retorna `list[RawMarketplaceProduct]`, não
`list[Product]`. A CLI existente permanece igual. Para consumidores Python que
querem somente o resultado normalizado, `SearchService.search()` continua sendo
a fachada compatível e retorna `SearchResult`.
