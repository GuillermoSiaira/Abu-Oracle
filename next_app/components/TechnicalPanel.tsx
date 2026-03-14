'use client';

import { useEffect, useState, useMemo } from 'react';
import { Activity, Shield, Cpu, Database, Clock } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { UI } from '@/lib/i18n';
import { ABU_BASE_URL } from '@/services/abu';

// --- Sign → Ruler (traditional) ---
const RULERSHIPS: Record<string, string> = {
  Aries: 'Mars', Taurus: 'Venus', Gemini: 'Mercury', Cancer: 'Moon',
  Leo: 'Sun', Virgo: 'Mercury', Libra: 'Venus', Scorpio: 'Mars',
  Sagittarius: 'Jupiter', Capricorn: 'Saturn', Aquarius: 'Saturn', Pisces: 'Jupiter',
};

function signFromLon(lon: number): string {
  const signs = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
    'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
  return signs[Math.floor(lon / 30) % 12];
}

function getDignityLabel(d: any): { label: string; positive: boolean; negative: boolean; score: number } {
  if (!d) return { label: 'Peregrine', positive: false, negative: false, score: 0 };
  if (d.domicile) return { label: 'Domicile', positive: true, negative: false, score: d.score ?? 5 };
  if (d.exaltation) return { label: 'Exaltation', positive: true, negative: false, score: d.score ?? 4 };
  if (d.detriment) return { label: 'Detriment', positive: false, negative: true, score: d.score ?? -5 };
  if (d.fall) return { label: 'Fall', positive: false, negative: true, score: d.score ?? -4 };
  // kind-based format (from get_planet_dignity)
  if (d.kind === 'domicile') return { label: 'Domicile', positive: true, negative: false, score: d.score ?? 5 };
  if (d.kind === 'exaltation') return { label: 'Exaltation', positive: true, negative: false, score: d.score ?? 4 };
  if (d.kind === 'detriment') return { label: 'Detriment', positive: false, negative: true, score: d.score ?? -5 };
  if (d.kind === 'fall') return { label: 'Fall', positive: false, negative: true, score: d.score ?? -4 };
  return { label: 'Peregrine', positive: false, negative: false, score: d.score ?? 0 };
}

const LILLY_BASE_URL = process.env.NEXT_PUBLIC_LILLY_URL || 'http://localhost:8001';

type ConnStatus = 'checking' | 'ok' | 'fail';

