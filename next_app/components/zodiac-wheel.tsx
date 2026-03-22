"use client";

import { useMemo, useState } from "react";

interface Planet {
  name: string;
  longitude: number;
  sign: string;
  degree?: number;
  formatted?: string;
  house?: number;
  dignity?: string;
  retrograde?: boolean;
}

export interface PlanetPosition extends Planet {
  x: number;
  y: number;
  symbol: string;
  color: string;
  deg: number;
}

interface House {
  number: number;
  cusp: number;
  sign: string;
}

interface ZodiacWheelProps {
  planets: Planet[];
  transitPlanets?: Planet[];
  houses?: {
    houses?: House[];
    asc?: number | null;
    mc?: number | null;
  };
  birthData?: {
    name?: string;
    date?: string;
    location?: string;
    lat?: number;
    lon?: number;
  };
  sunSign?: string;
  moonSign?: string;
  ascendantSign?: string;
  orientation?: "aries" | "ascendant";
  onPlanetClick?: (planet: PlanetPosition) => void;
  natalAspects?: Array<{
    planet_a: string;
    planet_b: string;
    type: 'conjunction' | 'sextile' | 'square' | 'trine' | 'opposition';
    orb: number;
  }>;
}

const ASPECT_LINE_COLORS: Record<string, string> = {
  conjunction: '#7F77DD',
  trine:       '#3266ad',
  sextile:     '#3B6D11',
  square:      '#A32D2D',
  opposition:  '#993C1D',
};

const SIGN_SYMBOLS: Record<string, string> = {
  Aries: '♈', Taurus: '♉', Gemini: '♊', Cancer: '♋',
  Leo: '♌', Virgo: '♍', Libra: '♎', Scorpio: '♏',
  Sagittarius: '♐', Capricorn: '♑', Aquarius: '♒', Pisces: '♓',
};

const SIGN_NAMES_ES: Record<string, string> = {
  Aries: 'ARIES', Taurus: 'TAURO', Gemini: 'GÉMINIS', Cancer: 'CÁNCER',
  Leo: 'LEO', Virgo: 'VIRGO', Libra: 'LIBRA', Scorpio: 'ESCORPIO',
  Sagittarius: 'SAGIT', Capricorn: 'CAPRIC', Aquarius: 'ACUARIO', Pisces: 'PISCIS',
};

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: "☉",
  Moon: "☽",
  Mercury: "☿",
  Venus: "♀",
  Mars: "♂",
  Jupiter: "♃",
  Saturn: "♄",
  Uranus: "♅",
  Neptune: "♆",
  Pluto: "♇",
};

const PLANET_COLORS: Record<string, string> = {
  Sun: "#FFD700",
  Moon: "#E0E0E0",
  Mercury: "#87CEEB",
  Venus: "#FFB6C1",
  Mars: "#FF6347",
  Jupiter: "#FFA500",
  Saturn: "#DAA520",
  Uranus: "#40E0D0",
  Neptune: "#4169E1",
  Pluto: "#8B4513",
};

