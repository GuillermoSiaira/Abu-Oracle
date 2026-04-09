/**
 * lilly-usage-logger.ts
 *
 * Fire-and-forget: registra tokens consumidos por cada llamada a Lilly.
 * No bloquea la respuesta — los errores de storage son silenciosos.
 *
 * Schema Firestore:
 *   lilly_usage_log/{docId}:
 *     route         string   — nombre de la ruta ('transit', 'planet', …)
 *     model         string   — modelo usado ('claude-sonnet-4-6', …)
 *     input_tokens  number
 *     output_tokens number
 *     continuations number   — 0 = respuesta en un solo turno
 *     user_id       string | null
 *     created_at    string   — ISO 8601
 */

import { getAdminDb } from '@/lib/firebase-admin';
import type { LillyUsage } from '@/lib/lilly-complete';

export function logLillyUsage(
  route:   string,
  model:   string,
  usage:   LillyUsage,
  userId:  string | null,
): void {
  // Fire-and-forget: no await, no throw
  (async () => {
    try {
      const db = getAdminDb();
      await db.collection('lilly_usage_log').add({
        route,
        model,
        input_tokens:  usage.input_tokens,
        output_tokens: usage.output_tokens,
        continuations: usage.continuations,
        user_id:       userId ?? null,
        created_at:    new Date().toISOString(),
      });
    } catch {
      // Silencioso — el logging nunca debe romper la respuesta a Lilly
    }
  })();
}
