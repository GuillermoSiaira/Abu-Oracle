import { createHmac, timingSafeEqual } from 'crypto';
import { NextResponse } from 'next/server';
import { Resend } from 'resend';
import { adminAuth, adminDb } from '../../../../lib/firebase-admin';

export const dynamic = 'force-dynamic';

// Paddle-Signature header format: "ts=<unix_timestamp>;h1=<hex_digest>"
// HMAC-SHA256 is computed over "<ts>:<raw_body>" using the webhook secret.
// Multiple signatures can appear separated by semicolons — any valid one is accepted.
function verifyPaddleSignature(rawBody: string, signatureHeader: string, secret: string): boolean {
  // Extract timestamp
  const tsMatch = signatureHeader.match(/ts=(\d+)/);
  if (!tsMatch) return false;
  const ts = tsMatch[1];

  // Build the signed payload
  const signed = `${ts}:${rawBody}`;
  const expected = createHmac('sha256', secret).update(signed, 'utf8').digest('hex');

  // Extract all h1=... values and check any match
  const h1Matches = Array.from(signatureHeader.matchAll(/h1=([0-9a-f]+)/g));
  for (const m of h1Matches) {
    try {
      if (timingSafeEqual(Buffer.from(m[1], 'hex'), Buffer.from(expected, 'hex'))) return true;
    } catch {
      // length mismatch — not a valid hex pair, skip
    }
  }
  return false;
}

function generateTempPassword(): string {
  // 16 random alphanumeric chars
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => chars[b % chars.length]).join('');
}

function generateApiKey(): string {
  return `abu_${crypto.randomUUID().replace(/-/g, '')}`;
}

async function sendWelcomeEmail(
  resend: Resend,
  email: string,
  name: string,
  password: string,
  apiKey: string
): Promise<void> {
  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? 'https://abu-oracle.com';
  await resend.emails.send({
    from: 'Abu Oracle <noreply@abu-oracle.com>',
    to: email,
    subject: 'Abu Oracle — Acceso Genesis activado ♃ ♄',
    html: `
<!DOCTYPE html>
<html>
<body style="font-family: Georgia, serif; background: #0a0a0a; color: #d4a853; padding: 40px; max-width: 600px; margin: 0 auto;">
  <h1 style="font-size: 24px; letter-spacing: 4px; color: #fbbf24;">ABU ORACLE</h1>
  <hr style="border-color: #333; margin: 20px 0;" />
  <p>Bienvenido${name ? ', ' + name : ''}.</p>
  <p>Tu acceso <strong>Genesis</strong> está activo.</p>
  <table style="width:100%; border-collapse:collapse; margin: 24px 0;">
    <tr>
      <td style="padding: 8px 0; color: #888;">Email</td>
      <td style="padding: 8px 0;">${email}</td>
    </tr>
    <tr>
      <td style="padding: 8px 0; color: #888;">Contraseña temporal</td>
      <td style="padding: 8px 0; font-family: monospace; font-size: 16px;">${password}</td>
    </tr>
    <tr>
      <td style="padding: 8px 0; color: #888;">API key</td>
      <td style="padding: 8px 0; font-family: monospace; font-size: 12px;">${apiKey}</td>
    </tr>
  </table>
  <p>
    <a href="${appUrl}/chart"
       style="display:inline-block; padding:12px 28px; background:#92400e; color:#fbbf24; text-decoration:none; letter-spacing:2px; font-size:13px;">
      ACCEDER AL ORACLE
    </a>
  </p>
  <p style="font-size: 12px; color: #555; margin-top: 32px;">
    Cupo Genesis: acceso de por vida · todas las features futuras incluidas.<br/>
    Cambiá tu contraseña en el primer login.
  </p>
  <p style="font-size: 12px; color: #555;">— El equipo de Abu Oracle</p>
</body>
</html>
    `.trim(),
  });
}

export async function POST(req: Request) {
  const webhookSecret = process.env.PADDLE_WEBHOOK_SECRET;
  const resendApiKey = process.env.RESEND_API_KEY;

  if (!webhookSecret) {
    console.error('[webhook/payment] PADDLE_WEBHOOK_SECRET not configured');
    return NextResponse.json({ error: 'Webhook secret not configured' }, { status: 503 });
  }

  // Read raw body for signature verification
  const rawBody = await req.text();
  const signatureHeader = req.headers.get('paddle-signature') ?? '';

  if (!verifyPaddleSignature(rawBody, signatureHeader, webhookSecret)) {
    console.warn('[webhook/payment] Invalid Paddle signature');
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
  }

  let payload: any;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const eventType: string = payload?.event_type ?? '';
  // Only handle completed transactions
  if (eventType !== 'transaction.completed') {
    return NextResponse.json({ received: true, action: 'ignored', event: eventType });
  }

  // Paddle transaction.completed: customer info at data.customer
  const customer = payload?.data?.customer ?? {};
  const email: string = customer.email ?? '';
  const name: string = customer.name ?? '';

  if (!email) {
    console.error('[webhook/payment] No email in Paddle payload', JSON.stringify(payload?.data?.id));
    return NextResponse.json({ error: 'No email in payload' }, { status: 422 });
  }

  // 1. Create Firebase Auth user (or get existing)
  let uid: string;
  const tempPassword = generateTempPassword();
  try {
    const existing = await adminAuth.getUserByEmail(email).catch(() => null);
    if (existing) {
      uid = existing.uid;
      // Update password so the new welcome email is valid
      await adminAuth.updateUser(uid, { password: tempPassword, displayName: name || undefined });
    } else {
      const user = await adminAuth.createUser({
        email,
        password: tempPassword,
        displayName: name || undefined,
        emailVerified: false,
      });
      uid = user.uid;
    }
  } catch (err: any) {
    console.error('[webhook/payment] Firebase Auth error', err.message);
    return NextResponse.json({ error: 'Firebase Auth error', detail: err.message }, { status: 500 });
  }

  // 2. Create / update Firestore document
  const apiKey = generateApiKey();
  const paddleTransactionId = payload?.data?.id ?? null;
  try {
    const userRef = adminDb.collection('users').doc(uid);
    const existing = await userRef.get();
    if (!existing.exists) {
      await userRef.set({
        uid,
        email,
        api_key: apiKey,
        plan: 'genesis',
        quota_used: 0,
        quota_limit: 10000,
        genesis_member: true,
        payment_verified: true,
        created_at: new Date(),
        paddle_transaction_id: paddleTransactionId,
      });
    } else {
      // Already has a document — just mark payment verified
      await userRef.update({
        payment_verified: true,
        plan: 'genesis',
        quota_limit: 10000,
        paddle_transaction_id: paddleTransactionId,
      });
    }
  } catch (err: any) {
    console.error('[webhook/payment] Firestore error', err.message);
    return NextResponse.json({ error: 'Firestore error', detail: err.message }, { status: 500 });
  }

  // 3. Send welcome email (non-fatal — log and continue if Resend not configured)
  if (resendApiKey) {
    try {
      const resend = new Resend(resendApiKey);
      await sendWelcomeEmail(resend, email, name, tempPassword, apiKey);
    } catch (err: any) {
      console.error('[webhook/payment] Resend error', err.message);
      // Don't fail the webhook — user already created
    }
  } else {
    console.warn('[webhook/payment] RESEND_API_KEY not configured — skipping welcome email');
  }

  console.log(`[webhook/payment] Genesis user provisioned: ${email} (${uid})`);
  return NextResponse.json({ received: true, uid, email });
}
