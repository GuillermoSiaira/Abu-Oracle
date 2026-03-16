"use client";

import { useEffect, useState } from "react";
import { useAppStore } from "@/lib/store";

const ABU_URL = process.env.NEXT_PUBLIC_ABU_URL || "http://localhost:8000";

const SIGNS = [
  "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
  "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
];

const ASPECT_META: Record<string,{ label: string; symbol: string; color: string }> = {
  conjunction:  { label: "Conjunción",  symbol: "☌", color: "text-amber-400 border-amber-400/40 bg-amber-400/10" },
  opposition:   { label: "Oposición",   symbol: "☍", color: "text-red-400 border-red-400/40 bg-red-400/10" },
  square:       { label: "Cuadratura",  symbol: "□", color: "text-orange-400 border-orange-400/40 bg-orange-400/10" },
  trine:        { label: "Trígono",     symbol: "△", color: "text-emerald-400 border-emerald-400/40 bg-emerald-400/10" },
  sextile:      { label: "Sextil",      symbol: "⚹", color: "text-teal-400 border-teal-400/40 bg-teal-400/10" },
  semisextile:  { label: "Semisextil",  symbol: "⚺", color: "text-slate-400 border-slate-400/40 bg-slate-400/10" },
  quincunx:     { label: "Quincuncio",  symbol: "⚻", color: "text-violet-400 border-violet-400/40 bg-violet-400/10" },
};

const PLANET_SYMBOLS: Record<string, string> = {
  Sun:"☉", Moon:"☽", Mercury:"☿", Venus:"♀", Mars:"♂",
  Jupiter:"♃", Saturn:"♄", Uranus:"♅", Neptune:"♆", Pluto:"♇",
  "North Node":"☊", "South Node":"☋", ASC:"AC", MC:"MC",
};

function lonToSignDeg(lon: number): { sign: string; deg: number } {
  const idx = Math.floor((lon % 360) / 30);
  const deg = (lon % 360) % 30;
  return { sign: SIGNS[idx] ?? "?", deg };
}

interface TransitAspect {
  natal_planet: string;
  transit_planet: string;
  aspect: string;
  orb: number;
  applying: boolean;
  exactness: string;
  natal_longitude: number;
  transit_longitude: number;
}

interface GroupedTransit {
  planet: string;
  longitude: number;
  sign: string;
  deg: number;
  aspects: TransitAspect[];
}

