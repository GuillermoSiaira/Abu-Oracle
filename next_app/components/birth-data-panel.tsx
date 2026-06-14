"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/lib/store";
import { UI } from "@/lib/i18n";
import { runAbuAnalyze } from "@/services/abu";
import CityAutocomplete from "./city-autocomplete";
import { UpgradeModal } from "./UpgradeModal";

export default function BirthDataPanel() {
  const router = useRouter();

  const {
    setBirthData,
    setAbuData,
    setIsLoading,
    setError,
    userName,
    setUserName,
    lang,
  } = useAppStore();
  const t = UI[lang];

  const userPlan = useAppStore((s) => s.userPlan);
  const isPro = userPlan === "genesis" || userPlan === "oracle";

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

  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
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

  const handleFutureToggle = () => {
    if (isPro) {
      setShowFuture((v) => !v);
    } else {
      setShowUpgradeModal(true);
    }
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    setError(null);

    if (!birthLat || !birthLon) {
      setLocalError(t.formErrorCityRequired);
      return;
    }

    let isoDate: string;
    try {
      isoDate = buildISODate(birthDate, utcOffset);
      if (!isoDate) {
        setLocalError(t.formErrorInvalidDate);
        return;
      }
    } catch (e) {
      console.error("Error building ISO date", e);
      setLocalError(t.formErrorInvalidDate);
      return;
    }

    const birthLatNum = parseFloat(birthLat);
    const birthLonNum = parseFloat(birthLon);
    const resLatNum = residenceLat ? parseFloat(residenceLat) : birthLatNum;
    const resLonNum = residenceLon ? parseFloat(residenceLon) : birthLonNum;

    // Persist userName if changed
    const trimmedName = nameInput.trim();
    if (trimmedName !== userName) setUserName(trimmedName);

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
        birth: { date: isoDate, lat: birthLatNum, lon: birthLonNum, utc_offset: utcOffset },
        current: { lat: resLatNum, lon: resLonNum, date: new Date().toISOString() },
      });

      setAbuData(abuRes);
      router.push("/chart");
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Error inesperado.");
      if (err.kind === "network") {
        setLocalError(t.formErrorNetwork);
      } else if (err.kind === "server") {
        setLocalError(t.formErrorServer);
      } else {
        setLocalError(t.formErrorGeneric);
      }
    } finally {
      setIsLoading(false);
    }
  }

  const inputClasses =
    "w-full bg-slate-800/60 text-slate-100 border border-slate-700/60 rounded-md px-3 py-2 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500/60 focus:border-amber-500/50 transition-all";
  const disabledInputClasses =
    "w-full bg-slate-700/30 text-slate-400 border border-slate-700/40 rounded-md px-3 py-2 font-medium cursor-not-allowed";

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 bg-slate-900/60 p-6 rounded-xl shadow-md border border-slate-700/40"
    >
      {/* NOMBRE */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <label className="block text-sm font-semibold text-slate-300">
            {t.formName}
          </label>
          {userName && (
            <span className="text-xs bg-amber-500/15 text-amber-400 px-2 py-0.5 rounded-full font-medium">
              {t.formNameRemembered}
            </span>
          )}
        </div>
        <input
          type="text"
          placeholder={t.formNamePlaceholder}
          className={inputClasses}
          value={nameInput}
          onChange={(e) => setNameInput(e.target.value)}
          autoComplete="given-name"
        />
        <p className="text-xs text-slate-500">
          {t.formNameHint}
        </p>
      </div>

      {/* FECHA + HUSO HORARIO */}
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm font-semibold text-slate-300">
            {t.formDate} <span className="text-xs font-normal text-gray-500">{t.formDateLocal}</span>
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
          <label className="block text-sm font-semibold text-slate-300">
            {t.formTimezone}
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
            <span className="text-sm text-slate-500">
              {utcOffset >= 0 ? `UTC+${utcOffset}` : `UTC${utcOffset}`}
              {" · "} {t.formTimezoneExample}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            {t.formTimezoneHint}
          </p>
        </div>
      </div>

      {/* CIUDAD DE NACIMIENTO */}
      <CityAutocomplete
        label={t.formBirthCity}
        placeholder={t.formBirthCityPlaceholder}
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
          <label className="block text-sm font-medium text-slate-400">
            {t.formBirthLat}
          </label>
          <input type="number" step="0.0001" className={disabledInputClasses} value={birthLat} disabled />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-slate-400">
            {t.formBirthLon}
          </label>
          <input type="number" step="0.0001" className={disabledInputClasses} value={birthLon} disabled />
        </div>
      </div>

      {/* CIUDAD DE RESIDENCIA ACTUAL */}
      <div className="space-y-1">
        <CityAutocomplete
          label={t.formResidenceCity}
          placeholder={t.formResidenceCityPlaceholder}
          onSelect={({ city, lat, lon }) => {
            setResidenceCity(city);
            setResidenceLat(String(lat));
            setResidenceLon(String(lon));
          }}
        />
        <p className="text-xs text-slate-500">
          {t.formResidenceCityHint}
        </p>
      </div>

      {/* PROYECCIÓN FUTURA — toggle */}
      <div className="border-t border-slate-700/40 pt-4">
        <button
          type="button"
          onClick={handleFutureToggle}
          className="flex items-center gap-2 text-sm font-semibold text-amber-600 hover:text-amber-700 transition-colors"
        >
          <span>{showFuture && isPro ? "▼" : "▶"}</span>
          {t.formFuture}
          {!isPro && (
            <span className="ml-2 rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-bold text-amber-400">
              {t.formFuturePro}
            </span>
          )}
        </button>
        <p className="text-xs text-gray-500 mt-1">
          {t.formFutureHint}
        </p>

        {showFuture && isPro && (
          <div className="mt-4 space-y-4 rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
            <CityAutocomplete
              label={t.formFutureCity}
              placeholder={t.formFutureCityPlaceholder}
              onSelect={({ city, lat, lon }) => {
                setFutureCity(city);
                setFutureLat(String(lat));
                setFutureLon(String(lon));
              }}
            />

            <div className="space-y-1">
              <label className="block text-sm font-semibold text-slate-300">
                {t.formFutureDate}
              </label>
              <input
                type="date"
                className={inputClasses}
                value={futureDate}
                onChange={(e) => setFutureDate(e.target.value)}
              />
              <p className="text-xs text-slate-500">
                {t.formFutureDateHint}
              </p>
            </div>
          </div>
        )}
      </div>

      {localError && (
        <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-md">
          <p className="text-red-400 text-sm font-medium flex items-center gap-2">
            ⚠️ {localError}
          </p>
        </div>
      )}

      <button
        type="submit"
        className="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold py-3 px-4 rounded-md transition-colors shadow-sm focus:ring-2 focus:ring-offset-2 focus:ring-amber-500"
      >
        {t.formSubmit}
      </button>

      <UpgradeModal
        open={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        title={t.upgradeModalTitle}
        subtitle={t.upgradeModalSubtitle}
      />
    </form>
  );
}
