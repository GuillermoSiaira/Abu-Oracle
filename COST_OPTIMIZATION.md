# COST_OPTIMIZATION.md — Abu Oracle: Estrategia de optimización de costos API

> Creado: 2026-03-27. Leer junto a CLAUDE.md al inicio de cualquier sesión que toque llamadas a Anthropic.

## Contexto

Abu Oracle usa Claude Sonnet 4.6 como motor de Lilly en 8 routes.
Cada request consume ~3,500–5,000 tokens de input + ~300 tokens de output.
Precios Sonnet 4.6: input $3.00/1M tok · cache write $3.75/1M · cache read $0.30/1M · output $15.00/1M

## Costo por sesión típica (10 interacciones)

| Escenario | Costo/sesión |
|---|---|
| Sin optimización | ~$0.17 |
| Caching mínimo (system prompt) | ~$0.126 |
| Caching avanzado (system + base context) | ~$0.094 |
| Caching avanzado + Haiku en routes simples | ~$0.06 |

## Proyección mensual (30 sesiones/usuario)

| Usuarios activos | Sin opt. | Caching mín. | Optimización completa |
|---|---|---|---|
| 100 | $510 | $378 | $180 |
| 500 | $2,550 | $1,890 | $900 |
| 1,000 | $5,100 | $3,780 | $1,800 |

## Margen por plan con optimización completa

| Plan | Ingreso/mes | Costo API (30 ses) | Margen |
|---|---|---|---|
| Mensual $5 | $5.00 | $1.80 | $3.20 (64%) |
| Anual $3.75 | $3.75 | $1.80 | $1.95 (52%) |

## Plan de optimización — estado

### Fase A — Caching mínimo ✅ COMPLETA (commit aedfe1a · 2026-03-27)
- `LILLY_SYSTEM_PROMPT` cacheado con `cache_control: ephemeral` en las 8 routes
- En `/api/chat`: segundo bloque cacheado con `assembleContextBlock` output cuando `abuData` disponible
- Nota: el segundo bloque contiene `memoryBlock` y `lunarBlock` — dinámicos por usuario/momento. Cache hit garantizado solo en primer bloque. Ahorro real del segundo bloque menor al teórico pero presente en sesiones largas.
- Implementación: `system` de string plano → array de bloques en todas las routes

### Fase B — Haiku en routes simples ✅ COMPLETA (2026-04-02)
- `selectModel(route, plan)` en `next_app/lib/selectModel.ts` — única fuente de verdad para selección de modelo.
  - `technique`, `city` → `claude-haiku-4-5-20251001` (baja complejidad doctrinal)
  - `screen-open`, `planet`, `transit`, `domain`, `solar-return`, `sky`, `house`, `chat` → `claude-sonnet-4-6`
- Logging estructurado (JSON a stdout) por cada request: `route`, `plan`, `model_selected`, `routing_reason`, `tokens_input_est`, `cost_est_usd`.
- 11 routes migradas: hardcoded string → `selectModel(route, 'genesis')`.
- `tsc --noEmit` exit 0.
- Punto de entrada para Fase E (MILP): solo hay que modificar `selectModel.ts`.
- Ahorro adicional: ~15% sobre costo total

### Fase C — Caching avanzado ⏳ PENDIENTE
- Separar `assembleContextBlock()` en parte estática (cacheable) y dinámica
- Requiere refactor de `context-builder.ts` + las 8 routes
- Ahorro adicional: ~20% sobre costo total post-Fase A

### Fase D — Auditoría contextBlock ⏳ PENDIENTE
- Reducir redundancias entre system prompt, buildBaseContext y assembleContextBlock
- Objetivo: reducir contextBlock 20-30% sin pérdida de calidad interpretativa
- Ejecutar junto con Fase C

### Fase E — Módulo de optimización dinámica 🔭 ESTRATÉGICO
- Optimizador que conoce costo por ruta, plan del usuario y margen objetivo
- Decide en tiempo real qué modelo usar por request
- Basado en programación lineal
- Potencialmente extrapolable como producto independiente
- Sesión estratégica separada requerida

## Regla operativa

Antes de cualquier feature que agregue una llamada nueva a Anthropic:
1. Estimar tokens de input/output
2. Calcular costo por sesión con y sin caching
3. Decidir modelo (Sonnet vs Haiku) según complejidad doctrinal requerida
4. Documentar la decisión en este archivo
