# OB-C03 — Health Check + Alerta Email

**Fecha:** 2026-05-10  
**Track:** Observability  
**Prioridad:** Media — completa el ciclo de observabilidad con notificaciones activas  
**Depende de:** OB-C01 completado (`lilly_errors` activo)  
**Independiente de:** OB-C02 (el dashboard es opcional para que esto funcione)  

---

## Contexto

OB-C01 captura errores en Firestore. OB-C02 los muestra en un dashboard.
Pero ambos son **reactivos**: el operador tiene que ir a mirar.

Este spec agrega un endpoint que puede ser llamado por:
1. El dashboard OB-C02 (al cargar la página — verifica condiciones al instante)
2. Cloud Scheduler (HTTP target) — verificación automática sin intervención humana

Cuando detecta una condición de alerta, envía un email via Resend al operador.

---

## Condiciones de alerta

| Condición | Umbral | Severidad | Descripción |
|---|---|---|---|
| `high_error_rate` | errores > 15% de llamadas en última hora | 🔴 Alta | Sistema degradado |
| `vertex_quota` | ≥ 3 errores con source='vertex' en última hora | 🔴 Alta | Quota Vertex exhausta |
| `system_silent` | 0 llamadas en últimas 6h (horario UTC 10-22) | 🟡 Media | Sistema sin tráfico |
| `max_tokens_abuse` | continuaciones > 20% de llamadas en 24h | 🟡 Media | max_tokens muy bajo en alguna ruta |
| `mundana_stale` | último post > 48h (leer GCS state file) | 🟡 Media | Publisher detenido |

**Fail-open**: si cualquier check falla (Firestore timeout, GCS error) → no enviar alerta,
loggear el error a consola. Las alertas nunca deben romper el sistema.

---

## Archivo: `next_app/app/api/admin/health/route.ts` (nuevo)

