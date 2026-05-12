# OB-C02 — Admin Dashboard: Panoptikon UI

**Fecha:** 2026-05-10  
**Track:** Observability  
**Prioridad:** Alta — primera visualización de datos reales del sistema  
**Depende de:** OB-C01 completado (colección `lilly_errors` debe existir)  
**Independiente de:** QA-C01, FI-C01, KG-C03, MU-C01  

---

## Contexto

Abu Oracle ya escribe a tres colecciones Firestore:

| Colección | Logger | Qué contiene |
|---|---|---|
| `lilly_usage_log` | `lilly-usage-logger.ts` | route, model, tokens, continuations, user_id |
| `kg_baseline_logs` | `interpretation-logger.ts` | route, eventType, provider, model, tokens, costUsd, userId, chartKey, lang |
| `lilly_errors` | `error-tracker.ts` (OB-C01) | route, error_message, error_source, status_code, user_id |

Este spec crea `/admin` — ruta protegida que lee esas tres colecciones y muestra
el estado real del sistema. Sin dashboards de terceros, sin LangSmith, sin LangFuse.

---

## Auth

Solo accesible para el UID administrador:

```typescript
const ADMIN_UID = 'xJhOVmVFRUXoRBRGK6mJWyMeZOu1'; // guillermosiaira@gmail.com
```

Patrón de verificación al inicio del componente (Server Component):

```typescript
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { getAdminAuth } from '@/lib/firebase-admin';

// Verificar sesión — si no es admin, redirect a /chart
const cookieStore = cookies();
const sessionCookie = cookieStore.get('__session')?.value;

// Alternativa más simple: leer el header Authorization desde un Client Component
// que hace fetch a /api/admin/data — ver implementación abajo
```

**Nota de implementación**: dado que Next.js App Router con Firebase Auth usa
client-side auth (no session cookies server-side), la forma más directa es:

1. `app/admin/page.tsx` es un **Client Component** (`'use client'`)
2. Usa `useAuth()` del contexto Firebase para obtener el UID actual
3. Si `user?.uid !== ADMIN_UID` → `router.push('/chart')`
4. Hace fetch a `/api/admin/data?range=7d` con el Bearer token del usuario
5. `/api/admin/data` verifica el UID server-side → devuelve los datos

---

## Archivo 1: `next_app/app/api/admin/data/route.ts` (nuevo)

```typescript
// GET /api/admin/data?range=1d|7d|30d
// Protected: solo ADMIN_UID

import { NextRequest, NextResponse } from 'next/server';
import { getAdminDb } from '@/lib/firebase-admin';
import { getUserIdFromRequest } from '@/lib/get-user-id';

const ADMIN_UID = 'xJhOVmVFRUXoRBRGK6mJWyMeZOu1';

export async function GET(req: NextRequest) {
  const userId = await getUserIdFromRequest(req).catch(() => null);
  if (userId !== ADMIN_UID) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
  }

  const range = req.nextUrl.searchParams.get('range') ?? '7d';
  const days  = range === '1d' ? 1 : range === '30d' ? 30 : 7;
  const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

  const db = getAdminDb();

  // Query paralela a las tres colecciones
  const [logsSnap, errorsSnap] = await Promise.all([
    db.collection('kg_baseline_logs')
      .where('timestamp', '>=', since)
      .orderBy('timestamp', 'desc')
      .limit(500)
      .get(),
    db.collection('lilly_errors')
      .where('timestamp', '>=', since)
      .orderBy('timestamp', 'desc')
      .limit(100)
      .get(),
  ]);

  const logs   = logsSnap.docs.map(d => d.data());
  const errors = errorsSnap.docs.map(d => d.data());

  // Aggregaciones server-side (no mandar documentos raw al cliente)
  
  // 1. Costo total y por ruta
  const costByRoute: Record<string, { calls: number; costUsd: number; continuations: number }> = {};
  let totalCost = 0;
  for (const log of logs) {
    const r = log.route as string ?? 'unknown';
    if (!costByRoute[r]) costByRoute[r] = { calls: 0, costUsd: 0, continuations: 0 };
    costByRoute[r].calls++;
    costByRoute[r].costUsd += (log.costUsd as number) ?? 0;
    costByRoute[r].continuations += (log.continuations as number) ?? 0;
    totalCost += (log.costUsd as number) ?? 0;
  }

  // 2. Distribución de eventos
  const eventDist: Record<string, number> = {};
  for (const log of logs) {
    const e = log.eventType as string ?? 'unknown';
    eventDist[e] = (eventDist[e] ?? 0) + 1;
  }

  // 3. Usuarios únicos
  const uniqueUsers = new Set(logs.map(l => l.userId).filter(Boolean)).size;

  // 4. Max tokens hits (continuations > 0)
  const maxTokensHits = logs.filter(l => ((l.continuations as number) ?? 0) > 0).length;

  // 5. Errores recientes (últimos 20)
  const recentErrors = errors.slice(0, 20).map(e => ({
    timestamp:    e.timestamp,
    route:        e.route,
    error_source: e.error_source,
    error_message: (e.error_message as string ?? '').slice(0, 120),
    user_id:      e.user_id,
  }));

  // 6. Error breakdown por source
  const errorsBySource: Record<string, number> = {};
  for (const e of errors) {
    const src = e.error_source as string ?? 'unknown';
    errorsBySource[src] = (errorsBySource[src] ?? 0) + 1;
  }

  return NextResponse.json({
    range,
    since,
    summary: {
      totalCalls:    logs.length,
      totalErrors:   errors.length,
      totalCostUsd:  Math.round(totalCost * 10000) / 10000,
      uniqueUsers,
      maxTokensHits,
      errorRate:     logs.length > 0 
        ? Math.round((errors.length / logs.length) * 1000) / 10 
        : 0,
    },
    costByRoute: Object.entries(costByRoute)
      .sort((a, b) => b[1].costUsd - a[1].costUsd)
      .map(([route, data]) => ({ route, ...data, costUsd: Math.round(data.costUsd * 10000) / 10000 })),
    eventDist: Object.entries(eventDist)
      .sort((a, b) => b[1] - a[1]),
    recentErrors,
    errorsBySource,
  });
}
```

