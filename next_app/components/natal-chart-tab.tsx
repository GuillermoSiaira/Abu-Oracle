"use client";

import { useAppStore } from "@/lib/store";
import { ZodiacWheel } from "./zodiac-wheel";
import { useState, useMemo } from "react";

// ------------------------------------
// Utils
// ------------------------------------
function getSignFromLongitude(long: number): string {
  const signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
  ];
  const index = Math.floor(((long % 360) + 360) % 360 / 30);
  return signs[index];
}

function formatDegMin(longitude: number): string {
  const degInSign = ((longitude % 360) + 360) % 360 % 30;
  const deg = Math.floor(degInSign);
  const min = Math.round((degInSign - deg) * 60);
  return `${deg}°${String(min).padStart(2, "0")}'`;
}

// ------------------------------------
// Dignity helpers
// ------------------------------------
type DignityInfo = { label: string; color: string; score: number };

function getDignityInfo(dignity: any): DignityInfo {
  if (!dignity) return { label: "Peregrine", color: "text-slate-500", score: 0 };
  if (dignity.domicile  || dignity.kind === "domicile")  return { label: "Domicile",  color: "text-amber-400",  score: dignity.score ?? 5  };
  if (dignity.exaltation|| dignity.kind === "exaltation")return { label: "Exaltation",color: "text-yellow-300", score: dignity.score ?? 4  };
  if (dignity.detriment || dignity.kind === "detriment") return { label: "Detriment", color: "text-red-400",    score: dignity.score ?? -5 };
  if (dignity.fall      || dignity.kind === "fall")      return { label: "Fall",       color: "text-orange-400",score: dignity.score ?? -4 };
  return { label: "Peregrine", color: "text-slate-500", score: dignity.score ?? 0 };
}

function dignityBadgeClass(d: DignityInfo): string {
  if (d.label === "Domicile" || d.label === "Exaltation")
    return "border-amber-800/40 bg-amber-900/20 text-amber-400";
  if (d.label === "Detriment" || d.label === "Fall")
    return "border-red-800/30 bg-red-900/10 text-red-400";
  return "border-slate-700/40 bg-slate-800/20 text-slate-500";
}

// Dignity scores per D4 (matches backend extended_calc.py)
const DIGNITY_SCORES_MAP: Record<string, number> = {
  domicile: 5, exaltation: 4, peregrine: 0, detriment: -4, fall: -5,
};

/** Build DignityInfo from a canonical string ("domicile" | "exaltation" | …) */
function getDignityInfoFromString(s: string): DignityInfo {
  const lower = (s ?? "peregrine").toLowerCase();
  const score = DIGNITY_SCORES_MAP[lower] ?? 0;
  const label = lower.charAt(0).toUpperCase() + lower.slice(1);
  if (lower === "domicile" || lower === "exaltation")
    return { label, color: "text-amber-400", score };
  if (lower === "detriment" || lower === "fall")
    return { label, color: "text-red-400", score };
  return { label: "Peregrine", color: "text-slate-500", score: 0 };
}

function fmtScore(n: number): string {
  return n > 0 ? `+${n}` : n < 0 ? `${n}` : "0";
}

// ------------------------------------
// Aspect computation (natal aspects)
// ------------------------------------
const NATAL_ASPECTS = [
  { type: "conjunction",  angle: 0,   orb: 8,  symbol: "☌" },
  { type: "sextile",      angle: 60,  orb: 6,  symbol: "⚹" },
  { type: "square",       angle: 90,  orb: 8,  symbol: "□" },
  { type: "trine",        angle: 120, orb: 8,  symbol: "△" },
  { type: "opposition",   angle: 180, orb: 8,  symbol: "☍" },
];

