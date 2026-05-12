import { NextRequest, NextResponse } from 'next/server';
import { Resend } from 'resend';
import { getAdminDb } from '@/lib/firebase-admin';
import { getUserIdFromRequest } from '@/lib/get-user-id';

const ADMIN_UID = 'xJhOVmVFRUXoRBRGK6mJWyMeZOu1';
const ADMIN_EMAIL = 'guillermosiaira@gmail.com';
const HEALTH_SECRET = process.env.HEALTH_CHECK_SECRET ?? '';
const RESEND_API_KEY = process.env.RESEND_API_KEY ?? '';

interface Alert {
  condition: string;
  severity: 'high' | 'medium';
  message: string;
  detail?: string;
}

interface HealthResult {
  ok: boolean;
  timestamp: string;
  alerts: Alert[];
  checks: Record<string, 'ok' | 'alert' | 'error'>;
}

interface CheckResult {
  key: string;
  status: 'ok' | 'alert' | 'error';
  alert: Alert | null;
}

async function isAuthorized(req: NextRequest): Promise<boolean> {
  if (process.env.NODE_ENV === 'development') {
    const host = req.nextUrl.hostname;
    if (host === 'localhost' || host === '127.0.0.1') return true;
  }

  const userId = await getUserIdFromRequest(req).catch(() => null);
  if (userId === ADMIN_UID) return true;

  const secret = req.headers.get('x-health-secret');
  return Boolean(HEALTH_SECRET && secret === HEALTH_SECRET);
}

function ok(key: string): CheckResult {
  return { key, status: 'ok', alert: null };
}

function alert(key: string, value: Alert): CheckResult {
  return { key, status: 'alert', alert: value };
}

function error(key: string, err: unknown): CheckResult {
  console.error(`[health] ${key} check failed:`, err);
  return { key, status: 'error', alert: null };
}

async function checkErrorRate(db: FirebaseFirestore.Firestore): Promise<CheckResult> {
  const key = 'error_rate';
  try {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    const [callsSnap, errorsSnap] = await Promise.all([
      db.collection('kg_baseline_logs').where('timestamp', '>=', oneHourAgo).count().get(),
      db.collection('lilly_errors').where('timestamp', '>=', oneHourAgo).count().get(),
    ]);

    const calls = callsSnap.data().count;
    const errors = errorsSnap.data().count;

    if (calls > 0 && errors / calls > 0.15) {
      return alert(key, {
        condition: 'high_error_rate',
        severity: 'high',
        message: `Error rate ${Math.round((errors / calls) * 100)}% en la ultima hora`,
        detail: `${errors} errores de ${calls} llamadas`,
      });
    }

    return ok(key);
  } catch (err) {
    return error(key, err);
  }
}

async function checkVertexQuota(db: FirebaseFirestore.Firestore): Promise<CheckResult> {
  const key = 'vertex_quota';
  try {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    const snap = await db.collection('lilly_errors')
      .where('timestamp', '>=', oneHourAgo)
      .limit(100)
      .get();

    const count = snap.docs.filter((doc) => doc.data().error_source === 'vertex').length;
    if (count >= 3) {
      return alert(key, {
        condition: 'vertex_quota',
        severity: 'high',
        message: `${count} errores Vertex en la ultima hora`,
        detail: 'Posible quota exhausta en us-east5.',
      });
    }

    return ok(key);
  } catch (err) {
    return error(key, err);
  }
}

async function checkMaxTokensAbuse(db: FirebaseFirestore.Firestore): Promise<CheckResult> {
  const key = 'max_tokens';
  try {
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    const snap = await db.collection('lilly_usage_log')
      .where('created_at', '>=', oneDayAgo)
      .get();

    const docs = snap.docs.map((doc) => doc.data());
    const total = docs.length;
    const withContinuations = docs.filter((doc) => {
      const continuations = typeof doc.continuations === 'number' ? doc.continuations : 0;
      return continuations > 0;
    }).length;

    if (total > 10 && withContinuations / total > 0.20) {
      return alert(key, {
        condition: 'max_tokens_abuse',
        severity: 'medium',
        message: `${Math.round((withContinuations / total) * 100)}% de llamadas con continuaciones en 24h`,
        detail: 'Revisar max_tokens por ruta en Panoptikon/FinOps.',
      });
    }

    return ok(key);
  } catch (err) {
    return error(key, err);
  }
}

async function checkSystemSilent(db: FirebaseFirestore.Firestore): Promise<CheckResult> {
  const key = 'system_silent';
  try {
    const utcHour = new Date().getUTCHours();
    if (utcHour < 10 || utcHour > 22) return ok(key);

    const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString();
    const snap = await db.collection('kg_baseline_logs')
      .where('timestamp', '>=', sixHoursAgo)
      .count()
      .get();

    if (snap.data().count === 0) {
      return alert(key, {
        condition: 'system_silent',
        severity: 'medium',
        message: 'Sin llamadas Lilly en las ultimas 6 horas',
        detail: 'Posible problema de conectividad, auth o deploy.',
      });
    }

    return ok(key);
  } catch (err) {
    return error(key, err);
  }
}

async function checkMundanaStale(): Promise<CheckResult> {
  return ok('mundana');
}

async function sendAlertEmail(alerts: Alert[]): Promise<void> {
  if (!RESEND_API_KEY || alerts.length === 0) return;

  try {
    const resend = new Resend(RESEND_API_KEY);
    const highAlerts = alerts.filter((item) => item.severity === 'high');
    const subject = highAlerts.length > 0
      ? `Abu Oracle - ${highAlerts.length} alerta(s) critica(s)`
      : `Abu Oracle - ${alerts.length} alerta(s) media(s)`;

    const body = [
      '<h2>Panoptikon - Health Check</h2>',
      `<p><strong>Timestamp:</strong> ${new Date().toISOString()}</p>`,
      ...alerts.map((item) => `
        <div style="margin:12px 0;padding:8px;border-left:3px solid ${item.severity === 'high' ? '#ef4444' : '#f59e0b'}">
          <strong>${item.severity.toUpperCase()} - ${item.condition}</strong><br/>
          ${item.message}<br/>
          ${item.detail ? `<small>${item.detail}</small>` : ''}
        </div>
      `),
      '<hr/><p><small>Abu Oracle Panoptikon - app.abu-oracle.com/admin</small></p>',
    ].join('\n');

    await resend.emails.send({
      from: 'panoptikon@abu-oracle.com',
      to: ADMIN_EMAIL,
      subject,
      html: body,
    });
  } catch (err) {
    console.error('[health] Failed to send alert email:', err);
  }
}

export async function GET(req: NextRequest) {
  if (!await isAuthorized(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
  }

  const db = getAdminDb();
  const results = await Promise.all([
    checkErrorRate(db),
    checkVertexQuota(db),
    checkMaxTokensAbuse(db),
    checkSystemSilent(db),
    checkMundanaStale(),
  ]);

  const alerts = results
    .map((result) => result.alert)
    .filter((item): item is Alert => item !== null);

  const shouldNotify = req.nextUrl.searchParams.get('notify') !== '0';
  if (shouldNotify && alerts.length > 0) {
    void sendAlertEmail(alerts);
  }

  const checks = Object.fromEntries(
    results.map((result) => [result.key, result.status]),
  ) as HealthResult['checks'];

  const result: HealthResult = {
    ok: alerts.length === 0,
    timestamp: new Date().toISOString(),
    alerts,
    checks,
  };

  return NextResponse.json(result, {
    status: alerts.some((item) => item.severity === 'high') ? 503 : 200,
  });
}
