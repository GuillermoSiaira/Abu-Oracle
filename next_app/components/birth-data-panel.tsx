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

      router.push("/chart");

    } catch (err: any) {
      console.error(err);
      setError(err.message || "Error inesperado.");
      setLocalError("Ocurrió un error. Inténtalo nuevamente.");

    } finally {
      setIsLoading(false);
    }
  }

  // Clases comunes para inputs habilitados (Alto Contraste)
  const inputClasses = "w-full bg-white text-gray-950 border border-gray-300 rounded-md px-3 py-2 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all";
  
  // Clases para inputs deshabilitados (Legibles pero diferenciados)
  const disabledInputClasses = "w-full bg-gray-200 text-gray-900 border border-gray-300 rounded-md px-3 py-2 font-medium cursor-not-allowed";

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 bg-card p-6 rounded-xl shadow-md border border-gray-100"
    >
      {/* FECHA DE NACIMIENTO */}
      <div className="space-y-1">
        <label className="block text-sm font-semibold text-gray-700">Fecha de nacimiento</label>
        <input
          type="datetime-local"
          className={inputClasses}
          value={birthDate}
          onChange={(e) => setBirthDate(e.target.value)}
          required
        />
      </div>

      {/* AUTOCOMPLETE DE CIUDAD */}
      {/* Nota: Asegúrate de pasar estilos similares al CityAutocomplete si acepta className, 
          o edita ese componente internamente para usar 'text-gray-950' */}
      <CityAutocomplete
        onSelect={({ city, lat, lon }) => {
          setCity(city);
          setLat(String(lat));
          setLon(String(lon));
        }}
      />

      {/* LAT/LON */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-600">Latitud (auto)</label>
          <input
            type="number"
            step="0.0001"
            className={disabledInputClasses}
            value={lat}
            disabled
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-600">Longitud (auto)</label>
          <input
            type="number"
            step="0.0001"
            className={disabledInputClasses}
            value={lon}
            disabled
          />
        </div>
      </div>

      {localError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-700 text-sm font-medium flex items-center gap-2">
                ⚠️ {localError}
            </p>
        </div>
      )}

      <button
        type="submit"
        className="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold py-3 px-4 rounded-md transition-colors shadow-sm focus:ring-2 focus:ring-offset-2 focus:ring-amber-500"
      >
        Generar Carta Astral
      </button>
    </form>
  );
}