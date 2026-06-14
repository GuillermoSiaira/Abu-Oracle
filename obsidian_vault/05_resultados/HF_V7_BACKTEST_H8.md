---
tags: [resultados, harmony_field, hf_v7, compuerta, backtest, h8]
fecha: 2026-06-14
estado: NO-GO (por datos/diseño, no refutación)
---

# HF v7 — Backtest de ablación + compuerta h8

> **Resultado: NO-GO de v7 sobre v6.** Ningún operador de completitud pasa el
> criterio preregistrado. Pero **no es refutación** — el corpus y el diseño del
> test no pueden validar el reclamo real del HF. Decisión: HF sale "en validación".

## Qué se corrió

`scripts/hf_backtest_v7.py` — runner reproducible (seed 42, sanity v6_base==engine).
Ablación acumulativa top-down sobre dos corpus:
- **Temporal** (`biographical_events_v2/`, 446 eventos +/−): HF de tránsito por evento,
  correlación HF↔valencia por dominio. Operadores aplicados a planetas transitantes.
- **Espacial** (`hf_relocation_corpus/`, 131 eventos +/−): HF en la ubicación del evento
  vs ubicaciones shuffleadas (hit-rate condicionado por valencia, baseline 0.5).

Operadores: N1 secta · N2 dignidad · N3a recepción · N3b antiscios · N3d aspectos-a-ángulos.
(N3c parans y N5 tránsito→ángulo NO implementados → excluidos.)

## Resultados

| Brazo | Temporal test Pearson | Espacial hit-rate (vs 0.5) |
|---|---|---|
| v6_base | 0.113 | 0.527 |
| +N1 | 0.105 | 0.527 |
| +N1+N2 | 0.108 | 0.519 |
| +N1+N2+N3a | 0.111 | 0.519 |
| +N1+N2+N3a+N3b | 0.107 | 0.519 |
| **v7_full (+N3d)** | **0.074 ↓** | **0.473 ↓ (bajo azar)** |

- Temporal: señal débil (~0.05–0.11, p>0.13, no significativa). Operadores ±0.01. N3d baja.
- Espacial: hit-rate ≈ azar (perm p ≈ 0.51 en todos los brazos). N3d empuja bajo el azar.
- **Criterio preregistrado (≥+0.05 Pearson o ≥+0.10 rank-biserial): ningún operador pasa.**

## Por qué NO es refutación (3 razones)

1. **Pocos negativos**: corpus +111/−20 → ~20 negativos espaciales. Sin poder discriminante.
2. **Fechas imprecisas**: eventos sin mes/día → cielo de tránsito equivocado.
3. **El runner testeó la cosa equivocada** (hallazgo de revisión): usó posiciones de
   TRÁNSITO a la fecha del evento, no la carta **NATAL** proyectada sobre la ubicación —
   que es el reclamo real de relocalización ("dónde funciona tu carta", estático). Los
   operadores N1-N3b son natales y no aplican limpio a tránsitos.

La metodología del runner es sólida (hit-rate valence-aware, secta/dignidad de tránsito
vía funciones del engine, sanity check pasó). Mide bien — pero mide mal el reclamo natal.

## Decisión (G, 2026-06-14)

- El **HF sale "en validación"** — NO frena el lanzamiento. El tier pago lidera con lo
  doctrinal/Lilly (cuándo + perfil), no con relocalización espacial.
- La validación del HF es **trabajo manual de G** (astrólogo en formación): construir el
  corpus correcto — más sujetos, fechado, ubicado, balanceado en negativos. NO es trabajo
  de algoritmo (operadores preregistrados, no se tunean).

## Rediseño pendiente (si se retoma el track de validación)

- Test espacial con posiciones **NATALES** en la ubicación del evento (no tránsitos).
- Corpus a propósito: escalar `hf_relocation_corpus` con más sujetos y balance de valencias.
- Parans (N3c) y N5 **parados** — no construir más operadores hasta que la validación
  tenga datos.

Ver: `scripts/hf_backtest_v7.py`, `results/hf_backtest_v7_*.json`, [[HF_validation_gate]].
