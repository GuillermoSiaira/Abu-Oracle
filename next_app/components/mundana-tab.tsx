"use client";

import { useEffect, useMemo, useState } from "react";
import { useAppStore } from "@/lib/store";

interface MundanaConfig {
  type: string;
  label?: string;
  planets?: string[];
  orb?: number;
  exact_date?: string | null;
  p_value?: number | null;
  density_ratio?: number | null;
  significance: "high" | "medium" | "low";
}

interface CalendarEvent {
  type: string;
  date: string;
  description: string;
  significance: "high" | "medium" | "low";
  icon: string;
  details: Record<string, unknown>;
}

interface MundanaCalendarResponse {
  current_sky: {
    date?: string;
    timestamp?: string;
    planets?: Record<string, number> | Array<{ name: string; sign: string; degree: number; symbol?: string }>;
    active_configurations?: MundanaConfig[];
  };
  calendar: CalendarEvent[];
}

const PLANET_SYMBOLS: Record<string, string> = {
  sun: "Su",
  moon: "Mo",
  mercury: "Me",
  venus: "Ve",
  mars: "Ma",
  jupiter: "Ju",
  saturn: "Sa",
  uranus: "Ur",
  neptune: "Ne",
  pluto: "Pl",
  Sol: "Su",
  Luna: "Mo",
  Mercurio: "Me",
  Venus: "Ve",
  Marte: "Ma",
  Jupiter: "Ju",
  Saturno: "Sa",
};

const PLANET_LABELS: Record<string, string> = {
  sun: "Sol",
  moon: "Luna",
  mercury: "Mercurio",
  venus: "Venus",
  mars: "Marte",
  jupiter: "Jupiter",
  saturn: "Saturno",
  uranus: "Urano",
  neptune: "Neptuno",
  pluto: "Pluton",
};

const SIGNS = [
  "Aries",
  "Tauro",
  "Geminis",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Escorpio",
  "Sagitario",
  "Capricornio",
  "Acuario",
  "Piscis",
];

const SIGNIFICANCE_STYLES: Record<string, string> = {
  high: "border-l-amber-400/80 bg-amber-400/5",
  medium: "border-l-slate-500/70 bg-slate-800/35",
  low: "border-l-slate-700/50 bg-slate-800/20",
};

const SIGNIFICANCE_BADGE: Record<string, string> = {
  high: "border-amber-400/40 text-amber-300 bg-amber-400/10",
  medium: "border-slate-500/40 text-slate-300 bg-slate-700/20",
  low: "border-slate-700/50 text-slate-500 bg-slate-800/30",
};

const EVENT_TYPE_LABELS: Record<string, Record<string, string>> = {
  eclipse_solar: { es: "Eclipse Solar", en: "Solar Eclipse", pt: "Eclipse Solar", fr: "Eclipse Solaire" },
  eclipse_lunar: { es: "Eclipse Lunar", en: "Lunar Eclipse", pt: "Eclipse Lunar", fr: "Eclipse Lunaire" },
  mercury_retrograde: { es: "Mercurio Rx", en: "Mercury Rx", pt: "Mercurio Rx", fr: "Mercure Rx" },
  mercury_direct: { es: "Mercurio Directo", en: "Mercury Direct", pt: "Mercurio Direto", fr: "Mercure Direct" },
  planet_ingress: { es: "Ingreso", en: "Ingress", pt: "Ingresso", fr: "Entree" },
  configuration: { es: "Configuracion", en: "Configuration", pt: "Configuracao", fr: "Configuration" },
  stellium: { es: "Stellium", en: "Stellium", pt: "Stellium", fr: "Stellium" },
};

function signFromLon(lon: number): string {
  return SIGNS[Math.floor((((lon % 360) + 360) % 360) / 30) % 12];
}

function degreeInSign(lon: number): number {
  return (((lon % 30) + 30) % 30);
}

function localeFor(lang: string): string {
  if (lang === "en") return "en-US";
  if (lang === "pt") return "pt-BR";
  if (lang === "fr") return "fr-FR";
  return "es-ES";
}

function eventLabel(type: string, lang: string): string {
  return EVENT_TYPE_LABELS[type]?.[lang] ?? EVENT_TYPE_LABELS[type]?.es ?? type;
}

function normalizePlanets(
  planets: MundanaCalendarResponse["current_sky"]["planets"],
): Array<{ name: string; sign: string; degree: number; symbol: string }> {
  if (!planets) return [];
  if (Array.isArray(planets)) {
    return planets.map((planet) => ({
      name: planet.name,
      sign: planet.sign,
      degree: planet.degree,
      symbol: planet.symbol ?? PLANET_SYMBOLS[planet.name] ?? planet.name.slice(0, 2),
    }));
  }

  return Object.entries(planets).map(([name, lon]) => ({
    name: PLANET_LABELS[name] ?? name,
    sign: signFromLon(lon),
    degree: degreeInSign(lon),
    symbol: PLANET_SYMBOLS[name] ?? name.slice(0, 2).toUpperCase(),
  }));
}

