# Desenvolvimento do Crowley

## Estrutura de módulos

O código segue uma arquitetura de monólito modular em `src/`.

### `src/crawler`

Responsável por coleta e normalização.

### `src/market_intelligence`

Responsável por inferência de mercado e ranking.

## Convenções do projeto

- lógica determinística e auditável
- uso explícito de `model_version`
- persistência por execução por análise
- separação por camada funcional
- dados brutos imutáveis

## Como adicionar uma nova dimensão

1. criar submódulo em `src/market_intelligence/<dimension>/`
2. definir `config.py`, `models.py`, `features.py` e `service.py` conforme o padrão
3. persistir `*_analysis_runs` e `cluster_*_scores`
4. incluir a nova dimensão nos resultados de `opportunity`
5. atualizar a documentação e os testes

## Como adicionar um novo provider

1. implementar `MarketplaceProvider` em `src/crawler/providers/`
2. registrar o normalizer correspondente
3. adicionar o provider à CLI `crawler`
4. validar payload e normalização sem mudar o domínio canônico

## Testes

Os testes atuais estão em `tests/` e validam:

- integração de crawler
- persistência em JSON
- normalização
- deep research determinístico

## Regras de manutenção

- não inventar endpoints, tabelas ou workflows que não existam
- manter a rastreabilidade por `cluster_id` e `model_version`
- não conflitar `Opportunity Score` com `Eligibility` ou `Selection`
- documentar a diferença entre implementado e planejado
