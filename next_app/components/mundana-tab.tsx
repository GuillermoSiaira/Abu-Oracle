"use client";

import { useState, useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { UI } from "@/lib/i18n";
import { ABU_BASE_URL } from "@/services/abu";
import { getAbuAuthHeaders } from "@/lib/abu-auth";

// ── Types ─────────────────────────────────────────────────────────────────────

interface MundanaConfig {
  type:          string;
  label:         string;
  planets:       string[];
  orb:           number;
  exact_date:    string | null;
  days_to_exact?: number | null;
  p_value:       number | null;
  density_ratio: number | null;
  significance:  "high" | "medium" | "low";
}

interface CurrentSky {
  date:                  string;
  planets:               Record<string, number>;
  active_configurations: MundanaConfig[];
}

// ── Constants ─────────────────────────────────────────────────────────────────

const PLANET_SYMBOLS: Record<string, string> = {
  sun: "☉", moon: "☽", mercury: "☿", venus: "♀", mars: "♂",
  jupiter: "♃", saturn: "♄", uranus: "♅", neptune: "♆", pluto: "♇",
};

const SIGNIFICANCE_BADGE: Record<string, { label: string; classes: string }> = {
  high:   { label: "Alta",  classes: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
  medium: { label: "Media", classes: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
  low:    { label: "Baja",  classes: "bg-slate-700/50 text-slate-500 border-slate-600/30" },
};

// ── Component ─────────────────────────────────────────────────────────────────

export function MundanaTab() {
  const { lang, setPendingLillyEvent } = useAppStore();
  const t = UI[lang];

  const [sky,      setSky]      = useState<CurrentSky | null>(null);
  const [upcoming, setUpcoming] = useState<MundanaConfig[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [filter,   setFilter]   = useState<"all" | "high" | "medium">("all");
  const [selectedConfig, setSelectedConfig] = useState<MundanaConfig | null>(null);

  // ── Fetch sky + forecast ────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    getAbuAuthHeaders().then(async (headers) => {
      try {
        const [skyRes, forecastRes] = await Promise.all([
          fetch(`${ABU_BASE_URL}/api/mundana/sky`,           { headers }),
          fetch(`${ABU_BASE_URL}/api/mundana/forecast?days=90`, { headers }),
        ]);

        const skyData      = skyRes.ok      ? await skyRes.json()      : null;
        const forecastData = forecastRes.ok ? await forecastRes.json() : [];

        if (!cancelled) {
          if (skyData) setSky(skyData);
          setUpcoming(Array.isArray(forecastData) ? forecastData : []);
        }
      } catch (err) {
        console.error('[mundana-tab] fetch error', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    });

    return () => { cancelled = true; };
  }, []);

  // ── Trigger Lilly ───────────────────────────────────────────────────────────
  const handleLillyInterpret = (config: MundanaConfig) => {
    setSelectedConfig(config);
    setPendingLillyEvent({
      type: 'mundana_config',
      payload: { config, lang },
    });
  };

  const handleLillyAll = () => {
    if (!sky) return;
    const active = sky.active_configurations;
    const primaryConfig = active.find(c => c.significance === 'high') ?? active[0] ?? null;
    setPendingLillyEvent({
      type: 'mundana_config',
      payload: { config: primaryConfig, lang },
    });
  };

  // ── Filter upcoming ─────────────────────────────────────────────────────────
  const filteredUpcoming = upcoming.filter((c) => {
    if (filter === "all")    return true;
    if (filter === "high")   return c.significance === "high";
    if (filter === "medium") return c.significance === "high" || c.significance === "medium";
    return true;
  });

  // ── Helpers ─────────────────────────────────────────────────────────────────
  const formatPlanets = (planets: string[]) =>
    planets.map(p => PLANET_SYMBOLS[p.toLowerCase()] ?? p[0].toUpperCase()).join(" ");

  const formatPValue = (p: number | null) => {
    if (p == null) return null;
    if (p < 0.001) return "p < 0.001";
    return `p = ${p.toFixed(3)}`;
  };

  // ── Loading state ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="p-4 space-y-3">
        {[1, 2, 3].map(i => (
          <div key={i}
            className="h-20 rounded-lg bg-slate-800/60 animate-pulse"
            style={{ opacity: 1 - i * 0.25 }}
          />
        ))}
      </div>
    );
  }

  const activeConfigs = sky?.active_configurations ?? [];

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="p-4 space-y-6 overflow-y-auto" style={{ maxHeight: "calc(100vh - 160px)" }}>

      {/* ── Header ── */}
      <div>
        <h3 className="text-[13px] font-semibold tracking-wider text-amber-300/90">
          {t.mundanaTitle}
        </h3>
        <p className="text-[10px] text-slate-500 mt-0.5">{t.mundanaSubtitle}</p>
      </div>

      {/* ── Configuraciones activas ── */}
      <section>
        <h4 className="text-[11px] font-semibold tracking-widest uppercase text-amber-400/60 mb-3">
          {t.mundanaActive}
        </h4>

        {activeConfigs.length === 0 ? (
          <p className="text-[11px] text-slate-600 italic">{t.mundanaNoActive}</p>
        ) : (
          <div className="space-y-2">
            {activeConfigs.map((config, i) => {
              const badge = SIGNIFICANCE_BADGE[config.significance] ?? SIGNIFICANCE_BADGE.low;
              const isSelected = selectedConfig?.type === config.type;
              return (
                <button
                  key={i}
                  onClick={() => handleLillyInterpret(config)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors
                    ${isSelected
                      ? "border-amber-400/50 bg-amber-400/8"
                      : "border-slate-700/60 bg-slate-800/50 hover:border-amber-400/30 hover:bg-slate-800/80"
                    }`}
                >
                  {/* Row 1: label + badge */}
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="text-[12px] text-slate-200 font-medium leading-tight">
                      {config.label}
                    </span>
                    <span className={`text-[9px] font-semibold px-2 py-0.5 rounded-full border shrink-0 ${badge.classes}`}>
                      {badge.label}
                    </span>
                  </div>

                  {/* Row 2: planetas + orbe */}
                  <div className="flex items-center gap-3 text-[11px]">
                    <span className="text-slate-400 font-mono tracking-wider">
                      {formatPlanets(config.planets)}
                    </span>
                    <span className="text-slate-600">·</span>
                    <span className="text-slate-500">orbe {config.orb.toFixed(1)}°</span>
                    {config.exact_date && (
                      <>
                        <span className="text-slate-600">·</span>
                        <span className="text-slate-500">
                          {t.mundanaExact} {config.exact_date}
                        </span>
                      </>
                    )}
                  </div>

                  {/* Row 3: estadísticas H_mundana_A */}
                  {(config.density_ratio != null || config.p_value != null) && (
                    <div className="flex items-center gap-3 mt-1.5 text-[10px] text-emerald-400/70">
                      {config.density_ratio != null && (
                        <span>{config.density_ratio}× {t.mundanaDensity}</span>
                      )}
                      {config.p_value != null && (
                        <span className="text-slate-500">{formatPValue(config.p_value)}</span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Botón Lilly interpreta todo ── */}
      {activeConfigs.length > 0 && (
        <button
          onClick={handleLillyAll}
          className="w-full py-2.5 px-4 rounded-lg border border-amber-400/30 bg-amber-400/5
                     text-amber-300/80 text-[12px] font-medium tracking-wide
                     hover:bg-amber-400/10 hover:border-amber-400/50 transition-colors"
        >
          {t.mundanaLillyButton}
        </button>
      )}

      {/* ── Pronóstico próximas 90 días ── */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-[11px] font-semibold tracking-widest uppercase text-amber-400/60">
            {t.mundanaUpcoming}
          </h4>
          {/* Filtro de significancia */}
          <div className="flex gap-1">
            {(["all", "high", "medium"] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`text-[9px] px-2 py-0.5 rounded-full border transition-colors
                  ${filter === f
                    ? "border-amber-400/50 bg-amber-400/15 text-amber-300"
                    : "border-slate-700/50 text-slate-500 hover:border-slate-600"
                  }`}
              >
                {f === "all"    ? t.mundanaFilterAll
                 : f === "high" ? t.mundanaFilterHigh
                                : t.mundanaFilterMedium}
              </button>
            ))}
          </div>
        </div>

        {filteredUpcoming.length === 0 ? (
          <p className="text-[11px] text-slate-600 italic">{t.mundanaNoUpcoming}</p>
        ) : (
          <div className="space-y-1.5">
            {filteredUpcoming.map((config, i) => {
              const badge = SIGNIFICANCE_BADGE[config.significance] ?? SIGNIFICANCE_BADGE.low;
              return (
                <button
                  key={i}
                  onClick={() => handleLillyInterpret(config)}
                  className="w-full text-left flex items-center gap-3 px-3 py-2 rounded-md
                             border border-slate-700/40 bg-slate-800/40
                             hover:border-amber-400/25 hover:bg-slate-800/70 transition-colors"
                >
                  {/* Fecha exacta */}
                  <span className="text-[10px] font-mono text-slate-500 shrink-0 w-[72px]">
                    {config.exact_date ?? "—"}
                  </span>

                  {/* Label */}
                  <span className="text-[11px] text-slate-300 flex-1 truncate">
                    {formatPlanets(config.planets)} {config.label}
                  </span>

                  {/* Días hasta exactitud */}
                  {config.days_to_exact != null && (
                    <span className="text-[10px] text-slate-600 shrink-0">
                      {config.days_to_exact} {t.mundanaDaysTo}
                    </span>
                  )}

                  {/* Badge significancia */}
                  <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full border shrink-0 ${badge.classes}`}>
                    {badge.label}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Fecha del cielo ── */}
      {sky?.date && (
        <p className="text-[10px] text-slate-700 font-mono text-right">
          {sky.date.slice(0, 16).replace("T", " ")} UTC
        </p>
      )}

    </div>
  );
}
