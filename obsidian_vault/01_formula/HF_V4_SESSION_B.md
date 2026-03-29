---
name: HF_V4_SESSION_B
description: Spec de implementación HF v4 — pesos diferenciados y correlador de eventos biográficos
tipo: formula
version: v4 (spec de implementación)
estado: implementado
tags: [harmony-field, v4, pesos, correlador, optimizacion, sesion-b]
---

# Session B — HF v4 Weighted + Event Correlator

Archivo fuente: `docs/SESSION_B_HF_V4_CORRELATOR.md`

Ver también: [[resonance_weights]] · [[field_v3]] · [[HF_EXPERIMENT_LOG]] · [[domain_correlation_report]]

---

## Problema que resuelve

HF v3 sumaba todos los aspectos con peso 1.0. Resultado: un lugar con muchas squares/oposiciones puntuaba igual que uno con trines/sextiles. La fórmula v4 diferencia los grupos por signo.

---

## Fórmula HF v4

### Core (aspectos)

```
hf_weighted = w_h * hf_harmony + w_t * hf_tension + w_c * hf_conjunction
```

Donde:
- `hf_harmony = sextile + trine`
- `hf_tension = square + opposition`
- `hf_conjunction = conjunction`

### Relocation completa

```
hf_v4(φ,λ) = hf_weighted(φ,λ) + β * hf_angles(φ,λ) + γ * hf_houses(φ,λ)
```

- β = 0.6, γ = 0.3 (heredados de v3, no tocar)

---

## Pesos iniciales vs. pesos optimizados

| Versión | w_harmony | w_tension | w_conjunction | Resultado |
|---------|-----------|-----------|---------------|-----------|
| Spec v4 inicial | +1.5 | −0.8 | +1.0 | (referencia) |
| **v2 optimizado** | **−1.0** | **−1.0** | **+2.5** | corr=+0.156, d=+0.447 |

Los pesos óptimos (producción) son negativos para harmony y tension. Hallazgo contraintuitivo: el HF global mezcla eventos de distintas casas, lo que invierte la señal esperada. El filtrado por dominio mejora la señal — ver [[AXIOMATICS_v0_4#Axioma 8.1]].

---

## Correlador de eventos

```python
for event in biographical_events:
    transit_chart = compute_chart(event.date, event.lat, event.lon)
    hf_at_event = compute_hf_v4(natal_angles, transit_angles)
    correlations.append((hf_at_event, event.valence))

# Correlación hf_value ↔ valence_numeric (+1 / 0 / -1)
```

### Grid search de pesos

```python
for w_h in [-1.0, -0.75, 1.0, 1.5, 2.0]:
    for w_t in [-1.0, -0.8, -0.5, 0.0]:
        for w_c in [1.0, 1.5, 2.0, 2.5, 3.0]:
            corr = compute_correlation(events, w_h, w_t, w_c)
```

Dataset: 527 eventos · 26 sujetos · 9,261 combinaciones evaluadas.

---

## Archivos creados por el correlador

```
scripts/hf_correlator/
  compute.py    — HF en cada evento
  correlate.py  — Pearson + Cohen's d
  optimize.py   — grid search sobre (w_h, w_t, w_c)
  report.py     — CSV + plots

analysis/
  domain_correlation_report.md   → [[domain_correlation_report]]
  domain_correlation_results.json → [[correlation_results]]
```
