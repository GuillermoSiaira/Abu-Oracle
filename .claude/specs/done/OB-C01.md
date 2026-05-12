# OB-C01 — Error Tracker: logging de errores a Firestore

**Fecha:** 2026-05-10  
**Track:** Observability  
**Prioridad:** Alta — sin esto el sistema falla silenciosamente en producción  
**Independiente de:** QA-C01, FI-C01, KG-C03, MU-C01, FIX-C01/C02/C03  

---

## Contexto

Abu Oracle ya tiene dos loggers de uso:
- `next_app/lib/lilly-usage-logger.ts` → colección `lilly_usage_log` (11 rutas)
- `next_app/lib/interpretation-logger.ts` → colección `kg_baseline_logs` (10 rutas)

**Ninguno captura errores.** Cuando Vertex devuelve 429, cuando Abu Engine no responde,
o cuando Firestore falla, el error va a `console.error` y desaparece. El operador
no sabe cuándo ni por qué falló el sistema en producción.

Este spec agrega un tercer módulo fire-and-forget que captura solo errores.

---

## Archivo 1: `next_app/lib/error-tracker.ts` (nuevo)

```typescript
/**
 * error-tracker.ts
 *
 * Fire-and-forget: registra errores de las rutas Lilly en Firestore.
 * No bloquea la respuesta — cualquier fallo de storage es silencioso.
 *
 * Schema Firestore:
 *   lilly_errors/{docId}:
 *     timestamp      string   — ISO 8601
 *     route          string   — 'transit' | 'planet' | 'chat' | …
 *     event_type     string   — 'click_transit' | 'screen_open' | …
 *     error_message  string   — message del Error capturado
 *     error_source   string   — 'vertex' | 'abu_engine' | 'firestore' | 'rate_limit' | 'unknown'
 *     status_code    number | null  — HTTP status si aplica (429, 503, etc.)
 *     user_id        string | null
 *     stack          string | null  — primeros 500 chars del stack trace
 */

import { getAdminDb } from '@/lib/firebase-admin';

export type ErrorSource =
  | 'vertex'
  | 'abu_engine'
  | 'firestore'
  | 'rate_limit'
  | 'unknown';

export interface ErrorEntry {
  route:        string;
  eventType:    string;
  errorMessage: string;
  errorSource:  ErrorSource;
  statusCode?:  number | null;
  userId?:      string | null;
  stack?:       string | null;
}

/**
 * Clasifica automáticamente el origen del error según el mensaje.
 * Permite sobreescribir con errorSource explícito si se conoce.
 */
export function classifyError(err: unknown): ErrorSource {
  const msg = err instanceof Error ? err.message.toLowerCase() : String(err).toLowerCase();
  if (msg.includes('429') || msg.includes('rate limit') || msg.includes('quota')) return 'vertex';
  if (msg.includes('abu') || msg.includes('engine') || msg.includes('econnrefused')) return 'abu_engine';
  if (msg.includes('firestore') || msg.includes('firebase')) return 'firestore';
  return 'unknown';
}

/**
 * Fire-and-forget: escribe un documento en lilly_errors.
 * Nunca lanza excepciones al caller.
 */
export function trackError(entry: ErrorEntry): void {
  void (async () => {
    try {
      const db = getAdminDb();
      await db.collection('lilly_errors').add({
        timestamp:     new Date().toISOString(),
        route:         entry.route,
        event_type:    entry.eventType,
        error_message: entry.errorMessage.slice(0, 500),
        error_source:  entry.errorSource,
        status_code:   entry.statusCode ?? null,
        user_id:       entry.userId ?? null,
        stack:         entry.stack ? entry.stack.slice(0, 500) : null,
      });
    } catch (storageErr: unknown) {
      // El tracker nunca debe romper nada — solo loggear a consola
      console.error('[error-tracker] Firestore write failed:', storageErr);
    }
  })();
}
```

---

## Archivo 2: integración en las 11 rutas

### Patrón de integración

Cada ruta tiene una estructura similar a:

```typescript
// ANTES (fragmento típico en cualquier ruta Lilly):
try {
  const result = await completeLilly(client, params);
  // ...
  return NextResponse.json({ response: result.text });
} catch (err) {
  console.error('[lilly/transit] Error:', err);
  return NextResponse.json({ error: 'Error interno' }, { status: 500 });
}
```

