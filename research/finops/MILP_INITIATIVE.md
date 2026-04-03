# FinOps MILP — Iniciativa de Optimización de Costos

## Problema

Abu Oracle opera múltiples rutas LLM con modelos distintos (Haiku, Sonnet).
El costo por usuario varía según ruta, modelo y plan de suscripción.
Objetivo: maximizar margen por plan minimizando costo por request
sujeto a restricciones de calidad mínima por tipo de ruta.

Ningún paper existente aborda optimización de SaaS multi-plan sobre LLMs
con restricciones de margen por plan de suscripción.

## Formulación MILP

### Variables de decisión

- `x_r ∈ {Haiku, Sonnet}` — modelo por ruta (discreta)
- `t_r ∈ [256, 4096]` — max_tokens por ruta (continua)

Detalle técnico de variables: ver
`obsidian_vault/06_engineering/FINOPS_MILP_VARIABLES.md`

### Restricciones

- `P(truncación | t_r) ≤ ε_r` por ruta — calidad mínima
- `E[costo(r)] ≤ budget(plan, r)` por plan

### Interacción entre variables

`x_r` y `t_r` no son independientes: Haiku con `max_tokens=2048` puede
ser más barato Y más confiable que Sonnet con `max_tokens=1024` +
continuación frecuente (completeLilly() cobra 2×).

## Rutas actuales y heurísticos vigentes

| Ruta | Modelo | max_tokens | Tipo |
|------|--------|-----------|------|
| `screen-open` | Sonnet | 1024 | No degradable a Haiku |
| `planet` | Sonnet | 1024 | No degradable a Haiku |
| `technique` (lot/firdaria) | Haiku | 2048 | Ya en Haiku |
| `technique` (lunar/cycle) | Haiku | 1536 | Ya en Haiku |
| `city` | Haiku | 1024 | Ya en Haiku |
| `domain` | Sonnet | 1024 | Candidato a Haiku |
| `house` | Sonnet | 1024 | Candidato a Haiku |
| `sky` | Sonnet | 1536 | Evaluar |
| `transit` | Sonnet | 1024 | Candidato a Haiku |
| `chat` | Sonnet | 2500 | No degradable |

Los valores de `max_tokens` son heurísticos — no optimizados.
Ver TOKEN_EXPERIMENT_DESIGN.md para cómo medirlos empíricamente.

## Plan de implementación

**Fase A** — Medir distribución output_tokens (TOKEN_EXPERIMENT_DESIGN.md)
- Input: 26 sujetos históricos × 10 rutas × 100 llamadas
- Output: percentil 99 por ruta → `max_tokens` mínimo seguro
- Costo estimado: < $2 en API

**Fase B** — Formular y resolver el MILP con datos reales
- Datos de Fase A como parámetros ε_r
- Datos de ingresos por plan como budget(plan, r)
- Resolver con scipy.optimize.milp o PuLP

**Fase C** — Implementar `selectModel()` como gateway único
- Reemplazar hardcoding de modelo en cada ruta
- Gateway decide modelo + max_tokens por ruta × plan

## Publicación objetivo

MLSys o SIGMOD — optimización de SaaS multi-plan sobre LLMs
con restricciones de margen por plan de suscripción.

Referencia: FrugalGPT optimiza costo global; RouteLLM optimiza calidad.
Abu Oracle necesita un optimizador que conoce el contexto de negocio
completo (margen por plan). Eso es distinto y publicable.

## Estado

Fase C completada como prerequisito (sesión 2026-04-02).
Fase A en progreso — script de medición pendiente de ejecución.

---

## Roadmaps paralelos — no mezclar

Existen dos roadmaps con propósitos distintos:

| Fase | COST_OPTIMIZATION.md (producto) | MILP_INITIATIVE.md (investigación) |
|------|----------------------------------|-------------------------------------|
| A | ✅ Caching mínimo (commit aedfe1a) | ⏳ TOKEN_EXPERIMENT: medir distribución real |
| B | ✅ selectModel + Haiku (2026-04-02) | ⏳ Formular y resolver MILP con datos reales |
| C | ⏳ Caching avanzado contextBlock | ✅ selectModel gateway — completado como Fase B de COST_OPT |
| D | ⏳ Auditoría tokens contextBlock | — |
| E | ⏳ Módulo MILP dinámico en producción | — |

**Nota:** Fase C de MILP_INITIATIVE completada como Fase B de COST_OPTIMIZATION —
`next_app/lib/selectModel.ts` es el gateway unificado. Es prerequisito del módulo
dinámico (Fase E de COST_OPT / Fase B de MILP_INITIATIVE).

---

## Modos del simulador MILP

### Modo prescriptivo
Restricción R5 activa con $\mu_{p(u)} > 0$ — garantiza margen mínimo por plan.
Úsalo para decisiones de producción: qué modelo y max_tokens asignar a cada
ruta × plan para sostener el margen objetivo.

### Modo descriptivo
Restricción R5 libre ($\mu_{p(u)} = 0$) — muestra la realidad sin restricción
de piso de margen. Útil para:
- Diagnóstico: cuánto cuesta el sistema sin restricciones
- Paper: caracterizar el espacio de soluciones completo
- Comparar con modo prescriptivo para cuantificar el costo de calidad
