"use client";

import { useAppStore } from "@/lib/store";
import { ZodiacWheel } from "./zodiac-wheel";
import { useState } from "react";

// Función determinística para obtener signo a partir de longitud
function getSignFromLongitude(long: number): string {
  const signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
  ];
  const index = Math.floor(((long % 360) + 360) % 360 / 30);
  return signs[index];
}

export function NatalChartTab() {
  const abuData = useAppStore((s) => s.abuData);
  const isLoading = useAppStore((s) => s.isLoading);

  // Nuevo: orientación seleccionada por el usuario
  const [orientation, setOrientation] = useState<"aries" | "ascendant">(
    "ascendant"
  );

  if (isLoading) return <div>Cargando carta…</div>;
  if (!abuData) return <div>No hay análisis disponible.</div>;

  const { chart } = abuData;

  // -------------------------
  // ADAPTER → Casas para el Wheel
  // -------------------------
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

  // -------------------------
  // ADAPTER → Planetas
  // -------------------------
  const planetData = chart.planets.map((p: any) => ({
    name: p.name,
    longitude: p.longitude,
    sign: p.sign,
    degree: p.degree_in_sign,
    formatted: p.formatted,
    house: p.house,
  }));

  return (
    <div className="space-y-10">
      <h2 className="text-xl font-semibold">Carta Natal</h2>

      {/* Selector de orientación */}
      <div className="flex gap-4 items-center">
        <button
          className={`px-3 py-1 rounded-md border ${
            orientation === "aries"
              ? "bg-primary text-primary-foreground"
              : "bg-muted"
          }`}
          onClick={() => setOrientation("aries")}
        >
          Aries arriba
        </button>

        <button
          className={`px-3 py-1 rounded-md border ${
            orientation === "ascendant"
              ? "bg-primary text-primary-foreground"
              : "bg-muted"
          }`}
          onClick={() => setOrientation("ascendant")}
        >
          Ascendente arriba
        </button>
      </div>

      {/* Rueda zodiacal */}
      <ZodiacWheel
        planets={planetData}
        houses={houseData}
        orientation={orientation}
      />

      {/* Panel → Posiciones planetarias */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Posiciones planetarias</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {planetData.map((p) => (
            <div
              key={p.name}
              className="p-3 rounded-md border bg-card/50 backdrop-blur-sm"
            >
              <p className="font-semibold">{p.name}</p>
              <p className="text-sm opacity-80">{p.formatted}</p>
              <p className="text-sm opacity-80">Signo: {p.sign}</p>
              <p className="text-sm opacity-80">Casa: {p.house}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Debug opcional */}
      <details className="mt-4">
        <summary className="cursor-pointer text-sm opacity-70">
          Ver JSON completo (debug)
        </summary>
        <pre className="bg-black/20 p-3 rounded text-xs mt-2 overflow-auto max-h-96">
          {JSON.stringify(chart, null, 2)}
        </pre>
      </details>
    </div>
  );
}
