import { createHmac } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { v4 as uuidv4 } from "uuid";
import { getAdminAuth, getAdminDb } from "@/lib/firebase-admin";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
const SAFE_WALLET = "0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82".toLowerCase();
const GENESIS_PRICE_USDC = parseFloat(process.env.GENESIS_PRICE_USDC ?? "500");

// ---------------------------------------------------------------------------
// HMAC verification — Alchemy signs with the raw body bytes
// ---------------------------------------------------------------------------
function verifyAlchemySignature(rawBody: string, signature: string, secret: string): boolean {
  const hmac = createHmac("sha256", secret);
  hmac.update(rawBody, "utf8");
  const digest = hmac.digest("hex");
  // Use timing-safe comparison
  if (digest.length !== signature.length) return false;
  let diff = 0;
  for (let i = 0; i < digest.length; i++) {
    diff |= digest.charCodeAt(i) ^ signature.charCodeAt(i);
  }
  return diff === 0;
}

// ---------------------------------------------------------------------------
// Types — Alchemy GraphQL webhook payload (mined-transaction activity)
// ---------------------------------------------------------------------------
interface AlchemyActivity {
  fromAddress: string;
  toAddress: string;
  value: number; // token units already converted by Alchemy (e.g. 500 for 500 USDC)
  hash: string;
  asset: string; // "USDC", "ETH", etc.
  category: string; // "token", "external", etc.
  rawContract?: { address: string }; // ERC-20 contract address (optional, for logs)
}

interface AlchemyWebhookPayload {
  webhookId: string;
  id: string;
  event: {
    network: string;
    activity: AlchemyActivity[];
  };
}

// ---------------------------------------------------------------------------
// Firestore — provision a new Genesis user
// ---------------------------------------------------------------------------
async function provisionGenesisUser(walletAddress: string, txHash: string) {
  // Look up real email from pending_payments (registered before payment)
  let email: string;
  const snapshot = await getAdminDb()
    .collection("pending_payments")
    .where("wallet_address", "==", walletAddress.toLowerCase())
    .get();
  const pendingDocs = snapshot.docs.filter((d) => d.data().status === "pending");
  if (pendingDocs.length > 0) {
    const doc = pendingDocs.sort((a, b) =>
      b.data().created_at.localeCompare(a.data().created_at)
    )[0];
    email = doc.data().email as string;
    await doc.ref.update({ status: "matched", matched_at: new Date().toISOString(), tx_hash: txHash });
    console.log(`[crypto-webhook] Matched wallet ${walletAddress} → email ${email}`);
  } else {
    email = `${walletAddress.toLowerCase()}@abu-oracle.com`;
    console.warn(`[crypto-webhook] No pending_payment found for wallet ${walletAddress} — using fallback email`);
  }

  const password = uuidv4();

  // Idempotency: skip if the user already exists
  try {
    await getAdminAuth().getUserByEmail(email);
    console.log(`[crypto-webhook] User already exists for wallet ${walletAddress} — skipping`);
    return;
  } catch {
    // getUserByEmail throws if not found — proceed with creation
  }

  // Create Firebase Auth user
  const userRecord = await getAdminAuth().createUser({
    email,
    password,
    displayName: walletAddress,
    emailVerified: false,
  });

  // Create Firestore document
  await getAdminDb().collection("users").doc(userRecord.uid).set({
    uid: userRecord.uid,
    email,
    api_key: uuidv4(),
    plan: "genesis",
    quota_used: 0,
    quota_limit: 10000,
    genesis_member: true,
    payment_verified: true,
    wallet_address: walletAddress.toLowerCase(),
    tx_hash: txHash,
    created_at: new Date().toISOString(),
  });

  // Send welcome email if Resend is configured
  const resendKey = process.env.RESEND_API_KEY;
  if (resendKey) {
    try {
      const { Resend } = await import("resend");
      const resend = new Resend(resendKey);
      await resend.emails.send({
        from: "Abu Oracle <noreply@abu-oracle.com>",
        to: email,
        subject: "Abu Oracle — Acceso Genesis activado ♃",
        html: `<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#09090b;font-family:'Georgia',serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#09090b;padding:48px 16px;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="background:#111113;border:1px solid #292524;border-radius:12px;overflow:hidden;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1c1108 0%,#0f0a04 100%);padding:40px 40px 32px;text-align:center;border-bottom:1px solid #292524;">
            <div style="font-size:28px;letter-spacing:0.25em;color:#fbbf24;font-weight:normal;margin-bottom:8px;">ABU ORACLE</div>
            <div style="font-size:12px;letter-spacing:0.3em;color:#78716c;text-transform:uppercase;">Astrological Intelligence Engine</div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px;">

            <p style="margin:0 0 24px;font-size:17px;color:#e7e5e4;line-height:1.6;">
              Tu acceso <strong style="color:#fbbf24;">Genesis</strong> está activo.
            </p>

            <p style="margin:0 0 28px;font-size:14px;color:#a8a29e;line-height:1.7;">
              Sos parte del primer grupo de 100 miembros con acceso de por vida a Abu Oracle — incluyendo todas las features futuras.
            </p>

            <!-- Credentials box -->
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

            <!-- CTA -->
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

        <!-- Footer -->
        <tr>
          <td style="padding:24px 40px;border-top:1px solid #1c1917;text-align:center;">
            <p style="margin:0;font-size:11px;color:#44403c;font-family:sans-serif;line-height:1.6;">
              Abu Oracle · Genesis Member · Acceso de por vida<br>
              <a href="https://abu-oracle.com" style="color:#78716c;text-decoration:none;">abu-oracle.com</a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`,
      });
    } catch (emailErr) {
      // Non-fatal — user was already created in Firebase
      console.error("[crypto-webhook] Resend error:", emailErr);
    }
  }

  console.log(`[crypto-webhook] Genesis user provisioned: uid=${userRecord.uid} wallet=${walletAddress} tx=${txHash}`);
}

