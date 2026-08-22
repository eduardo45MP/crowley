# Scoring do Crowley

## Objetivo

O Crowley define scores independentes por dimensão e depois consolida um score final para oportunidade. O objetivo é separar observação de decisão.

## Dimensões implementadas

- demand
- competition
- purchase_intent
- build_ease
- differentiation
- price_potential (presente como parte do contrato de opportunity, mas ainda não como camada completa)

## Regra de opportunity score

A lógica atual é determinística e usa pesos fixos em `OpportunityScoreConfig`.

```text
Opportunity Score =
  0.30 * demand
+ 0.20 * purchase_intent
+ 0.15 * competition
+ 0.15 * differentiation
+ 0.10 * build_ease
+ 0.10 * price_potential
```

### Observações

- a dimensão de `price_potential` faz parte do contrato de input, mas a camada separada não está pronta como módulo completo
- o `OpportunityScorer` só agrega resultados finais já produzidos por outras camadas
- o score não descobre novas evidências; ele apenas combina as evidências disponíveis

## Qualificação do score

O resultado pode receber status como:

- `complete`
- `provisional`
- `insufficient_data`

E qualificação:

- `exceptional`
- `strong`
- `interesting`
- `speculative`
- `weak`

## Critérios de elegibilidade

A elegibilidade usa a combinação de:

- `opportunity_score`
- `opportunity_confidence`
- `evidence_coverage`
- regras de risco
- baixa qualidade de demanda ou diferenciação

Se a oportunidade falha em critérios críticos, ela é marcada como `ineligible` ou `review_required`.

## Seleção final

A seleção não usa apenas score descendente. Ela aplica quotas e diversificação por buyer group, nicho e problema.

## Deep research

O deep research não altera o score principal. Ele apenas acrescenta observação e contexto para as oportunidades já elegíveis e selecionadas.
