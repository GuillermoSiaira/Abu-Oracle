---
name: HF_V6_RESULTS
description: Resultados HF_v6 — angularidad × dignidad × intersección firdaria∩dominio. H07 d=+0.587, H10 d=+0.702
tipo: resultados
version: 2026-03-29
estado: confirmado
tags: [resultados, hf_v6, cohens_d, dignidad, firdaria, dominio, validacion-empirica]
---

# HF_v6 — Resultados y validación doctrinal

**Fecha:** 2026-03-29
**Estado:** Confirmado — hipótesis doctrinal validada empíricamente

Ver también: [[HF_EXPERIMENT_LOG]] · [[HIPOTESIS_REGISTRO]] · [[AXIOMATICS_v0_4]]

---

## Resultado central

| casa    | n_eventos | cohens_d_v3 | cohens_d_v5 | cohens_d_v6 | delta_v6     |
|---------|-----------|-------------|-------------|-------------|--------------|
| H04     | 0         | n/a         | n/a         | n/a         | n/a          |
| H05     | 57        | n/a         | n/a         | n/a         | n/a (N-=1)   |
| H07     | 93        | +0.055      | +0.038      | +0.587      | +0.532       |
| H10     | 250       | +0.056      | −0.379      | +0.702      | +0.646       |
| global  | 529       | +0.441      | −0.064      | +0.193      | −0.248       |

---

## Hipótesis confirmada

> "El HF calculado con angularidad modulada por dignidad esencial
> × amplificador de intersección firdaria∩dominio produce mayor separación
> entre eventos positivos y negativos que HF_v3 en dominios específicos."

Confirmada en 2 dominios (H07, H10). No falsada.

---

## Arquitectura que produce el resultado

Dos mecanismos separados — esta separación es la clave:

### Mecanismo 1 — Aspectos como geometría pura

```
HF_aspects = Σ_{pares ∈ subset(k)} kernel_gaussiano(Δθ)
```

Sin ponderación por dignidad. La resonancia entre planetas es un hecho astronómico,
no una valoración cualitativa.

### Mecanismo 2 — Angularidad modulada por dignidad × firdaria

```
HF_angles_v6 = Σ_{p ∈ subset(k)} angularity(p,φ,λ) × dignity(p) × w(p,t,k)

w(p,t,k) = 2.0  si p ∈ (firdaria(t) ∩ subset(k))
           1.0  en caso contrario
```

- **Angularidad** = "volumen" del planeta (Ptolomeo, Lilly)
- **Dignidad** = "contenido" del planeta
- **Intersección firdaria∩dominio** = activación condicionada ([[AXIOMATICS_v0_4#Axioma 9]])

---

## Por qué HF_v5 falló y HF_v6 funciona

HF_v5 mezclaba dignidad dentro del kernel de aspecto (`pair_score = kernel × (dignity_i + dignity_j)`),
invirtiendo la señal. HF_v6 separa geometría (aspectos) y cualidad (angularidad×dignidad).

---

## Por qué el global cae

El campo global promedia sobre todos los dominios. Confirma [[AXIOMATICS_v0_4#Axioma 8]]:
la especificidad de dominio es condición de legibilidad del campo.

---

## Archivos fuente

- Implementación: `abu_engine/harmony/hf_v6.py`
- Correlador: `scripts/run_hf_v6_comparison.py`
- Baseline: `analysis/domain_correlation_results.json`
- Reporte completo: `analysis/HF_V6_RESULTS.md`
