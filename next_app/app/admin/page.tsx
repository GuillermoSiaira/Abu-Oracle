'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getAbuAuthHeaders } from '@/lib/abu-auth';
import { useAuth } from '@/lib/auth-context';

const ADMIN_UID = 'xJhOVmVFRUXoRBRGK6mJWyMeZOu1';

function isLocalDevelopment(): boolean {
  if (process.env.NODE_ENV !== 'development') return false;
  if (typeof window === 'undefined') return false;
  return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
}

type Range = '1d' | '7d' | '30d';

interface Summary {
  totalCalls: number;
  totalErrors: number;
  totalCostUsd: number;
  uniqueUsers: number;
  maxTokensHits: number;
  errorRate: number;
}

interface CostByRoute {
  route: string;
  calls: number;
  costUsd: number;
  continuations: number;
  avgCostUsd: number;
}

interface RecentError {
  timestamp: string | null;
  route: string;
  error_source: string;
  error_message: string;
  user_id: string | null;
}

interface AdminData {
  range: Range;
  since: string;
  summary: Summary;
  costByRoute: CostByRoute[];
  eventDist: Array<[string, number]>;
  recentErrors: RecentError[];
  errorsBySource: Record<string, number>;
}

interface HealthAlert {
  condition: string;
  severity: 'high' | 'medium';
  message: string;
  detail?: string;
}

interface HealthData {
  ok: boolean;
  timestamp: string;
  alerts: HealthAlert[];
  checks: Record<string, 'ok' | 'alert' | 'error'>;
}

function formatUsd(value: number): string {
  return `$${value.toFixed(value >= 1 ? 2 : 4)}`;
}

function formatTimestamp(value: string | null): string {
  if (!value) return '-';
  return value.replace('T', ' ').replace(/\.\d+Z$/, ' UTC');
}

