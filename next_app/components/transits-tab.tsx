"use client";

import { useState, useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";

// ── Constants ────────────────────────────────────────────────────────────────

const SIGNS = [
  "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
  "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
];

const ASPECT_META: Record<string, {
  label: string; symbol: string;
  color: string; barColor: string;
}> = {
  conjunction: { label: "Conjunción",  symbol: "☌", color: "text-amber-400",   barColor: "rgba(251,191,36,0.55)"   },
  opposition:  { label: "Oposición",   symbol: "☍", color: "text-red-400",     barColor: "rgba(248,113,113,0.55)"  },
  square:      { label: "Cuadratura",  symbol: "□", color: "text-orange-400",  barColor: "rgba(251,146,60,0.55)"   },
  trine:       { label: "Trígono",     symbol: "△", color: "text-emerald-400", barColor: "rgba(52,211,153,0.55)"   },
  sextile:     { label: "Sextil",      symbol: "⚹", color: "text-teal-400",    barColor: "rgba(45,212,191,0.55)"   },
  semisextile: { label: "Semisextil",  symbol: "⚺", color: "text-slate-400",   barColor: "rgba(148,163,184,0.35)"  },
  quincunx:    { label: "Quincuncio",  symbol: "⚻", color: "text-violet-400",  barColor: "rgba(167,139,250,0.55)"  },
};

const PLANET_SYMBOLS: Record<string, string> = {
  Sun:"☉", Moon:"☽", Mercury:"☿", Venus:"♀", Mars:"♂",
  Jupiter:"♃", Saturn:"♄", Uranus:"♅", Neptune:"♆", Pluto:"♇",
  "North Node":"☊", "South Node":"☋", ASC:"AC", MC:"MC",
};

const PLANET_LABELS: Record<string, Record<string, string>> = {
  Sun:      { es:"Sol",      en:"Sun",      pt:"Sol",      fr:"Soleil"  },
  Moon:     { es:"Luna",     en:"Moon",     pt:"Lua",      fr:"Lune"    },
  Mercury:  { es:"Mercurio", en:"Mercury",  pt:"Mercúrio", fr:"Mercure" },
  Venus:    { es:"Venus",    en:"Venus",    pt:"Vênus",    fr:"Vénus"   },
  Mars:     { es:"Marte",    en:"Mars",     pt:"Marte",    fr:"Mars"    },
  Jupiter:  { es:"Júpiter",  en:"Jupiter",  pt:"Júpiter",  fr:"Jupiter" },
  Saturn:   { es:"Saturno",  en:"Saturn",   pt:"Saturno",  fr:"Saturne" },
  Uranus:   { es:"Urano",    en:"Uranus",   pt:"Urano",    fr:"Uranus"  },
  Neptune:  { es:"Neptuno",  en:"Neptune",  pt:"Netuno",   fr:"Neptune" },
  Pluto:    { es:"Plutón",   en:"Pluto",    pt:"Plutão",   fr:"Pluton"  },
  ASC:      { es:"ASC",      en:"ASC",      pt:"ASC",      fr:"ASC"     },
  MC:       { es:"MC",       en:"MC",       pt:"MC",       fr:"MC"      },
  "North Node": { es:"N.Node", en:"N.Node", pt:"N.Node",   fr:"N.Nœud" },
  "South Node": { es:"S.Node", en:"S.Node", pt:"S.Node",   fr:"N.Desc" },
};

function planetLabel(name: string, lang: string): string {
  return PLANET_LABELS[name]?.[lang] ?? PLANET_LABELS[name]?.["en"] ?? name;
}

const PLANET_ORDER = ["Pluto","Neptune","Uranus","Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"];
const MONTHS_ES    = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];

// Speed classes visible per window size (wider window → less noise)
const SPEED_CLASSES_BY_WINDOW: { maxMonths: number; classes: string[] }[] = [
  { maxMonths: 0.5, classes: ["slow", "fast", "lunar"] }, // ≤ ~2 semanas
  { maxMonths: 6,   classes: ["slow", "fast"] },          // ≤ 6 meses
  { maxMonths: 99,  classes: ["slow"] },                  // > 6 meses
];

