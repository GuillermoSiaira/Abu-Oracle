import { NextRequest, NextResponse } from 'next/server';
import { getAdminDb } from '@/lib/firebase-admin';
import { getUserIdFromRequest } from '@/lib/get-user-id';

const ADMIN_UID = 'xJhOVmVFRUXoRBRGK6mJWyMeZOu1';

const PRICING: Record<string, { input: number; output: number }> = {
  'claude-sonnet-4-6': { input: 3.00, output: 15.00 },
  'claude-haiku-4-5-20251001': { input: 0.80, output: 4.00 },
  'gemini-2.0-flash': { input: 0.075, output: 0.30 },
};

type Range = '1d' | '7d' | '30d';

function isLocalDevelopment(req: NextRequest): boolean {
  if (process.env.NODE_ENV !== 'development') return false;
  const host = req.nextUrl.hostname;
  return host === 'localhost' || host === '127.0.0.1';
}

function resolveRange(value: string | null): { range: Range; days: number } {
  if (value === '1d') return { range: '1d', days: 1 };
  if (value === '30d') return { range: '30d', days: 30 };
  return { range: '7d', days: 7 };
}

function estimateCost(model: string, inputTokens: number, outputTokens: number): number {
  const pricing = PRICING[model] ?? PRICING['claude-sonnet-4-6'];
  return (inputTokens / 1_000_000) * pricing.input + (outputTokens / 1_000_000) * pricing.output;
}

function roundUsd(value: number): number {
  return Math.round(value * 10000) / 10000;
}

export async function GET(req: NextRequest) {
  const userId = await getUserIdFromRequest(req).catch(() => null);
  if (userId !== ADMIN_UID && !isLocalDevelopment(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
  }

  const { range, days } = resolveRange(req.nextUrl.searchParams.get('range'));
  const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
  const db = getAdminDb();

  const [usageSnap, interpretationSnap, errorsSnap] = await Promise.all([
    db.collection('lilly_usage_log')
      .where('created_at', '>=', since)
      .orderBy('created_at', 'desc')
      .limit(500)
      .get(),
    db.collection('kg_baseline_logs')
      .where('timestamp', '>=', since)
      .orderBy('timestamp', 'desc')
      .limit(500)
      .get(),
    db.collection('lilly_errors')
      .where('timestamp', '>=', since)
      .orderBy('timestamp', 'desc')
      .limit(100)
      .get(),
  ]);

  const usageLogs = usageSnap.docs.map((doc) => doc.data());
  const interpretationLogs = interpretationSnap.docs.map((doc) => doc.data());
  const errors = errorsSnap.docs.map((doc) => doc.data());

  const costByRoute: Record<string, { calls: number; costUsd: number; continuations: number }> = {};
  let totalCost = 0;

  for (const log of usageLogs) {
    const route = typeof log.route === 'string' ? log.route : 'unknown';
    const model = typeof log.model === 'string' ? log.model : 'claude-sonnet-4-6';
    const inputTokens = typeof log.input_tokens === 'number' ? log.input_tokens : 0;
    const outputTokens = typeof log.output_tokens === 'number' ? log.output_tokens : 0;
    const continuations = typeof log.continuations === 'number' ? log.continuations : 0;
    const costUsd = estimateCost(model, inputTokens, outputTokens);

    if (!costByRoute[route]) {
      costByRoute[route] = { calls: 0, costUsd: 0, continuations: 0 };
    }

    costByRoute[route].calls += 1;
    costByRoute[route].costUsd += costUsd;
    costByRoute[route].continuations += continuations;
    totalCost += costUsd;
  }

  const eventDist: Record<string, number> = {};
  for (const log of interpretationLogs) {
    const eventType = typeof log.eventType === 'string' ? log.eventType : 'unknown';
    eventDist[eventType] = (eventDist[eventType] ?? 0) + 1;
  }

  const uniqueUsers = new Set(
    usageLogs
      .map((log) => log.user_id)
      .filter((id): id is string => typeof id === 'string' && id.length > 0),
  ).size;

  const maxTokensHits = usageLogs.filter((log) => {
    const continuations = typeof log.continuations === 'number' ? log.continuations : 0;
    return continuations > 0;
  }).length;

  const recentErrors = errors.slice(0, 20).map((error) => ({
    timestamp: error.timestamp ?? null,
    route: error.route ?? 'unknown',
    error_source: error.error_source ?? 'unknown',
    error_message: typeof error.error_message === 'string'
      ? error.error_message.slice(0, 120)
      : '',
    user_id: error.user_id ?? null,
  }));

  const errorsBySource: Record<string, number> = {};
  for (const error of errors) {
    const source = typeof error.error_source === 'string' ? error.error_source : 'unknown';
    errorsBySource[source] = (errorsBySource[source] ?? 0) + 1;
  }

  return NextResponse.json({
    range,
    since,
    summary: {
      totalCalls: usageLogs.length,
      totalErrors: errors.length,
      totalCostUsd: roundUsd(totalCost),
      uniqueUsers,
      maxTokensHits,
      errorRate: usageLogs.length > 0
        ? Math.round((errors.length / usageLogs.length) * 1000) / 10
        : 0,
    },
    costByRoute: Object.entries(costByRoute)
      .sort((a, b) => b[1].costUsd - a[1].costUsd)
      .map(([route, data]) => ({
        route,
        calls: data.calls,
        continuations: data.continuations,
        costUsd: roundUsd(data.costUsd),
        avgCostUsd: data.calls > 0 ? roundUsd(data.costUsd / data.calls) : 0,
      })),
    eventDist: Object.entries(eventDist).sort((a, b) => b[1] - a[1]),
    recentErrors,
    errorsBySource,
  });
}
