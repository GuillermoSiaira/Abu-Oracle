---
name: hf_v6
description: Fórmula HF_v6 — angularidad × dignidad esencial × amplificador intersección firdaria∩dominio
tipo: formula
version: v6
estado: activo
tags: [formula, HF, dignidad, firdaria, dominio, angularidad]
---

# HF_v6

Ver resultados empíricos: [[HF_V6_RESULTS]]
Fundamento doctrinal: [[AXIOMATICS_v0_4]] Axiomas 8 y 9
Baseline de referencia: [[field_v3]]
Hipótesis validada: [[HIPOTESIS_REGISTRO#H_v6]]

---

## Fórmula completa

```
HF_v6 = HF_aspects(v3, subset_k) + 0.6 × HF_angles_v6 + 0.3 × HF_houses(v3, subset_k)
```

### HF_aspects — sin cambios respecto a [[field_v3]]

```
HF_aspects = w_h × (sextil + trígono) + w_t × (cuadratura + oposición) + w_c × conjunción
```

Pesos: w_h = −1.0, w_t = −1.0, w_c = +2.5
Filtrado por `planet_subset = house_significators(natal, house=k)`

### HF_angles_v6 — nuevo

```
HF_angles_v6 = Σ_{p ∈ subset_k} angularity(p,φ,λ) × dignity_score(p) × w(p,t,k)

w(p,t,k) = 2.0  si p ∈ (firdaria_planets(t) ∩ subset_k)
           1.0  en caso contrario
```

- `angularity(p)` = `mean_strength` de `planet_angular_strengths()` en la ubicación (φ,λ)
- `dignity_score(p)` = D4 de `calculate_dignity()`: +5/+4/0/−4/−5
- Peregrine (score=0): contribución = 0
- Detrimento/caída (score<0): contribución negativa → valle de adversidad

### HF_houses — sin cambios respecto a [[field_v3]]

---

## Diferencias respecto a versiones anteriores

| Componente | HF_v3 | HF_v5 | HF_v6 |
|------------|-------|-------|-------|
| HF_aspects | geometría pura | dignity × kernel | geometría pura |
| HF_angles  | suma angular | angularity_sum | angularity × dignity × w |
| Firdaria   | no | w=1.5 en todos los pares | w=2.0 solo en intersección ∩ dominio |
| HF_houses  | estándar | no incluido | estándar |

---

## Resultado empírico

H07 d=+0.587 · H10 d=+0.702 · global d=+0.193
(vs HF_v3 global d=+0.441 — degradación global esperada por Axioma 8)

---

## Implementación

`abu_engine/harmony/hf_v6.py` — `compute_hf_v6(natal_data, query_date, house_domain, lat, lon)`
