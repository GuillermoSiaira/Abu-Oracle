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

**Reformulación (2026-04-05):** la variable de decisión correcta no es el modelo
por ruta — es el precio por plan. Ver `research/finops/MILP_INITIATIVE.md § Reformulación v2`.

**Axioma de producto:** la calidad de Lilly no se degrada por ruta. El modelo es
Sonnet en todas las rutas de interpretación doctrinal. La calidad es fija; el precio
es la variable que el MILP debe optimizar.

- Dados el patrón de demanda observado (logs `selectModel.ts`) y el presupuesto
  Anthropic (supply), el MILP resuelve el precio mínimo por plan que hace el sistema
  sostenible con Sonnet everywhere.
- La política actual Fase B (Haiku en `technique` y `city`) es una heurística
  provisional — pendiente de revisión una vez que el MILP de precios esté formulado.
- Potencialmente publicable y extrapolable como producto independiente.
- Sesión estratégica separada requerida.

## Regla operativa

Antes de cualquier feature que agregue una llamada nueva a Anthropic:
1. Estimar tokens de input/output
2. Calcular costo por sesión con y sin caching
3. Decidir modelo (Sonnet vs Haiku) según complejidad doctrinal requerida
4. Documentar la decisión en este archivo

### Fase F — Entry Point Inteligente ✅ COMPLETA (2026-04-04)

**Motivación**: Análisis FinOps Fase A-2b (commit `54c8738`) reveló que `screen-open` tiene una tasa de continuación empírica del 71.1% (32/45 respuestas alcanzan el límite de 1024 tokens). `completeLilly()` dispara una segunda llamada automáticamente, duplicando el costo efectivo de la orientación inicial. Además, el disparo automático al montar el componente genera costo aunque el usuario no haya interactuado.

**Cambios implementados:**

| Cambio | Archivo | Impacto |
|---|---|---|
| `max_tokens: 1024 → 1536` en screen-open | `app/api/lilly/screen-open/route.ts` | Elimina el 71.1% de continuaciones (sin costo extra si la respuesta cabe) |
| screen-open automático → opt-in explícito | `components/OracleChat.tsx` | Elimina el 100% de las llamadas a screen-open en usuarios que no presionan "Panorama actual" |
| `EntryNav.tsx` con 4 botones persistentes | `components/EntryNav.tsx` | UX neutral — los demás botones dispatchen `pendingLillyEvent` (sin costo adicional) |
| `GET /api/lilly/greeting` | `app/api/lilly/greeting/route.ts` | Sin costo LLM — solo Firestore read para Estado A/B |

**Ahorro estimado:**
- Screen-open consumía ~$0.006 por carga de carta. Con opt-in, solo los usuarios que explícitamente presionan "Panorama" pagan ese costo.
- Eliminación continuaciones: el 71.1% de duplicaciones desaparece con `max_tokens=1536` (Normal(960,39) tiene masa < 1% por encima de 1536).
- Ahorro combinado estimado: 40-60% del costo de screen-open a nivel flota.
