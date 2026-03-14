"use client";

export type LifeDomain =
  | "career"
  | "love"
  | "health"
  | "family"
  | "resources"
  | "creativity"
  | "expansion";

interface LifeDomainConfig {
  key: LifeDomain;
  label: string;
  house: number;
  description: string;
}

const LIFE_DOMAINS: LifeDomainConfig[] = [
  { key: "career",     label: "Carrera",     house: 10, description: "Profesion, autoridad, reconocimiento" },
  { key: "love",       label: "Amor",        house: 7,  description: "Pareja, vinculos, contratos" },
  { key: "health",     label: "Salud",       house: 1,  description: "Vitalidad, cuerpo, identidad" },
  { key: "family",     label: "Familia",     house: 4,  description: "Hogar, raices, historia familiar" },
  { key: "resources",  label: "Recursos",    house: 2,  description: "Finanzas, bienes, ingresos" },
  { key: "creativity", label: "Creatividad", house: 5,  description: "Expresion, creacion, hijos" },
  { key: "expansion",  label: "Expansion",   house: 9,  description: "Viajes, filosofia, espiritualidad" },
];

type LifeDomainSelectorProps = {
  domain: LifeDomain | null;
  onDomainChange: (d: LifeDomain) => void;
  disabled?: boolean;
};

export function LifeDomainSelector({
  domain,
  onDomainChange,
  disabled = false,
}: LifeDomainSelectorProps) {
  return (
    <div style={{ padding: "8px 0 12px" }}>
      <p
        style={{
          fontSize: "11px",
          color: "#64748b",
          marginBottom: "8px",
          fontWeight: 500,
          letterSpacing: "0.05em",
          textTransform: "uppercase",
        }}
      >
        {domain === null ? "Selecciona un dominio para ver el ranking" : "Dominio activo"}
      </p>
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
        {LIFE_DOMAINS.map((opt) => {
          const active = domain === opt.key;
          return (
            <button
              key={opt.key}
              onClick={() => onDomainChange(opt.key)}
              disabled={disabled}
              title={`Casa ${opt.house} — ${opt.description}`}
              style={{
                padding: "5px 12px",
                fontSize: "11px",
                fontWeight: active ? 700 : 500,
                borderRadius: "20px",
                border: active
                  ? "1px solid #f59e0b"
                  : "1px solid rgba(100,100,120,0.35)",
                background: active
                  ? "rgba(245,158,11,0.15)"
                  : "rgba(15,15,25,0.7)",
                color: active ? "#fbbf24" : "#94a3b8",
                cursor: disabled ? "not-allowed" : "pointer",
                opacity: disabled ? 0.5 : 1,
                transition: "all 0.15s",
                backdropFilter: "blur(4px)",
                whiteSpace: "nowrap",
              }}
            >
              {opt.label}
              <span
                style={{
                  marginLeft: "5px",
                  fontSize: "9px",
                  opacity: 0.6,
                  fontWeight: 400,
                }}
              >
                H{opt.house}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default LifeDomainSelector;
