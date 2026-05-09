# KG-C01 — Interpretation Logger: Baseline Token Data Collection

**Fecha:** 2026-05-05  
**Track:** Knowledge Graph / FinOps  
**Prioridad:** Alta — bloquea el experimento A/B definido en `docs/theory/KG_EXPERIMENT_PROTOCOL.md`  
**Independiente de:** KG-C02, BV-C01 — implementar en paralelo

---

## Objetivo

Registrar el uso de tokens de cada llamada a Lilly en Firestore. Esto es la **Condición A
(baseline)** del experimento comparativo JSON plano vs. Knowledge Graph. Sin estos datos no
hay paper.

Cada llamada exitosa a `completeLilly()` debe disparar (fire-and-forget) un log con:
- tokens de input / output
- costo estimado en USD
- ruta que llamó (planet, transit, screen-open, etc.)
- tipo de evento del usuario (click_planet, click_transit, etc.)
- timestamp

---

## Archivo a crear: `next_app/lib/interpretation-logger.ts`

```typescript
import { getAdminDb } from './firebase-admin';

// Sonnet 4.6 pricing (May 2026)
const PRICE_INPUT_PER_M  = 3.00;
const PRICE_OUTPUT_PER_M = 15.00;

export interface LogEntry {
  route:         string;   // 'planet' | 'transit' | 'screen-open' | etc.
  eventType:     string;   // 'click_planet' | 'click_transit' | 'screen_open' | etc.
  inputTokens:   number;
  outputTokens:  number;
  costUsd:       number;   // computed here
  continuations: number;   // from LillyUsage — how many max_tokens continuations
  userId?:       string;   // Firebase UID, if available
  chartKey?:     string;   // "{birthDate}|{lat}|{lon}" — identifies the chart
  lang?:         string;   // 'es' | 'en' | 'fr' | 'pt'
  condition:     'A';      // always 'A' for baseline — 'B' reserved for KG arch
}

/**
 * Fire-and-forget: write one log entry to Firestore.
 * Non-fatal — any error is swallowed so Lilly is never blocked.
 */
export function logInterpretation(entry: LogEntry): void {
  const cost = (entry.inputTokens / 1_000_000) * PRICE_INPUT_PER_M
             + (entry.outputTokens / 1_000_000) * PRICE_OUTPUT_PER_M;

  const doc = {
    ...entry,
    costUsd:   cost,
    timestamp: new Date().toISOString(),
    condition: 'A' as const,
  };

  // fire-and-forget
  getAdminDb()
    .collection('kg_baseline_logs')
    .add(doc)
    .catch((err: unknown) => {
      console.error('[interpretation-logger] Firestore write failed:', err);
    });
}
```

### Notas de implementación

- `getAdminDb()` ya existe en `next_app/lib/firebase-admin.ts` — importar desde ahí.
- No usar `await` en el caller — el caller hace `void logInterpretation(...)`.
- El campo `condition: 'A'` está hardcodeado — cuando se implemente la arquitectura KG
  habrá un segundo logger con `condition: 'B'` para comparación.
- `chartKey` se construye en el caller como `\`${birthData?.date}|${birthData?.lat}|${birthData?.lon}\`` — puede ser undefined si el route no tiene acceso a birthData (ej: mundana).

---

## Rutas a modificar

Todas las rutas usan `completeLilly(client, params)` que retorna `Promise<LillyResult>` donde
`LillyResult = { text: string; usage: LillyUsage }` y
`LillyUsage = { input_tokens: number; output_tokens: number; continuations: number }`.

### Patrón de modificación

```typescript
// ANTES (en cada ruta):
const text = await completeLilly(client, params);

// DESPUÉS:
import { logInterpretation } from '@/lib/interpretation-logger';
import { getUserIdFromRequest } from '@/lib/get-user-id';

// ... dentro del handler:
const result = await completeLilly(client, params);
const text   = result.text;

void logInterpretation({
  route:         'planet',           // ← nombre de la ruta
  eventType:     body.eventType ?? 'click_planet',  // ← del body si viene
  inputTokens:   result.usage.input_tokens,
  outputTokens:  result.usage.output_tokens,
  costUsd:       0,  // overridden inside logInterpretation
  continuations: result.usage.continuations,
  userId:        await getUserIdFromRequest(req).catch(() => undefined),
  chartKey:      body.birthData
    ? `${body.birthData.date}|${body.birthData.lat}|${body.birthData.lon}`
    : undefined,
  lang:          body.lang ?? 'es',
  condition:     'A',
});
```