// ---------------------------------------------------------------------------
// Route handler
// ---------------------------------------------------------------------------
export async function POST(req: NextRequest) {
  const webhookSecret = process.env.ALCHEMY_WEBHOOK_SECRET;
  if (!webhookSecret) {
    console.error("[crypto-webhook] ALCHEMY_WEBHOOK_SECRET is not set");
    return NextResponse.json({ error: "server misconfiguration" }, { status: 500 });
  }

  // Read raw body (needed for HMAC verification)
  const rawBody = await req.text();
  const signature = req.headers.get("x-alchemy-signature") ?? "";

  if (!verifyAlchemySignature(rawBody, signature, webhookSecret)) {
    console.warn("[crypto-webhook] Invalid signature");
    return NextResponse.json({ error: "invalid signature" }, { status: 401 });
  }

  let payload: AlchemyWebhookPayload;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  const activity: AlchemyActivity[] = payload?.event?.activity ?? [];

  // Filter: incoming USDC transfers to the Safe wallet at or above the Genesis price
  const validTxs = activity.filter(
    (tx) =>
      tx.asset === "USDC" &&
      tx.toAddress?.toLowerCase() === SAFE_WALLET &&
      tx.value >= GENESIS_PRICE_USDC
  );

  console.log(`[crypto-webhook] activities: ${activity.length}, valid USDC txs: ${validTxs.length}`);
  activity.forEach(tx => {
    console.log(`[crypto-webhook] tx: asset=${tx.asset} value=${tx.value} to=${tx.toAddress}`);
  });

  if (validTxs.length === 0) {
    // Could be an outgoing tx or different token — acknowledge and ignore
    return NextResponse.json({ received: true, processed: 0 });
  }

  const results: Array<{ wallet: string; tx: string; status: string }> = [];

  for (const tx of validTxs) {
    try {
      await provisionGenesisUser(tx.fromAddress, tx.hash);
      results.push({ wallet: tx.fromAddress, tx: tx.hash, status: "ok" });
    } catch (err) {
      console.error(`[crypto-webhook] provisionGenesisUser failed for ${tx.fromAddress}:`, err);
      results.push({ wallet: tx.fromAddress, tx: tx.hash, status: "error" });
      // Continue processing other txs — do NOT return non-200 (Alchemy would retry)
    }
  }

  return NextResponse.json({ received: true, processed: results.length, results });
}
