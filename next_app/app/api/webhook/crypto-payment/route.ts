import { createHmac } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { v4 as uuidv4 } from "uuid";
import { adminAuth, adminDb } from "@/lib/firebase-admin";

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
  const snapshot = await adminDb
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
    await adminAuth.getUserByEmail(email);
    console.log(`[crypto-webhook] User already exists for wallet ${walletAddress} — skipping`);
    return;
  } catch {
    // getUserByEmail throws if not found — proceed with creation
  }

  // Create Firebase Auth user
  const userRecord = await adminAuth.createUser({
    email,
    password,
    displayName: walletAddress,
    emailVerified: false,
  });

  // Create Firestore document
  await adminDb.collection("users").doc(userRecord.uid).set({
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
        subject: "Abu Oracle — Acceso Genesis activado ♃ ♄",
        html: `
          <p>Bienvenido a <strong>Abu Oracle</strong>.</p>
          <p>Tu acceso Genesis está activo.</p>
          <p><strong>Email:</strong> ${email}<br/>
          <strong>Contraseña temporal:</strong> ${password}</p>
          <p>Accedé en: <a href="https://app.abu-oracle.com">app.abu-oracle.com</a></p>
          <p>Cambiá la contraseña en tu primer login.</p>
          <p>Cupo Genesis: acceso de por vida · todas las features futuras incluidas.</p>
          <p>— El equipo de Abu Oracle</p>
        `,
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
