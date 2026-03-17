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
    userName,
    setUserName,
  } = useAppStore();

  const [nameInput, setNameInput] = useState(userName);
  const [birthDate, setBirthDate] = useState("");
  // UTC offset in hours (e.g. -3 for Argentina, +1 for Madrid)
  // Default: browser's current offset
  const [utcOffset, setUtcOffset] = useState<number>(
    -(new Date().getTimezoneOffset() / 60)
  );

  // Birth city
  const [birthLat, setBirthLat] = useState("");
  const [birthLon, setBirthLon] = useState("");
  const [birthCity, setBirthCity] = useState("");

  // Current residence (optional — defaults to birth city)
  const [residenceLat, setResidenceLat] = useState("");
  const [residenceLon, setResidenceLon] = useState("");
  const [residenceCity, setResidenceCity] = useState("");

  // Future projection (optional)
  const [showFuture, setShowFuture] = useState(false);
  const [futureCity, setFutureCity] = useState("");
  const [futureLat, setFutureLat] = useState("");
  const [futureLon, setFutureLon] = useState("");
  const [futureDate, setFutureDate] = useState("");

  const [localError, setLocalError] = useState<string | null>(null);

  // Convert local datetime + UTC offset → UTC ISO string "1978-07-06T00:15:00.000Z"
  function buildISODate(localDate: string, offsetHours: number): string {
    if (!localDate) return "";
    const [datePart, timePart] = localDate.split("T");
    const [year, month, day] = datePart.split("-").map(Number);
    const [hour, minute] = timePart.split(":").map(Number);
    // Create UTC ms from local components, then subtract offset to get real UTC
    const localMs = Date.UTC(year, month - 1, day, hour, minute, 0);
    const offsetMs = offsetHours * 60 * 60 * 1000;
    return new Date(localMs - offsetMs).toISOString();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    setError(null);

    if (!birthDate || !birthLat || !birthLon) {
      setLocalError("Selecciona una ciudad de nacimiento y una fecha.");
      return;
    }

    const birthLatNum = parseFloat(birthLat);
    const birthLonNum = parseFloat(birthLon);
    const resLatNum = residenceLat ? parseFloat(residenceLat) : birthLatNum;
    const resLonNum = residenceLon ? parseFloat(residenceLon) : birthLonNum;

    // Persist userName if changed
    const trimmedName = nameInput.trim();
    if (trimmedName !== userName) setUserName(trimmedName);

    const isoDate = buildISODate(birthDate, utcOffset);

    const birthDataPayload = {
      birthDate: isoDate,
      utcOffset,
      lat: birthLatNum,
      lon: birthLonNum,
      city: birthCity || null,
      userName: trimmedName || null,
      residenceCity: residenceCity || birthCity || null,
      residenceLat: resLatNum,
      residenceLon: resLonNum,
      futureCity: futureCity || null,
      futureLat: futureLat ? parseFloat(futureLat) : null,
      futureLon: futureLon ? parseFloat(futureLon) : null,
      futureDate: futureDate || null,
    };

    try {
      setIsLoading(true);
      setBirthData(birthDataPayload);

      const abuRes = await runAbuAnalyze({
        person: { name: trimmedName || null, question: "" },
        birth: { date: isoDate, lat: birthLatNum, lon: birthLonNum },
        current: { lat: resLatNum, lon: resLonNum, date: new Date().toISOString() },
      });

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

  const inputClasses =
    "w-full bg-white text-gray-950 border border-gray-300 rounded-md px-3 py-2 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all";
  const disabledInputClasses =
    "w-full bg-gray-200 text-gray-900 border border-gray-300 rounded-md px-3 py-2 font-medium cursor-not-allowed";

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 bg-card p-6 rounded-xl shadow-md border border-gray-100"
    >
      {/* NOMBRE */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <label className="block text-sm font-semibold text-gray-700">
            Tu nombre
          </label>
          {userName && (
            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">
              recordado
            </span>
          )}
        </div>
        <input
          type="text"
          placeholder="¿Cómo te llamás?"
          className={inputClasses}
          value={nameInput}
          onChange={(e) => setNameInput(e.target.value)}
          autoComplete="given-name"
        />
        <p className="text-xs text-gray-500">
          Abu recordará tu nombre entre sesiones.
        </p>
      </div>

      {/* FECHA + HUSO HORARIO */}
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm font-semibold text-gray-700">
            Fecha y hora de nacimiento <span className="text-xs font-normal text-gray-500">(hora local)</span>
          </label>
          <input
            type="datetime-local"
            className={inputClasses}
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            required
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-semibold text-gray-700">
            Huso horario (UTC offset)
          </label>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={-12}
              max={14}
              step={0.5}
              className={`${inputClasses} w-32`}
              value={utcOffset}
              onChange={(e) => setUtcOffset(parseFloat(e.target.value))}
            />
            <span className="text-sm text-gray-500">
              {utcOffset >= 0 ? `UTC+${utcOffset}` : `UTC${utcOffset}`}
              {" · "} Ej: Argentina = −3, España = +1, NYC = −5
            </span>
          </div>
          <p className="text-xs text-gray-400">
            Usá el huso horario del lugar de nacimiento en el momento del evento.
          </p>
        </div>
      </div>

      {/* CIUDAD DE NACIMIENTO */}
      <CityAutocomplete
        label="Ciudad de nacimiento"
        placeholder="Ingresa tu ciudad natal"
        onSelect={({ city, lat, lon }) => {
          setBirthCity(city);
          setBirthLat(String(lat));
          setBirthLon(String(lon));
          // Pre-fill residence with birth city if not already set
          if (!residenceCity) {
            setResidenceCity(city);
            setResidenceLat(String(lat));
            setResidenceLon(String(lon));
          }
        }}
      />

      {/* LAT/LON NACIMIENTO */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-600">
            Latitud natal
          </label>
          <input type="number" step="0.0001" className={disabledInputClasses} value={birthLat} disabled />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-600">
            Longitud natal
          </label>
          <input type="number" step="0.0001" className={disabledInputClasses} value={birthLon} disabled />
        </div>
      </div>

      {/* CIUDAD DE RESIDENCIA ACTUAL */}
      <div className="space-y-1">
        <CityAutocomplete
          label="Ciudad de residencia actual"
          placeholder="¿Dónde vivís actualmente?"
          onSelect={({ city, lat, lon }) => {
            setResidenceCity(city);
            setResidenceLat(String(lat));
            setResidenceLon(String(lon));
          }}
        />
        <p className="text-xs text-gray-500">
          Se usa para calcular tus tránsitos actuales. Por defecto igual a ciudad natal.
        </p>
      </div>

      {/* PROYECCIÓN FUTURA — toggle */}
      <div className="border-t border-gray-200 pt-4">
        <button
          type="button"
          onClick={() => setShowFuture((v) => !v)}
          className="flex items-center gap-2 text-sm font-semibold text-amber-600 hover:text-amber-700 transition-colors"
        >
          <span>{showFuture ? "▼" : "▶"}</span>
          Proyección futura (opcional)
        </button>
        <p className="text-xs text-gray-500 mt-1">
          Calculá tu HF en otra ciudad y fecha para explorar relocalización.
        </p>

        {showFuture && (
          <div className="mt-4 space-y-4 p-4 bg-amber-50 rounded-lg border border-amber-100">
            <CityAutocomplete
              label="Ciudad objetivo"
              placeholder="¿A dónde querés mudarte?"
              onSelect={({ city, lat, lon }) => {
                setFutureCity(city);
                setFutureLat(String(lat));
                setFutureLon(String(lon));
              }}
            />

            <div className="space-y-1">
              <label className="block text-sm font-semibold text-gray-700">
                Fecha objetivo
              </label>
              <input
                type="date"
                className={inputClasses}
                value={futureDate}
                onChange={(e) => setFutureDate(e.target.value)}
              />
              <p className="text-xs text-gray-500">
                Fecha para la que querés calcular el HF transitorio en esa ciudad.
              </p>
            </div>
          </div>
        )}
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
