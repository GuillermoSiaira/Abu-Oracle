/**
 * get-user-id.ts
 *
 * Extracts the Firebase uid from the Authorization: Bearer <token> header
 * of an incoming Next.js API route request.
 *
 * Returns null (not throws) when:
 *   - No Authorization header is present (dev local without auth)
 *   - Token is invalid or expired
 *   - Firebase Admin SDK is not configured
 *
 * This allows all Lilly routes to be used in dev without auth while
 * silently skipping memory persistence.
 */

import { getAdminAuth } from "@/lib/firebase-admin";

export async function getUserIdFromRequest(req: Request): Promise<string | null> {
  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) return null;

    const token = authHeader.slice(7).trim();
    if (!token) return null;

    const decoded = await getAdminAuth().verifyIdToken(token);
    return decoded.uid ?? null;
  } catch {
    // Invalid token, expired, or Firebase not configured — non-fatal
    return null;
  }
}
