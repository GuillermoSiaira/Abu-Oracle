'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Cpu } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { UI } from '@/lib/i18n';
import { ABU_BASE_URL } from '@/services/abu';

const LILLY_BASE_URL = process.env.NEXT_PUBLIC_LILLY_URL || 'http://localhost:8001';

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

function getPlanetDignity(planets: any[], name: string): string {
  const p = planets?.find((pl: any) => pl.name === name);
  if (!p?.dignity) return 'Peregrine';
  const d = p.dignity;
  if (d.domicile || d.kind === 'domicile') return 'Domicile';
  if (d.exaltation || d.kind === 'exaltation') return 'Exaltation';
  if (d.detriment || d.kind === 'detriment') return 'Detriment';
  if (d.fall || d.kind === 'fall') return 'Fall';
  return 'Peregrine';
}

type ConnStatus = 'checking' | 'ok' | 'fail';

function StatusDot({ status, label }: { status: ConnStatus; label: string }) {
  const color = status === 'ok' ? 'bg-green-500' : status === 'fail' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse';
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-1.5 h-1.5 rounded-full ${color}`} />
      <span className="text-slate-500 text-[10px]">{label}</span>
    </div>
  );
}

const ROUTE_MAP: Record<string, string> = {
  click_planet: '/api/lilly/planet',
  click_technique: '/api/lilly/technique',
  click_domain: '/api/lilly/domain',
};

export default function TechnicalPanel() {
  const { abuData, lang, lastLillyEvent, lillySuggestions, setPendingLillyEvent } = useAppStore() as any;
  const t = UI[lang as keyof typeof UI] ?? UI.es;
  const pathname = usePathname();
  const isChartPage = pathname === '/chart';

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

  const hasChart = isChartPage && !!abuData?.chart?.planets?.length;
  const planets: any[] = abuData?.chart?.planets ?? [];

  // --- Year lord from profection ---
  const profectionHouse: number | null = abuData?.derived?.profection?.house ?? null;
  let yearLord: string | null = null;
  let yearLordDignity: string = '';
  let profectionSign: string | null = null;

  if (profectionHouse && abuData?.chart?.houses?.houses) {
    const entry = abuData.chart.houses.houses.find((h: any) => h.house === profectionHouse);
    if (entry) {
      profectionSign = signFromLon(entry.start);
      yearLord = profectionSign ? (RULERSHIPS[profectionSign] ?? null) : null;
      if (yearLord) yearLordDignity = getPlanetDignity(planets, yearLord);
    }
  }

  const dignityColor = (d: string) => {
    if (d === 'Domicile' || d === 'Exaltation') return 'text-amber-400';
    if (d === 'Detriment' || d === 'Fall') return 'text-orange-400';
    return 'text-slate-500';
  };

  function fireSuggestion(sug: { type: string; target: string; label: string }) {
    if (sug.type === 'click_planet') {
      setPendingLillyEvent({ type: 'click_planet', payload: { planet_name: sug.target, label: sug.label } });
    } else if (sug.type === 'click_technique') {
      setPendingLillyEvent({ type: 'click_technique', payload: { technique: sug.target, data: {}, subject_name: '', lang } });
    } else if (sug.type === 'click_domain') {
      setPendingLillyEvent({ type: 'domain_select', payload: { domain: sug.target, label: sug.label } });
    }
  }

  return (
    <div className="h-full bg-[#050505] text-slate-400 p-4 font-mono text-sm overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800 flex flex-col gap-4">

      {/* CONNECTION STATUS */}
      <div className="border-b border-slate-900 pb-3">
        <div className="flex items-center justify-between mb-2">
          <StatusDot status={abuStatus} label="Abu" />
          <StatusDot status={lillyStatus} label="Lilly" />
        </div>
        <button
          onClick={() => setIsArchOpen(v => !v)}
          className="w-full flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-700 hover:text-slate-500 transition-colors py-0.5"
        >
          <span className="flex items-center gap-1.5">
            <Cpu className="w-3 h-3" /> {t.tpSysArch}
          </span>
          <span>{isArchOpen ? '▲' : '▼'}</span>
        </button>
        {isArchOpen && (
          <div className="space-y-1.5 text-[10px] mt-2 text-slate-600">
            <div className="flex justify-between"><span>Kernel:</span><span className="text-green-600">Python + Skyfield</span></div>
            <div className="flex justify-between"><span>Ephem:</span><span>Swiss DE440s</span></div>
            <div className="flex justify-between"><span>Ref:</span><span>Topocentric</span></div>
            <div className="flex justify-between"><span>Houses:</span><span>Placidus</span></div>
          </div>
        )}
      </div>

      {/* GUIDE PANEL — only when chart loaded */}
      {hasChart && (
        <>
          {/* LEYENDO AHORA */}
          <div>
            <h3 className="text-[9px] uppercase tracking-widest text-slate-600 mb-2">
              {t.tpReadingNow}
            </h3>
            <div className="border border-slate-800 rounded bg-[#080808] p-2.5">
              {lastLillyEvent ? (
                <p className="text-slate-200 text-[11px] font-medium leading-snug">
                  {lastLillyEvent.label}
                </p>
              ) : (
                <p className="text-slate-600 text-[10px]">{t.tpNoSelection}</p>
              )}
            </div>
          </div>

          {/* SEÑOR DEL AÑO */}
          <div>
            <h3 className="text-[9px] uppercase tracking-widest text-slate-600 mb-2">
              {t.tpYearLord}
            </h3>
            <div className="border border-slate-800 rounded bg-[#080808] p-2.5 space-y-1">
              {yearLord ? (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-amber-400 font-semibold text-[12px]">{yearLord}</span>
                    {yearLordDignity && (
                      <span className={`text-[9px] ${dignityColor(yearLordDignity)}`}>
                        {yearLordDignity}
                      </span>
                    )}
                  </div>
                  {profectionHouse && (
                    <p className="text-slate-600 text-[10px]">
                      {t.tpActivatedHouse} {profectionHouse}
                      {profectionSign ? ` · ${profectionSign}` : ''}
                    </p>
                  )}
                </>
              ) : (
                <p className="text-slate-600 text-[10px]">—</p>
              )}
            </div>
          </div>

          {/* EXPLORAR */}
          <div>
            <h3 className="text-[9px] uppercase tracking-widest text-slate-600 mb-2">
              {t.tpExplore}
            </h3>
            <div className="space-y-1.5">
              {lillySuggestions && lillySuggestions.length > 0 ? (
                lillySuggestions.map((sug: any, i: number) => (
                  <button
                    key={i}
                    onClick={() => fireSuggestion(sug)}
                    className="w-full text-left text-[11px] text-slate-400 hover:text-amber-300 border border-slate-800 hover:border-amber-700/40 rounded px-2.5 py-1.5 bg-[#080808] hover:bg-amber-900/10 transition-colors leading-snug"
                  >
                    → {sug.label}
                  </button>
                ))
              ) : (
                <p className="text-slate-700 text-[10px]">—</p>
              )}
            </div>
          </div>
        </>
      )}

    </div>
  );
}