export function ZodiacWheel({
  planets,
  transitPlanets,
  houses,
  birthData,
  sunSign,
  moonSign,
  ascendantSign,
  orientation = "aries",
  onPlanetClick,
  natalAspects,
}: ZodiacWheelProps) {
  const [hoveredPlanet, setHoveredPlanet] = useState<PlanetPosition | null>(null);
  // -------------------------
  // CONSTS DE DIBUJO
  // -------------------------
  const centerX = 300;
  const centerY = 300;
  const outerRadius = 260;
  const houseRadius = 220;
  const signRadius = 180;
  const innerRadius = 140;

  // -------------------------
  // CORRECCIÓN DE ROTACIÓN
  // -------------------------
  const rotationOffset = useMemo(() => {
    if (orientation === "ascendant" && houses?.asc != null) {
      // CCW rendering: x = -sin(normalized), y = -cos(normalized)
      // ASC must land at normalized=90 (left/9-o'clock). normalized = asc - offset = 90 → offset = asc - 90
      return (houses.asc - 90 + 360) % 360;
    }
    return 0; // Aries arriba
  }, [orientation, houses?.asc]);

  const polarToCartesian = (angle: number, radius: number) => {
    const normalized = (angle - rotationOffset + 360) % 360;
    const adjusted = normalized * (Math.PI / 180);

    return {
      x: centerX - radius * Math.sin(adjusted),
      y: centerY - radius * Math.cos(adjusted),
    };
  };

  // -------------------------
  // PLANETS
  // -------------------------
  const planetPositions = useMemo(
    () =>
      planets.map((planet) => {
        const pos = polarToCartesian(planet.longitude, signRadius + 35);
        const degInSign = ((planet.longitude % 360) + 360) % 360 % 30;
        return {
          ...planet,
          x: pos.x,
          y: pos.y,
          symbol: PLANET_SYMBOLS[planet.name] || planet.name.charAt(0),
          color: PLANET_COLORS[planet.name] || "#FFD700",
          deg: Math.floor(degInSign),
        } as PlanetPosition;
      }),
    [planets, rotationOffset]
  );

  // -------------------------
  // TRANSIT PLANETS
  // -------------------------
  const transitPlanetPositions = useMemo(
    () =>
      transitPlanets?.map((planet) => {
        const pos = polarToCartesian(planet.longitude, signRadius + 65);
        return {
          ...planet,
          x: pos.x,
          y: pos.y,
          symbol: PLANET_SYMBOLS[planet.name] || planet.name.charAt(0),
          color: PLANET_COLORS[planet.name] || "#FFD700",
        };
      }) ?? [],
    [transitPlanets, rotationOffset]
  );

  // -------------------------
  // HOUSES
  // -------------------------
  const houseCusps = houses?.houses ?? [];

  const angles = useMemo(() => {
    const asc = houses?.asc ?? null;
    const mc = houses?.mc ?? null;
    const desc = asc != null ? (asc + 180) % 360 : null;
    const ic = mc != null ? (mc + 180) % 360 : null;
    return { asc, mc, desc, ic };
  }, [houses?.asc, houses?.mc]);

  // -------------------------
  // RENDER
  // -------------------------
  return (
    <div className="w-full space-y-6">
      {(birthData || sunSign || moonSign || ascendantSign) && (
        <div className="space-y-4 pb-6 border-b-2 border-primary/30 text-center" />
      )}

      <svg viewBox="0 0 600 600" className="w-full h-full max-w-3xl mx-auto">
        <defs>
          <radialGradient id="zodiacGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#1a1a2e" stopOpacity="1" />
            <stop offset="100%" stopColor="#0f0f1e" stopOpacity="1" />
          </radialGradient>

          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <filter id="strongGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Círculos base */}
        <circle
          cx={centerX}
          cy={centerY}
          r={outerRadius}
          fill="url(#zodiacGradient)"
          stroke="#D4AF37"
          strokeWidth="3"
        />
        <circle
          cx={centerX}
          cy={centerY}
          r={houseRadius}
          fill="none"
          stroke="#D4AF37"
          strokeWidth="2"
          opacity="0.5"
        />
        <circle
          cx={centerX}
          cy={centerY}
          r={signRadius}
          fill="none"
          stroke="#D4AF37"
          strokeWidth="2"
          opacity="0.7"
        />
        <circle
          cx={centerX}
          cy={centerY}
          r={innerRadius}
          fill="none"
          stroke="#D4AF37"
          strokeWidth="2"
          opacity="0.8"
        />

        {/* SIGNOS — derivados de cúspides reales */}
        {houseCusps.map((h, i) => {
          const nextCusp = houseCusps[(i + 1) % 12]?.cusp ?? h.cusp + 30;
          const span = ((nextCusp - h.cusp + 360) % 360);
          const midAngle = h.cusp + span / 2;

          const divStart = polarToCartesian(h.cusp, outerRadius);
          const divEnd   = polarToCartesian(h.cusp, houseRadius);

          const symbolPos = polarToCartesian(midAngle, (outerRadius + houseRadius) / 2);
          const namePos   = polarToCartesian(midAngle, houseRadius - 20);

          return (
            <g key={`sign-${h.number}`}>
              <line
                x1={divStart.x} y1={divStart.y}
                x2={divEnd.x}   y2={divEnd.y}
                stroke="#D4AF37" strokeWidth="0.5" opacity="0.4"
              />
              <text
                x={symbolPos.x} y={symbolPos.y}
                textAnchor="middle" dominantBaseline="middle"
                fill="#D4AF37" fontSize="28" fontWeight="bold"
                filter="url(#glow)"
              >
                {SIGN_SYMBOLS[h.sign] ?? '?'}
              </text>
              <text
                x={namePos.x} y={namePos.y}
                textAnchor="middle" dominantBaseline="middle"
                fill="#D4AF37" fontSize="10" opacity="0.7"
              >
                {SIGN_NAMES_ES[h.sign] ?? h.sign.toUpperCase()}
              </text>
            </g>
          );
        })}

        {/* DEGREE MARKERS */}
        {Array.from({ length: 36 }).map((_, i) => {
          const angle = i * 10;
          const isMain = i % 3 === 0;
          const start = polarToCartesian(angle, signRadius);
          const end = polarToCartesian(
            angle,
            signRadius - (isMain ? 15 : 8)
          );
          return (
            <line
              key={`deg-${i}`}
              x1={start.x}
              y1={start.y}
              x2={end.x}
              y2={end.y}
              stroke="#D4AF37"
              strokeWidth={isMain ? 2 : 1}
              opacity={isMain ? 0.8 : 0.4}
            />
          );
        })}

        {/* HOUSES */}
        {houseCusps.map((h) => {
          const start = polarToCartesian(h.cusp, houseRadius);
          const end = polarToCartesian(h.cusp, innerRadius);

          const next = houseCusps[h.number % 12]?.cusp ?? h.cusp + 30;
          const mid = h.cusp + ((next - h.cusp + 360) % 360) / 2;
          const numPos = polarToCartesian(mid, 180);

          return (
            <g key={`h-${h.number}`}>
              <line
                x1={start.x}
                y1={start.y}
                x2={end.x}
                y2={end.y}
                stroke="#8B7355"
                strokeWidth="1.5"
                opacity="0.6"
                strokeDasharray="4 2"
              />
              <circle
                cx={numPos.x}
                cy={numPos.y}
                r="14"
                fill="#1a1a2e"
                stroke="#8B7355"
                strokeWidth="1.5"
              />
              <text
                x={numPos.x}
                y={numPos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#8B7355"
                fontSize="12"
                fontWeight="bold"
              >
                {h.number}
              </text>
            </g>
          );
        })}

        {/* ANGLES → ASC / MC / DC / IC */}
        {angles.asc != null && (
          <g>
            <line
              x1={centerX}
              y1={centerY}
              x2={polarToCartesian(angles.asc, outerRadius + 10).x}
              y2={polarToCartesian(angles.asc, outerRadius + 10).y}
              stroke="#FFD700"
              strokeWidth="4"
            />
            <text
              x={polarToCartesian(angles.asc, outerRadius + 30).x}
              y={polarToCartesian(angles.asc, outerRadius + 30).y}
              textAnchor="middle"
              fill="#FFD700"
              fontSize="18"
              fontWeight="bold"
            >
              AC
            </text>
          </g>
        )}

        {angles.mc != null && (
          <g>
            <line
              x1={centerX}
              y1={centerY}
              x2={polarToCartesian(angles.mc, outerRadius + 10).x}
              y2={polarToCartesian(angles.mc, outerRadius + 10).y}
              stroke="#FF6B6B"
              strokeWidth="4"
            />
            <text
              x={polarToCartesian(angles.mc, outerRadius + 30).x}
              y={polarToCartesian(angles.mc, outerRadius + 30).y}
              textAnchor="middle"
              fill="#FF6B6B"
              fontSize="18"
              fontWeight="bold"
            >
              MC
            </text>
          </g>
        )}

        {angles.desc != null && (
          <g>
            <line
              x1={centerX}
              y1={centerY}
              x2={polarToCartesian(angles.desc, outerRadius + 10).x}
              y2={polarToCartesian(angles.desc, outerRadius + 10).y}
              stroke="#87CEEB"
              strokeWidth="4"
            />
            <text
              x={polarToCartesian(angles.desc, outerRadius + 30).x}
              y={polarToCartesian(angles.desc, outerRadius + 30).y}
              textAnchor="middle"
              fill="#87CEEB"
              fontSize="18"
              fontWeight="bold"
            >
              DC
            </text>
          </g>
        )}

        {angles.ic != null && (
          <g>
            <line
              x1={centerX}
              y1={centerY}
              x2={polarToCartesian(angles.ic, outerRadius + 10).x}
              y2={polarToCartesian(angles.ic, outerRadius + 10).y}
              stroke="#9370DB"
              strokeWidth="4"
            />
            <text
              x={polarToCartesian(angles.ic, outerRadius + 30).x}
              y={polarToCartesian(angles.ic, outerRadius + 30).y}
              textAnchor="middle"
              fill="#9370DB"
              fontSize="18"
              fontWeight="bold"
            >
              IC
            </text>
          </g>
        )}

        {/* ASPECTOS */}
        {natalAspects?.map((asp, i) => {
          const pa = planets.find(p => p.name === asp.planet_a);
          const pb = planets.find(p => p.name === asp.planet_b);
          if (!pa || !pb) return null;
          const posA = polarToCartesian(pa.longitude, 130);
          const posB = polarToCartesian(pb.longitude, 130);
          const color = ASPECT_LINE_COLORS[asp.type] ?? '#888';
          return (
            <line
              key={`asp-${i}`}
              x1={posA.x} y1={posA.y}
              x2={posB.x} y2={posB.y}
              stroke={color}
              strokeWidth={asp.orb < 1 ? 1.5 : 0.8}
              strokeOpacity={0.7}
              strokeDasharray={
                asp.type === 'square' || asp.type === 'opposition' ? '4 3' : undefined
              }
            />
          );
        })}

        {/* PLANETS */}
        {planetPositions.map((p) => (
          <g
            key={p.name}
            onClick={() => onPlanetClick?.(p)}
            onMouseEnter={() => setHoveredPlanet(p)}
            onMouseLeave={() => setHoveredPlanet(null)}
            style={{ cursor: onPlanetClick ? 'pointer' : 'default' }}
          >
            <circle
              cx={p.x}
              cy={p.y}
              r="24"
              fill="#1a1a2e"
              stroke={hoveredPlanet?.name === p.name ? '#fbbf24' : p.color}
              strokeWidth={hoveredPlanet?.name === p.name ? 4 : 3}
              filter="url(#strongGlow)"
            />
            <text
              x={p.x}
              y={p.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fill={p.color}
              fontSize="20"
              fontWeight="bold"
            >
              {p.symbol}
            </text>
          </g>
        ))}

        {/* TRANSIT PLANETS - OUTER RING */}
        {transitPlanetPositions.map((p) => (
          <g
            key={`transit-${p.name}`}
            onMouseEnter={() => setHoveredPlanet(p as PlanetPosition)}
            onMouseLeave={() => setHoveredPlanet(null)}
            style={{ cursor: 'default' }}
          >
            <circle
              cx={p.x}
              cy={p.y}
              r="18"
              fill="none"
              stroke={p.color}
              strokeWidth="2"
              opacity="0.6"
              strokeDasharray="4 2"
            />
            <text
              x={p.x}
              y={p.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fill={p.color}
              fontSize="14"
              fontWeight="bold"
              opacity="0.7"
            >
              {p.symbol}
            </text>
          </g>
        ))}

        {/* Centro */}
        <circle
          cx={centerX}
          cy={centerY}
          r="6"
          fill="#D4AF37"
          filter="url(#glow)"
        />

        {/* TOOLTIP */}
        {hoveredPlanet && (
          <foreignObject
            x={Math.min(Math.max(hoveredPlanet.x - 80, 0), 440)}
            y={Math.min(hoveredPlanet.y + 30, 520)}
            width="160"
            height="80"
            style={{ pointerEvents: 'none', overflow: 'visible' }}
          >
            <div style={{
              background: 'rgba(10,10,20,0.95)',
              border: '1px solid rgba(251,191,36,0.4)',
              borderRadius: '6px',
              padding: '6px 10px',
              color: '#f5f5f5',
              fontSize: '12px',
              lineHeight: '1.5',
              fontFamily: 'monospace',
            }}>
              <div style={{ color: hoveredPlanet.color, fontWeight: 'bold', fontSize: '13px' }}>
                {hoveredPlanet.symbol} {hoveredPlanet.name}
              </div>
              <div>{hoveredPlanet.sign} {hoveredPlanet.deg}° · Casa {hoveredPlanet.house ?? '—'}</div>
              {hoveredPlanet.dignity && (
                <div style={{ color: '#9ca3af', fontSize: '11px' }}>
                  {hoveredPlanet.dignity}{hoveredPlanet.retrograde ? ' · ℞' : ''}
                </div>
              )}
            </div>
          </foreignObject>
        )}
      </svg>
    </div>
  );
}
