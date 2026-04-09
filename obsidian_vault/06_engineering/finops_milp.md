---
name: finops_milp
description: FinOps MILP — precio por plan como variable de decisión principal (Sonnet everywhere)
tipo: engineering
version: 2026-04-05
estado: reformulación activa — sesión dedicada requerida
tags: [finops, milp, optimizacion, precios, lilly, supply-demand]
---

# FinOps MILP — Entry Point

## Axioma de producto (2026-04-05)

> El MILP no optimiza calidad — optimiza precio.
> La calidad de Lilly no se degrada por ruta. El modelo es Sonnet en todas
> las rutas de interpretación doctrinal.

## Reformulación v2 — Precio como variable de decisión

La formulación original trataba la elección de modelo (Haiku/Sonnet) como
variable de decisión. Eso asume que los modelos son sustituibles en el
contexto doctrinal — no lo son.

**Nueva formulación:**
- **Supply:** presupuesto mensual Anthropic (tokens × costo/token, conocido)
- **Demand:** distribución de requests por ruta × plan (observable desde logs `selectModel.ts`)
- **Variables:** precios `{p_genesis, p_monthly, p_annual}`
- **Pregunta:** "¿Cuál es el precio mínimo por plan que hace Sonnet everywhere sostenible?"

Cuando la demanda se acerca a la oferta disponible, el precio es el mecanismo de
equilibrio — no la calidad. El MILP puede sugerir ajustar precios de nuevos planes
antes de degradar servicio a usuarios existentes.

Ver spec completa: `research/finops/MILP_INITIATIVE.md § Reformulación v2`

## Documentos técnicos

- `research/finops/MILP_INITIATIVE.md` — spec completa, formulación v1 y v2, resultados empíricos
- `research/finops/TOKEN_EXPERIMENT_DESIGN.md` — diseño experimental
- [[FINOPS_MILP_VARIABLES]] — variables técnicas (max_tokens, shadow prices)

## Estado fases

| Fase | COST_OPTIMIZATION (producto) | MILP_INITIATIVE (investigación) |
|------|------------------------------|----------------------------------|
| A | ✅ Caching mínimo | ✅ TOKEN_EXPERIMENT + recalibración empírica |
| B | ✅ selectModel gateway | ⏳ Formular MILP de precios con datos reales |
| C | ⏳ Caching avanzado | — |
| E | ⏳ Módulo dinámico producción | — |

**Nota sobre Fase B:** La política Haiku en `technique`/`city` es una heurística
provisional — pendiente de revisión bajo la formulación v2.

## Links

[[FINOPS_MILP_VARIABLES]] — variables técnicas identificadas
[[COST_OPTIMIZATION]] — implementación actual Fases A–F
