# FI-C01 — Free Tier Routing: Gemini Flash + Access Context

**Fecha:** 2026-05-08  
**Track:** FinOps / Infrastructure  
**Prioridad:** Alta — activa modelo económicamente viable para usuarios free  
**Depende de:** QA-C01 completado (red de seguridad primero)  
**Independiente de:** KG-C03

---

## Objetivo

Routear usuarios free tier a Gemini Flash (coste ~0) y usuarios pagos a Claude Sonnet.
`FREE_TIER_LIMIT` sube de 3 a 15 llamadas de por vida.
El logger queda provider-aware desde el primer día para no contaminar los datos FinOps.

---

## Arquitectura: `getAccessContext(req)`

El problema actual: `applyRateLimit()` devuelve `NextResponse | null` — pierde la información
del plan del usuario. Cada ruta sabe si pasó el límite, pero no sabe qué modelo usar.

**Solución**: un helper centralizado que resuelve identidad + plan + límites de una vez.

```typescript
// next_app/lib/access-context.ts
export interface AccessContext {
  userId:    string | null;
  plan:      'free' | 'genesis' | 'monthly' | 'annual' | null;
  paying:    boolean;
  allowed:   boolean;   // false = límite alcanzado → responder 429
  provider:  'anthropic' | 'gemini';
  limitType?: 'free_lifetime' | 'daily';
}
```

**Lógica de `getAccessContext(req)`:**

```
sin userId (anónimo)      → provider: 'gemini', paying: false, allowed: true
                            (sin auth = sin límite por ahora, pero sin memoria)

userId + plan pago        → provider: 'anthropic', paying: true
  (genesis/monthly/annual)  → aplicar daily limit 50 calls/day
                            → allowed: false + limitType: 'daily' si supera

userId + plan free        → provider: 'gemini', paying: false
  (o sin campo plan)        → aplicar free lifetime limit (FREE_TIER_LIMIT = 15)
                            → allowed: false + limitType: 'free_lifetime' si supera
```

---

## Archivo 1: `next_app/lib/access-context.ts` (nuevo)

```typescript
import { getAdminDb } from './firebase-admin';
import { getUserIdFromRequest } from './get-user-id';

export interface AccessContext {
  userId:    string | null;
  plan:      'free' | 'genesis' | 'monthly' | 'annual' | null;
  paying:    boolean;
  allowed:   boolean;
  provider:  'anthropic' | 'gemini';
  limitType?: 'free_lifetime' | 'daily';
}

const FREE_TIER_LIMIT = 15;
const DAILY_LIMIT     = 50;

export async function getAccessContext(req: Request): Promise<AccessContext> {
  const userId = await getUserIdFromRequest(req).catch(() => null);

  // Anónimo: permiso, Gemini, sin límites por ahora
  if (!userId) {
    return { userId: null, plan: null, paying: false, allowed: true, provider: 'gemini' };
  }

  const db   = getAdminDb();
  const snap = await db.collection('users').doc(userId).get().catch(() => null);
  const data = snap?.data() ?? {};
  const plan = (data.plan as AccessContext['plan']) ?? 'free';
  const paying = ['genesis', 'monthly', 'annual'].includes(plan ?? '');

  if (paying) {
    // Daily limit para usuarios pagos
    const today   = new Date().toISOString().slice(0, 10);
    const usageRef = db.collection('users').doc(userId).collection('usage').doc('daily');
    
    const result = await db.runTransaction(async (tx) => {
      const usageSnap = await tx.get(usageRef);
      const usageData = usageSnap.data() ?? {};
      const currentCount = usageData.date === today ? (usageData.lilly_calls ?? 0) : 0;
      
      if (currentCount >= DAILY_LIMIT) {
        return { allowed: false, limitType: 'daily' as const };
      }
      
      tx.set(usageRef, { date: today, lilly_calls: currentCount + 1 }, { merge: true });
      return { allowed: true };
    }).catch(() => ({ allowed: true })); // fail-open en error de storage

    return { userId, plan, paying: true, provider: 'anthropic', ...result };
  }

  // Free tier: lifetime limit
  const freeRef = db.collection('users').doc(userId).collection('usage').doc('free_tier');
  
  const result = await db.runTransaction(async (tx) => {
    const snap = await tx.get(freeRef);
    const count = snap.data()?.lilly_calls ?? 0;
    
    if (count >= FREE_TIER_LIMIT) {
      return { allowed: false, limitType: 'free_lifetime' as const };
    }
    
    tx.set(freeRef, { lilly_calls: count + 1 }, { merge: true });
    return { allowed: true };
  }).catch(() => ({ allowed: true })); // fail-open

  return { userId, plan, paying: false, provider: 'gemini', ...result };
}

/**
 * Helper: retorna NextResponse 429 con mensaje adecuado al tipo de límite.
 */
export function rateLimitResponse(ctx: AccessContext): Response {
  const message = ctx.limitType === 'free_lifetime'
    ? `Has usado tus ${FREE_TIER_LIMIT} consultas gratuitas. Hazte miembro Genesis para acceso ilimitado.`
    : `Límite diario alcanzado (${DAILY_LIMIT} consultas). Se restablece mañana.`;
  
  return new Response(JSON.stringify({ error: message }), {
    status: 429,
    headers: { 'Content-Type': 'application/json' },
  });
}
```