// ── Helpers ──────────────────────────────────────────────────────────────────

function daysBetween(a: Date, b: Date): number {
  return (b.getTime() - a.getTime()) / 86_400_000;
}

/** Returns 0–100 clamped percentage position of `date` within [startDate, startDate + totalDays]. */
function dateToPct(date: Date, startDate: Date, totalDays: number): number {
  return Math.max(0, Math.min(100, (daysBetween(startDate, date) / totalDays) * 100));
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS_ES[d.getMonth()]} ${d.getFullYear()}`;
}

// ── Component ────────────────────────────────────────────────────────────────

export function TransitsTab() {
  const abuData            = useAppStore((s) => s.abuData);
  const birthData          = useAppStore((s) => s.birthData);
  const timeline           = useAppStore((s) => s.timeline);
  const lang               = useAppStore((s) => s.lang);
  const setPendingLillyEvent = useAppStore((s) => s.setPendingLillyEvent);

  const [windowMonths, setWindowMonths]   = useState(18);
  const [onlyActive, setOnlyActive]       = useState(false);
  const activeSpeedClasses = SPEED_CLASSES_BY_WINDOW.find((r) => windowMonths <= r.maxMonths)?.classes ?? ["slow"];
  const [barAreaPx, setBarAreaPx]         = useState(0);

  interface TooltipState {
    rowId: string; screenX: number; screenY: number;
    planet: string; sym: string; natSym: string; natalPlanet: string;
    meta: { label: string; symbol: string; color: string; barColor: string };
    exact_date: string; ingress_date: string; egress_date: string; is_active: boolean;
  }
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const hoveredId = tooltip?.rowId ?? null;

  interface FirdariaTooltip {
    screenX: number; screenY: number;
    majorPlanet: string; minorPlanet: string;
    dateStart: string; dateEnd: string; isActive: boolean;
  }
  const [firTooltip, setFirTooltip] = useState<FirdariaTooltip | null>(null);
  const barAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = barAreaRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setBarAreaPx(entry.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const subjectName  = (birthData as any)?.userName || (abuData as any)?.person?.name || "Anónimo";
  const transits     = timeline?.transits_window ?? [];
  const firdariaRaw  = timeline?.firdaria ?? [];

  // ── Window bounds ─────────────────────────────────────────────────────────
  const today      = new Date();
  const ganttStart = new Date(today);
  ganttStart.setMonth(ganttStart.getMonth() - windowMonths);
  const ganttEnd   = new Date(today);
  ganttEnd.setMonth(ganttEnd.getMonth() + windowMonths);
  const totalDays  = daysBetween(ganttStart, ganttEnd);
  const todayPct   = dateToPct(today, ganttStart, totalDays);

  // ── Firdaria major periods (derived by grouping minor sub-periods) ─────────
  const majorMap = new Map<string, { start: Date; end: Date }>();
  for (const f of firdariaRaw) {
    const s = new Date(f.date_start);
    const e = new Date(f.date_end);
    if (!majorMap.has(f.major_planet)) {
      majorMap.set(f.major_planet, { start: s, end: e });
    } else {
      const r = majorMap.get(f.major_planet)!;
      if (s < r.start) r.start = s;
      if (e > r.end)   r.end   = e;
    }
  }
  const majorPeriods = Array.from(majorMap.entries())
    .map(([planet, r]) => ({ planet, ...r }))
    .filter((m) => m.start <= ganttEnd && m.end >= ganttStart);

  const minorVisible = firdariaRaw.filter((f) => {
    const s = new Date(f.date_start);
    const e = new Date(f.date_end);
    return s <= ganttEnd && e >= ganttStart;
  });

  // ── Group transits by planet (respecting onlyActive + speed_class filters) ─
  const visibleTransits = (onlyActive ? transits.filter((t) => t.is_active) : transits)
    .filter((t) => activeSpeedClasses.includes((t as any).speed_class ?? "slow"));
  const grouped = new Map<string, typeof transits>();
  for (const t of visibleTransits) {
    if (!grouped.has(t.transit_planet)) grouped.set(t.transit_planet, []);
    grouped.get(t.transit_planet)!.push(t);
  }
  const sortedPlanets = Array.from(grouped.keys()).sort(
    (a, b) => PLANET_ORDER.indexOf(a) - PLANET_ORDER.indexOf(b)
  );
  const activeCount = transits.filter((t) => t.is_active).length;

  // ── Month axis labels ──────────────────────────────────────────────────────
  const monthLabels: { label: string; pct: number }[] = [];
  {
    const d = new Date(ganttStart);
    d.setDate(1);
    d.setMonth(d.getMonth() + 1);
    while (d < ganttEnd) {
      const pct = dateToPct(d, ganttStart, totalDays);
      const lbl = d.getMonth() === 0
        ? `${MONTHS_ES[0]} '${String(d.getFullYear()).slice(2)}`
        : MONTHS_ES[d.getMonth()];
      monthLabels.push({ label: lbl, pct });
      d.setMonth(d.getMonth() + 1);
    }
  }

  // ── Guards ─────────────────────────────────────────────────────────────────
  if (!abuData) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        Ingresá tus datos natales para ver los tránsitos activos.
      </div>
    );
  }

  if (transits.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        No hay tránsitos de planetas lentos disponibles.
        {!timeline && " Cargando línea de tiempo…"}
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-3 text-xs select-none">

      {/* ── Controls ────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-slate-400 font-semibold">Ventana:</span>
        {([0.25, 6, 12, 18] as const).map((m) => (
          <button
            key={m}
            onClick={() => setWindowMonths(m)}
            className={`px-2 py-1 rounded transition-colors border ${
              windowMonths === m
                ? "bg-amber-400/20 text-amber-300 border-amber-400/40"
                : "bg-slate-700/40 text-slate-400 border-slate-700/60 hover:border-slate-500/70"
            }`}
          >
            {m === 0.25 ? "± 1s" : `± ${m}m`}
          </button>
        ))}
        <button
          onClick={() => setOnlyActive((v) => !v)}
          className={`ml-auto px-2 py-1 rounded transition-colors border flex items-center gap-1.5 ${
            onlyActive
              ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
              : "bg-slate-700/40 text-slate-400 border-slate-700/60 hover:border-slate-500/70"
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${onlyActive ? "bg-emerald-400" : "bg-slate-500"}`} />
          Solo activos {activeCount > 0 && `(${activeCount})`}
        </button>
        <span className="text-slate-600">
          {visibleTransits.length}/{transits.length} ·{" "}
          {activeSpeedClasses.includes("lunar") ? "lentos+rápidos+luna" :
           activeSpeedClasses.includes("fast")  ? "lentos+rápidos" : "planetas lentos"}
        </span>
      </div>

      {/* ── Gantt chart ─────────────────────────────────────────────────── */}
      {/* isolation:isolate creates a stacking context so z:-1 children sit above the container background */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 relative" style={{ isolation: "isolate" }}>

        {/* ── Firdaria overlay — z:-1 keeps it behind rows but above container bg ── */}
        <div className="absolute inset-0 flex pointer-events-none overflow-hidden" style={{ zIndex: -1 }}>
          <div className="w-[150px] shrink-0" />
          <div className="flex-1 relative" ref={barAreaRef}>
            {/* Major bands */}
            {majorPeriods.map((m) => {
              const lp     = dateToPct(m.start, ganttStart, totalDays);
              const wp     = dateToPct(m.end,   ganttStart, totalDays) - lp;
              if (wp <= 0) return null;
              const bandPx = (wp / 100) * barAreaPx;
              // Find the active minor period for this major planet (for tooltip)
              const activMinor = minorVisible.find(f => f.major_planet === m.planet && f.is_active);
              const anyMinor   = minorVisible.find(f => f.major_planet === m.planet);
              const minorLabel = (activMinor ?? anyMinor)?.minor_planet ?? "—";
              return (
                <div
                  key={`maj-${m.planet}`}
                  className="absolute inset-y-0 cursor-default"
                  style={{
                    left: `${lp}%`, width: `${wp}%`,
                    background: "rgba(127,119,221,0.13)",
                    pointerEvents: "auto",
                  }}
                  onMouseEnter={(e) => {
                    const r = e.currentTarget.getBoundingClientRect();
                    setFirTooltip({
                      screenX: r.left + r.width / 2, screenY: r.top + 64,
                      majorPlanet: m.planet, minorPlanet: minorLabel,
                      dateStart: m.start.toISOString().slice(0, 10),
                      dateEnd:   m.end.toISOString().slice(0, 10),
                      isActive:  activMinor !== undefined,
                    });
                  }}
                  onMouseLeave={() => setFirTooltip(null)}
                >
                  {bandPx > 120 && (
                    <span className="absolute left-1 text-[9px] text-purple-300/50 whitespace-nowrap pointer-events-none" style={{ top: 60 }}>
                      ▶ Firdaria {m.planet} (mayor)
                    </span>
                  )}
                </div>
              );
            })}
            {/* Minor bands */}
            {minorVisible.map((f, i) => {
              const s      = new Date(f.date_start);
              const e      = new Date(f.date_end);
              const lp     = dateToPct(s, ganttStart, totalDays);
              const wp     = dateToPct(e, ganttStart, totalDays) - lp;
              if (wp <= 0) return null;
              const bandPx = (wp / 100) * barAreaPx;
              return (
                <div
                  key={`min-${i}`}
                  className="absolute inset-y-0"
                  style={{
                    left: `${lp}%`,
                    width: `${wp}%`,
                    background: f.is_active ? "rgba(29,158,117,0.22)" : "rgba(29,158,117,0.10)",
                    borderLeft: f.is_active ? "1px solid rgba(29,158,117,0.35)" : undefined,
                  }}
                >
                  {bandPx > 120 && (
                    <span className="absolute left-1 text-[9px] text-teal-400/45 whitespace-nowrap pointer-events-none" style={{ top: 78 }}>
                      ↳ {f.minor_planet}
                    </span>
                  )}
                </div>
              );
            })}
            {/* Today line */}
            <div
              className="absolute top-0 bottom-0 w-px bg-amber-400/55"
              style={{ left: `${todayPct}%` }}
            />
          </div>
        </div>

        {/* Month axis header — static (does NOT scroll, sibling to rows) */}
        <div
          className="flex shrink-0 border-b border-slate-700/40 bg-slate-900/60 rounded-t-xl"
          style={{ height: 56, position: "relative", zIndex: 10 }}
        >
          <div className="w-[150px] shrink-0" />
          <div className="flex-1 relative">
            {monthLabels.map((l, i) => (
              <span
                key={i}
                className="absolute -translate-x-1/2 text-slate-500 pointer-events-none"
                style={{
                  left: `${l.pct}%`,
                  top: 0,
                  writingMode: "vertical-rl",
                  transform: "rotate(180deg)",
                  height: 56,
                  fontSize: 10,
                  display: "flex",
                  justifyContent: "center",
                  overflow: "visible",
                }}
              >
                {l.label}
              </span>
            ))}
            {/* Today tick in axis */}
            <div
              className="absolute top-0 bottom-0 w-px bg-amber-400/70"
              style={{ left: `${todayPct}%` }}
            />
          </div>
        </div>

        {/* Scrollable rows — only this div scrolls; firdaria overlay is above it */}
        <div style={{ overflowY: "auto", height: "calc(100vh - 220px)", position: "relative", zIndex: 1 }}>

          {/* ── Transit rows ──────────────────────────────────────────────── */}
          {sortedPlanets.map((planet) => {
            const aspects = grouped.get(planet)!;
            const sym     = PLANET_SYMBOLS[planet] ?? planet[0];
            return (
              <div key={planet} className="border-b border-slate-700/25 last:border-0">
                {aspects.map((t, i) => {
                  const meta    = ASPECT_META[t.aspect] ?? {
                    label: t.aspect, symbol: "?",
                    color: "text-slate-400", barColor: "rgba(148,163,184,0.4)",
                  };
                  const ingress  = new Date(t.ingress_date);
                  const egress   = new Date(t.egress_date);
                  const exact    = new Date(t.exact_date);
                  const lp       = dateToPct(ingress, ganttStart, totalDays);
                  const rp       = dateToPct(egress,  ganttStart, totalDays);
                  const wp       = Math.max(rp - lp, 0.4);
                  const exactPct = dateToPct(exact, ganttStart, totalDays);
                  const rowId    = `${planet}-${t.natal_planet}-${t.aspect}-${i}`;
                  const isHov    = hoveredId === rowId;
                  const natSym   = PLANET_SYMBOLS[t.natal_planet] ?? t.natal_planet[0];

                  return (
                    <div key={rowId} className="flex items-center h-8">

                      {/* Label column */}
                      <div className="w-[150px] shrink-0 px-2 flex items-center justify-between gap-1 z-10">
                        {/* Transit planet: symbol + name — first row of group only */}
                        <div className="flex items-center gap-1 w-[68px] shrink-0 overflow-hidden">
                          {i === 0 ? (
                            <>
                              <span className="text-amber-400 font-semibold shrink-0">{sym}</span>
                              <span className="text-[10px] text-amber-400/55 truncate">{planetLabel(planet, lang)}</span>
                            </>
                          ) : (
                            <span className="w-full" />
                          )}
                        </div>
                        {/* Natal planet: symbol + abbreviated name + aspect symbol */}
                        <div className="flex items-center gap-0.5 text-slate-400 shrink-0">
                          <span className="text-[11px]">{natSym}</span>
                          <span className="text-[9px] text-slate-500 max-w-[30px] truncate">{planetLabel(t.natal_planet, lang)}</span>
                          <span className={`opacity-80 ${meta.color}`}>{meta.symbol}</span>
                        </div>
                      </div>

                      {/* Bar area */}
                      <div className="flex-1 relative h-full">

                        {/* Bar */}
                        {lp < 100 && rp > 0 && (
                          <button
                            className="absolute top-1/2 -translate-y-1/2 h-[14px] rounded-sm z-20 transition-opacity"
                            style={{
                              left:    `${lp}%`,
                              width:   `${wp}%`,
                              background: meta.barColor,
                              opacity: isHov ? 1 : 0.75,
                              boxShadow: isHov
                                ? `0 0 0 1px ${meta.barColor}, 0 2px 6px rgba(0,0,0,0.4)`
                                : "none",
                            }}
                            onMouseEnter={(e) => {
                              const r = e.currentTarget.getBoundingClientRect();
                              setTooltip({
                                rowId, screenX: r.left + r.width / 2, screenY: r.top,
                                planet, sym, natSym, natalPlanet: t.natal_planet, meta,
                                exact_date: t.exact_date, ingress_date: t.ingress_date,
                                egress_date: t.egress_date, is_active: t.is_active,
                              });
                            }}
                            onMouseLeave={() => setTooltip(null)}
                            onClick={() =>
                              setPendingLillyEvent({
                                type: "click_transit",
                                payload: {
                                  transit_planet: planet,
                                  transit_sign:   "",
                                  transit_deg:    0,
                                  aspects: [{
                                    natal_planet: t.natal_planet,
                                    aspect:       t.aspect,
                                    orb:          0,
                                    applying:     true,
                                  }],
                                  transit_date:   t.exact_date,
                                  subject_name:   subjectName,
                                  lang,
                                },
                              })
                            }
                          />
                        )}

                        {/* Exact-date marker */}
                        {exactPct > 0 && exactPct < 100 && (
                          <div
                            className="absolute top-1 bottom-1 w-0.5 bg-white/22 z-20 pointer-events-none"
                            style={{ left: `${exactPct}%` }}
                          />
                        )}

                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      <p className="text-center text-slate-600 pt-1">
        {activeSpeedClasses.includes("lunar")
          ? "Lentos · Rápidos · Luna · haz click en una barra para consultar a Lilly"
          : activeSpeedClasses.includes("fast")
          ? "Planetas rápidos + lentos · Sol · Mercurio · Venus · Marte · Júpiter→Plutón · haz click para Lilly"
          : "Planetas lentos · Júpiter · Saturno · Urano · Neptuno · Plutón · haz click en una barra para consultar a Lilly"}
      </p>

      {/* ── Firdaria tooltip ─────────────────────────────────────────────── */}
      {firTooltip && (() => {
        const vw  = typeof window !== "undefined" ? window.innerWidth : 800;
        const cx  = Math.min(Math.max(firTooltip.screenX, 115), vw - 115);
        return (
          <div
            className="bg-slate-900/95 border border-purple-500/30 rounded-lg px-3 py-2 space-y-1 shadow-xl pointer-events-none text-xs"
            style={{ position: "fixed", left: cx, top: firTooltip.screenY, transform: "translateX(-50%)", zIndex: 9999 }}
          >
            <div className="font-semibold text-purple-300 whitespace-nowrap">
              ▶ Firdaria {firTooltip.majorPlanet} (mayor)
            </div>
            <div className="text-teal-400/80">↳ Menor: {firTooltip.minorPlanet}</div>
            <div className="text-slate-500 space-y-0.5">
              <div>Inicio:&nbsp;<span className="text-slate-300">{fmtDate(firTooltip.dateStart)}</span></div>
              <div>Fin:&nbsp;<span className="text-slate-300">{fmtDate(firTooltip.dateEnd)}</span></div>
            </div>
            {firTooltip.isActive && <div className="text-emerald-400 font-medium">● Período activo</div>}
          </div>
        );
      })()}

      {/* ── Global tooltip — position:fixed escapes any overflow clipping ── */}
      {tooltip && (() => {
        const vw       = typeof window !== "undefined" ? window.innerWidth : 800;
        const estW     = 210;
        const cx       = Math.min(Math.max(tooltip.screenX, estW / 2 + 8), vw - estW / 2 - 8);
        return (
          <div
            className="bg-slate-900/95 border border-slate-600/60 rounded-lg px-3 py-2 space-y-1 shadow-xl pointer-events-none text-xs"
            style={{ position: "fixed", left: cx, top: tooltip.screenY - 8, transform: "translate(-50%,-100%)", zIndex: 9999 }}
          >
            <div className="font-semibold text-slate-100 whitespace-nowrap">
              {tooltip.sym} {tooltip.planet}&nbsp;
              <span className={tooltip.meta.color}>{tooltip.meta.symbol}</span>&nbsp;
              {tooltip.natSym} {tooltip.natalPlanet}
            </div>
            <div className={`${tooltip.meta.color} opacity-80`}>{tooltip.meta.label}</div>
            <div className="text-slate-500 space-y-0.5">
              <div>Exacto:&nbsp;<span className="text-slate-300">{fmtDate(tooltip.exact_date)}</span></div>
              <div>Ingreso:&nbsp;<span className="text-slate-300">{fmtDate(tooltip.ingress_date)}</span></div>
              <div>Egreso:&nbsp;<span className="text-slate-300">{fmtDate(tooltip.egress_date)}</span></div>
            </div>
            {tooltip.is_active && <div className="text-emerald-400 font-medium">● Activo ahora</div>}
          </div>
        );
      })()}
    </div>
  );
}
