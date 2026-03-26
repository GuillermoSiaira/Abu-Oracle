"use client";

import { useState, useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { UI } from "@/lib/i18n";
import { LunarDial, type LunarData } from "@/components/LunarDial";
import { ABU_BASE_URL } from "@/services/abu";
import { getAbuAuthHeaders } from "@/lib/abu-auth";

function getSignFromLongitude(long: number): string {
  const signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
  ];
  return signs[Math.floor(((long % 360) + 360) % 360 / 30)];
}

const RULERSHIPS: Record<string, string> = {
  Aries: "Mars", Taurus: "Venus", Gemini: "Mercury", Cancer: "Moon",
  Leo: "Sun", Virgo: "Mercury", Libra: "Venus", Scorpio: "Mars",
  Sagittarius: "Jupiter", Capricorn: "Saturn", Aquarius: "Saturn", Pisces: "Jupiter",
};

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("es-ES", { dateStyle: "long" });
  } catch {
    return iso;
  }
}

function getPlanetDignity(planets: any[], planetName: string): string {
  const p = planets?.find((pl: any) => pl.name === planetName);
  if (!p?.dignity) return "Peregrine";
  const d = p.dignity;
  if (d.domicile || d.kind === "domicile") return "Domicile";
  if (d.exaltation || d.kind === "exaltation") return "Exaltation";
  if (d.detriment || d.kind === "detriment") return "Detriment";
  if (d.fall || d.kind === "fall") return "Fall";
  return "Peregrine";
}

/** Groups retrograde passes of the same cycle that fall within 18 months of each other. */
function groupCloseCycles(cycles: any[]): any[] {
  const MERGE_MONTHS = 18;
  const result: any[] = [];
  for (const ev of cycles) {
    const last = result[result.length - 1];
    const sameType = last && last.planet === ev.planet && last.cycle === ev.cycle;
    const close = sameType &&
      (new Date(ev.approx).getTime() - new Date(last.approxEnd ?? last.approx).getTime()) /
      (1000 * 3600 * 24 * 30) <= MERGE_MONTHS;
    if (close) {
      last.approxEnd = ev.approx;
    } else {
      result.push({ ...ev, approxEnd: undefined });
    }
  }
  return result;
}

/** Returns Tailwind color classes based on cycle type (angle). */
function cycleColors(angle: number): { planet: string; badge: string; badgeBg: string } {
  if (angle === 0)   return { planet: "text-amber-300",  badge: "text-amber-400",  badgeBg: "bg-amber-400/10 border-amber-400/20" };
  if (angle === 180) return { planet: "text-sky-300",    badge: "text-sky-400",    badgeBg: "bg-sky-400/10 border-sky-400/20" };
  return               { planet: "text-orange-300",  badge: "text-orange-400", badgeBg: "bg-orange-400/10 border-orange-400/20" };
}

/** Tooltip wrapper — renders a small ⓘ hint + absolute tooltip on hover. */
function SectionTitle({
  label,
  tooltip,
  className = "",
}: {
  label: string;
  tooltip: string;
  className?: string;
}) {
  return (
    <div className={`relative group inline-flex items-center gap-1 text-[10px] text-amber-400/50 uppercase tracking-widest ${className}`}>
      {label}
      <span className="text-amber-400/30 group-hover:text-amber-400/60 transition-colors text-[9px] leading-none">ⓘ</span>
      <div className="absolute left-0 top-full mt-2 z-50 hidden group-hover:block w-60 bg-[#0d0d14] border-l-2 border-l-amber-500/40 border border-slate-700/60 rounded-r rounded-bl p-3 text-[11px] text-slate-300 normal-case tracking-normal leading-relaxed shadow-2xl pointer-events-none font-sans">
        {tooltip}
      </div>
    </div>
  );
}

const CLICKABLE_CLASS =
  "w-full text-left p-4 border border-slate-800 rounded-lg bg-[#080808] hover:border-amber-500/30 hover:bg-amber-500/5 cursor-pointer transition-colors";