---

## Archivo 2: `next_app/lib/gemini-client.ts` (nuevo)

### Dependencia

```bash
cd d:/projects/ai-oracle/next_app
npm install @google/genai
```

### Implementación

```typescript
// next_app/lib/gemini-client.ts
import { GoogleGenAI } from '@google/genai';
import type { LillyResult } from './lilly-complete';

const MODEL = 'gemini-2.0-flash';

function getGeminiClient(): GoogleGenAI {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error('GEMINI_API_KEY not set');
  return new GoogleGenAI({ apiKey });
}

/**
 * Equivalente a completeLilly() pero para Gemini Flash.
 * system:   system prompt (LILLY_SYSTEM_PROMPT)
 * messages: array { role: 'user'|'model', content: string }
 * maxTokens: output token cap
 */
export async function completeLillyGemini(
  system:    string,
  messages:  Array<{ role: 'user' | 'model'; content: string }>,
  maxTokens: number,
): Promise<LillyResult> {
  const client = getGeminiClient();
  
  // Gemini usa 'model' en lugar de 'assistant' para el rol del asistente
  const response = await client.models.generateContent({
    model: MODEL,
    config: {
      systemInstruction: system,
      maxOutputTokens:   maxTokens,
      temperature:       0.7,
    },
    contents: messages.map(m => ({
      role:  m.role,
      parts: [{ text: m.content }],
    })),
  });

  const text           = response.text ?? '';
  const usageMetadata  = response.usageMetadata ?? {};
  
  return {
    text,
    usage: {
      input_tokens:  usageMetadata.promptTokenCount    ?? 0,
      output_tokens: usageMetadata.candidatesTokenCount ?? 0,
      continuations: 0,
    },
  };
}
```

**Nota sobre mensajes:** Las rutas actuales envían `messages` en formato Anthropic
(`role: 'user'|'assistant'`). Al llamar Gemini, mapear `'assistant'` → `'model'`.

---

## Archivo 3: `next_app/lib/interpretation-logger.ts` (modificar)

Agregar campo `provider` al `LogEntry`:

```typescript
// ANTES:
export interface LogEntry {
  route:         string;
  eventType:     string;
  inputTokens:   number;
  outputTokens:  number;
  costUsd:       number;
  continuations: number;
  userId?:       string;
  chartKey?:     string;
  lang?:         string;
  condition:     'A';
}

// DESPUÉS: agregar provider + pricing condicional
export interface LogEntry {
  route:         string;
  eventType:     string;
  provider:      'anthropic' | 'gemini';   // ← nuevo
  model:         string;                    // ← nuevo: 'claude-sonnet-4-6' | 'gemini-2.0-flash'
  inputTokens:   number;
  outputTokens:  number;
  costUsd:       number;
  continuations: number;
  userId?:       string;
  chartKey?:     string;
  lang?:         string;
  condition:     'A';
}
```

Actualizar el cálculo de costo en `logInterpretation()`:

```typescript
// Pricing por modelo (mayo 2026)
const PRICING: Record<string, { input: number; output: number }> = {
  'claude-sonnet-4-6':   { input: 3.00,    output: 15.00   },  // $/M tokens
  'gemini-2.0-flash':    { input: 0.075,   output: 0.30    },  // $/M tokens
};

export function logInterpretation(entry: LogEntry): void {
  const pricing = PRICING[entry.model] ?? PRICING['claude-sonnet-4-6'];
  const cost = (entry.inputTokens  / 1_000_000) * pricing.input
             + (entry.outputTokens / 1_000_000) * pricing.output;
  // ... resto igual
}
```

---

## Archivo 4: `next_app/lib/usage-limiter.ts` (modificar)

**Solo este cambio** — `applyRateLimit` se mantiene para compatibilidad con rutas no migradas aún:

```typescript
// ANTES:
const FREE_TIER_LIMIT = 3;

// DESPUÉS:
const FREE_TIER_LIMIT = 15;
```

---

## Patrón de migración en cada ruta

### ANTES (patrón actual en cada ruta)

```typescript
// Fragmento típico en cualquier ruta Lilly:
const rateRes = await applyRateLimit(req);
if (rateRes) return rateRes;

const client = getAnthropicClient();
const result = await completeLilly(client, { ...params });

void logInterpretation({
  ...
  // sin provider ni model
});
```

