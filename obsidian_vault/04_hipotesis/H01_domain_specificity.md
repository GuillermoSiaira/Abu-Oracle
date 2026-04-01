# H01 — Domain Specificity Hypothesis

## Enunciado
```
corr(HF_domain_k, eventos_casa_k) > corr(HF_global, eventos_casa_k)
para todo k con n_eventos >= 10.
```

## Fundamento doctrinal
**Axioma 8 — Especificidad de Dominio** (Axiomatics of Heavens v0.4):

> "El HF global mezcla señales de distintas casas. La correlación significativa
> emerge cuando el campo se calcula exclusivamente con los significadores
> de la casa correspondiente al tipo de evento."

Abu Mashar: "cuando los señores de los tiempos coinciden con los señores
del evento, el efecto es extremo e inconfundible."

## Estado

**PARCIALMENTE CONFIRMADA en H05 · REFUTADA EN H10 POR CORPUS** — [[EXP_004_HF_v6_domain]]

| Casa | Resultado | Evidencia |
|------|-----------|-----------|
| H05 Creatividad | ✅ CONFIRMADA | Δr = +0.150 (0.200 → 0.350) |
| H07 Relaciones | ⬜ NEUTRO | Señal marginal en ambos modos |
| H09 Expansión | ⬜ DÉBIL | Señal negativa en ambos modos |
| H10 Carrera | ❌ NO TESTEABLE | N−=5, IC bootstrap = [−0.96, +0.95] — corpus insuficiente |
| H01/H02/H03/H04 | ⬜ N/A | N insuficiente |

**Distinción crítica para H10:**
El rechazo de H01 en H10 es un rechazo por corpus, no por modelo.
El diagnóstico bootstrap confirmó que d=0.551 es estadísticamente indistinguible
de ruido con N−=5. La hipótesis no puede evaluarse sin eventos negativos balanceados.

## Sub-hipótesis generada por diagnósticos (2026-04-01)
[[H01b_significator_speed]]: La eficacia del filtro depende de la velocidad orbital
de los significadores. H05 (velocidad media 2.67 deg/día) confirma la hipótesis.
H10 (velocidad media 0.96 deg/día) no puede evaluarse aún.
La varianza geográfica HF_domain es similar entre H05 y H10 (0.323 vs 0.362),
por lo que la hipótesis de velocidad queda como pendiente de validación.

## Limitación estructural conocida
- Corpus: 21/26 sujetos en H10 sin ningún evento negativo de carrera
- Wikidata scraper (2026-04-01): 54 candidatos totales, 2 legales confirmados,
  52 nominaciones que requieren revisión manual
- La adición de eventos negativos balanceados cambiaría el resultado de H10

## Próximo paso
1. Curar manualmente los 52 candidatos de nominaciones Wikidata
2. Con N−≥20 en H10, re-ejecutar bootstrap — d_domain será evaluable
3. Si d_domain_H10 sigue siendo bajo con corpus balanceado → hipótesis refutada
4. Si d_domain_H10 mejora → hipótesis confirmada, colapso anterior fue artefacto

## Links
[[EXP_003_HF_v3_global]] — baseline global
[[EXP_004_HF_v6_domain]] — experimento de validación con diagnósticos
[[H01b_significator_speed]] — sub-hipótesis de velocidad orbital