export function TransitsTab() {
  const birthData = useAppStore((s) => s.birthData);
  const abuData = useAppStore((s) => s.abuData);
  const transitDate = useAppStore((s) => s.transitDate);
  const setTransitDate = useAppStore((s) => s.setTransitDate);
  const lang = useAppStore((s) => s.lang);
  const setPendingLillyEvent = useAppStore((s) => s.setPendingLillyEvent);
  const subjectName = (birthData as any)?.userName || (abuData as any)?.person?.name || 'Anónimo';
  const [data, setData] = useState<TransitAspect[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [defaultDate] = useState(() => new Date().toISOString());
  const effectiveTransitDate = transitDate ?? defaultDate;

  const fetchTransits = () => {
    if (!birthData?.birthDate || !birthData.lat || !birthData.lon) return;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    setLoading(true);
    setError(null);

    fetch(`${ABU_URL}/api/astro/transits/with-natal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        birthDate: birthData.birthDate,
        birthLat: birthData.lat,
        birthLon: birthData.lon,
        transitDate: effectiveTransitDate,
        transitLat: birthData.lat,
        transitLon: birthData.lon,
      }),
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => setData(d))
      .catch((e) => {
        if (e.name === "AbortError") {
          setError("El cálculo tardó demasiado. Intentá de nuevo.");
        } else {
          setError(e.message);
        }
      })
      .finally(() => {
        clearTimeout(timeoutId);
        setLoading(false);
      });

    return controller;
  };

  useEffect(() => {
    const controller = fetchTransits();
    return () => { controller?.abort(); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [birthData?.birthDate, birthData?.lat, birthData?.lon, effectiveTransitDate]);

  if (!abuData) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        Ingresá tus datos natales para ver los tránsitos activos.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 text-center text-sm text-slate-400 animate-pulse">
        Calculando tránsitos…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-3 text-sm text-red-400 bg-red-400/10 rounded-lg border border-red-400/20">
        <p>Error al calcular tránsitos: {error}</p>
        <button
          onClick={() => fetchTransits()}
          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-xs transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        No hay tránsitos significativos en este momento.
      </div>
    );
  }

  // Group aspects by transit planet
  const grouped: Record<string, GroupedTransit> = {};
  for (const asp of data) {
    if (!grouped[asp.transit_planet]) {
      const { sign, deg } = lonToSignDeg(asp.transit_longitude);
      grouped[asp.transit_planet] = {
        planet: asp.transit_planet,
        longitude: asp.transit_longitude,
        sign,
        deg,
        aspects: [],
      };
    }
    grouped[asp.transit_planet].aspects.push(asp);
  }

  // Sort aspects within each group by orb (closest first)
  Object.values(grouped).forEach((g) =>
    g.aspects.sort((a, b) => Math.abs(a.orb) - Math.abs(b.orb))
  );

  // Sort groups: outer planets first (most significant)
  const PLANET_ORDER = ["Pluto","Neptune","Uranus","Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"];
  const sortedGroups = Object.values(grouped).sort(
    (a, b) => PLANET_ORDER.indexOf(a.planet) - PLANET_ORDER.indexOf(b.planet)
  );

  // Format the displayed date
  const displayDate = new Date(effectiveTransitDate);
  const dateLabel = displayDate.toLocaleDateString("es-AR", {
    day: "numeric", month: "long", year: "numeric",
  });

  // Date input value (YYYY-MM-DD format)
  const dateInputValue = effectiveTransitDate.split('T')[0];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-400">Fecha:</label>
          <input
            type="date"
            value={dateInputValue}
            onChange={(e) => {
              if (e.target.value) {
                const date = new Date(e.target.value + 'T00:00:00Z');
                setTransitDate(date.toISOString());
              }
            }}
            className="px-2 py-1 text-sm rounded bg-slate-700/50 border border-slate-600/50 text-slate-200 hover:border-slate-500/70 focus:border-amber-400/70 focus:outline-none"
          />
        </div>
        <h3 className="text-sm font-semibold text-slate-300">
          Tránsitos activos al {dateLabel}
        </h3>
        <span className="text-xs text-slate-500">{data.length} aspectos</span>
      </div>

      {sortedGroups.map((group) => {
        const sym = PLANET_SYMBOLS[group.planet] ?? group.planet[0];
        return (
          <div
            key={group.planet}
            className="rounded-xl border border-slate-700/50 bg-slate-800/40 overflow-hidden"
          >
            {/* Planet header */}
            <div
              className="flex items-center gap-3 px-4 py-3 bg-slate-700/30 border-b border-slate-700/40 cursor-pointer hover:border-amber-400/40 hover:bg-slate-700/50 transition-colors"
              onClick={() => {
                console.log('[click_transit] payload:', {
                  transit_planet: group.planet,
                  transit_sign: group.sign,
                  transit_deg: group.deg,
                  aspects: group.aspects,
                  transit_date: effectiveTransitDate,
                  subject_name: subjectName,
                  lang,
                });
                setPendingLillyEvent({
                  type: 'click_transit',
                  payload: {
                    transit_planet: group.planet,
                    transit_sign: group.sign,
                    transit_deg: group.deg,
                    aspects: group.aspects.map(a => ({
                      natal_planet: a.natal_planet,
                      aspect: a.aspect,
                      orb: a.orb,
                      applying: a.applying,
                    })),
                    transit_date: effectiveTransitDate,
                    subject_name: subjectName,
                    lang,
                  },
                });
              }}
            >
              <span className="text-lg w-6 text-center text-amber-400">{sym}</span>
              <div>
                <span className="font-semibold text-slate-200">{group.planet}</span>
                <span className="ml-2 text-xs text-slate-400">
                  en {group.sign} {group.deg.toFixed(1)}°
                </span>
              </div>
            </div>

            {/* Aspects list */}
            <div className="divide-y divide-slate-700/30">
              {group.aspects.map((asp, i) => {
                const meta = ASPECT_META[asp.aspect] ?? {
                  label: asp.aspect,
                  symbol: "?",
                  color: "text-slate-400 border-slate-400/40 bg-slate-400/10",
                };
                const natSym = PLANET_SYMBOLS[asp.natal_planet] ?? asp.natal_planet[0];
                const orbStr = Math.abs(asp.orb).toFixed(2) + "°";
                const isExact = Math.abs(asp.orb) <= 1;

                return (
                  <div
                    key={i}
                    className={`flex items-center justify-between px-4 py-2.5 text-sm ${
                      isExact ? "bg-amber-500/5" : ""
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span
                        className={`shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${meta.color}`}
                      >
                        <span>{meta.symbol}</span>
                        <span className="hidden sm:inline">{meta.label}</span>
                      </span>
                      <span className="text-slate-300">
                        <span className="text-amber-400 mr-1">{natSym}</span>
                        {asp.natal_planet}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 ml-2 text-xs">
                      <span
                        className={`px-1.5 py-0.5 rounded ${
                          asp.applying
                            ? "text-emerald-400 bg-emerald-400/10"
                            : "text-slate-500 bg-slate-700/40"
                        }`}
                      >
                        {asp.applying ? "▶ aplicante" : "◀ separante"}
                      </span>
                      <span
                        className={`font-mono font-semibold ${
                          isExact ? "text-amber-400" : "text-slate-400"
                        }`}
                      >
                        {orbStr}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      <p className="text-xs text-center text-slate-600 pt-2">
        Aspectos calculados para la ubicación natal · solo aspectos mayores (orbe ≤ 8°)
      </p>
    </div>
  );
}
