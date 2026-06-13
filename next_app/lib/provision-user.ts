import { v4 as uuidv4 } from "uuid";
import { randomBytes } from "crypto";
import { getAdminAuth, getAdminDb } from "@/lib/firebase-admin";

export type Plan = "genesis" | "monthly" | "annual";

const QUOTA_LIMITS: Record<Plan, number> = {
  genesis: 10000,
  monthly: 1000,
  annual: 10000,
};

interface ProvisionOptions {
  email: string;
  plan: Plan;
  wallet_address?: string;
  tx_hash?: string;
  paddle_transaction_id?: string;
  paddle_subscription_id?: string;
}

export interface ProvisionResult {
  uid: string;
  email: string;
  created: boolean;
}

/**
 * Creates a Firebase Auth user + Firestore document and sends a welcome email.
 * Idempotent: if the user already exists, returns created=false and skips provisioning.
 */
export async function provisionUser(opts: ProvisionOptions): Promise<ProvisionResult> {
  const { email, plan, ...meta } = opts;

  // Idempotency: skip if user already exists
  try {
    const existing = await getAdminAuth().getUserByEmail(email);
    console.log(`[provision-user] User already exists: uid=${existing.uid} email=${email}`);
    return { uid: existing.uid, email, created: false };
  } catch {
    // getUserByEmail throws auth/user-not-found — proceed with creation
  }

  const password = uuidv4();

  const userRecord = await getAdminAuth().createUser({
    email,
    password,
    emailVerified: false,
  });

  const apiKey = "ak_" + randomBytes(24).toString("hex");

  await getAdminDb()
    .collection("users")
    .doc(userRecord.uid)
    .set({
      uid: userRecord.uid,
      email,
      api_key: apiKey,
      plan,
      quota_used: 0,
      quota_limit: QUOTA_LIMITS[plan],
      genesis_member: plan === "genesis",
      payment_verified: true,
      created_at: new Date().toISOString(),
      ...meta,
    });

  await sendWelcomeEmail(email, password, plan, apiKey);

  console.log(
    `[provision-user] Provisioned: uid=${userRecord.uid} email=${email} plan=${plan}`
  );
  return { uid: userRecord.uid, email, created: true };
}

// ---------------------------------------------------------------------------
// Welcome email
// ---------------------------------------------------------------------------

const PLAN_LABELS: Record<Plan, string> = {
  genesis: "Genesis · Lifetime",
  monthly: "Monthly",
  annual: "Annual",
};

async function sendWelcomeEmail(email: string, password: string, plan: Plan, apiKey: string) {
  const resendKey = process.env.RESEND_API_KEY;
  if (!resendKey) return;
  try {
    const { Resend } = await import("resend");
    const resend = new Resend(resendKey);
    const planLabel = PLAN_LABELS[plan];
    await resend.emails.send({
      from: "Abu Oracle <noreply@abu-oracle.com>",
      to: email,
      subject: "Abu Oracle — Acceso activado ♃",
      html: buildWelcomeHtml(email, password, planLabel, apiKey),
    });
  } catch (err) {
    // Non-fatal — user was already created in Firebase
    console.error("[provision-user] Resend error:", err);
  }
}

function buildWelcomeHtml(email: string, password: string, planLabel: string, apiKey: string): string {
  return `<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#09090b;font-family:'Georgia',serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#09090b;padding:48px 16px;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="background:#111113;border:1px solid #292524;border-radius:12px;overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#1c1108 0%,#0f0a04 100%);padding:40px 40px 32px;text-align:center;border-bottom:1px solid #292524;">
            <div style="font-size:28px;letter-spacing:0.25em;color:#fbbf24;font-weight:normal;margin-bottom:8px;">ABU ORACLE</div>
            <div style="font-size:12px;letter-spacing:0.3em;color:#78716c;text-transform:uppercase;">Astrological Intelligence Engine</div>
          </td>
        </tr>
        <tr>
          <td style="padding:40px;">
            <p style="margin:0 0 24px;font-size:17px;color:#e7e5e4;line-height:1.6;">
              Tu acceso <strong style="color:#fbbf24;">${planLabel}</strong> está activo.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f10;border:1px solid #292524;border-radius:8px;margin-bottom:32px;">
              <tr>
                <td style="padding:20px 24px;">
                  <div style="font-size:10px;letter-spacing:0.2em;color:#78716c;text-transform:uppercase;margin-bottom:16px;">Credenciales de acceso</div>
                  <div style="margin-bottom:12px;">
                    <span style="font-size:11px;color:#57534e;display:block;margin-bottom:2px;">Email</span>
                    <span style="font-size:14px;color:#e7e5e4;font-family:monospace;">${email}</span>
                  </div>
                  <div>
                    <span style="font-size:11px;color:#57534e;display:block;margin-bottom:2px;">Contraseña temporal</span>
                    <span style="font-size:14px;color:#fbbf24;font-family:monospace;">${password}</span>
                  </div>
                </td>
              </tr>
            </table>
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f10;border:1px solid #292524;border-radius:8px;margin-bottom:32px;">
              <tr>
                <td style="padding:20px 24px;">
                  <div style="font-size:10px;letter-spacing:0.2em;color:#78716c;text-transform:uppercase;margin-bottom:16px;">Tu API key + config MCP</div>
                  <div>
                    <span style="font-size:11px;color:#57534e;display:block;margin-bottom:2px;">API Key</span>
                    <span style="font-size:14px;color:#e7e5e4;font-family:monospace;">${apiKey}</span>
                  </div>
                </td>
              </tr>
            </table>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
              <tr>
                <td align="center">
                  <a href="https://app.abu-oracle.com/auth/login"
                     style="display:inline-block;background:#d97706;color:#fff;text-decoration:none;font-size:14px;font-family:sans-serif;font-weight:600;letter-spacing:0.05em;padding:14px 36px;border-radius:6px;">
                    Acceder a Abu Oracle →
                  </a>
                </td>
              </tr>
            </table>
            <p style="margin:0 0 8px;font-size:12px;color:#57534e;line-height:1.6;font-family:sans-serif;">
              Para cambiar tu contraseña: en la pantalla de login, usá <em>¿Olvidaste tu contraseña?</em>
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 40px;border-top:1px solid #1c1917;text-align:center;">
            <p style="margin:0;font-size:11px;color:#44403c;font-family:sans-serif;line-height:1.6;">
              Abu Oracle · ${planLabel} · <a href="https://abu-oracle.com" style="color:#78716c;text-decoration:none;">abu-oracle.com</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
}
