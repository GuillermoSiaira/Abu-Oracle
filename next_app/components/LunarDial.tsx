"use client"

export interface LunarData {
  sun: { lon: number; sign: string; sign_degree: number }
  moon: { lon: number; sign: string; sign_degree: number }
  phase: { separation: number; name: string; pct: number }
  sun_moon_aspect: { type: string | null; orb: number | null; applying: boolean | null }
  next_new_moon: { dt: string; sign: string; natal_house: number | null }
  next_full_moon: { dt: string; sign: string; natal_house: number | null }
  next_solar_eclipse?: { dt: string; type: string; sign: string; natal_house: number | null } | null
  next_lunar_eclipse?: { dt: string; type: string; sign: string; natal_house: number | null } | null
}

const PHASE_NAMES: Record<string, Record<string, string>> = {
  "New Moon":        { es: "Luna Nueva",      en: "New Moon",        pt: "Lua Nova",         fr: "Nouvelle Lune"          },
  "Waxing Crescent": { es: "Creciente",        en: "Waxing Crescent", pt: "Crescente",        fr: "Croissant"              },
  "First Quarter":   { es: "Cuarto Creciente", en: "First Quarter",   pt: "Primeiro Quarto",  fr: "Premier Quartier"       },
  "Waxing Gibbous":  { es: "Gibosa Creciente", en: "Waxing Gibbous",  pt: "Gibosa Crescente", fr: "Gibbeuse Croissante"    },
  "Full Moon":       { es: "Luna Llena",       en: "Full Moon",       pt: "Lua Cheia",        fr: "Pleine Lune"            },
  "Waning Gibbous":  { es: "Gibosa Menguante", en: "Waning Gibbous",  pt: "Gibosa Minguante", fr: "Gibbeuse Décroissante"  },
  "Last Quarter":    { es: "Cuarto Menguante", en: "Last Quarter",    pt: "Último Quarto",    fr: "Dernier Quartier"       },
  "Waning Crescent": { es: "Menguante",        en: "Waning Crescent", pt: "Minguante",        fr: "Croissant Décroissant"  },
}

const NEXT_NEW:    Record<string, string> = { es: "Próx. Luna Nueva",   en: "Next New Moon",     pt: "Próx. Lua Nova",     fr: "Proch. Nouvelle Lune"  }
const NEXT_FULL:   Record<string, string> = { es: "Próx. Luna Llena",   en: "Next Full Moon",    pt: "Próx. Lua Cheia",    fr: "Proch. Pleine Lune"    }
const NEXT_SOLAR:  Record<string, string> = { es: "Eclipse Solar",      en: "Solar Eclipse",     pt: "Eclipse Solar",      fr: "Éclipse Solaire"       }
const NEXT_LUNAR:  Record<string, string> = { es: "Eclipse Lunar",      en: "Lunar Eclipse",     pt: "Eclipse Lunar",      fr: "Éclipse Lunaire"       }

function phaseArcColor(sep: number): string {
  if (sep < 22.5 || sep >= 337.5) return "rgba(148,163,184,0.2)"
  if (sep < 157.5) return "rgba(251,191,36,0.75)"
  if (sep < 202.5) return "rgba(220,228,255,0.9)"
  return "rgba(129,140,248,0.65)"
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("es-ES", { month: "short", day: "numeric" })
  } catch {
    return iso.slice(5, 10)
  }
}

