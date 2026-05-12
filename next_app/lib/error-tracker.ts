/**
 * Fire-and-forget error tracking for Lilly routes.
 *
 * Writes only operational failures. Storage failures are swallowed so
 * observability can never block the user-facing response.
 */

import { getAdminDb } from '@/lib/firebase-admin';

export type ErrorSource =
  | 'vertex'
  | 'abu_engine'
  | 'firestore'
  | 'rate_limit'
  | 'unknown';

export interface ErrorEntry {
  route: string;
  eventType: string;
  errorMessage: string;
  errorSource: ErrorSource;
  statusCode?: number | null;
  userId?: string | null;
  stack?: string | null;
}

export function classifyError(err: unknown): ErrorSource {
  const message = err instanceof Error ? err.message : String(err);
  const msg = message.toLowerCase();

  if (msg.includes('429') || msg.includes('rate limit') || msg.includes('quota')) {
    return 'vertex';
  }
  if (msg.includes('abu') || msg.includes('engine') || msg.includes('econnrefused')) {
    return 'abu_engine';
  }
  if (msg.includes('firestore') || msg.includes('firebase')) {
    return 'firestore';
  }
  return 'unknown';
}

export function trackError(entry: ErrorEntry): void {
  void (async () => {
    try {
      const db = getAdminDb();
      await db.collection('lilly_errors').add({
        timestamp: new Date().toISOString(),
        route: entry.route,
        event_type: entry.eventType,
        error_message: entry.errorMessage.slice(0, 500),
        error_source: entry.errorSource,
        status_code: entry.statusCode ?? null,
        user_id: entry.userId ?? null,
        stack: entry.stack ? entry.stack.slice(0, 500) : null,
      });
    } catch (storageErr: unknown) {
      console.error('[error-tracker] Firestore write failed:', storageErr);
    }
  })();
}
