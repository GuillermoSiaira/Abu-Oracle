---
name: NOTE_SESSION_B
description: Nota de referencia — sesión de implementación HF v4 y correlador de eventos
tipo: experimentos
version: 2026-03-13
estado: completo
tags: [sesion-b, hf-v4, correlador, referencia]
---

# Nota — Session B

Esta nota es un puntero a la especificación técnica completa de la Sesión B.

Ver: [[HF_V4_SESSION_B]]

---

## Qué se hizo en Session B

1. Implementación de pesos diferenciados por grupo de aspecto (harmony/tension/conjunction)
2. Construcción del correlador de eventos biográficos (`scripts/hf_correlator/`)
3. Grid search sobre (w_h, w_t, w_c) — 9,261 combinaciones sobre 527 eventos
4. Resultado: pesos v2 (−1.0, −1.0, +2.5) con corr=+0.156, d=+0.447

## Hallazgo principal

Los pesos óptimos son negativos para harmony **y** tension. Contraintuitivo a primera vista, pero coherente con el Axioma 8.1 ([[AXIOMATICS_v0_4]]): el campo global mezcla eventos de distintas casas, invirtiendo la señal esperada. La solución correcta no es ajustar más los pesos globales — es filtrar por dominio (planet_subset).

## Artefactos producidos

| Archivo | Descripción |
|---------|-------------|
| `abu_engine/harmony/resonance.py` | GROUP_WEIGHTS actualizado |
| `abu_engine/harmony/field_v3.py` | compute_hf_aspects() con pesos v4 |
| `scripts/hf_correlator/` | Pipeline completo de correlación |
| `analysis/domain_correlation_results.json` | → [[correlation_results]] |
| `analysis/domain_correlation_report.md` | → [[domain_correlation_report]] |