### DESPUÉS (patrón nuevo)

```typescript
import { getAccessContext, rateLimitResponse } from '@/lib/access-context';
import { completeLillyGemini } from '@/lib/gemini-client';
import { LILLY_SYSTEM_PROMPT } from '@/lib/lilly-prompt';

// En el handler POST:
const ctx = await getAccessContext(req);
if (!ctx.allowed) return rateLimitResponse(ctx);

let result: LillyResult;
let modelName: string;

if (ctx.provider === 'gemini') {
  // Convertir messages de Anthropic a Gemini format
  const geminiMessages = (body.messages ?? [])
    .filter((m: { hidden?: boolean }) => !m.hidden)
    .map((m: { role: string; content: string }) => ({
      role:    m.role === 'assistant' ? 'model' : 'user',
      content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
    }));
  
  // Agregar el context block como último mensaje user
  geminiMessages.push({ role: 'user', content: contextBlock });
  
  result    = await completeLillyGemini(LILLY_SYSTEM_PROMPT, geminiMessages, maxTokens);
  modelName = 'gemini-2.0-flash';
} else {
  const client = getAnthropicClient();
  result    = await completeLilly(client, { ...anthropicParams });
  modelName = 'claude-sonnet-4-6';
}

void logInterpretation({
  route:         'planet',       // ← nombre de la ruta
  eventType:     'click_planet',
  provider:      ctx.provider,
  model:         modelName,
  inputTokens:   result.usage.input_tokens,
  outputTokens:  result.usage.output_tokens,
  costUsd:       0,              // overridden inside logInterpretation
  continuations: result.usage.continuations,
  userId:        ctx.userId ?? undefined,
  lang:          body.lang ?? 'es',
  condition:     'A',
});

return NextResponse.json({ response: result.text });
```

---

## Rutas a migrar (11)

Migrar en este orden (de menor a mayor complejidad):

| # | Ruta | Prioridad | Notas |
|---|---|---|---|
| 1 | `screen-open` | Alta | screen_open es la primera llamada — define la impresión inicial |
| 2 | `planet` | Alta | Más frecuente en producción |
| 3 | `transit` | Alta | — |
| 4 | `technique` | Media | — |
| 5 | `house` | Media | — |
| 6 | `sky` | Media | — |
| 7 | `domain` | Media | — |
| 8 | `city` | Media | — |
| 9 | `solar-return` | Baja | — |
| 10 | `mundana` | Baja | Funciona sin carta natal — `ctx.userId` puede ser null |
| 11 | `chat` | Baja | Maneja historial largo — verificar que Gemini acepta el context size |

---

## Variables de entorno

```bash
# Agregar en next_app/.env.local
GEMINI_API_KEY=AIza...

# En Cloud Run (gcloud run services update abu-oracle-app --update-env-vars):
GEMINI_API_KEY=AIza...
```

`ANTHROPIC_API_KEY` ya está configurada — no tocar.

---

## TypeScript check

```bash
cd d:/projects/ai-oracle/next_app
npx tsc --noEmit
```

No debe haber errores nuevos en los archivos tocados.

---

## Criterios de aceptación

- [ ] `getAccessContext(req)` retorna `provider: 'gemini'` para usuarios free
- [ ] `getAccessContext(req)` retorna `provider: 'anthropic'` para usuarios Genesis
- [ ] `rateLimitResponse` devuelve 429 con mensaje en español
- [ ] `completeLillyGemini` retorna `LillyResult` bien formado
- [ ] `logInterpretation` incluye `provider` y `model` en el documento Firestore
- [ ] `FREE_TIER_LIMIT` actualizado a 15 en `usage-limiter.ts`
- [ ] Al menos 3 rutas migradas al nuevo patrón y probadas con QA-C01 smoke test
- [ ] `npx tsc --noEmit` sin errores nuevos

---

## Lo que NO hace este spec

- **NO** elimina `applyRateLimit()` — se mantiene para compatibilidad durante la migración
- **NO** cambia el comportamiento para usuarios Genesis — siguen usando Sonnet siempre
- **NO** implementa streaming para Gemini — respuesta completa igual que Anthropic
- **NO** agrega Gemini al Abu Engine — solo frontend Next.js

---

## Commit sugerido

```
feat(finops): Gemini free tier routing + provider-aware logger (FI-C01)

- lib/access-context.ts: getAccessContext() → { userId, plan, paying, provider, allowed }
- lib/gemini-client.ts: completeLillyGemini() wrapping @google/genai
- lib/interpretation-logger.ts: provider + model fields, per-model pricing
- lib/usage-limiter.ts: FREE_TIER_LIMIT 3 → 15
- Migrated routes: screen-open, planet, transit (3 of 11)
```
