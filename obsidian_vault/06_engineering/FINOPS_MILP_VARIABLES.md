---
name: FINOPS_MILP_VARIABLES
description: Variables de decisión pendientes para el módulo FinOps MILP — max_tokens por ruta como caso central
tipo: hipotesis
version: 2026-04-01
estado: pendiente — no iniciar hasta sesión dedicada
tags: [finops, milp, optimizacion, costos, max_tokens, calidad]
---

# FinOps MILP — Variables de decisión pendientes

> Este documento registra observaciones surgidas en otras sesiones que son
> input directo para el módulo MILP. No desarrollar aquí — abrir sesión dedicada.

---

## `max_tokens` por ruta — variable de decisión, no parámetro técnico

**Origen de la observación:** sesión 2026-04-01, fix de truncación de Lilly.

**Estado actual:** los valores de `max_tokens` en las rutas Lilly son heurísticos:

| Ruta | Modelo | max_tokens actual |
|------|--------|-------------------|
| `screen-open` | Sonnet | 1024 |
| `planet` | Sonnet | 1024 |
| `technique` (lot/firdaria) | Haiku | 2048 |
| `technique` (lunar/cycle) | Haiku | 1536 |
| `city` | Haiku | 1024 |
| `domain` | Sonnet | 1024 |
| `house` | Sonnet | 1024 |
| `sky` | Sonnet | 1536 |
| `transit` | Sonnet | 1024 |
| `chat` | Sonnet | 2500 |

**El problema:** `max_tokens` no es solo un parámetro técnico. Es la frontera entre:
- Calidad percibida (respuesta completa sin continuación)
- Costo marginal esperado (tokens × precio del modelo)

Un `max_tokens` bajo → mayor probabilidad de continuación → `completeLilly()` hace
2 llamadas → costo real ~2× para esa ruta. Un `max_tokens` alto → sin continuación
pero costo esperado mayor en el caso normal (el modelo puede gastar más tokens).

**Lo que el MILP debe resolver:**

```
Para cada ruta r con modelo m:
  max_tokens*(r) = argmin E[costo(r, max_tokens)]
  sujeto a:
    P(truncación | max_tokens) ≤ ε_r   (calidad mínima por tipo de ruta)
    E[costo(r)] ≤ budget(plan, r)       (margen por plan)
```

Donde `P(truncación | max_tokens)` se estima empíricamente de la distribución
de longitud de respuesta por tipo de evento — que se puede recolectar desde
los logs de producción.

**Input empírico necesario:**
- Distribución de `output_tokens` por ruta × tipo de evento (de Cloud Run logs)
- Percentil 99 de longitud de respuesta por ruta → `max_tokens` mínimo seguro
- Comparar con `budget(plan)` para decidir si vale degradar a Haiku en alguna ruta

**Conexión con el modelo de capas:**
- Elección de modelo (Haiku vs Sonnet) → variable discreta del MILP ✅ (ya modelado)
- `max_tokens` por ruta → variable continua del MILP ⚠️ (pendiente de modelar)
- Ambas interactúan: Haiku con `max_tokens=2048` puede ser más barato Y más
  confiable que Sonnet con `max_tokens=1024` + continuación frecuente

---

## Referencias cruzadas

- Implementación actual: `next_app/lib/lilly-complete.ts`
- Descripción del MILP: `CLAUDE.md § Capa 3 — Optimizador de Recursos`
- Conversación de diseño: "Módulo FinOp MILP" (chat paralelo)