```typescript
// GET /api/admin/health
// Verifica condiciones de alerta y envía email si hay alertas activas.
// Protegido: solo ADMIN_UID o llamada sin auth (para Cloud Scheduler via token secreto).

import { NextRequest, NextResponse } from 'next/server';
import { getAdminDb } from '@/lib/firebase-admin';
import { getUserIdFromRequest } from '@/lib/get-user-id';
import { Resend } from 'resend';

const ADMIN_UID         = 'xJhOVmVFRUXoRBRGK6mJWyMeZOu1';
const ADMIN_EMAIL       = 'guillermosiaira@gmail.com';
const HEALTH_SECRET     = process.env.HEALTH_CHECK_SECRET ?? '';  // para Cloud Scheduler
const RESEND_API_KEY    = process.env.RESEND_API_KEY ?? '';

// ── Tipos ────────────────────────────────────────────────────────────────────

interface Alert {
  condition: string;
  severity:  'high' | 'medium';
  message:   string;
  detail?:   string;
}

interface HealthResult {
  ok:        boolean;
  timestamp: string;
  alerts:    Alert[];
  checks:    Record<string, 'ok' | 'alert' | 'error'>;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

async function isAuthorized(req: NextRequest): Promise<boolean> {
  // Opción 1: usuario admin autenticado
  const userId = await getUserIdFromRequest(req).catch(() => null);
  if (userId === ADMIN_UID) return true;
  
  // Opción 2: Cloud Scheduler con secret header
  const secret = req.headers.get('x-health-secret');
  if (HEALTH_SECRET && secret === HEALTH_SECRET) return true;
  
  return false;
}

// ── Checks ───────────────────────────────────────────────────────────────────

async function checkErrorRate(db: FirebaseFirestore.Firestore): Promise<Alert | null> {
  try {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    
    const [callsSnap, errorsSnap] = await Promise.all([
      db.collection('kg_baseline_logs').where('timestamp', '>=', oneHourAgo).count().get(),
      db.collection('lilly_errors').where('timestamp', '>=', oneHourAgo).count().get(),
    ]);
    
    const calls  = callsSnap.data().count;
    const errors = errorsSnap.data().count;
    
    if (calls > 0 && errors / calls > 0.15) {
      return {
        condition: 'high_error_rate',
        severity:  'high',
        message:   `Error rate ${Math.round(errors / calls * 100)}% en la última hora`,
        detail:    `${errors} errores de ${calls} llamadas`,
      };
    }
    return null;
  } catch { return null; }
}

async function checkVertexQuota(db: FirebaseFirestore.Firestore): Promise<Alert | null> {
  try {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    
    const snap = await db.collection('lilly_errors')
      .where('timestamp', '>=', oneHourAgo)
      .where('error_source', '==', 'vertex')
      .count()
      .get();
    
    const count = snap.data().count;
    if (count >= 3) {
      return {
        condition: 'vertex_quota',
        severity:  'high',
        message:   `${count} errores Vertex en la última hora`,
        detail:    'Posible quota exhausta en us-east5. Verificar console.cloud.google.com',
      };
    }
    return null;
  } catch { return null; }
}

async function checkMaxTokensAbuse(db: FirebaseFirestore.Firestore): Promise<Alert | null> {
  try {
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    
    const snap = await db.collection('lilly_usage_log')
      .where('created_at', '>=', oneDayAgo)
      .get();
    
    const docs = snap.docs.map(d => d.data());
    const total = docs.length;
    const withContinuations = docs.filter(d => ((d.continuations as number) ?? 0) > 0).length;
    
    if (total > 10 && withContinuations / total > 0.20) {
      return {
        condition: 'max_tokens_abuse',
        severity:  'medium',
        message:   `${Math.round(withContinuations / total * 100)}% de llamadas con continuaciones en 24h`,
        detail:    'max_tokens demasiado bajo en alguna ruta — revisar /finops',
      };
    }
    return null;
  } catch { return null; }
}

async function checkSystemSilent(db: FirebaseFirestore.Firestore): Promise<Alert | null> {
  try {
    const utcHour = new Date().getUTCHours();
    // Solo alertar entre 10:00 y 22:00 UTC (horario de actividad esperada)
    if (utcHour < 10 || utcHour > 22) return null;
    
    const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString();
    
    const snap = await db.collection('kg_baseline_logs')
      .where('timestamp', '>=', sixHoursAgo)
      .count()
      .get();
    
    if (snap.data().count === 0) {
      return {
        condition: 'system_silent',
        severity:  'medium',
        message:   'Sin llamadas Lilly en las últimas 6 horas',
        detail:    'Posible problema de conectividad o deploy fallido',
      };
    }
    return null;
  } catch { return null; }
}

async function checkMundanaStale(): Promise<Alert | null> {
  try {
    // El state file del mundana publisher está en GCS
    // gs://abu-oracle-predictions/state/last_published.json
    // Leer via fetch al endpoint de Abu Engine si está disponible,
    // o via @google-cloud/storage si está instalado.
    
    // Implementación simplificada: leer variable de entorno MUNDANA_LAST_PUBLISH
    // que el publisher actualiza, o leer desde Firestore si se agrega ese registro.
    
    // Por ahora: skip si no hay forma de leer GCS desde Next.js sin SDK adicional.
    // TODO: cuando MU-C01 esté completo, el publisher puede escribir en Firestore
    // collection 'mundana_state' además de GCS.
    
    return null; // Implementación futura cuando MU-C01 agregue Firestore state
  } catch { return null; }
}

// ── Email ────────────────────────────────────────────────────────────────────

async function sendAlertEmail(alerts: Alert[]): Promise<void> {
  if (!RESEND_API_KEY || alerts.length === 0) return;
  
  try {
    const resend = new Resend(RESEND_API_KEY);
    
    const highAlerts   = alerts.filter(a => a.severity === 'high');
    const mediumAlerts = alerts.filter(a => a.severity === 'medium');
    
    const subject = highAlerts.length > 0
      ? `🔴 Abu Oracle — ${highAlerts.length} alerta(s) crítica(s)`
      : `🟡 Abu Oracle — ${mediumAlerts.length} alerta(s) media(s)`;
    
    const body = [
      `<h2>Panoptikon — Health Check</h2>`,
      `<p><strong>Timestamp:</strong> ${new Date().toISOString()}</p>`,
      ...alerts.map(a => `
        <div style="margin: 12px 0; padding: 8px; border-left: 3px solid ${a.severity === 'high' ? '#ef4444' : '#f59e0b'}">
          <strong>${a.severity === 'high' ? '🔴' : '🟡'} ${a.condition}</strong><br/>
          ${a.message}<br/>
          ${a.detail ? `<small>${a.detail}</small>` : ''}
        </div>
      `),
      `<hr/><p><small>Abu Oracle Panoptikon · app.abu-oracle.com/admin</small></p>`,
    ].join('\n');
    
    await resend.emails.send({
      from:    'panoptikon@abu-oracle.com',
      to:      ADMIN_EMAIL,
      subject,
      html:    body,
    });
  } catch (err) {
    console.error('[health] Failed to send alert email:', err);
  }
}

// ── Handler ──────────────────────────────────────────────────────────────────

export async function GET(req: NextRequest) {
  if (!await isAuthorized(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
  }
  
  const db = getAdminDb();
  
  // Correr todos los checks en paralelo
  const [errorRateAlert, vertexAlert, maxTokensAlert, silentAlert, mundanaAlert] =
    await Promise.all([
      checkErrorRate(db),
      checkVertexQuota(db),
      checkMaxTokensAbuse(db),
      checkSystemSilent(db),
      checkMundanaStale(),
    ]);
  
  const alerts: Alert[] = [
    errorRateAlert,
    vertexAlert,
    maxTokensAlert,
    silentAlert,
    mundanaAlert,
  ].filter((a): a is Alert => a !== null);
  
  // Enviar email si hay alertas (fire-and-forget)
  if (alerts.length > 0) {
    void sendAlertEmail(alerts);
  }
  
  const result: HealthResult = {
    ok:        alerts.length === 0,
    timestamp: new Date().toISOString(),
    alerts,
    checks: {
      error_rate:    errorRateAlert   ? 'alert' : 'ok',
      vertex_quota:  vertexAlert      ? 'alert' : 'ok',
      max_tokens:    maxTokensAlert   ? 'alert' : 'ok',
      system_silent: silentAlert      ? 'alert' : 'ok',
      mundana:       mundanaAlert     ? 'alert' : 'ok',
    },
  };
  
  return NextResponse.json(result, {
    status: alerts.some(a => a.severity === 'high') ? 503 : 200,
  });
}
```

