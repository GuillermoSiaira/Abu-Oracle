import { getAdminDb } from './firebase-admin';

// Sonnet 4.6 pricing (May 2026)
const PRICE_INPUT_PER_M = 3.00;
const PRICE_OUTPUT_PER_M = 15.00;

export interface LogEntry {
  route: string;
  eventType: string;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  continuations: number;
  userId?: string;
  chartKey?: string;
  lang?: string;
  condition: 'A';
}

export function chartKeyFromBirthData(birthData: unknown): string | undefined {
  if (!birthData || typeof birthData !== 'object') return undefined;

  const data = birthData as Record<string, unknown>;
  const date = data.birthDate ?? data.date;
  const lat = data.lat ?? data.latitude;
  const lon = data.lon ?? data.longitude;

  if (date == null || lat == null || lon == null) return undefined;
  return `${date}|${lat}|${lon}`;
}

/**
 * Fire-and-forget: write one baseline interpretation log to Firestore.
 * Non-fatal: any error is swallowed so Lilly is never blocked.
 */
export function logInterpretation(entry: LogEntry): void {
  const cost =
    (entry.inputTokens / 1_000_000) * PRICE_INPUT_PER_M +
    (entry.outputTokens / 1_000_000) * PRICE_OUTPUT_PER_M;

  const doc = Object.fromEntries(
    Object.entries({
      ...entry,
      costUsd: cost,
      timestamp: new Date().toISOString(),
      condition: 'A' as const,
    }).filter(([, value]) => value !== undefined),
  );

  void (async () => {
    try {
      await getAdminDb().collection('kg_baseline_logs').add(doc);
    } catch (err: unknown) {
      console.error('[interpretation-logger] Firestore write failed:', err);
    }
  })();
}