export function PersianTechniquesTab() {
  const abuData = useAppStore((s) => s.abuData);
  const isLoading = useAppStore((s) => s.isLoading);
  const lang = useAppStore((s) => s.lang);
  const birthData = useAppStore((s) => s.birthData);
  const setPendingLillyEvent = useAppStore((s) => s.setPendingLillyEvent);
  const t = UI[lang as keyof typeof UI] ?? UI.es;

  const [lunarData, setLunarData] = useState<LunarData | null>(null);

  useEffect(() => {
    if (!birthData?.birthDate || birthData.lat == null || birthData.lon == null) return;
    getAbuAuthHeaders().then((headers) => {
      const url = new URL(`${ABU_BASE_URL}/api/astro/lunar`);
      url.searchParams.set("birthDate", birthData.birthDate);
      url.searchParams.set("lat", String(birthData.lat));
      url.searchParams.set("lon", String(birthData.lon));
      fetch(url.toString(), { headers })
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => { if (data) setLunarData(data as LunarData); })
        .catch(() => {});
    });
  }, [birthData?.birthDate, birthData?.lat, birthData?.lon]);

  if (isLoading) return <div className="p-6 text-slate-500 text-sm">{t.persianSect}…</div>;
  if (!abuData) return <div className="p-6 text-slate-500 text-sm">{t.persianNoData}</div>;

  const { derived, chart, life_cycles } = abuData;
  const planets: any[] = chart?.planets ?? [];

  const subjectName =
    (birthData as any)?.userName ||
    abuData.person?.name ||
    "Anónimo";

  // ---------------------------
  // SECT
  // ---------------------------
  const sect = derived?.sect ?? null;
  const sectMaster = sect === "diurnal" ? "Jupiter" : "Venus";
  const sectMasterDignity = getPlanetDignity(planets, sectMaster);

  function handleSectClick() {
    if (!sect) return;
    setPendingLillyEvent({
      type: "click_technique",
      payload: { technique: "sect", data: { sect, sect_master: sectMaster, sect_master_dignity: sectMasterDignity }, subject_name: subjectName, lang },
    });
  }

  // ---------------------------
  // PROFECCIÓN
  // ---------------------------
  const profectionHouse: number | null = derived?.profection?.house ?? null;
  let profectionSign: string | null = null;
  let profectionLord: string | null = null;

  if (profectionHouse && chart?.houses?.houses) {
    const entry = chart.houses.houses.find((h: any) => h.house === profectionHouse);
    if (entry) {
      profectionSign = getSignFromLongitude(entry.start);
      profectionLord = profectionSign ? (RULERSHIPS[profectionSign] ?? null) : null;
    }
  }
  const profectionLordDignity = profectionLord ? getPlanetDignity(planets, profectionLord) : "—";

  function handleProfectionClick() {
    if (!profectionHouse) return;
    setPendingLillyEvent({
      type: "click_technique",
      payload: {
        technique: "profection",
        data: { annual_house: profectionHouse, annual_sign: profectionSign ?? "—", annual_lord: profectionLord ?? "—", annual_lord_dignity: profectionLordDignity },
        subject_name: subjectName, lang,
      },
    });
  }

  // ---------------------------
  // FIRDARIA
  // ---------------------------
  const firdaria = derived?.firdaria?.current ?? null;
  const isHistorical = (firdaria as any)?.historical_fallback === true;
  const firdariaValid = firdaria && firdaria.major !== "N/A" && firdaria.major !== null;
  const majorDignity = firdariaValid ? getPlanetDignity(planets, firdaria!.major as string) : "—";
  const minorDignity = firdariaValid && firdaria!.sub ? getPlanetDignity(planets, firdaria!.sub as string) : "—";

  function handleFirdariaClick() {
    if (!firdariaValid) return;
    setPendingLillyEvent({
      type: "click_technique",
      payload: {
        technique: "firdaria",
        data: { major_planet: firdaria.major, minor_planet: firdaria.sub ?? "—", start_date: firdaria.start ?? "—", end_date: firdaria.end ?? "—", major_dignity: majorDignity, minor_dignity: minorDignity },
        subject_name: subjectName, lang,
      },
    });
  }

  // ---------------------------
  // LOTS (Partes Arábicas)
  // ---------------------------
  const lots: any[] = Array.isArray(derived?.lots) ? derived!.lots : [];
  const lotFortuna = lots.find((l: any) => l.name === "Fortuna") ?? null;
  const lotSpirit = lots.find((l: any) => l.name === "Spirit") ?? null;

  function handleLotClick(lot: any) {
    if (!lot) return;
    const lordDignity = getPlanetDignity(planets, lot.lord);
    setPendingLillyEvent({
      type: "click_technique",
      payload: {
        technique: "lot",
        data: { lot_name: lot.name === "Fortuna" ? "fortuna" : "spirit", lon: lot.longitude, sign: lot.sign, degree: lot.degree, house: lot.house ?? null, lord: lot.lord, lord_dignity: lordDignity },
        subject_name: subjectName, lang,
      },
    });
  }

  // ---------------------------
  // LUNAR TRANSITS
  // ---------------------------
  const lunar = derived?.lunar_transit ?? null;
  const moonPos = lunar?.moon_position != null ? lunar.moon_position.toFixed(2) + "°" : "—";
  const lunarAspects = Array.isArray(lunar?.aspects) ? lunar!.aspects : [];

  // ---------------------------
  // LIFE CYCLES
  // ---------------------------
  const allCycles = Array.isArray(life_cycles?.events) ? life_cycles!.events : [];
  const today = new Date().toISOString().slice(0, 10);
  const rawFuture = allCycles
    .filter((c: any) => c.approx >= today)
    .sort((a: any, b: any) => a.approx.localeCompare(b.approx));
  const rawPast = allCycles
    .filter((c: any) => c.approx < today)
    .sort((a: any, b: any) => b.approx.localeCompare(a.approx))
    .slice(0, 8);

  const futureCycles = groupCloseCycles(rawFuture).slice(0, 12);
  const pastCycles = groupCloseCycles(rawPast.slice().reverse()).reverse();

  function dispatchCycle(ev: any) {
    setPendingLillyEvent({
      type: "click_technique",
      payload: {
        technique: "planetary_cycle",
        data: { cycle: ev.cycle, planet: ev.planet, aspect_type: ev.cycle, angle: ev.angle, exact_date: ev.approx },
        subject_name: subjectName, lang,
      },
    });
  }

  return (
    <div className="p-4 space-y-3">

      {/* BLOQUE SUPERIOR — Sect / Profección / Firdaria */}
      <div className="grid grid-cols-3 divide-x divide-amber-400/15 border border-amber-400/15 rounded-lg overflow-visible">

        {/* Sect */}
        <button onClick={handleSectClick} className="px-4 py-3 text-left hover:bg-amber-500/5 transition-colors rounded-l-lg overflow-visible">
          <SectionTitle label={t.persianSect} tooltip={t.persianTooltipSect} className="mb-2" />
          <div className="text-sm font-medium text-white">
            {sect === "diurnal" ? "☀ " + (t.persianSectDiurnal ?? "Diurna") : "☽ " + (t.persianSectNocturnal ?? "Nocturna")}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            {sect === "diurnal" ? "♃ Jupiter" : "♀ Venus"}
          </div>
        </button>

        {/* Profección */}
        <button onClick={handleProfectionClick} className="px-4 py-3 text-left hover:bg-amber-500/5 transition-colors overflow-visible">
          <SectionTitle label={t.persianProfection} tooltip={t.persianTooltipProfection} className="mb-2" />
          <div className="text-sm font-medium text-white">
            {t.persianHouseLabel} {profectionHouse ?? "—"} · <span className="text-slate-300">{profectionSign ?? "—"}</span>
          </div>
          <div className="text-[11px] mt-0.5">
            <span className="text-slate-500">{t.persianAnnualLord}: </span>
            <span className="text-amber-400 font-medium">{profectionLord ?? "—"}</span>
          </div>
        </button>

        {/* Firdaria */}
        <button onClick={handleFirdariaClick} className="px-4 py-3 text-left hover:bg-amber-500/5 transition-colors rounded-r-lg overflow-visible">
          <div className="mb-2 flex items-center gap-2">
            <SectionTitle label={t.persianFirdaria} tooltip={t.persianTooltipFirdaria} />
            {isHistorical && (
              <span className="text-[8px] text-slate-600 border border-slate-800 px-1 py-px rounded">hist</span>
            )}
          </div>
          {firdariaValid ? (
            <>
              <div className="text-sm font-medium">
                <span className="text-amber-400">{firdaria.major}</span>
                <span className="text-slate-600 mx-1.5">/</span>
                <span className="text-amber-300/60">{firdaria.sub ?? "—"}</span>
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
                {firdaria.start?.slice(0, 10)} → {firdaria.end?.slice(0, 10)}
              </div>
            </>
          ) : (
            <div className="text-[11px] text-slate-600">{t.persianOutOfCycle}</div>
          )}
        </button>

      </div>

      {/* BLOQUE MEDIO — Partes Arábicas / Dial Lunar */}
      <div className="grid grid-cols-2 gap-3">

        {/* Partes Arábicas */}
        <div className="border border-amber-400/15 rounded-lg p-3">
          <SectionTitle label={t.persianLotsTitle} tooltip={t.persianTooltipLots} className="mb-3" />
          {[lotFortuna, lotSpirit].filter(Boolean).map((part: any) => (
            <button
              key={part.name}
              onClick={() => handleLotClick(part)}
              className="w-full text-left p-2 rounded hover:bg-amber-500/5 border border-transparent hover:border-amber-500/15 transition-colors mb-1 last:mb-0"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-200">
                  {part.name === "Fortuna" ? t.persianLotFortuna : t.persianLotSpirit}
                </span>
                <span className="text-[11px] text-amber-400 font-medium">{part.lord}</span>
              </div>
              <div className="text-[11px] text-slate-600 mt-0.5">
                {part.sign} {Math.floor(part.degree)}°{part.house ? ` · ${t.persianHouseLabel} ${part.house}` : ""}
              </div>
            </button>
          ))}
          {!lotFortuna && !lotSpirit && (
            <p className="text-[11px] text-slate-600">{t.persianNoData}</p>
          )}
        </div>

        {/* Dial Lunar */}
        <div className="border border-amber-400/15 rounded-lg p-3 flex flex-col">
          <SectionTitle label={t.persianLunarDialTitle} tooltip={t.persianTooltipLunar} className="mb-2" />
          {lunarData ? (
            <LunarDial data={lunarData} lang={lang} />
          ) : (
            <div className="flex-1 flex items-center justify-center text-[11px] text-slate-600 py-8">
              {t.persianNoLunar}
            </div>
          )}
        </div>

      </div>

      {/* BLOQUE INFERIOR — Tránsitos Lunares / Ciclos Planetarios */}
      <div className="grid grid-cols-2 gap-3">

        {/* Tránsitos Lunares */}
        <div className="border border-amber-400/15 rounded-lg p-3">
          <SectionTitle label={t.persianLunarTransits} tooltip={t.persianTooltipLunar} className="mb-3" />
          {!lunar ? (
            <p className="text-[11px] text-slate-600">{t.persianNoLunar}</p>
          ) : (
            <>
              <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-white/5">
                <span className="text-[11px] text-slate-500">☽ Moon</span>
                <span className="text-xs text-slate-200 font-mono">{moonPos}</span>
              </div>
              {lunarAspects.map((asp: any, i: number) => (
                <button
                  key={i}
                  onClick={() => setPendingLillyEvent({
                    type: "click_technique",
                    payload: {
                      technique: "lunar_transit",
                      data: { moon_position: lunar.moon_position, moon_sign: lunar.moon_position != null ? getSignFromLongitude(lunar.moon_position) : null, aspects: [asp] },
                      subject_name: subjectName, lang,
                    },
                  })}
                  className="w-full flex items-center justify-between p-1 rounded hover:bg-amber-500/5 border border-transparent hover:border-amber-500/15 transition-colors mb-1 last:mb-0"
                >
                  <span className="text-[11px] text-slate-400">{asp.type} {asp.planet}</span>
                  <span className="text-[11px] text-slate-600 font-mono">{asp.orb?.toFixed(2)}°</span>
                </button>
              ))}
            </>
          )}
        </div>

        {/* Ciclos Planetarios */}
        <div className="border border-amber-400/15 rounded-lg p-3">
          <SectionTitle label={t.persianCycles} tooltip={t.persianTooltipCycles} className="mb-3" />
          {allCycles.length === 0 ? (
            <p className="text-[11px] text-slate-600">{t.persianNoEvents}</p>
          ) : (
            <>
              {futureCycles.length > 0 && (
                <div className="mb-2">
                  <div className="text-[9px] text-amber-400/40 uppercase tracking-widest mb-1.5">{t.persianCyclesUpcoming}</div>
                  {futureCycles.map((ev: any, idx: number) => {
                    const c = cycleColors(ev.angle);
                    return (
                      <button
                        key={`f-${idx}`}
                        onClick={() => dispatchCycle(ev)}
                        className="w-full flex items-center justify-between py-1 px-1 rounded hover:bg-white/3 border border-transparent hover:border-white/5 transition-colors"
                      >
                        <div className="flex items-center gap-1.5 min-w-0">
                          <span className={`text-[11px] font-medium ${c.planet}`}>{ev.planet}</span>
                          <span className={`text-[9px] px-1 py-px rounded border ${c.badge} ${c.badgeBg}`}>{ev.cycle.replace(ev.planet + " ", "")}</span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono shrink-0 ml-1">
                          {ev.approx.slice(0, 7)}{ev.approxEnd ? `–${ev.approxEnd.slice(2, 7)}` : ""}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
              {pastCycles.length > 0 && (
                <div>
                  <div className="text-[9px] text-slate-600 uppercase tracking-widest mb-1.5 border-t border-white/5 pt-2">{t.persianCyclesRecent}</div>
                  {pastCycles.map((ev: any, idx: number) => {
                    const c = cycleColors(ev.angle);
                    return (
                      <button
                        key={`p-${idx}`}
                        onClick={() => dispatchCycle(ev)}
                        className="w-full flex items-center justify-between py-1 px-1 rounded hover:bg-white/3 border border-transparent hover:border-white/5 transition-colors opacity-50 hover:opacity-70"
                      >
                        <div className="flex items-center gap-1.5 min-w-0">
                          <span className={`text-[11px] ${c.planet}`}>{ev.planet}</span>
                          <span className="text-[9px] text-slate-600">{ev.cycle.replace(ev.planet + " ", "")}</span>
                        </div>
                        <span className="text-[10px] text-slate-600 font-mono shrink-0 ml-1">
                          {ev.approx.slice(0, 7)}{ev.approxEnd ? `–${ev.approxEnd.slice(2, 7)}` : ""}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>

      </div>

    </div>
  );
}
