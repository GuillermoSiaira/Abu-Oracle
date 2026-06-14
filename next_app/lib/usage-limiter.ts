/**
 * usage-limiter.ts
 *
 * Rate limiting for Lilly API calls per authenticated user.
 *
 * Schema:
 *   users/{userId}/usage/daily → { date: "YYYY-MM-DD", lilly_calls: number }
 *
 * Behaviour:
 *   - checkAndIncrementDailyUsage(userId) — atomically checks + increments.
 *     Returns true if allowed, false if limit exceeded.
 *     Fail-open on Firestore errors (never blocks on storage issues).
 *   - Call ONLY for authenticated users (userId != null).
 */

import { NextResponse } from "next/server";
import { getAdminDb } from "@/lib/firebase-admin";
import { getUserIdFromRequest } from "@/lib/get-user-id";

export const DAILY_LIMIT = 50;
export const FREE_TIER_LIMIT = 7;

export const LIMIT_MESSAGE =
  "Has alcanzado el límite diario de consultas a Lilly. Vuelve mañana.";
export const FREE_LIMIT_MESSAGE =
  "Has completado tus 7 consultas gratuitas. Para continuar con Lilly, adquirí acceso Genesis en abu-oracle.com";

export async function checkFreeTierUsage(
  userId: string
): Promise<{ allowed: boolean; paying: boolean }> {
  try {
    const db = getAdminDb();
    const userRef = db.collection("users").doc(userId);
    const userSnap = await userRef.get();
    const userData = userSnap.exists ? userSnap.data() : null;

    if (userData?.payment_verified === true) {
      return { allowed: true, paying: true };
    }

    const freeRef = userRef.collection("usage").doc("free_tier");
    return await db.runTransaction(async (tx) => {
      const snap = await tx.get(freeRef);
      const calls = snap.exists ? (snap.data()?.calls ?? 0) : 0;

      if (calls >= FREE_TIER_LIMIT) {
        return { allowed: false, paying: false };
      }

      tx.set(freeRef, { calls: calls + 1 }, { merge: true });
      return { allowed: true, paying: false };
    });
  } catch (err) {
    console.error("[usage-limiter] checkFreeTierUsage error:", err);
    return { allowed: true, paying: false };
  }
}

/**
 * Convenience wrapper: extracts userId from the request, checks + increments
 * free tier and/or daily counter, and returns a ready NextResponse if a limit
 * is hit.
 * Returns null when the call is allowed (route should proceed normally).
 * Unauthenticated requests are not rate-limited (fail-open).
 */
export async function applyRateLimit(req: Request): Promise<NextResponse | null> {
  const userId = await getUserIdFromRequest(req);
  if (!userId) return null; // anonymous — no rate limit applied

  // Operator bypass
  const operatorUid = process.env.OPERATOR_UID;
  if (operatorUid) {
    if (userId === operatorUid) return null;
  } else {
    console.warn("[usage-limiter] OPERATOR_UID not set — operator bypass unavailable");
  }

  const freeTier = await checkFreeTierUsage(userId);
  if (!freeTier.allowed) {
    return NextResponse.json({ response: FREE_LIMIT_MESSAGE });
  }

  if (freeTier.paying) {
    const allowed = await checkAndIncrementDailyUsage(userId);
    if (!allowed) {
      return NextResponse.json({ response: LIMIT_MESSAGE });
    }
  }
  return null;
}

/**
 * Atomically checks the daily Lilly call counter for a user and increments it
 * if under the limit.
 *
 * @returns true  — call is allowed (counter incremented)
 * @returns false — daily limit reached (counter not incremented)
 */
export async function checkAndIncrementDailyUsage(userId: string): Promise<boolean> {
  try {
    const db  = getAdminDb();
    const today = new Date().toISOString().slice(0, 10); // "YYYY-MM-DD"
    const ref = db.collection("users").doc(userId).collection("usage").doc("daily");

    return await db.runTransaction(async (tx) => {
      const snap = await tx.get(ref);

      if (snap.exists) {
        const data = snap.data()!;
        // New day — reset counter
        if (data.date !== today) {
          tx.set(ref, { date: today, lilly_calls: 1 });
          return true;
        }
        // Same day — check limit
        if (data.lilly_calls >= DAILY_LIMIT) {
          return false;
        }
        tx.update(ref, { lilly_calls: data.lilly_calls + 1 });
        return true;
      }

      // First call ever
      tx.set(ref, { date: today, lilly_calls: 1 });
      return true;
    });
  } catch (err) {
    // Fail-open: storage errors must not block Lilly responses
    console.error("[usage-limiter] checkAndIncrementDailyUsage error:", err);
    return true;
  }
}
