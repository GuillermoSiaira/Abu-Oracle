"use client";

export type Domain = "global" | "h1" | "h2" | "h4" | "h5" | "h6" | "h7" | "h9" | "h10";

const DOMAIN_OPTIONS: { key: Domain; label: string; short: string }[] = [
  { key: "global", label: "Global",                    short: "Global" },
  { key: "h1",     label: "Casa 1 · Identidad",        short: "Identidad" },
  { key: "h2",     label: "Casa 2 · Recursos",         short: "Recursos" },
  { key: "h4",     label: "Casa 4 · Hogar",            short: "Hogar" },
  { key: "h5",     label: "Casa 5 · Creatividad",      short: "Creatividad" },
  { key: "h6",     label: "Casa 6 · Trabajo/Salud",    short: "Trabajo" },
  { key: "h7",     label: "Casa 7 · Relaciones",       short: "Relaciones" },
  { key: "h9",     label: "Casa 9 · Expansión",        short: "Expansión" },
  { key: "h10",    label: "Casa 10 · Carrera",         short: "Carrera" },
];

type DomainSelectorProps = {
  domain: Domain;
  onDomainChange: (d: Domain) => void;
};

export function DomainSelector({ domain, onDomainChange }: DomainSelectorProps) {
  return (
    <div
      style={{
        display: "flex",
        gap: "6px",
        flexWrap: "wrap",
        padding: "8px 0 12px",
      }}
    >
      {DOMAIN_OPTIONS.map((opt) => {
        const active = domain === opt.key;
        return (
          <button
            key={opt.key}
            onClick={() => onDomainChange(opt.key)}
            title={opt.label}
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
              cursor: "pointer",
              transition: "all 0.15s",
              backdropFilter: "blur(4px)",
              whiteSpace: "nowrap",
            }}
          >
            {opt.short}
          </button>
        );
      })}
    </div>
  );
}

export default DomainSelector;
