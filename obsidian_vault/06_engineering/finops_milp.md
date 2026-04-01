---
name: finops_milp
description: Entry point del módulo FinOps MILP — optimización de costos LLM por ruta y plan
tipo: engineering
version: 2026-04-01
estado: pendiente — sesión dedicada post-lanzamiento
tags: [finops, milp, optimizacion, costos, lilly, rutas]
---

# FinOps MILP — Entry Point

## Descripción

Módulo de optimización de costos LLM para Abu Oracle.
Formulación MILP con variables de modelo (Haiku/Sonnet) y max_tokens
por ruta, sujeta a restricciones de calidad mínima por tipo de evento
y margen por plan de suscripción.

## Documentos técnicos

- `research/finops/MILP_INITIATIVE.md` — spec de alto nivel, formulación, plan
- `research/finops/TOKEN_EXPERIMENT_DESIGN.md` — diseño experimental (~$2, 700 llamadas)
- [[FINOPS_MILP_VARIABLES]] — variables técnicas identificadas (este vault)

## Estado

Pendiente — sesión dedicada post-lanzamiento.
Fase A (medición) ejecutable en cualquier momento.

## Links

[[COST_OPTIMIZATION]] — implementación actual Fases A y B
