"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/lib/store";

import { runAbuAnalyze } from "@/services/abu";
import CityAutocomplete from "./city-autocomplete";

export default function BirthDataPanel() {
  const router = useRouter();

  const {
    setBirthData,
    setAbuData,
    setIsLoading,
    setError,
  } = useAppStore();

  const [birthDate, setBirthDate] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [city, setCity] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  function convertLocalToISOZ(local: string) {
    if (!local) return "";
    return local + ":00Z";
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    setError(null);

    if (!birthDate || !lat || !lon) {
      setLocalError("Debes seleccionar una ciudad y una fecha.");
      return;
    }

    const latNum = parseFloat(lat);
    const lonNum = parseFloat(lon);

    if (isNaN(latNum) || isNaN(lonNum)) {
      setLocalError("Latitud y longitud deben ser números válidos.");
      return;
    }

    const isoDate = convertLocalToISOZ(birthDate);

    const birthDataZustand = {
      birthDate: isoDate,
      lat: latNum,
      lon: lonNum,
      city: city || null,
    };

    try {
      setIsLoading(true);

      // Guardamos datos básicos
      setBirthData(birthDataZustand);

      // === Abu Engine ===
      const abuPayload = {
        person: {
          name: null,
          question: "",
        },
        birth: {
          date: isoDate,
          lat: latNum,
          lon: lonNum,
        },
        current: {
          lat: latNum,
          lon: lonNum,
          date: new Date().toISOString(),
        },
      };

      const abuRes = await runAbuAnalyze(abuPayload);
      setAbuData(abuRes);

      // Ahora NO llamamos a Lilly Engine.
      // El nuevo flujo de interpretación ocurre en el sidebar (OracleChat) usando OpenAI.

      router.push("/chart");

    } catch (err: any) {
      console.error(err);
      setError(err.message || "Error inesperado.");
      setLocalError("Ocurrió un error. Inténtalo nuevamente.");

    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 bg-card p-6 rounded-xl shadow-sm"
    >
      {/* FECHA DE NACIMIENTO */}
      <div className="space-y-1">
        <label className="block text-sm font-medium">Fecha de nacimiento</label>
        <input
          type="datetime-local"
          className="w-full rounded-md border px-3 py-2"
          value={birthDate}
          onChange={(e) => setBirthDate(e.target.value)}
          required
        />
      </div>

      {/* AUTOCOMPLETE DE CIUDAD */}
      <CityAutocomplete
        onSelect={({ city, lat, lon }) => {
          setCity(city);
          setLat(String(lat));
          setLon(String(lon));
        }}
      />

      {/* LAT/LON */}
      <div className="space-y-1">
        <label className="block text-sm font-medium">Latitud (auto)</label>
        <input
          type="number"
          step="0.0001"
          className="w-full rounded-md border px-3 py-2 bg-gray-100"
          value={lat}
          disabled
        />
      </div>

      <div className="space-y-1">
        <label className="block text-sm font-medium">Longitud (auto)</label>
        <input
          type="number"
          step="0.0001"
          className="w-full rounded-md border px-3 py-2 bg-gray-100"
          value={lon}
          disabled
        />
      </div>

      {localError && (
        <p className="text-red-600 text-sm">{localError}</p>
      )}

      <button
        type="submit"
        className="bg-primary text-primary-foreground px-4 py-2 rounded-md w-full font-medium"
      >
        Generar carta
      </button>
    </form>
  );
}
