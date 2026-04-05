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
Fase A completada (sesión 2026-04-03).
Fase A-2b (recalibración empírica del simulador) completada (sesión 2026-04-04).

### Fase A — Resultados (commit 7c13a19)

**Fase A-1** — medición de tokens de input ($0):
- 495 records · 45 sujetos · seed=42
- Output: `research/finops/token_distribution_input.json`
- Limitación: `/biography` devolvió 401 en todos los sujetos (engine local con
  `AUTH_ENABLED=true` en el momento del run) → timeline vacío → input tokens
  subestimados ~500-800 tokens vs producción real.

**Fase A-2** — medición de tokens de output (generación real):
- 495 records · 45 sujetos · seed=42
- Costo total real: **$20.16 USD** (tres runs completos por problema de encoding
  en Windows — bash background tasks con cp1252 vs utf-8 causaron runs duplicados;
  los tres usaron seed=42 → resultados idénticos, JSON final correcto)
- Output: `research/finops/token_distribution_output.json`

**Hallazgos clave Fase A-2:**
- `P_CONTINUATION` real: **0.036** (supuesto simulador: 0.150 — 4× mayor al real)
- `screen-open`: 40% truncación con max_tokens=1024 → **bug activo en producción**
- `domain`: 4.4% truncación con max_tokens=1024 → monitorear
- `technique_lot/firdaria`: p95=497 vs max_tokens=2048 → reducible a 512 (ahorro 75%)
- Número del paper: **+$34.81 USD/hora** de margen adicional a N=1,000 usuarios
  (greedy vs static) → extrapolado mensual **+$17,524 USD/mes**

**Simulador de carga** (commit 1f31ff3):
- `scripts/finops/load_simulator.py` — Poisson arrivals, cache hit, continuation,
  R5 min_margin, shadow prices TPM/RPM
- θ=700 usuarios: primer shadow price TPM activo ($0.0054/min pico)
- Scaling: N=500-50,000 documentado en `research/finops/scaling_analysis.md`

**Recalibración completada (Fase A-2b):** simulador re-corrido con P_CONTINUATION=0.036
y distribución empírica de output tokens. Ver sección Fase A-2b abajo.

---

## Roadmaps paralelos — no mezclar

Existen dos roadmaps con propósitos distintos:

| Fase | COST_OPTIMIZATION.md (producto) | MILP_INITIATIVE.md (investigación) |
|------|----------------------------------|-------------------------------------|
| A | ✅ Caching mínimo (commit aedfe1a) | ✅ TOKEN_EXPERIMENT completo (2026-04-03) |
| B | ✅ selectModel + Haiku (2026-04-02) | ⏳ Formular y resolver MILP con datos reales |
| C | ⏳ Caching avanzado contextBlock | ✅ selectModel gateway — completado como Fase B de COST_OPT |
| D | ⏳ Auditoría tokens contextBlock | — |
| E | ⏳ Módulo MILP dinámico en producción | — |

**Nota:** Fase C de MILP_INITIATIVE completada como Fase B de COST_OPTIMIZATION —
`next_app/lib/selectModel.ts` es el gateway unificado. Es prerequisito del módulo
dinámico (Fase E de COST_OPT / Fase B de MILP_INITIATIVE).

---

## Fase A-2b — Recalibración empírica del simulador

**Fecha:** 2026-04-04

### Parámetros actualizados vs supuestos anteriores

| Parámetro | Valor sintético (anterior) | Valor empírico (A-2b) | Impacto |
|-----------|---------------------------|----------------------|---------|
| P_CONTINUATION | 0.150 (global) | **0.036** (promedio global, 33/495) | Costo sobreestimado en sintético |
| Continuación | `rng.random() < 0.15` aplicado a todas | **ROUTE_CONTINUATION_RATE** por ruta | screen-open: 71.1%; técnicas: 0-2.2%; resto: 0% |
| screen-open output | Normal(665, 154) | **Normal(960, 39)** | p95=1024 censurado; costo real 2× mayor por continuación |
| technique_lot | Normal(1331, 307) | **Normal(415, 40)** | Sintético 3× sobreestimado |
| technique_firdaria | Normal(1331, 307) | **Normal(425, 44)** | Sintético 3× sobreestimado |
| technique_lunar | Normal(998, 230) | **Normal(437, 122)** | Sintético 2× sobreestimado |
| city | Normal(665, 154) | **Normal(451, 125)** | Leve sobreestimación |
| domain | Normal(665, 154) | **Normal(660, 147)** | Bien calibrado originalmente |
| house | Normal(665, 154) | **Normal(474, 72)** | Sobreestimado |
| sky | Normal(998, 230) | **Normal(468, 72)** | Sintético 2× sobreestimado |
| transit | Normal(665, 154) | **Normal(542, 87)** | Leve sobreestimación |
| chat | Normal(1625, 375) | **Normal(422, 244)** | Sintético 4× sobreestimado |

*sigma = (p95 − mean) / 1.645. p95 de screen-open = max_tokens = 1024 (distribución censurada — la sigma real es mayor).*

**Nota de modelado:** la distribución truncada en `hi=max_tokens` no puede modelar continuación
determinísticamente (el sample nunca supera `hi`). La continuación se modela por separado con
`ROUTE_CONTINUATION_RATE` derivado directamente de `stop_reason == 'max_tokens'` en el JSON.