### Lista de rutas (10)

| Ruta | `route` field | `eventType` field |
|---|---|---|
| `app/api/lilly/screen-open/route.ts` | `'screen-open'` | `'screen_open'` |
| `app/api/lilly/planet/route.ts` | `'planet'` | `'click_planet'` |
| `app/api/lilly/technique/route.ts` | `'technique'` | `body.data?.technique ?? 'click_technique'` |
| `app/api/lilly/transit/route.ts` | `'transit'` | `'click_transit'` |
| `app/api/lilly/domain/route.ts` | `'domain'` | `'domain_select'` |
| `app/api/lilly/city/route.ts` | `'city'` | `'city_select'` |
| `app/api/lilly/house/route.ts` | `'house'` | `'click_house'` |
| `app/api/lilly/sky/route.ts` | `'sky'` | `'sky_open'` |
| `app/api/lilly/solar-return/route.ts` | `'solar-return'` | `'sr_domain_select'` |
| `app/api/chat/route.ts` | `'chat'` | `'chat'` |

**Importante:** Si alguna ruta ya tiene la firma `const text = await completeLilly(...)`,
verificar si `completeLilly` retorna `string` o `LillyResult`. Si retorna `string` (versión
anterior), actualizar la importación para usar la versión que retorna `LillyResult`.
El archivo `next_app/lib/lilly-complete.ts` define `completeLilly` retornando `Promise<LillyResult>`.

---

## Schema Firestore

```
Collection: kg_baseline_logs
Document: (auto-id)
{
  route:         string,   // 'planet'
  eventType:     string,   // 'click_planet'
  inputTokens:   number,   // 1842
  outputTokens:  number,   // 387
  costUsd:       number,   // 0.00553
  continuations: number,   // 0 (normal) | 1-3 (si hubo max_tokens hit)
  userId:        string?,  // Firebase UID o undefined
  chartKey:      string?,  // "1992-05-15|51.5|-0.1"
  lang:          string?,  // 'es'
  condition:     'A',      // siempre 'A' para baseline
  timestamp:     string,   // ISO 8601
}
```

No crear índices manualmente — Firestore los crea automáticamente bajo demanda.

---

## Type check

```bash
cd d:/projects/ai-oracle/next_app
node_modules/.bin/tsc --noEmit
```

No debe haber errores nuevos. Los errores pre-existentes en otras rutas (namespace Anthropic,
MapIterator) son pre-existentes — ignorarlos.

---

## Verificación funcional

1. Iniciar dev server: `cd next_app && npx next dev --port 3001`
2. Cargar carta natal de cualquier sujeto demo
3. Click en cualquier planeta → debe disparar evento Lilly
4. En Firestore Console → `kg_baseline_logs` → verificar que aparece un documento con:
   - `route: "planet"`
   - `inputTokens > 0`
   - `costUsd > 0`
   - `condition: "A"`
5. Verificar que la respuesta de Lilly NO se demora (fire-and-forget — el log no bloquea)

---

## Commit sugerido

```
feat(kg): interpretation logger — baseline token collection (KG-C01)

- lib/interpretation-logger.ts: Firestore fire-and-forget per Lilly call
- Wired into 10 Lilly routes: planet, transit, technique, domain, city,
  house, sky, solar-return, screen-open, chat
- Collects: input_tokens, output_tokens, cost_usd, continuations, userId,
  chartKey, lang — condition='A' (JSON baseline)
- Non-fatal: any Firestore error is swallowed, Lilly response unaffected
```

---

## Referencias

- `docs/theory/KG_EXPERIMENT_PROTOCOL.md` — diseño completo del experimento A/B
- `next_app/lib/lilly-complete.ts` — `LillyResult`, `LillyUsage`, `completeLilly()`
- `next_app/lib/firebase-admin.ts` — `getAdminDb()`
- `next_app/lib/get-user-id.ts` — `getUserIdFromRequest()`
- `next_app/lib/usage-limiter.ts` — patrón de referencia para acceso a Firestore en rutas