```typescript
// DESPUÉS — agregar trackError en el catch:
import { trackError, classifyError } from '@/lib/error-tracker';

// Al inicio del handler, obtener userId (ya disponible en la mayoría de rutas):
const userId = await getUserIdFromRequest(req).catch(() => null);

try {
  const result = await completeLilly(client, params);
  // ... (sin cambios)
  return NextResponse.json({ response: result.text });
} catch (err: unknown) {
  const msg = err instanceof Error ? err.message : String(err);
  
  // Fire-and-forget — no await
  void trackError({
    route:        'transit',          // ← nombre de la ruta (hardcoded por ruta)
    eventType:    body?.eventType ?? 'click_transit',  // ← evento (hardcoded por ruta)
    errorMessage: msg,
    errorSource:  classifyError(err),
    statusCode:   null,               // ← si hay res.status disponible, usarlo
    userId,
    stack:        err instanceof Error ? err.stack ?? null : null,
  });

  console.error('[lilly/transit] Error:', err);
  return NextResponse.json({ error: 'Error interno' }, { status: 500 });
}
```

### Tabla de rutas — valores hardcoded por ruta

| Archivo | route | eventType default |
|---|---|---|
| `lilly/screen-open/route.ts` | `'screen-open'` | `'screen_open'` |
| `lilly/planet/route.ts` | `'planet'` | `'click_planet'` |
| `lilly/technique/route.ts` | `'technique'` | `'click_technique'` |
| `lilly/domain/route.ts` | `'domain'` | `'domain_select'` |
| `lilly/city/route.ts` | `'city'` | `'city_select'` |
| `lilly/transit/route.ts` | `'transit'` | `'click_transit'` |
| `lilly/house/route.ts` | `'house'` | `'click_house'` |
| `lilly/sky/route.ts` | `'sky'` | `'sky_open'` |
| `lilly/solar-return/route.ts` | `'solar-return'` | `'sr_domain_select'` |
| `lilly/mundana/route.ts` | `'mundana'` | `'mundana_config'` |
| `chat/route.ts` | `'chat'` | `'chat'` |

### Nota sobre getUserIdFromRequest

La función ya existe en `next_app/lib/get-user-id.ts`. Si la ruta ya la importa,
reutilizar la misma llamada. Si no, agregar la importación.

En rutas donde `getUserIdFromRequest` falla o no hay token → pasar `userId: null`.
**Nunca dejar que un error en getUserIdFromRequest bloquee el trackeo del error principal.**

---

## Archivos a crear

- `next_app/lib/error-tracker.ts`

## Archivos a modificar

- `next_app/app/api/lilly/screen-open/route.ts`
- `next_app/app/api/lilly/planet/route.ts`
- `next_app/app/api/lilly/technique/route.ts`
- `next_app/app/api/lilly/domain/route.ts`
- `next_app/app/api/lilly/city/route.ts`
- `next_app/app/api/lilly/transit/route.ts`
- `next_app/app/api/lilly/house/route.ts`
- `next_app/app/api/lilly/sky/route.ts`
- `next_app/app/api/lilly/solar-return/route.ts`
- `next_app/app/api/lilly/mundana/route.ts`
- `next_app/app/api/chat/route.ts`

## Archivos de referencia (leer antes de implementar)

- `next_app/lib/lilly-usage-logger.ts` — patrón fire-and-forget existente
- `next_app/lib/firebase-admin.ts` — inicialización Firebase Admin
- `next_app/lib/get-user-id.ts` — extracción userId

---

## TypeScript check

```bash
cd d:/projects/ai-oracle/next_app
npx tsc --noEmit
```

No debe haber errores nuevos en los archivos tocados.

---

## Criterios de aceptación

- [ ] `error-tracker.ts` compila sin errores TypeScript
- [ ] `trackError()` nunca lanza excepciones al caller (try/catch interno)
- [ ] `classifyError()` devuelve `'vertex'` para errores con "429" en el mensaje
- [ ] Las 11 rutas tienen `trackError` en su bloque `catch`
- [ ] Al simular un error (comentar temporalmente la llamada a completeLilly), aparece un documento en `lilly_errors` en Firestore
- [ ] `npx tsc --noEmit` sin errores nuevos

---

## Lo que NO hace este spec

- **NO** modifica los loggers existentes (`lilly-usage-logger`, `interpretation-logger`)
- **NO** trackea errores de rate limit ya manejados por `usage-limiter.ts` (esos son 429 esperados)
- **NO** crea UI de visualización — eso es OB-C02
- **NO** envía alertas — eso es OB-C03

---

## Commit sugerido

```
feat(observability): error tracker Firestore para 11 rutas Lilly (OB-C01)

- lib/error-tracker.ts: trackError() + classifyError() fire-and-forget
- Firestore collection: lilly_errors
- Integrado en catch blocks de las 11 rutas Lilly + chat
```