function CieloAhoraSection({
  data,
  loading,
}: {
  data?: MundanaCalendarResponse["current_sky"];
  loading: boolean;
}) {
  if (loading) return <div className="h-28 rounded bg-slate-800/60 animate-pulse" />;

  const planets = normalizePlanets(data?.planets);
  return (
    <section>
      <h3 className="text-[11px] font-semibold tracking-widest uppercase text-amber-400/70 mb-3">
        Cielo Ahora
      </h3>
      <div className="grid grid-cols-2 gap-1.5">
        {planets.map((planet) => (
          <div
            key={planet.name}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded border border-slate-700/30 bg-slate-800/40"
          >
            <span className="w-6 shrink-0 text-center text-[10px] font-mono text-amber-300/80">
              {planet.symbol}
            </span>
            <span className="w-[72px] shrink-0 truncate text-[11px] text-slate-400">
              {planet.name}
            </span>
            <span className="ml-auto text-[11px] font-mono text-slate-300">
              {planet.sign} {planet.degree.toFixed(1)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function CalendarioSection({
  events,
  loading,
  lang,
}: {
  events: CalendarEvent[];
  loading: boolean;
  lang: string;
}) {
  const grouped = useMemo(() => {
    const byMonth: Record<string, CalendarEvent[]> = {};
    for (const event of events) {
      const month = event.date?.slice(0, 7) || "unknown";
      byMonth[month] = byMonth[month] ?? [];
      byMonth[month].push(event);
    }
    return Object.entries(byMonth);
  }, [events]);

  if (loading) {
    return (
      <section className="space-y-2">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-10 rounded bg-slate-800/50 animate-pulse"
            style={{ opacity: 1 - i * 0.15 }}
          />
        ))}
      </section>
    );
  }

  return (
    <section>
      <h3 className="text-[11px] font-semibold tracking-widest uppercase text-slate-500 mb-3">
        Proximos 12 meses
      </h3>
      {events.length === 0 ? (
        <p className="py-2 text-[11px] italic text-slate-600">
          No hay eventos destacados en los proximos 12 meses.
        </p>
      ) : (
        <div className="space-y-4">
          {grouped.map(([month, monthEvents]) => (
            <div key={month}>
              <div className="mb-1.5 pl-1 text-[10px] font-mono uppercase tracking-widest text-slate-600">
                {new Date(`${month}-01T00:00:00Z`).toLocaleDateString(localeFor(lang), {
                  month: "long",
                  year: "numeric",
                  timeZone: "UTC",
                })}
              </div>
              <div className="space-y-1">
                {monthEvents.map((event, index) => (
                  <div
                    key={`${event.date}-${event.type}-${index}`}
                    className={`flex items-center gap-3 rounded border-l-2 px-3 py-2 ${
                      SIGNIFICANCE_STYLES[event.significance] ?? SIGNIFICANCE_STYLES.low
                    }`}
                  >
                    <span className="w-9 shrink-0 text-center text-[10px] font-mono text-slate-400">
                      {event.icon}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[11px] text-slate-300">{event.description}</div>
                      <div className="text-[10px] font-mono text-slate-600">
                        {eventLabel(event.type, lang)}
                      </div>
                    </div>
                    <span className="shrink-0 text-[10px] font-mono text-slate-600">
                      {event.date?.slice(5)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function ConfiguracionesSection({
  configs,
  onConfigClick,
}: {
  configs: MundanaConfig[];
  onConfigClick: (config: MundanaConfig) => void;
}) {
  const formatPlanets = (planets: string[] = []) =>
    planets.map((planet) => PLANET_SYMBOLS[planet.toLowerCase()] ?? planet.slice(0, 2)).join(" ");

  return (
    <section className="border-t border-slate-800/60 pt-4">
      <h3 className="mb-3 text-[11px] font-semibold tracking-widest uppercase text-amber-400/70">
        Configuraciones Estadisticas Activas
      </h3>
      <div className="space-y-2">
        {configs.map((config, index) => (
          <button
            key={`${config.type}-${index}`}
            onClick={() => onConfigClick(config)}
            className="w-full rounded border border-slate-700/60 bg-slate-800/45 p-3 text-left transition-colors hover:border-amber-400/30 hover:bg-slate-800/75"
          >
            <div className="mb-1.5 flex items-start justify-between gap-2">
              <span className="text-[12px] font-medium leading-tight text-slate-200">
                {config.label ?? config.type}
              </span>
              <span
                className={`shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-semibold ${
                  SIGNIFICANCE_BADGE[config.significance] ?? SIGNIFICANCE_BADGE.low
                }`}
              >
                {config.significance}
              </span>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-slate-500">
              <span className="font-mono tracking-wider text-slate-400">{formatPlanets(config.planets)}</span>
              {config.orb != null && <span>orbe {config.orb.toFixed(1)}</span>}
              {config.exact_date && <span>{config.exact_date}</span>}
            </div>
            {(config.density_ratio != null || config.p_value != null) && (
              <div className="mt-1.5 flex items-center gap-3 text-[10px] text-emerald-400/70">
                {config.density_ratio != null && <span>{config.density_ratio}x baseline</span>}
                {config.p_value != null && <span>p={config.p_value}</span>}
              </div>
            )}
          </button>
        ))}
      </div>
    </section>
  );
}

export function MundanaTab() {
  const { lang, setPendingLillyEvent } = useAppStore();
  const [calendarData, setCalendarData] = useState<MundanaCalendarResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetch("/api/mundana/calendar?months=12")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled && data) setCalendarData(data);
      })
      .catch((err) => console.error("[mundana-tab] calendar fetch error", err))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const activeConfigs = calendarData?.current_sky?.active_configurations ?? [];

  return (
    <div className="space-y-6 overflow-y-auto p-4" style={{ maxHeight: "calc(100vh - 160px)" }}>
      <CieloAhoraSection data={calendarData?.current_sky} loading={loading} />
      <CalendarioSection events={calendarData?.calendar ?? []} loading={loading} lang={lang} />
      {activeConfigs.length > 0 && (
        <ConfiguracionesSection
          configs={activeConfigs}
          onConfigClick={(config) =>
            setPendingLillyEvent({
              type: "mundana_config",
              payload: { config, lang },
            })
          }
        />
      )}
    </div>
  );
}