---

## Archivo 2: `next_app/app/admin/page.tsx` (nuevo)

### Estructura del componente

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { getAbuAuthHeaders } from '@/lib/abu-auth';

const ADMIN_UID = 'xJhOVmVFRUXoRBRGK6mJWyMeZOu1';

type Range = '1d' | '7d' | '30d';
```

### Secciones a renderizar (en orden)

**Header**
```
PANOPTIKON — Abu Oracle
[1d] [7d] [30d]   ← botones de rango activos
Desde: {since} · Actualizado: {now}
```

**Panel 1 — Resumen ejecutivo (6 cards en grilla 3×2)**
```
Total llamadas    Total errores    Costo USD
{N}               {N} ({rate}%)    ${totalCostUsd}

Usuarios únicos   Max token hits   Costo prom/llamada
{N}               {N}              ${avg}
```

**Panel 2 — Costo por ruta (tabla ordenada por costo desc)**
```
Ruta          Llamadas    Costo USD    Continuaciones    Costo prom
screen-open   {N}         ${X}         {N}               ${avg}
transit       ...
...
```

**Panel 3 — Eventos más disparados (tabla)**
```
Evento            Frecuencia    % del total
screen_open       {N}           {X}%
click_transit     ...
```

**Panel 4 — Errores recientes**
```
Timestamp          Ruta         Fuente        Mensaje (120 chars)
{ISO}              transit      vertex        429 Too Many Requests...
...
```
Si no hay errores: mostrar "Sin errores en el período ✓"

**Panel 5 — Errores por fuente (mini tabla)**
```
Fuente          Cantidad
vertex          {N}
abu_engine      {N}
unknown         {N}
```

### Diseño

- Dark theme consistente con el resto de la app (`bg-slate-900`, `text-slate-100`)
- Sin colores llamativos — solo amber para valores que requieren atención
- Amber: si `errorRate > 10%`, si `maxTokensHits > 5%` de las llamadas
- Rojo: si `totalErrors > 0` en las últimas 24h para errorSource `'vertex'`
- Fuente monospace para números de costo y tokens
- Sin gráficos — tablas son suficientes para este volumen

### Loading / Error states

- Loading: "Cargando datos Panoptikon…" centrado
- Auth check fallido (no admin): redirect inmediato a `/chart`
- API error: mostrar mensaje de error, botón "Reintentar"

---

## Archivos a crear

- `next_app/app/admin/page.tsx`
- `next_app/app/api/admin/data/route.ts`

## Archivos de referencia (leer antes de implementar)

- `next_app/lib/auth-context.tsx` — useAuth hook
- `next_app/lib/abu-auth.ts` — getAbuAuthHeaders()
- `next_app/lib/firebase-admin.ts` — getAdminDb()
- `next_app/lib/get-user-id.ts` — getUserIdFromRequest()
- `next_app/app/finops/page.tsx` — estilo de tabla dark existente (referencia visual)
- `next_app/lib/interpretation-logger.ts` — schema de kg_baseline_logs
- `next_app/lib/error-tracker.ts` — schema de lilly_errors (creado en OB-C01)

---

## TypeScript check

```bash
cd d:/projects/ai-oracle/next_app
npx tsc --noEmit
```

---

## Criterios de aceptación

- [ ] `GET /api/admin/data` devuelve 403 para cualquier UID distinto al admin
- [ ] `GET /api/admin/data?range=7d` devuelve JSON con los 6 campos (summary, costByRoute, eventDist, recentErrors, errorsBySource, range)
- [ ] `/admin` redirige a `/chart` si el usuario logueado no es el admin UID
- [ ] `/admin` muestra los 5 paneles con datos reales desde Firestore
- [ ] Los botones 1d / 7d / 30d re-fetchean correctamente
- [ ] `npx tsc --noEmit` sin errores nuevos

---

## Lo que NO hace este spec

- **NO** implementa alertas automáticas — eso es OB-C03
- **NO** modifica los loggers existentes
- **NO** expone datos de usuarios individuales — solo aggregaciones
- **NO** requiere deploy de Abu Engine — es solo Next.js

---

## Commit sugerido

```
feat(observability): Admin dashboard Panoptikon /admin (OB-C02)

- app/admin/page.tsx: dashboard protegido con 5 paneles de métricas
- app/api/admin/data/route.ts: agregaciones server-side desde kg_baseline_logs + lilly_errors
- Auth: solo ADMIN_UID (xJhOVmVFRUXoRBRGK6mJWyMeZOu1)
```