function StatusDot({ status, label }: { status: ConnStatus; label: string }) {
  const color = status === 'ok' ? 'bg-green-500' : status === 'fail' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse';
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-1.5 h-1.5 rounded-full ${color}`} />
      <span className="text-slate-500">{label}</span>
    </div>
  );
}

function EmptyState({ t }: { t: typeof UI['es'] }) {
  return (
    <div className="text-center py-4 space-y-1">
      <p className="text-slate-600 text-[11px]">{t.tpNoChart}</p>
      <p className="text-slate-700 text-[10px]">{t.tpNoChartHint}</p>
    </div>
  );
}

export default function TechnicalPanel() {
  const { abuData, lang } = useAppStore();
  const t = UI[lang];

  // --- Health checks ---
  const [abuStatus, setAbuStatus] = useState<ConnStatus>('checking');
  const [lillyStatus, setLillyStatus] = useState<ConnStatus>('checking');
  const [isArchOpen, setIsArchOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function check(url: string, setter: (s: ConnStatus) => void) {
      try {
        const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
        if (!cancelled) setter(res.ok ? 'ok' : 'fail');
      } catch {
        if (!cancelled) setter('fail');
      }
    }

    check(`${ABU_BASE_URL}/health`, setAbuStatus);
    check(`${LILLY_BASE_URL}/`, setLillyStatus);

    const interval = setInterval(() => {
      check(`${ABU_BASE_URL}/health`, setAbuStatus);
      check(`${LILLY_BASE_URL}/`, setLillyStatus);
    }, 30_000);

    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  // --- Derived chart data ---
  const hasChart = !!abuData?.chart?.planets?.length;

  const planets = useMemo(() => {
    if (!hasChart) return [];
    return (abuData!.chart.planets as any[]).filter(
      (p) => !['North Node', 'South Node', 'Chiron'].includes(p.name)
    );
  }, [abuData, hasChart]);

  const houseSys = useMemo(() => {
    if (!hasChart) return null;
    const h = abuData!.chart.houses as any;
    return h?.house_system_used || 'Placidus';
  }, [abuData, hasChart]);

  const ascSign = useMemo(() => {
    if (!hasChart) return null;
    const asc = (abuData!.chart.houses as any)?.asc;
    return asc != null ? signFromLon(asc) : null;
  }, [abuData, hasChart]);

  const mcSign = useMemo(() => {
    if (!hasChart) return null;
    const mc = (abuData!.chart.houses as any)?.mc;
    return mc != null ? signFromLon(mc) : null;
  }, [abuData, hasChart]);

  const ascRuler = ascSign ? RULERSHIPS[ascSign] ?? '—' : null;
  const mcRuler = mcSign ? RULERSHIPS[mcSign] ?? '—' : null;

  const sect = abuData?.derived?.sect;
  const sectMaster = useMemo(() => {
    if (!sect) return null;
    return sect === 'diurnal' ? 'Jupiter' : 'Venus';
  }, [sect]);

  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const copyController = (key: string, planet: string, role: string) => {
    const text = `Explicá el rol de ${planet} como ${role} en esta carta natal.`;
    navigator.clipboard?.writeText(text).catch(() => {});
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1500);
  };

  return (
    <div className="h-full bg-[#050505] text-slate-400 p-3 font-mono text-xs overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800">

      {/* SECTION 1: SYSTEM ARCHITECTURE (collapsible) */}
      <div className="mb-4 border-b border-slate-900 pb-3">
        {/* Connection indicators always visible */}
        <div className="flex items-center justify-between mb-2">
          <StatusDot status={abuStatus} label="Abu" />
          <StatusDot status={lillyStatus} label="Lilly" />
        </div>
        <button
          onClick={() => setIsArchOpen(v => !v)}
          className="w-full flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-600 hover:text-slate-400 transition-colors py-1"
        >
          <span className="flex items-center gap-2">
            <Cpu className="w-3 h-3" /> {t.tpSysArch}
          </span>
          <span>{isArchOpen ? '▲' : '▼'}</span>
        </button>
        {isArchOpen && (
          <div className="space-y-2 text-[11px] mt-2">
            <div className="flex justify-between items-center">
              <span>{t.tpCoreKernel}:</span>
              <span className="text-green-500 font-bold">Python + Skyfield</span>
            </div>
            <div className="flex justify-between items-center">
              <span>{t.tpEphemeris}:</span>
              <span className="text-slate-300">Swiss Eph + DE440s</span>
            </div>
            <div className="flex justify-between items-center">
              <span>{t.tpGeoResolver}:</span>
              <span className="text-blue-400">WGS84 / rev_geocoder</span>
            </div>
            <div className="flex justify-between items-center">
              <span>{t.tpPrecision}:</span>
              <span className="text-slate-300">64-bit float</span>
            </div>
          </div>
        )}
      </div>

      {/* SECTION 2: COMPUTATION CONTEXT */}
      <div className="mb-6 border-b border-slate-900 pb-4">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2">
          <Clock className="w-3 h-3" /> {t.tpCompCtx}
        </h3>
        {hasChart ? (
          <div className="space-y-2 text-[11px]">
            <div className="flex justify-between">
              <span>{t.tpRefFrame}:</span>
              <span className="text-slate-200">Topocentric</span>
            </div>
            <div className="flex justify-between">
              <span>{t.tpHouseSys}:</span>
              <span className="text-slate-200">{houseSys}</span>
            </div>
            <div className="flex justify-between">
              <span>{t.tpSiderealTime}:</span>
              <span className="text-slate-500 font-mono">—</span>
            </div>
            <div className="flex justify-between">
              <span>{t.tpAyanamsha}:</span>
              <span className="text-slate-500">N/A (Tropical)</span>
            </div>
          </div>
        ) : (
          <EmptyState t={t} />
        )}
      </div>

      {/* SECTION 3: ESSENTIAL DIGNITIES */}
      <div className="mb-6 border-b border-slate-900 pb-4">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2">
          <Shield className="w-3 h-3" /> {t.tpDignities}
        </h3>
        {hasChart && planets.length > 0 ? (
          <div className="space-y-1">
            {planets.map((p: any) => {
              const d = getDignityLabel(p.dignity);
              return (
                <div key={p.name} className="flex justify-between items-center py-1 border-b border-slate-900/50 last:border-0">
                  <span className={d.positive ? 'text-slate-200 font-medium' : 'text-slate-400'}>{p.name}</span>
                  <div className="flex items-center gap-2">
                    <span className={`
                      px-1.5 py-0.5 rounded text-[10px] font-medium
                      ${d.positive ? 'bg-amber-900/30 text-amber-400 border border-amber-800/30' : ''}
                      ${d.negative ? 'bg-orange-900/20 text-orange-400' : ''}
                      ${!d.positive && !d.negative ? 'text-slate-600' : ''}
                    `}>
                      {d.label}
                    </span>
                    <span className={`w-6 text-right font-mono text-[10px] ${d.positive ? 'text-amber-500' : d.negative ? 'text-orange-500' : 'text-slate-700'}`}>
                      {d.score !== 0 ? (d.score > 0 ? `+${d.score}` : d.score) : ''}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState t={t} />
        )}
      </div>

      {/* SECTION 4: SCHEME CONTROLLERS */}
      <div className="mb-6">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2">
          <Database className="w-3 h-3" /> {t.tpScheme}
        </h3>
        {hasChart ? (
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => ascRuler && copyController('asc', ascRuler, t.tpAscRuler)}
              className="bg-slate-900/30 p-2 rounded border border-slate-800 hover:border-amber-800/50 hover:bg-slate-800/50 transition-colors text-left group"
            >
              <div className="text-[9px] text-slate-500 mb-1 group-hover:text-slate-400">{t.tpAscRuler}</div>
              <div className="text-sm text-yellow-500 font-semibold flex items-center justify-between">
                {ascRuler}
                <span className="text-[9px] text-slate-700 group-hover:text-slate-500">
                  {copiedKey === 'asc' ? '✓' : '⊕'}
                </span>
              </div>
            </button>
            <button
              onClick={() => mcRuler && copyController('mc', mcRuler, t.tpMcRuler)}
              className="bg-slate-900/30 p-2 rounded border border-slate-800 hover:border-amber-800/50 hover:bg-slate-800/50 transition-colors text-left group"
            >
              <div className="text-[9px] text-slate-500 mb-1 group-hover:text-slate-400">{t.tpMcRuler}</div>
              <div className="text-sm text-slate-200 font-semibold flex items-center justify-between">
                {mcRuler}
                <span className="text-[9px] text-slate-700 group-hover:text-slate-500">
                  {copiedKey === 'mc' ? '✓' : '⊕'}
                </span>
              </div>
            </button>
            <div className="bg-slate-900/30 p-2 rounded border border-slate-800 col-span-2">
              <div className="text-[9px] text-slate-500 mb-1">{t.tpSectMaster}</div>
              <div className="text-sm text-slate-200 flex justify-between items-center">
                <span>{sectMaster ?? '—'}</span>
                {sect && (
                  <span className="text-slate-500 text-[10px] bg-slate-800 px-1 rounded">
                    {sect === 'diurnal' ? t.tpDiurnal : t.tpNocturnal}
                  </span>
                )}
              </div>
            </div>
          </div>
        ) : (
          <EmptyState t={t} />
        )}
      </div>

    </div>
  );
}