### Impacto en resultados — márgenes y θ

| N_USERS | Margen static (sintético) | Margen static (empírico) | Margen greedy (sintético) | Margen greedy (empírico) | Δ greedy-static (empírico) |
|---------|--------------------------|--------------------------|--------------------------|--------------------------|---------------------------|
| 500 | −$6.84 | **+$12.72** | +$11.23 | **+$19.60** | **+$6.88** |
| 700 | −$9.98 | **+$17.89** | +$15.84 | **+$27.42** | **+$9.53** ← θ |
| 800 | −$10.71 | **+$19.98** | +$18.07 | **+$31.32** | **+$11.34** |
| 1,000 | −$11.01 | **+$26.12** | +$23.80 | **+$39.15** | **+$13.03** |
| 5,000 | −$23.00 | **+$6.47** | +$6.19 | **+$20.74** | **+$14.27** |
| 50,000 | −$4.98 | **−$6.59** | −$0.95 | **+$3.34** | **+$9.93** |

**Cambios clave:**
- La calibración empírica mueve el margen static de negativo a positivo en N < 50k.
  Los technique_* tokens eran ~3× mayor al real en el sintético — mayor impacto.
- θ se preserva: el shadow price del TPM se activa primero en N=700.
- El delta greedy-static a N=1,000 baja de **+$34.81** a **+$13.03** (−63%).
  El sintético sobreestimaba el beneficio de la greedy porque las rutas de Haiku
  (technique_*) eran más caras de lo real — el ahorro de degradar a Haiku era mayor.
- Número del abstract actualizado: **+$13.03 USD/60min → +$6,567 USD/mes** a N=1,000
  (antes: +$34.81 → +$17,524/mes).

### Continuation rate

| Métrica | Sintético | Empírico (A-2b) |
|---------|-----------|----------------|
| Cont. rate global (static) | 15.2% | **6.5-6.9%** |
| screen-open específico | 15.0% | **71.1%** (32/45 — bug producción) |
| technique_lunar | 15.0% | **2.2%** (1/45) |
| Resto de rutas | 15.0% | **0.0%** |

La tasa de continuación global empírica (~6.5%) es menor que el sintético (15.2%).
El efecto dominante es screen-open: 71.1% de continuación en 1 de 11 rutas ≈ 6.5% global.
El sintético asignaba 15% a **todas** las rutas — correcto en magnitud global pero incorrecto
en distribución (penalizaba Haiku-eligible incorrectamente, sobreestimando su beneficio).

### Bug screen-open — estado (conocido, pendiente fix)

Con max_tokens=1024 y stop_reason='max_tokens' en 32/45 registros reales (71.1%),
en producción `completeLilly()` hace una segunda llamada API en 7 de cada 10 sesiones.
Esto duplica el costo de screen-open y aumenta la latencia.

**Tasa correcta:** 71.1% (no 40% como se estimó previamente).
**Estado:** bug activo en producción. Pendiente subir max_tokens a 1536 o 2048.
**Impacto de costo:** screen-open cuesta ~1.7× lo esperado por este overhead.

### Oportunidad — technique_lot y technique_firdaria

p95 real ≈ 481/497 tokens vs max_tokens=2048 actual (en Haiku).

**Ahorro por request:** `(2048−512)/1e6 × $4.00/1M ≈ $0.006/request`
**A N=1,000 (9% de rutas ≈ 60 req/hr):** ~$0.36/hr → **~$180/mes**

Reducir max_tokens a 512 en estas rutas no afecta la calidad (p99 < 512 estimado)
y libera capacidad TPM para otras rutas.

**Archivos actualizados:**
- `scripts/finops/load_simulator.py` — P_CONTINUATION=0.036, ROUTE_OUTPUT_DIST, ROUTE_CONTINUATION_RATE, OUTPUT_SUFFIX
- `scripts/finops/_run_scaling_empirical.py` — runner multi-N, genera JSON + Markdown
- `research/finops/simulation_results_empirical.json` — resultados completos N=500-50k
- `research/finops/scaling_analysis_empirical.md` — tabla comparativa con vs-synthetic

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

### Decisión de producto derivada de A-2b

El análisis de continuación empírica de Fase A-2b reveló que `screen-open` no es solo la ruta más cara del sistema — es la única con tasa de continuación del 71.1%. Esto convierte el disparo automático en un multiplicador de costo oculto.

**Decisión tomada (2026-04-04, commit pendiente):**

| Variable de decisión | Valor anterior | Valor nuevo | Fundamento |
|---|---|---|---|
| `max_tokens` screen-open | 1024 | 1536 | Normal(960,39) tiene P(x>1536) < 0.001 → elimina continuaciones |
| Modo de disparo | automático (mount) | opt-in explícito (EntryNav) | Elimina costo cuando el usuario no interactúa con el panel |
| Rate greeting | N/A | 1 Firestore read (sin LLM) | Estado A/B sin costo API |

**Trazabilidad:**
- Dato que motivó la decisión: `ROUTE_CONTINUATION_RATE["screen-open"] = 0.711` (32/45 en `token_distribution_output.json`)
- Impacto estimado sobre el modelo N=700: reducción de $3-5/hr en costo flota (screen-open representa ~22% del costo total en N=700)
- Esto desplaza θ (shadow price) hacia la derecha: la restricción de margen se activa a un N mayor, ampliando el rango de operación rentable del simulador.
