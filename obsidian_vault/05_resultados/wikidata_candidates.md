---
name: wikidata_candidates
description: Candidatos a eventos negativos H10 obtenidos del scraper Wikidata — pendientes de curación manual
tipo: corpus
fecha: 2026-04-01
estado: pendiente-curación
tags: [corpus, wikidata, H10, eventos-negativos, curación]
---

# Wikidata — Candidatos Eventos Negativos H10

## Resumen del scraper (ejecución 2026-04-01)

| Parámetro | Valor |
|---|---|
| Sujetos procesados | 26 |
| Candidatos encontrados | 54 |
| Con fecha precisa | 54 |
| Listos (condenas legales confirmadas) | 2 |
| Necesitan revisión manual | 52 |

## Por sujeto

| Sujeto | Encontrados | Con fecha | Necesitan revisión |
|---|---|---|---|
| Carl Gustav Jung | 17 | 17 | 17 |
| Sigmund Freud | 13 | 13 | 13 |
| Albert Einstein | 11 | 11 | 11 |
| Mohandas Gandhi | 5 | 5 | 5 |
| James Dean | 4 | 4 | 4 |
| Muhammad Ali | 2 | 0 | 0 |
| Oscar Wilde | 1 | 1 | 0 (legal confirmado) |
| Bruce Lee | 1 | 1 | 1 |
| Nikola Tesla | 1 | 1 | 1 |
| Alan Turing | 1 | 1 | 0 (legal confirmado) |
| 16 sujetos restantes | 0 | 0 | 0 |

**Sujetos con 0 candidatos** (requieren fuente alternativa):
Jim Morrison, Edith Piaf, Jorge Luis Borges, Ingrid Bergman, Marilyn Monroe,
Neil Armstrong, Elvis Presley, David Bowie, Janis Joplin, Vincent van Gogh,
Audrey Hepburn, Miles Davis, Frida Kahlo, Pablo Picasso, Coco Chanel, Jimi Hendrix.

## Criterio de inclusión

**Fuentes Wikidata consultadas:**
- `P793` (significant event) — con keyword negativo en el label (cancel, fail, reject, banned, etc.)
- `P1411` (nomination for award) — nominaciones sin premio correspondiente → evento de pérdida
- `P1399` (convicted of) — condenas legales → confirmadas directamente

**Exclusiones aplicadas:** eventos con keywords de salud/muerte (death, illness, overdose, etc.)

**Precisión de fecha mínima:** año

## Gap de corpus H10

| Métrica | Valor |
|---|---|
| Eventos negativos H10 actuales | 5 |
| Candidatos Wikidata listos | 2 |
| Candidatos que necesitan curación | 52 |
| N− mínimo para EXP_005 | 20 |
| Gap restante (pesimista: 0% curación) | 13 |
| Gap restante (optimista: 25% curación) | 0 ✅ |

## Procedimiento de curación manual

1. Abrir `abu-oracle-research/data/corpus/wikidata_candidates.csv`
2. Para cada fila con `needs_manual_review=True`:
   - Verificar que la fecha corresponde a un evento negativo de carrera real
   - Verificar que el sujeto estaba activo en esa fecha (no post-mortem)
   - Para nominaciones: confirmar que NO ganó ese premio (eliminar si ganó)
3. Marcar `manual_verified=True` y `include=True/False` en el CSV
4. Con N−≥20 verificados: ejecutar EXP_005

## Grant proposal

El gap de corpus es el argumento central para el funding request.

**Argumento**: el sistema tiene efecto estadístico demostrable en H05 (Δr=+0.150),
pero no puede validarse en H10 por falta de eventos negativos documentados.
La curación de 52 candidatos Wikidata + búsqueda manual en 16 sujetos sin datos
es el trabajo que desbloquea la validación completa.

Ver [[grant_proposal_ResearchHub]] *(pendiente de crear)*

## Archivos

- CSV: `abu-oracle-research/data/corpus/wikidata_candidates.csv`
- Resumen JSON: `abu-oracle-research/data/corpus/wikidata_scrape_summary.json`
- Script: `abu-oracle-research/scripts/wikidata_negative_events.py`

## Links

[[EXP_004_HF_v6_domain]]
[[H01_domain_specificity]]
[[REVISION_2026_04_01]]