---

## Variables de entorno requeridas

```bash
# Ya existe en Cloud Run:
RESEND_API_KEY=re_...

# Agregar (opcional — para Cloud Scheduler):
HEALTH_CHECK_SECRET=un-string-aleatorio-largo

# En next_app/.env.local para testing local:
HEALTH_CHECK_SECRET=dev-secret
```

---

## Integración con el dashboard OB-C02 (opcional)

Si OB-C02 está implementado, agregar al dashboard:

```typescript
// En app/admin/page.tsx, al cargar:
const healthRes = await fetch('/api/admin/health', { headers: authHeaders });
const health    = await healthRes.json();

// Mostrar banner si hay alertas:
{health.alerts.length > 0 && (
  <div className="bg-red-900/30 border border-red-500/50 rounded p-3 mb-4">
    {health.alerts.map(a => (
      <div key={a.condition} className="text-red-300 text-sm">
        {a.severity === 'high' ? '🔴' : '🟡'} {a.message}
      </div>
    ))}
  </div>
)}
```

---

## Cloud Scheduler (configuración futura — no parte de este spec)

Una vez desplegado, se puede configurar Cloud Scheduler para llamar al endpoint
cada 4 horas sin intervención manual:

```bash
gcloud scheduler jobs create http abu-health-check \
  --schedule="0 */4 * * *" \
  --uri="https://app.abu-oracle.com/api/admin/health" \
  --headers="x-health-secret=HEALTH_CHECK_SECRET_VALUE" \
  --oidc-service-account-email="abu-engine-sa@abu-oracle.iam.gserviceaccount.com" \
  --project=abu-oracle \
  --location=us-central1
```

---

## Archivos a crear

- `next_app/app/api/admin/health/route.ts`

## Archivos de referencia (leer antes de implementar)

- `next_app/lib/firebase-admin.ts` — getAdminDb()
- `next_app/lib/get-user-id.ts` — getUserIdFromRequest()
- `next_app/lib/error-tracker.ts` — schema lilly_errors (OB-C01)
- `next_app/app/api/webhook/crypto-payment/route.ts` — ejemplo de uso de Resend existente

---

## TypeScript check

```bash
cd d:/projects/ai-oracle/next_app
npx tsc --noEmit
```

---

## Criterios de aceptación

- [ ] `GET /api/admin/health` devuelve 403 para requests no autorizados
- [ ] `GET /api/admin/health` devuelve JSON con `{ ok, timestamp, alerts, checks }`
- [ ] Si `lilly_errors` tiene ≥ 3 errores vertex en la última hora → `alerts` incluye `vertex_quota`
- [ ] Si hay alertas, se intenta enviar email via Resend (verificar en dashboard Resend)
- [ ] Con 0 alertas → HTTP 200 · Con alertas high → HTTP 503
- [ ] `npx tsc --noEmit` sin errores nuevos

---

## Lo que NO hace este spec

- **NO** implementa el check de mundana GCS (requiere @google-cloud/storage o cambio en MU-C01)
- **NO** configura Cloud Scheduler (pasos manuales post-deploy)
- **NO** implementa alertas Slack/Telegram — email Resend es suficiente
- **NO** modifica el mundana publisher

---

## Commit sugerido

```
feat(observability): health check endpoint + email alert via Resend (OB-C03)

- app/api/admin/health/route.ts: 5 checks en paralelo → Resend email si hay alertas
- Checks: error_rate, vertex_quota, max_tokens, system_silent, mundana (stub)
- Auth: admin UID o x-health-secret header (para Cloud Scheduler)
```