export function LunarDial({ data, lang }: { data: LunarData; lang: string }) {
  const cx = 90, cy = 90, r = 62

  function toXY(lon: number, radius: number) {
    const rad = (lon * Math.PI) / 180
    return {
      x: cx + radius * Math.cos(rad),
      y: cy - radius * Math.sin(rad),
    }
  }

  const mr = 9.5  // Moon/Sun circle radius — declared here for use in arc offset

  const sunPos  = toXY(data.sun.lon,  r)
  const moonPos = toXY(data.moon.lon, r)

  const sep = data.phase.separation
  const arcCol = phaseArcColor(sep)

  // Stop the arc just before the Moon circle edge so the arrowhead doesn't cover the glow.
  // Offset = angular distance corresponding to (moon radius + arrow clearance) on the orbit ring.
  const ARROW_CLEAR_DEG = Math.asin((mr + 5) / r) * (180 / Math.PI) // ≈ 13°
  const sepAdj = sep - ARROW_CLEAR_DEG
  const moonLonAdj = ((data.moon.lon - ARROW_CLEAR_DEG) + 360) % 360
  const moonPosAdj = toXY(moonLonAdj, r)
  const largeArc = sepAdj > 180 ? 1 : 0
  // sweepFlag=0 → CCW in SVG coords = direction of increasing ecliptic longitude (levógiro)
  const arcD = `M ${sunPos.x.toFixed(2)} ${sunPos.y.toFixed(2)} A ${r} ${r} 0 ${largeArc} 0 ${moonPosAdj.x.toFixed(2)} ${moonPosAdj.y.toFixed(2)}`

  // Illumination fraction: 0 = new moon, 1 = full moon
  const illum = (1 - Math.cos(sep * Math.PI / 180)) / 2

  // Unit vector from Moon toward Sun (screen space)
  const dx = sunPos.x - moonPos.x
  const dy = sunPos.y - moonPos.y
  const d  = Math.sqrt(dx * dx + dy * dy)
  const nx = d > 0.001 ? dx / d : 1
  const ny = d > 0.001 ? dy / d : 0

  // Glow center: slightly inside the Moon circle, toward the Sun
  const glowCx = moonPos.x + nx * mr * 0.55
  const glowCy = moonPos.y + ny * mr * 0.55

  const localPhase = PHASE_NAMES[data.phase.name]?.[lang]
    ?? PHASE_NAMES[data.phase.name]?.en
    ?? data.phase.name

  return (
    <div className="flex flex-col items-center gap-1">
      <svg viewBox="0 0 180 180" width="148" height="148">
        <defs>
          {/* Arrow marker for CCW direction on arc */}
          <marker
            id="arcArrow"
            markerWidth="5" markerHeight="5"
            refX="4" refY="2.5"
            orient="auto"
          >
            <path d="M0,0 L0,5 L5,2.5 z" fill={arcCol} fillOpacity="0.85" />
          </marker>

          {/* Radial gradient for illuminated limb of Moon */}
          <radialGradient
            id="moonIllum"
            cx={glowCx} cy={glowCy} r={mr * 1.6}
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0%"   stopColor="rgb(220,228,255)" stopOpacity={0.6 * illum} />
            <stop offset="55%"  stopColor="rgb(200,210,255)" stopOpacity={0.25 * illum} />
            <stop offset="100%" stopColor="rgb(0,0,0)"       stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Background halo */}
        <circle cx={cx} cy={cy} r={74} fill="rgba(10,10,18,0.7)" stroke="rgba(50,50,70,0.25)" strokeWidth={1} />

        {/* Orbit ring */}
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(80,80,110,0.3)" strokeWidth={0.75} />

        {/* Phase arc with directional arrowhead — guard: sep must exceed the arrow clearance angle */}
        {sepAdj > 5 && sepAdj < 355 && (
          <path
            d={arcD}
            fill="none"
            stroke={arcCol}
            strokeWidth={2.5}
            strokeLinecap="round"
            markerEnd="url(#arcArrow)"
          />
        )}

        {/* Center ring */}
        <circle cx={cx} cy={cy} r={15} fill="rgba(10,10,18,0.95)" stroke="rgba(70,70,95,0.4)" strokeWidth={0.75} />
        <text
          x={cx} y={cy + 4}
          textAnchor="middle" fontSize={9}
          fill="rgba(160,140,85,0.55)" fontFamily="monospace"
        >
          {Math.round(sep)}°
        </text>

        {/* Sun */}
        <circle cx={sunPos.x} cy={sunPos.y} r={mr}
          fill="rgba(251,191,36,0.1)" stroke="rgba(251,191,36,0.6)" strokeWidth={1.5} />
        <text x={sunPos.x} y={sunPos.y + 4}
          textAnchor="middle" fontSize={11} fill="rgba(251,191,36,0.9)">
          ☉
        </text>

        {/* Moon — base + illuminated glow overlay */}
        <circle cx={moonPos.x} cy={moonPos.y} r={mr}
          fill="rgba(148,163,184,0.07)" stroke="rgba(148,163,184,0.45)" strokeWidth={1.5} />
        {/* Illuminated limb glow (scales with phase) */}
        <circle cx={moonPos.x} cy={moonPos.y} r={mr}
          fill="url(#moonIllum)" stroke="none" />
        <text x={moonPos.x} y={moonPos.y + 4}
          textAnchor="middle" fontSize={11} fill="rgba(148,163,184,0.85)">
          ☽
        </text>
      </svg>

      {/* Phase name */}
      <div className="text-center leading-tight">
        <div className="text-[11px] text-slate-200 font-medium tracking-wide">{localPhase}</div>
        <div className="text-[10px] text-slate-600 font-mono">{data.phase.pct.toFixed(0)}%</div>
      </div>

      {/* Next lunations */}
      <div className="w-full mt-0.5 space-y-1 px-1">
        <div className="flex items-center justify-between gap-1 text-[10px]">
          <span className="text-slate-600 shrink-0">● {NEXT_NEW[lang] ?? NEXT_NEW.en}</span>
          <span className="text-slate-500 font-mono shrink-0">{fmtDate(data.next_new_moon.dt)}</span>
          <span className="text-slate-600 text-[9px] truncate text-right">
            {data.next_new_moon.sign}{data.next_new_moon.natal_house ? ` H${data.next_new_moon.natal_house}` : ""}
          </span>
        </div>
        <div className="flex items-center justify-between gap-1 text-[10px]">
          <span className="text-slate-600 shrink-0">○ {NEXT_FULL[lang] ?? NEXT_FULL.en}</span>
          <span className="text-slate-500 font-mono shrink-0">{fmtDate(data.next_full_moon.dt)}</span>
          <span className="text-slate-600 text-[9px] truncate text-right">
            {data.next_full_moon.sign}{data.next_full_moon.natal_house ? ` H${data.next_full_moon.natal_house}` : ""}
          </span>
        </div>
        {data.next_solar_eclipse && (
          <div className="flex items-center justify-between gap-1 text-[10px]">
            <span className="text-red-400/60 shrink-0">☉ {NEXT_SOLAR[lang] ?? NEXT_SOLAR.en}</span>
            <span className="text-slate-500 font-mono shrink-0">{fmtDate(data.next_solar_eclipse.dt)}</span>
            <span className="text-slate-600 text-[9px] truncate text-right">
              {data.next_solar_eclipse.sign}{data.next_solar_eclipse.natal_house ? ` H${data.next_solar_eclipse.natal_house}` : ""}
            </span>
          </div>
        )}
        {data.next_lunar_eclipse && (
          <div className="flex items-center justify-between gap-1 text-[10px]">
            <span className="text-indigo-400/60 shrink-0">☽ {NEXT_LUNAR[lang] ?? NEXT_LUNAR.en}</span>
            <span className="text-slate-500 font-mono shrink-0">{fmtDate(data.next_lunar_eclipse.dt)}</span>
            <span className="text-slate-600 text-[9px] truncate text-right">
              {data.next_lunar_eclipse.sign}{data.next_lunar_eclipse.natal_house ? ` H${data.next_lunar_eclipse.natal_house}` : ""}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
