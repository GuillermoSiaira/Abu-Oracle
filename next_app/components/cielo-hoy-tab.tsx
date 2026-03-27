"use client";

import { useState, useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";
import { UI } from "@/lib/i18n";
import { LunarDial, type LunarData } from "@/components/LunarDial";
import { ABU_BASE_URL } from "@/services/abu";
import { getAbuAuthHeaders } from "@/lib/abu-auth";

// ── Constants (shared with transits-tab) ─────────────────────────────────────

const ASPECT_META: Record<string, { label: string; symbol: string; color: string }> = {
  conjunction: { label: "Conjunción",  symbol: "☌", color: "text-amber-400"   },
  opposition:  { label: "Oposición",   symbol: "☍", color: "text-red-400"     },
  square:      { label: "Cuadratura",  symbol: "□", color: "text-orange-400"  },
  trine:       { label: "Trígono",     symbol: "△", color: "text-emerald-400" },
  sextile:     { label: "Sextil",      symbol: "⚹", color: "text-teal-400"    },
  semisextile: { label: "Semisextil",  symbol: "⚺", color: "text-slate-400"   },
  quincunx:    { label: "Quincuncio",  symbol: "⚻", color: "text-violet-400"  },
};

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀", Mars: "♂",
  Jupiter: "♃", Saturn: "♄", Uranus: "♅", Neptune: "♆", Pluto: "♇",
  ASC: "AC", MC: "MC", "North Node": "☊", "South Node": "☋",
};

// ── Component ─────────────────────────────────────────────────────────────────

export function CieloHoyTab() {
  const { abuData, birthData, timeline, lang, setPendingLillyEvent } = useAppStore();
  const t = UI[lang];

  const [lunarData, setLunarData] = useState<LunarData | null>(null);
  const initializedRef = useRef(false);

  // ── Fetch lunar data ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!birthData?.birthDate || birthData.lat == null || birthData.lon == null) return;
    getAbuAuthHeaders().then((headers) => {
      const url = new URL(`${ABU_BASE_URL}/api/astro/lunar`);
      url.searchParams.set("birthDate", birthData.birthDate);
      url.searchParams.set("lat",       String(birthData.lat));
      url.searchParams.set("lon",       String(birthData.lon));
      fetch(url.toString(), { headers })
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => { if (data) setLunarData(data); })
        .catch(() => {});
    });
  }, [birthData?.birthDate, birthData?.lat, birthData?.lon]);

  // ── Auto-trigger sky_open once on first mount (when data is available) ──────
  useEffect(() => {
    if (initializedRef.current) return;
    if (!abuData || !birthData) return;
    initializedRef.current = true;
    setPendingLillyEvent({ type: 'sky_open', payload: { lang } });
  }, [abuData, birthData, lang, setPendingLillyEvent]);

  // ── Reset initialized when subject changes ───────────────────────────────────
  const prevAbuRef = useRef<typeof abuData | undefined>(undefined);
  useEffect(() => {
    if (prevAbuRef.current !== undefined && prevAbuRef.current !== abuData) {
      initializedRef.current = false;
      setLunarData(null);
    }
    prevAbuRef.current = abuData;
  }, [abuData]);

  // ── Active fast + lunar transits from store timeline ────────────────────────
  const fastTransits = (timeline?.transits_window ?? []).filter(
    (t) => t.is_active && (t.speed_class === 'fast' || t.speed_class === 'lunar')
  );

  const handleSkyOpen = () => {
    setPendingLillyEvent({ type: 'sky_open', payload: { lang } });
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="p-4 space-y-5">

      {/* ── Sección: El cielo ahora ── */}
      <div>
        <h3 className="text-[11px] font-semibold tracking-widest uppercase text-amber-400/70 mb-3">
          {t.cieloHoyTitle}
        </h3>

        <div className="flex gap-4 items-start">
          {/* Dial lunar */}
          <div className="shrink-0 border border-amber-400/15 rounded-lg p-3">
            {lunarData ? (
              <LunarDial data={lunarData} lang={lang} />
            ) : (
              <div className="w-[148px] h-[148px] flex items-center justify-center text-[11px] text-slate-600">
                …
              </div>
            )}
          </div>

          {/* Tránsitos activos */}
          <div className="flex-1 min-w-0">
            <h4 className="text-[11px] font-semibold tracking-widest uppercase text-slate-500 mb-2">
              {t.cieloHoyTransitsTitle}
            </h4>

            {fastTransits.length === 0 ? (
              <p className="text-[11px] text-slate-600 italic py-4">
                {t.cieloHoyNoTransits}
              </p>
            ) : (
              <div className="space-y-1.5">
                {fastTransits.map((tr, i) => {
                  const meta = ASPECT_META[tr.aspect] ?? {
                    label: tr.aspect, symbol: "?", color: "text-slate-400",
                  };
                  const tSym  = PLANET_SYMBOLS[tr.transit_planet] ?? tr.transit_planet[0];
                  const nSym  = PLANET_SYMBOLS[tr.natal_planet]   ?? tr.natal_planet[0];
                  const ingress = tr.ingress_date ? tr.ingress_date.slice(0, 10) : null;

                  return (
                    <div
                      key={i}
                      className="flex items-center gap-2 px-3 py-2 rounded-md bg-slate-800/50 border border-slate-700/40"
                    >
                      {/* Transit planet */}
                      <span className="text-slate-300 font-mono text-[13px] shrink-0 w-5 text-center">
                        {tSym}
                      </span>
                      <span className="text-[11px] text-slate-400 shrink-0 w-[60px] truncate">
                        {tr.transit_planet}
                      </span>

                      {/* Aspect */}
                      <span className={`text-[13px] shrink-0 ${meta.color}`}>
                        {meta.symbol}
                      </span>

                      {/* Natal planet */}
                      <span className="text-slate-500 font-mono text-[13px] shrink-0 w-5 text-center">
                        {nSym}
                      </span>
                      <span className="text-[11px] text-slate-500 shrink-0 w-[60px] truncate">
                        {tr.natal_planet}
                      </span>

                      {/* Ingress date */}
                      {ingress && (
                        <span className="text-[10px] text-slate-600 font-mono ml-auto shrink-0">
                          {ingress}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Sección: Lilly lee el cielo ── */}
      <div className="pt-2 border-t border-slate-800/60">
        <button
          onClick={handleSkyOpen}
          className="w-full py-2.5 px-4 rounded-lg border border-amber-400/30 bg-amber-400/5
                     text-amber-300/80 text-[12px] font-medium tracking-wide
                     hover:bg-amber-400/10 hover:border-amber-400/50 transition-colors"
        >
          {t.cieloHoyLillyButton}
        </button>
      </div>

    </div>
  );
}
