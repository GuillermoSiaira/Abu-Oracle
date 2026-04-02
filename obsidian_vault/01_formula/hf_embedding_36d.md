---
name: hf_embedding_36d
description: Embedding 36D del HF Core v1 — representación vectorial de la carta natal usada en hf_dataset_v2.parquet
tipo: formula
version: 2026-04-01
estado: producción (solo dataset, no en scoring activo)
tags: [hf, embedding, dataset, circular-vector, armónicos, 36D]
---

# HF Embedding 36D — Representación vectorial de la carta natal

Usado en `data/processed/hf_dataset_v2.parquet` (4,650 sujetos).
**No confundir con HF scoring**: el embedding es la representación fija de la carta;
el scoring (HF_v3, HF_v6) se calcula sobre una grilla geográfica.

---

## Estructura (36 dimensiones)

### Bloque 1 — Vector circular (24D)

Para cada uno de los 12 puntos planetarios (Sol, Luna, Merc, Venus, Marte, Júpiter,
Saturno, Urano, Neptuno, Plutón, ASC, MC) con longitud θᵢ (radianes):

```
(cos θᵢ, sin θᵢ)  →  24 dimensiones total
```

Preserva simetría rotacional y permite agregación armónica.

### Bloque 2 — Firma armónica (8D)

Para armónicos k ∈ {1, 2, 3, 4, 5, 6, 8, 12}:

```
H_k = |Σ wᵢ · e^{i·k·θᵢ}|
```

donde wᵢ son los pesos de cada punto planetario desde HF Core v1.

### Bloque 3 — Métricas HF (4D)

```
hf_total       = suma de resonancias gaussianas sobre todos los pares
hf_harmony     = resonancia sextil (60°) + trígono (120°)
hf_tension     = resonancia cuadratura (90°) + oposición (180°)
hf_conjunction = resonancia conjunción (0°)
```

**Kernel gaussiano** (common a todos):
```
I_a(d) = exp(-d² / 2σ_a²)
```
donde σ_a es el orbe del aspecto a.

---

## Frontera arquitectónica

| Módulo | Responsabilidad |
|--------|-----------------|
| Abu Engine | Posiciones planetarias, tiempo sidéreo, ASC, MC, casas |
| HF Core | Transforms matemáticos (vector circular, armónicos, resonancia). Funciones puras/stateless. |

Las posiciones planetarias son invariantes bajo relocalización.
Solo ASC/MC/casas cambian con (lat, lon).

---

## Archivos relacionados

- `data/processed/hf_dataset_v2.parquet` — 4,650 embeddings 36D
- `abu_engine/harmony/field_v3.py` — implementación HF scoring (no embedding)
- `abu_engine/harmony/resonance.py` — pesos de aspectos y grupos

Fuente original: `docs/archive/HF_THEORETICAL_FRAMEWORK.md` (migrado 2026-04-01)