function MetricCard({
  label,
  value,
  hint,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: 'neutral' | 'amber' | 'red';
}) {
  const toneClass =
    tone === 'red'
      ? 'text-rose-300'
      : tone === 'amber'
        ? 'text-amber-300'
        : 'text-slate-100';

  return (
    <div className="rounded border border-slate-800 bg-slate-900/55 px-4 py-3">
      <div className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className={`mt-2 font-mono text-2xl ${toneClass}`}>{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [range, setRange] = useState<Range>('7d');
  const [data, setData] = useState<AdminData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingData, setLoadingData] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  const localBypass = isLocalDevelopment();
  const isAdmin = localBypass || user?.uid === ADMIN_UID;

  const fetchData = useCallback(async (nextRange: Range) => {
    setLoadingData(true);
    setError(null);

    try {
      const headers = await getAbuAuthHeaders();
      const res = await fetch(`/api/admin/data?range=${nextRange}`, {
        headers,
        cache: 'no-store',
      });

      if (!res.ok) {
        throw new Error(`Panoptikon API ${res.status}`);
      }

      const json = await res.json() as AdminData;
      setData(json);

      const healthRes = await fetch('/api/admin/health?notify=0', {
        headers,
        cache: 'no-store',
      }).catch(() => null);
      if (healthRes) {
        const healthJson = await healthRes.json().catch(() => null) as HealthData | null;
        if (healthJson?.alerts) setHealth(healthJson);
      }

      setUpdatedAt(new Date().toISOString());
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoadingData(false);
    }
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!isAdmin) {
      router.push('/chart');
      return;
    }
    void fetchData(range);
  }, [fetchData, isAdmin, loading, range, router]);

  const avgCost = useMemo(() => {
    if (!data || data.summary.totalCalls === 0) return 0;
    return data.summary.totalCostUsd / data.summary.totalCalls;
  }, [data]);

  if (loading || (!loading && !isAdmin)) {
    return (
      <div className="min-h-screen bg-slate-950 px-6 py-10 text-slate-300">
        Verificando acceso...
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100">
      <div className="mx-auto max-w-6xl">
        <header className="mb-7 flex flex-col gap-4 border-b border-slate-800 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="font-serif text-3xl text-slate-100">PANOPTIKON - Abu Oracle</h1>
            <p className="mt-2 text-sm text-slate-500">
              Desde {data ? formatTimestamp(data.since) : '-'} · Actualizado {updatedAt ? formatTimestamp(updatedAt) : '-'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {(['1d', '7d', '30d'] as Range[]).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setRange(option)}
                className={[
                  'h-9 rounded border px-4 text-sm transition-colors',
                  range === option
                    ? 'border-amber-400/60 bg-amber-500/15 text-amber-200'
                    : 'border-slate-700 bg-slate-900/60 text-slate-400 hover:border-slate-500 hover:text-slate-200',
                ].join(' ')}
              >
                {option}
              </button>
            ))}
          </div>
        </header>

        {error && (
          <div className="mb-5 rounded border border-rose-500/30 bg-rose-950/30 px-4 py-3 text-sm text-rose-200">
            <div>No pude cargar Panoptikon: {error}</div>
            <button
              type="button"
              onClick={() => void fetchData(range)}
              className="mt-3 rounded border border-rose-400/40 px-3 py-1 text-xs text-rose-100 hover:bg-rose-500/10"
            >
              Reintentar
            </button>
          </div>
        )}

        {loadingData && !data && (
          <div className="rounded border border-slate-800 bg-slate-900/50 px-5 py-8 text-center text-sm text-slate-400">
            Cargando datos Panoptikon...
          </div>
        )}

        {data && (
          <div className="space-y-7">
            {health && health.alerts.length > 0 && (
              <section className="rounded border border-rose-500/35 bg-rose-950/30 px-4 py-3">
                <div className="mb-2 text-xs uppercase tracking-[0.18em] text-rose-300">
                  Health check activo
                </div>
                <div className="space-y-2">
                  {health.alerts.map((item) => (
                    <div key={item.condition} className="text-sm text-rose-100">
                      <span className="font-mono text-xs uppercase text-rose-300">{item.severity}</span>
                      <span className="mx-2 text-slate-500">-</span>
                      {item.message}
                      {item.detail && <span className="ml-2 text-xs text-slate-400">{item.detail}</span>}
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="grid gap-3 md:grid-cols-3">
              <MetricCard label="Total llamadas" value={String(data.summary.totalCalls)} />
              <MetricCard
                label="Total errores"
                value={`${data.summary.totalErrors} (${data.summary.errorRate}%)`}
                tone={data.summary.errorRate > 10 ? 'amber' : 'neutral'}
              />
              <MetricCard label="Costo USD" value={formatUsd(data.summary.totalCostUsd)} />
              <MetricCard label="Usuarios unicos" value={String(data.summary.uniqueUsers)} />
              <MetricCard
                label="Max token hits"
                value={String(data.summary.maxTokensHits)}
                tone={data.summary.totalCalls > 0 && data.summary.maxTokensHits / data.summary.totalCalls > 0.05 ? 'amber' : 'neutral'}
              />
              <MetricCard label="Costo prom/llamada" value={formatUsd(avgCost)} />
            </section>

            <section>
              <h2 className="mb-3 text-xs uppercase tracking-[0.18em] text-slate-500">Costo por ruta</h2>
              <div className="overflow-hidden rounded border border-slate-800">
                <table className="w-full text-sm">
                  <thead className="bg-slate-900/80 text-xs text-slate-500">
                    <tr>
                      <th className="px-4 py-3 text-left font-normal">Ruta</th>
                      <th className="px-4 py-3 text-right font-normal">Llamadas</th>
                      <th className="px-4 py-3 text-right font-normal">Costo USD</th>
                      <th className="px-4 py-3 text-right font-normal">Continuaciones</th>
                      <th className="px-4 py-3 text-right font-normal">Costo prom</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.costByRoute.map((row, index) => (
                      <tr
                        key={row.route}
                        className={index % 2 === 0 ? 'bg-slate-900/35' : 'bg-slate-900/10'}
                      >
                        <td className="px-4 py-3 font-mono text-xs text-slate-300">{row.route}</td>
                        <td className="px-4 py-3 text-right font-mono text-xs">{row.calls}</td>
                        <td className="px-4 py-3 text-right font-mono text-xs">{formatUsd(row.costUsd)}</td>
                        <td className="px-4 py-3 text-right font-mono text-xs text-amber-300">{row.continuations}</td>
                        <td className="px-4 py-3 text-right font-mono text-xs">{formatUsd(row.avgCostUsd)}</td>
                      </tr>
                    ))}
                    {data.costByRoute.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-5 text-center text-sm text-slate-500">
                          Sin llamadas en el periodo.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="grid gap-7 lg:grid-cols-[1.1fr_1fr]">
              <div>
                <h2 className="mb-3 text-xs uppercase tracking-[0.18em] text-slate-500">Eventos mas disparados</h2>
                <div className="overflow-hidden rounded border border-slate-800">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-900/80 text-xs text-slate-500">
                      <tr>
                        <th className="px-4 py-3 text-left font-normal">Evento</th>
                        <th className="px-4 py-3 text-right font-normal">Frecuencia</th>
                        <th className="px-4 py-3 text-right font-normal">% total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.eventDist.map(([event, count], index) => (
                        <tr
                          key={event}
                          className={index % 2 === 0 ? 'bg-slate-900/35' : 'bg-slate-900/10'}
                        >
                          <td className="px-4 py-3 font-mono text-xs text-slate-300">{event}</td>
                          <td className="px-4 py-3 text-right font-mono text-xs">{count}</td>
                          <td className="px-4 py-3 text-right font-mono text-xs">
                            {data.summary.totalCalls > 0
                              ? `${Math.round((count / data.summary.totalCalls) * 1000) / 10}%`
                              : '0%'}
                          </td>
                        </tr>
                      ))}
                      {data.eventDist.length === 0 && (
                        <tr>
                          <td colSpan={3} className="px-4 py-5 text-center text-sm text-slate-500">
                            Sin eventos en el periodo.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h2 className="mb-3 text-xs uppercase tracking-[0.18em] text-slate-500">Errores por fuente</h2>
                <div className="overflow-hidden rounded border border-slate-800">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-900/80 text-xs text-slate-500">
                      <tr>
                        <th className="px-4 py-3 text-left font-normal">Fuente</th>
                        <th className="px-4 py-3 text-right font-normal">Cantidad</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(data.errorsBySource).map(([source, count], index) => (
                        <tr
                          key={source}
                          className={index % 2 === 0 ? 'bg-slate-900/35' : 'bg-slate-900/10'}
                        >
                          <td className="px-4 py-3 font-mono text-xs text-slate-300">{source}</td>
                          <td className="px-4 py-3 text-right font-mono text-xs">{count}</td>
                        </tr>
                      ))}
                      {Object.keys(data.errorsBySource).length === 0 && (
                        <tr>
                          <td colSpan={2} className="px-4 py-5 text-center text-sm text-emerald-300">
                            Sin errores en el periodo.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-xs uppercase tracking-[0.18em] text-slate-500">Errores recientes</h2>
              <div className="overflow-hidden rounded border border-slate-800">
                <table className="w-full text-sm">
                  <thead className="bg-slate-900/80 text-xs text-slate-500">
                    <tr>
                      <th className="px-4 py-3 text-left font-normal">Timestamp</th>
                      <th className="px-4 py-3 text-left font-normal">Ruta</th>
                      <th className="px-4 py-3 text-left font-normal">Fuente</th>
                      <th className="px-4 py-3 text-left font-normal">Mensaje</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recentErrors.map((row, index) => (
                      <tr
                        key={`${row.timestamp}-${row.route}-${index}`}
                        className={index % 2 === 0 ? 'bg-slate-900/35' : 'bg-slate-900/10'}
                      >
                        <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-500">
                          {formatTimestamp(row.timestamp)}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-slate-300">{row.route}</td>
                        <td className="px-4 py-3 font-mono text-xs text-amber-300">{row.error_source}</td>
                        <td className="px-4 py-3 text-xs text-slate-300">{row.error_message}</td>
                      </tr>
                    ))}
                    {data.recentErrors.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-5 text-center text-sm text-emerald-300">
                          Sin errores en el periodo.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
