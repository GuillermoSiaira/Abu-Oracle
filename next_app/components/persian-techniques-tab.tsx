"use client";

import { useAppStore } from "@/lib/store";

// Determinístico: signo desde longitud
function getSignFromLongitude(long: number): string {
  const signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
  ];
  const index = Math.floor(((long % 360) + 360) % 360 / 30);
  return signs[index];
}

export function PersianTechniquesTab() {
  const abuData = useAppStore((s) => s.abuData);
  const isLoading = useAppStore((s) => s.isLoading);

  if (isLoading) return <div>Cargando técnicas persas…</div>;
  if (!abuData) return <div>No hay análisis disponible.</div>;

  const { derived, chart, life_cycles } = abuData;

  // ---------------------------
  // SECT
  // ---------------------------
  let sectText = "Desconocido";
  if (derived?.sect === "diurnal") sectText = "Carta diurna (Sol arriba del horizonte)";
  if (derived?.sect === "nocturnal") sectText = "Carta nocturna (Sol abajo del horizonte)";

  // ---------------------------
  // PROFECCIÓN
  // ---------------------------
  const profectionHouse: number | null =
    derived?.profection?.house ?? null;

  let profectionSign: string | null = null;

  if (profectionHouse && chart?.houses?.houses) {
    const entry = chart.houses.houses.find(
      (h: any) => h.house === profectionHouse
    );
    if (entry) {
      profectionSign = getSignFromLongitude(entry.start);
    }
  }

  // ---------------------------
  // FIRDARIA
  // ---------------------------
  const firdaria = derived?.firdaria?.current ?? null;

  const firdariaStart =
    firdaria?.start && typeof firdaria.start === "string"
      ? new Date(firdaria.start)
      : null;

  const firdariaEnd =
    firdaria?.end && typeof firdaria.end === "string"
      ? new Date(firdaria.end)
      : null;

  // ---------------------------
  // LUNAR TRANSIT
  // ---------------------------
  const lunar = derived?.lunar_transit ?? null;

  const moonPos =
    lunar?.moon_position != null
      ? lunar.moon_position.toFixed(2) + "°"
      : "—";

  const lunarAspects = Array.isArray(lunar?.aspects)
    ? lunar!.aspects
    : [];

  // ---------------------------
  // LIFE CYCLES
  // ---------------------------
  const cycles = Array.isArray(life_cycles?.events)
    ? life_cycles!.events
    : [];

  return (
    <div className="space-y-8">

      {/* ---------- SECT ---------- */}
      <div className="p-4 border rounded-xl bg-card/50">
        <h2 className="text-lg font-semibold mb-2">Sect</h2>
        <p className="opacity-80">{sectText}</p>
      </div>

      {/* ---------- PROFECCIÓN ---------- */}
      <div className="p-4 border rounded-xl bg-card/50">
        <h2 className="text-lg font-semibold mb-2">Profección anual</h2>

        {!profectionHouse ? (
          <p className="opacity-60 text-sm">Sin datos de profección.</p>
        ) : (
          <div className="space-y-1">
            <p className="text-sm">
              <span className="font-medium">Casa:</span> {profectionHouse}
            </p>

            {profectionSign && (
              <p className="text-sm">
                <span className="font-medium">Signo:</span>{" "}
                {profectionSign}
              </p>
            )}
          </div>
        )}
      </div>

      {/* ---------- FIRDARIA ---------- */}
      <div className="p-4 border rounded-xl bg-card/50">
        <h2 className="text-lg font-semibold mb-2">Firdaria actual</h2>

        {!firdaria ? (
          <p className="opacity-60 text-sm">Sin datos de firdaria.</p>
        ) : (
          <div className="space-y-2">
            <p className="text-sm">
              <span className="font-medium">Mayor:</span>{" "}
              {firdaria.major ?? "—"}
            </p>
            <p className="text-sm">
              <span className="font-medium">Sub:</span>{" "}
              {firdaria.sub ?? "—"}
            </p>

            <p className="text-sm">
              <span className="font-medium">Inicio:</span>{" "}
              {firdariaStart
                ? firdariaStart.toLocaleDateString("es-ES", {
                    dateStyle: "long",
                  })
                : "—"}
            </p>

            <p className="text-sm">
              <span className="font-medium">Fin:</span>{" "}
              {firdariaEnd
                ? firdariaEnd.toLocaleDateString("es-ES", {
                    dateStyle: "long",
                  })
                : "—"}
            </p>
          </div>
        )}
      </div>

      {/* ---------- LUNAR TRANSITS ---------- */}
      <div className="p-4 border rounded-xl bg-card/50">
        <h2 className="text-lg font-semibold mb-2">Tránsitos lunares</h2>

        {!lunar ? (
          <p className="opacity-60 text-sm">Sin datos lunares.</p>
        ) : (
          <div className="space-y-3">
            <p className="text-sm">
              <span className="font-medium">Posición lunar:</span>{" "}
              {moonPos}
            </p>

            <div className="space-y-2">
              <p className="text-sm font-medium">Aspectos:</p>

              {lunarAspects.length === 0 ? (
                <p className="opacity-60 text-sm">Sin aspectos.</p>
              ) : (
                lunarAspects.map((a: any, i: number) => (
                  <div
                    key={i}
                    className="px-3 py-2 border rounded-md bg-muted/20 text-sm"
                  >
                    {a.type} con {a.planet} (orb {a.orb.toFixed(2)}°)
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* ---------- LIFE CYCLES ---------- */}
      <div className="p-4 border rounded-xl bg-card/50">
        <h2 className="text-lg font-semibold mb-2">Ciclos planetarios</h2>

        {cycles.length === 0 ? (
          <p className="opacity-60 text-sm">Sin eventos.</p>
        ) : (
          <div className="space-y-2">
            {cycles.slice(0, 12).map((ev: any, idx: number) => (
              <div
                key={idx}
                className="px-3 py-2 border rounded-md bg-muted/20 text-sm"
              >
                <p className="font-medium">{ev.cycle}</p>
                <p className="opacity-80">
                  {ev.planet} — ángulo {ev.angle}°
                </p>
                <p className="opacity-70 text-xs">
                  {" "}
                  {new Date(ev.approx).toLocaleDateString("es-ES", {
                    dateStyle: "medium",
                  })}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* DEBUG */}
      <details className="mt-6">
        <summary className="cursor-pointer text-sm opacity-60">
          Ver datos completos (debug)
        </summary>
        <pre className="bg-black/20 p-3 rounded text-xs mt-2 overflow-auto max-h-96">
          {JSON.stringify(derived, null, 2)}
        </pre>
      </details>
    </div>
  );
}
