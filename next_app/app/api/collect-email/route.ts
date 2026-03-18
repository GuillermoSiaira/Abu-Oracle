import { NextRequest, NextResponse } from "next/server";
import { adminDb } from "@/lib/firebase-admin";

const CORS = {
  "Access-Control-Allow-Origin": "https://abu-oracle.com",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS });
}

export async function POST(req: NextRequest) {
  let body: { email?: unknown; wallet_address?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400, headers: CORS });
  }

  const email =
    typeof body.email === "string" ? body.email.trim().toLowerCase() : null;
  const wallet =
    typeof body.wallet_address === "string"
      ? body.wallet_address.toLowerCase()
      : null;

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: "invalid email" }, { status: 400, headers: CORS });
  }

  await adminDb.collection("pending_payments").add({
    email,
    wallet_address: wallet,
    created_at: new Date().toISOString(),
    status: "pending",
  });

  return NextResponse.json({ ok: true }, { headers: CORS });
}
