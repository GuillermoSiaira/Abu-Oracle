import { getAdminDb } from './firebase-admin';

const PRICING: Record<string, { input: number; output: number }> = {
  'claude-sonnet-4-6': { input: 3.00, output: 15.00 },
  'claude-haiku-4-5-20251001': { input: 0.80, output: 4.00 },
  'gemini-2.0-flash': { input: 0.075, output: 0.30 },
};

export interface LogEntry {
  route: string;
  eventType: string;
  provider: 'anthropic' | 'gemini';
  model: string;
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
  const pricing = PRICING[entry.model] ?? PRICING['claude-sonnet-4-6'];
  const cost =
    (entry.inputTokens / 1_000_000) * pricing.input +
    (entry.outputTokens / 1_000_000) * pricing.output;

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
