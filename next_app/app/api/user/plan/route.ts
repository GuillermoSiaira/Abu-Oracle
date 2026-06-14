import { NextResponse } from "next/server";
import { getUserIdFromRequest } from "@/lib/get-user-id";
import { getAdminDb } from "@/lib/firebase-admin";

/**
 * GET /api/user/plan
 *
 * Returns the authenticated user's plan from Firestore (users/{uid}.plan).
 * The client uses it to gate free-tier features (e.g. proyección futura en
 * birth-data-panel.tsx) without exposing the Firestore doc directly.
 *
 * Auth: Authorization: Bearer <firebase id token>.
 * Non-fatal: responds { plan: null } when unauthenticated, the doc is missing,
 * or Firestore is unavailable — the client treats null as free tier.
 */
export async function GET(req: Request) {
  const uid = await getUserIdFromRequest(req);
  if (!uid) {
    return NextResponse.json({ plan: null }, { status: 200 });
  }

  try {
    const snap = await getAdminDb().collection("users").doc(uid).get();
    const plan = (snap.exists ? snap.get("plan") : null) ?? null;
    return NextResponse.json({ plan }, { status: 200 });
  } catch (err) {
    console.error("[api/user/plan] Firestore error:", err);
    return NextResponse.json({ plan: null }, { status: 200 });
  }
}