function computeClosestAspect(
  planets: any[],
  targetName: string
): { type: string; planet: string; orb: number; symbol: string } | null {
  const target = planets.find((p) => p.name === targetName);
  if (!target) return null;

  let closest: { type: string; planet: string; orb: number; symbol: string } | null = null;
  let minOrb = Infinity;

  for (const other of planets) {
    if (other.name === targetName) continue;
    const diff = Math.abs(
      ((Math.abs(target.longitude - other.longitude) % 360) + 360) % 360
    );
    const normalised = diff > 180 ? 360 - diff : diff;

    for (const asp of NATAL_ASPECTS) {
      const orb = Math.abs(normalised - asp.angle);
      if (orb <= asp.orb && orb < minOrb) {
        minOrb = orb;
        closest = { type: asp.type, planet: other.name, orb, symbol: asp.symbol };
      }
    }
  }
  return closest;
}

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀",
  Mars: "♂", Jupiter: "♃", Saturn: "♄",
  Uranus: "♅", Neptune: "♆", Pluto: "♇",
};

// ------------------------------------
// Planet Card
// ------------------------------------
interface PlanetCardProps {
  planet: any;
  allPlanets: any[];
  onClick: (p: any) => void;
}

function PlanetCard({ planet, allPlanets, onClick }: PlanetCardProps) {
  const sym = PLANET_SYMBOLS[planet.name] ?? planet.name[0];
  const d = getDignityInfo(planet.dignity);
  const aspect = computeClosestAspect(allPlanets, planet.name);
  const degMin = formatDegMin(planet.longitude);
  const isRetrograde = planet.retrograde === true;
  const scoreStr = d.score > 0 ? `+${d.score}` : d.score < 0 ? `${d.score}` : "";

  // Dual-dignity display: only when traditional ≠ modern (Escorpio/Acuario/Piscis cases)
  const hasDual = !!(
    planet.dignity_traditional &&
    planet.dignity_modern &&
    planet.dignity_traditional !== planet.dignity_modern
  );
  const dTrad = hasDual ? getDignityInfoFromString(planet.dignity_traditional) : d;
  const dMod  = hasDual ? getDignityInfoFromString(planet.dignity_modern)      : d;

  return (
    <button
      onClick={() => onClick(planet)}
      className="w-full text-left p-3 rounded-sm border border-slate-800 bg-[#080808] hover:border-amber-500/30 hover:bg-amber-500/5 cursor-pointer transition-colors group"
    >
      {/* Row 1 — Symbol + Name | Dignity badge(s) */}
      <div className="flex items-start justify-between mb-1">
        <span className="flex items-center gap-1.5 text-slate-200 text-sm font-medium">
          <span className="text-base">{sym}</span>
          {planet.name}
        </span>
        {hasDual ? (
          <div className="flex flex-col items-end gap-0.5">
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${dignityBadgeClass(dTrad)}`}>
              Trad: {dTrad.label} ({fmtScore(dTrad.score)})
            </span>
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${dignityBadgeClass(dMod)}`}>
              Mod: {dMod.label} ({fmtScore(dMod.score)})
            </span>
          </div>
        ) : (
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${dignityBadgeClass(d)}`}>
            {d.label}{scoreStr ? ` ${scoreStr}` : ""}
          </span>
        )}
      </div>

      {/* Row 2 — Degree + Sign · Casa | [R] */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span>
          {degMin} {planet.sign} · Casa {planet.house ?? "—"}
        </span>
        {isRetrograde && (
          <span className="text-amber-500/70 text-[10px]">℞</span>
        )}
      </div>

      {/* Divider */}
      <div className="my-2 border-t border-slate-800/80" />

      {/* Row 3 — Closest aspect */}
      <div className="text-[10px] text-slate-500 font-mono">
        {aspect ? (
          <span>
            <span className="text-slate-400">{aspect.symbol} {aspect.type}</span>
            {" con "}
            <span className="text-slate-300">{aspect.planet}</span>
            {" "}
            <span className="text-slate-600">(orb {aspect.orb.toFixed(1)}°)</span>
          </span>
        ) : (
          <span className="text-slate-700">sin aspecto mayor</span>
        )}
      </div>
    </button>
  );
}

// ------------------------------------
// Main component
// ------------------------------------
export function NatalChartTab() {
  const abuData = useAppStore((s) => s.abuData);
  const isLoading = useAppStore((s) => s.isLoading);
  const setPendingLillyEvent = useAppStore((s) => s.setPendingLillyEvent);
  const birthData = useAppStore((s) => s.birthData);
  const lang = useAppStore((s) => s.lang);

  const [orientation, setOrientation] = useState<"aries" | "ascendant">("ascendant");

  if (isLoading) return <div className="p-6 text-slate-500 text-sm">Cargando carta…</div>;
  if (!abuData) return <div className="p-6 text-slate-500 text-sm">No hay análisis disponible.</div>;

  const { chart } = abuData;

  // Houses
  const adaptedHouses = chart.houses.houses.map((h: any) => ({
    number: h.house,
    cusp: h.start,
    sign: getSignFromLongitude(h.start),
  }));

  const houseData = {
    houses: adaptedHouses,
    asc: chart.houses.asc,
    mc: chart.houses.mc,
  };

  // Natal planets (raw — keep dignity + retrograde for cards)
  const rawPlanets: any[] = chart.planets ?? [];

  // ASC / MC ruler labels — dual system (BUG-01)
  const ascRulerTrad  = chart.asc_ruler_traditional as string | undefined;
  const ascRulerMod   = chart.asc_ruler_modern      as string | undefined;
  const mcRulerTrad   = chart.mc_ruler_traditional  as string | undefined;
  const mcRulerMod    = chart.mc_ruler_modern       as string | undefined;
  const ascRulerLabel = ascRulerTrad && ascRulerMod && ascRulerTrad !== ascRulerMod
    ? `${ascRulerTrad} (trad.) / ${ascRulerMod} (mod.)`
    : (ascRulerTrad ?? "—");
  const mcRulerLabel  = mcRulerTrad  && mcRulerMod  && mcRulerTrad  !== mcRulerMod
    ? `${mcRulerTrad} (trad.) / ${mcRulerMod} (mod.)`
    : (mcRulerTrad ?? "—");

  // Aspect lines for ZodiacWheel — computed client-side over all planet pairs
  const natalAspectLines = useMemo(() => {
    if (!rawPlanets || rawPlanets.length === 0) return [];
    const results: Array<{
      planet_a: string;
      planet_b: string;
      type: 'conjunction' | 'sextile' | 'square' | 'trine' | 'opposition';
      orb: number;
    }> = [];
    for (let i = 0; i < rawPlanets.length; i++) {
      for (let j = i + 1; j < rawPlanets.length; j++) {
        const lonA = rawPlanets[i].longitude;
        const lonB = rawPlanets[j].longitude;
        const diff = Math.abs(((Math.abs(lonA - lonB) % 360) + 360) % 360);
        const normalised = diff > 180 ? 360 - diff : diff;
        let bestOrb = Infinity;
        let bestType: string | null = null;
        for (const asp of NATAL_ASPECTS) {
          const orb = Math.abs(normalised - asp.angle);
          if (orb <= asp.orb && orb < bestOrb) {
            bestOrb = orb;
            bestType = asp.type;
          }
        }
        if (bestType && bestOrb <= 8) {
          results.push({
            planet_a: rawPlanets[i].name,
            planet_b: rawPlanets[j].name,
            type: bestType as 'conjunction' | 'sextile' | 'square' | 'trine' | 'opposition',
            orb: bestOrb,
          });
        }
      }
    }
    return results;
  }, [rawPlanets]);

  // Adapted planets for ZodiacWheel (no transit ring in natal tab)
  const natalPlanets = rawPlanets.map((p: any) => ({
    name: p.name,
    longitude: p.longitude,
    sign: p.sign,
    degree: p.degree_in_sign,
    formatted: p.formatted,
    house: p.house,
    dignity: getDignityInfo(p.dignity).label,
    retrograde: p.retrograde === true,
  }));

  // Click handler — sends event to Lilly via store
  function handlePlanetClick(p: any) {
    const d = getDignityInfo(p.dignity);
    const subjectName =
      (birthData as any)?.userName ||
      abuData?.person?.name ||
      "Anónimo";

    const aspect = computeClosestAspect(rawPlanets, p.name);

    setPendingLillyEvent({
      type: "click_planet",
      payload: {
        planet_name: p.name,
        lon: p.longitude,
        sign: p.sign,
        house: p.house,
        dignity: d.label,
        dignity_score: d.score,
        retrograde: p.retrograde === true,
        subject_name: subjectName,
        closest_aspect: aspect,
        lang,
      },
    });
  }

  // House click handler
  function handleHouseClick(payload: { house_num: number; cusp_sign: string; house_lord: string }) {
    const subjectName =
      (birthData as any)?.userName ||
      abuData?.person?.name ||
      "Anónimo";
    setPendingLillyEvent({
      type: "click_house",
      payload: {
        ...payload,
        occupants: natalPlanets
          .filter((p: any) => p.house === payload.house_num)
          .map((p: any) => `${p.name} (${p.sign} ${Math.floor(p.degree ?? 0)}°)`)
          .join(', ') || 'Ninguno',
        subject_name: subjectName,
        lang,
      },
    });
  }

  return (
    <div className="space-y-4 p-4">

      {/* Orientation selector */}
      <div className="flex gap-2 items-center">
        {(["aries", "ascendant"] as const).map((o) => (
          <button
            key={o}
            className={`px-3 py-1 rounded text-xs border transition-colors ${
              orientation === o
                ? "bg-amber-500/10 border-amber-500/40 text-amber-400"
                : "bg-slate-900/50 border-slate-800 text-slate-500 hover:border-slate-600"
            }`}
            onClick={() => setOrientation(o)}
          >
            {o === "aries" ? "Aries arriba" : "Ascendente arriba"}
          </button>
        ))}
      </div>

      {/* Two-column layout on large screens */}
      <div className="flex flex-col lg:flex-row gap-4">

        {/* Zodiac wheel — natal only, no transit ring */}
        <div className="lg:w-3/5">
          <ZodiacWheel
            planets={natalPlanets}
            houses={houseData}
            orientation={orientation}
            onPlanetClick={(p) => handlePlanetClick({
              ...rawPlanets.find((r: any) => r.name === p.name),
              longitude: p.longitude,
            })}
            onHouseClick={handleHouseClick}
            natalAspects={natalAspectLines}
          />
        </div>

        {/* Planet cards */}
        <div className="lg:w-2/5 overflow-y-auto max-h-[600px]">

          {/* Angles panel — ASC/MC with dual rulers */}
          {(chart.houses?.asc != null || chart.houses?.mc != null) && (
            <div className="mb-3 p-2 rounded-sm border border-slate-800 bg-[#080808]">
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-slate-600 mb-1.5">
                Ángulos
              </h3>
              {chart.houses?.asc != null && (
                <div className="text-[11px] font-mono text-slate-400 leading-5">
                  <span className="text-slate-500">ASC</span>
                  {" · "}
                  {getSignFromLongitude(chart.houses.asc)} {formatDegMin(chart.houses.asc)}
                  {" · Señor: "}
                  <span className="text-slate-300">{ascRulerLabel}</span>
                </div>
              )}
              {chart.houses?.mc != null && (
                <div className="text-[11px] font-mono text-slate-400 leading-5">
                  <span className="text-slate-500">MC</span>
                  {" · "}
                  {getSignFromLongitude(chart.houses.mc)} {formatDegMin(chart.houses.mc)}
                  {" · Señor: "}
                  <span className="text-slate-300">{mcRulerLabel}</span>
                </div>
              )}
            </div>
          )}

          <h3 className="text-xs font-mono uppercase tracking-widest text-slate-600 mb-3">
            Posiciones planetarias
            <span className="ml-2 text-slate-700 normal-case">— click para interpretar</span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2">
            {rawPlanets.map((p: any) => (
              <PlanetCard
                key={p.name}
                planet={p}
                allPlanets={rawPlanets}
                onClick={handlePlanetClick}
              />
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}
