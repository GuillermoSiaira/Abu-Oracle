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

Pendiente — sesión dedicada post-lanzamiento.
No iniciar hasta tener datos reales de usuarios de producción,
o ejecutar Fase A con sujetos históricos como sustituto.
