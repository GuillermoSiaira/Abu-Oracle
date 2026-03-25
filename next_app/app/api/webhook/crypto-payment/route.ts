import { createHmac } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { provisionUser } from "@/lib/provision-user";
import { getAdminDb } from "@/lib/firebase-admin";

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
  rawContract?: { address: string };
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
// Look up email from pending_payments by wallet address
// ---------------------------------------------------------------------------
async function resolveEmail(walletAddress: string, txHash: string): Promise<string> {
  const snapshot = await getAdminDb()
    .collection("pending_payments")
    .where("wallet_address", "==", walletAddress.toLowerCase())
    .get();

  const pendingDocs = snapshot.docs.filter((d) => d.data().status === "pending");
  if (pendingDocs.length > 0) {
    const doc = pendingDocs.sort((a, b) =>
      b.data().created_at.localeCompare(a.data().created_at)
    )[0];
    const email = doc.data().email as string;
    await doc.ref.update({
      status: "matched",
      matched_at: new Date().toISOString(),
      tx_hash: txHash,
    });
    console.log(`[crypto-webhook] Matched wallet ${walletAddress} → email ${email}`);
    return email;
  }

  const fallback = `${walletAddress.toLowerCase()}@abu-oracle.com`;
  console.warn(
    `[crypto-webhook] No pending_payment found for wallet ${walletAddress} — using fallback email`
  );
  return fallback;
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

  const validTxs = activity.filter(
    (tx) =>
      tx.asset === "USDC" &&
      tx.toAddress?.toLowerCase() === SAFE_WALLET &&
      tx.value >= GENESIS_PRICE_USDC
  );

  console.log(`[crypto-webhook] activities: ${activity.length}, valid USDC txs: ${validTxs.length}`);
  activity.forEach((tx) => {
    console.log(`[crypto-webhook] tx: asset=${tx.asset} value=${tx.value} to=${tx.toAddress}`);
  });

  if (validTxs.length === 0) {
    return NextResponse.json({ received: true, processed: 0 });
  }

  const results: Array<{ wallet: string; tx: string; status: string }> = [];

  for (const tx of validTxs) {
    try {
      const email = await resolveEmail(tx.fromAddress, tx.hash);
      await provisionUser({
        email,
        plan: "genesis",
        wallet_address: tx.fromAddress.toLowerCase(),
        tx_hash: tx.hash,
      });
      results.push({ wallet: tx.fromAddress, tx: tx.hash, status: "ok" });
    } catch (err) {
      console.error(`[crypto-webhook] Failed for ${tx.fromAddress}:`, err);
      results.push({ wallet: tx.fromAddress, tx: tx.hash, status: "error" });
    }
  }

  return NextResponse.json({ received: true, processed: results.length, results });
}
