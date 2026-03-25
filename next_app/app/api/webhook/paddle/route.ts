import { createHmac, timingSafeEqual } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { provisionUser, Plan } from "@/lib/provision-user";

// ---------------------------------------------------------------------------
// Paddle Billing v2 — signature verification
//
// Header format:  Paddle-Signature: ts=TIMESTAMP;h1=HMAC_SHA256_HEX
// Signed payload: `${ts}:${rawBody}`
// ---------------------------------------------------------------------------
function verifyPaddleSignature(
  rawBody: string,
  header: string,
  secret: string
): boolean {
  // Parse ts and h1 from header
  const parts = Object.fromEntries(
    header.split(";").map((p) => {
      const [k, ...rest] = p.split("=");
      return [k.trim(), rest.join("=").trim()];
    })
  );
  const ts = parts["ts"];
  const h1 = parts["h1"];
  if (!ts || !h1) return false;

  const signed = `${ts}:${rawBody}`;
  const hmac = createHmac("sha256", secret);
  hmac.update(signed, "utf8");
  const digest = hmac.digest("hex");

  // Timing-safe comparison
  try {
    return timingSafeEqual(Buffer.from(digest, "hex"), Buffer.from(h1, "hex"));
  } catch {
    // Buffers differ in length → invalid
    return false;
  }
}

// ---------------------------------------------------------------------------
// Paddle webhook payload types (Billing API v2)
// ---------------------------------------------------------------------------
interface PaddleCustomer {
  email?: string;
  id?: string;
}

interface PaddlePriceItem {
  price?: {
    id?: string;
  };
}

interface PaddleTransactionCompleted {
  event_type: "transaction.completed";
  data: {
    id: string;
    customer_id?: string;
    customer?: PaddleCustomer;
    billing_details?: { email_address?: string };
    items?: PaddlePriceItem[];
  };
}

interface PaddleSubscriptionActivated {
  event_type: "subscription.activated";
  data: {
    id: string;
    customer_id?: string;
    customer?: PaddleCustomer;
    items?: PaddlePriceItem[];
  };
}

type PaddleEvent = PaddleTransactionCompleted | PaddleSubscriptionActivated;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Extract customer email from a Paddle event payload (multiple fallbacks). */
function extractEmail(data: PaddleTransactionCompleted["data"] | PaddleSubscriptionActivated["data"]): string | null {
  // Preferred: customer object embedded in webhook
  const customerEmail = data.customer?.email?.trim().toLowerCase();
  if (customerEmail) return customerEmail;

  // Fallback: billing_details for transaction events
  const billingEmail = (data as PaddleTransactionCompleted["data"]).billing_details?.email_address?.trim().toLowerCase();
  if (billingEmail) return billingEmail;

  return null;
}

/** Determine plan from price ID. Returns null if price ID doesn't match any known plan. */
function resolvePlan(priceId: string | undefined): Plan | null {
  if (!priceId) return null;
  if (priceId === process.env.PADDLE_PRICE_ID_GENESIS) return "genesis";
  if (priceId === process.env.PADDLE_PRICE_ID_ANNUAL)  return "annual";
  if (priceId === process.env.PADDLE_PRICE_ID_MONTHLY) return "monthly";
  return null;
}

function firstPriceId(items: PaddlePriceItem[] | undefined): string | undefined {
  return items?.[0]?.price?.id;
}

// ---------------------------------------------------------------------------
// Route handler
// ---------------------------------------------------------------------------
export async function POST(req: NextRequest) {
  const secret = process.env.PADDLE_WEBHOOK_SECRET;
  if (!secret) {
    console.error("[paddle-webhook] PADDLE_WEBHOOK_SECRET is not set");
    return NextResponse.json({ error: "server misconfiguration" }, { status: 500 });
  }

  const rawBody = await req.text();
  const signatureHeader = req.headers.get("paddle-signature") ?? "";

  if (!verifyPaddleSignature(rawBody, signatureHeader, secret)) {
    console.warn("[paddle-webhook] Invalid signature");
    return NextResponse.json({ error: "invalid signature" }, { status: 401 });
  }

  let event: PaddleEvent;
  try {
    event = JSON.parse(rawBody);
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  const { event_type, data } = event;

  // Only handle the two event types we care about
  if (event_type !== "transaction.completed" && event_type !== "subscription.activated") {
    console.log(`[paddle-webhook] Ignoring event: ${event_type}`);
    return NextResponse.json({ received: true, processed: false });
  }

  const email = extractEmail(data);
  if (!email) {
    console.error(`[paddle-webhook] No email found in ${event_type} payload — data.id=${data.id}`);
    // Return 200 so Paddle doesn't retry — this is a data issue not a server issue
    return NextResponse.json({ received: true, processed: false, reason: "no_email" });
  }

  const priceId = firstPriceId(data.items);
  const plan = resolvePlan(priceId);

  if (!plan) {
    console.warn(
      `[paddle-webhook] Unknown price ID "${priceId}" in ${event_type} — email=${email}. ` +
      "Check PADDLE_PRICE_ID_GENESIS / _MONTHLY / _ANNUAL env vars."
    );
    return NextResponse.json({ received: true, processed: false, reason: "unknown_price_id" });
  }

  const meta =
    event_type === "subscription.activated"
      ? { paddle_subscription_id: data.id }
      : { paddle_transaction_id: data.id };

  try {
    const result = await provisionUser({ email, plan, ...meta });
    console.log(
      `[paddle-webhook] ${event_type} → plan=${plan} email=${email} created=${result.created}`
    );
    return NextResponse.json({ received: true, processed: true, plan, created: result.created });
  } catch (err) {
    console.error(`[paddle-webhook] provisionUser failed for ${email}:`, err);
    // Return 500 so Paddle retries
    return NextResponse.json({ error: "provisioning failed" }, { status: 500 });
  }
}
