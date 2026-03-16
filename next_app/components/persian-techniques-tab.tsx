"use client";

import { useAppStore } from "@/lib/store";
import { UI } from "@/lib/i18n";

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

const CLICKABLE_CLASS =
  "w-full text-left p-4 border border-slate-800 rounded-lg bg-[#080808] hover:border-amber-500/30 hover:bg-amber-500/5 cursor-pointer transition-colors";

export function PersianTechniquesTab() {
  const abuData = useAppStore((s) => s.abuData);
  const isLoading = useAppStore((s) => s.isLoading);
  const lang = useAppStore((s) => s.lang);
  const birthData = useAppStore((s) => s.birthData);
  const setPendingLillyEvent = useAppStore((s) => s.setPendingLillyEvent);
  const t = UI[lang as keyof typeof UI] ?? UI.es;

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
  const sectLabel = sect === "diurnal" ? t.persianSectDiurnal : sect === "nocturnal" ? t.persianSectNocturnal : "—";
  const sectDetail = sect === "diurnal"
    ? t.persianSectDetailDiurnal
    : sect === "nocturnal"
    ? t.persianSectDetailNocturnal
    : null;
  const sectMaster = sect === "diurnal" ? "Jupiter" : "Venus";
  const sectMasterDignity = getPlanetDignity(planets, sectMaster);

  function handleSectClick() {
    if (!sect) return;
    setPendingLillyEvent({
      type: "click_technique",
      payload: {
        technique: "sect",
        data: {
          sect,
          sect_master: sectMaster,
          sect_master_dignity: sectMasterDignity,
        },
        subject_name: subjectName,
        lang,
      },
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
        data: {
          annual_house: profectionHouse,
          annual_sign: profectionSign ?? "—",
          annual_lord: profectionLord ?? "—",
          annual_lord_dignity: profectionLordDignity,
        },
        subject_name: subjectName,
        lang,
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
        data: {
          major_planet: firdaria.major,
          minor_planet: firdaria.sub ?? "—",
          start_date: firdaria.start ?? "—",
          end_date: firdaria.end ?? "—",
          major_dignity: majorDignity,
          minor_dignity: minorDignity,
        },
        subject_name: subjectName,
        lang,
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
        data: {
          lot_name: lot.name === "Fortuna" ? "fortuna" : "spirit",
          lon: lot.longitude,
          sign: lot.sign,
          degree: lot.degree,
          house: lot.house ?? null,
          lord: lot.lord,
          lord_dignity: lordDignity,
        },
        subject_name: subjectName,
        lang,
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
  const cycles = Array.isArray(life_cycles?.events) ? life_cycles!.events : [];

  return (
    <div className="space-y-5 p-4">

      {/* ---------- SECT ---------- */}
      <button onClick={handleSectClick} className={CLICKABLE_CLASS}>
        <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">{t.persianSect}</h2>
        <p className="text-slate-200 font-medium mb-1">{sectLabel}</p>
        {sectDetail && <p className="text-slate-400 text-sm leading-relaxed">{sectDetail}</p>}
      </button>

      {/* ---------- PROFECCIÓN ---------- */}
      <button onClick={handleProfectionClick} className={CLICKABLE_CLASS}>
        <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">{t.persianProfection}</h2>
        {!profectionHouse ? (
          <p className="text-slate-500 text-sm">{t.persianNoData}</p>
        ) : (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">{t.persianHouseActivated}</span>
              <span className="text-slate-200 font-mono font-semibold">{t.persianHouseLabel} {profectionHouse}</span>
            </div>
            {profectionSign && (
              <div className="flex justify-between items-center">
                <span className="text-slate-400">{t.persianCuspSign}</span>
                <span className="text-slate-200 font-mono">{profectionSign}</span>
              </div>
            )}
            {profectionLord && (
              <div className="flex justify-between items-center border-t border-slate-800/60 pt-2 mt-2">
                <span className="text-slate-400">{t.persianAnnualLord}</span>
                <span className="text-amber-400 font-semibold font-mono">{profectionLord}</span>
              </div>
            )}
          </div>
        )}
      </button>

      {/* ---------- FIRDARIA ---------- */}
      <button onClick={handleFirdariaClick} className={CLICKABLE_CLASS}>
        <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">
          {t.persianFirdaria}
          {isHistorical && (
            <span className="ml-2 normal-case text-[9px] text-slate-600 border border-slate-800 px-1.5 rounded">
              {t.persianLastPeriod}
            </span>
          )}
        </h2>
        {!firdariaValid ? (
          <p className="text-slate-500 text-sm">{t.persianOutOfCycle}</p>
        ) : (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">{t.persianMajorPeriod}</span>
              <span className="text-amber-400 font-semibold font-mono">{firdaria.major}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">{t.persianSubPeriod}</span>
              <span className="text-slate-200 font-mono">{firdaria.sub ?? "—"}</span>
            </div>
            <div className="flex justify-between items-center border-t border-slate-800/60 pt-2 mt-2">
              <span className="text-slate-400">{t.persianStart}</span>
              <span className="text-slate-300 font-mono text-xs">{formatDate(firdaria.start)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">{t.persianEnd}</span>
              <span className="text-slate-300 font-mono text-xs">{formatDate(firdaria.end)}</span>
            </div>
          </div>
        )}
      </button>

      {/* ---------- PARTES ARÁBICAS ---------- */}
      {(lotFortuna || lotSpirit) && (
        <section className="p-4 border border-slate-800 rounded-lg bg-[#080808] space-y-2">
          <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">{t.persianLotsTitle}</h2>
          {lotFortuna && (
            <button onClick={() => handleLotClick(lotFortuna)} className="w-full text-left p-3 border border-slate-800 rounded-lg hover:border-amber-500/30 hover:bg-amber-500/5 cursor-pointer transition-colors">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-300 font-medium">{t.persianLotFortuna}</span>
                <span className="text-slate-200 font-mono">{lotFortuna.sign} {Math.floor(lotFortuna.degree)}°{lotFortuna.house ? ` · Casa ${lotFortuna.house}` : ""}</span>
              </div>
              <div className="flex justify-between items-center text-xs mt-1">
                <span className="text-slate-500">{t.persianLotLord}</span>
                <span className="text-amber-400 font-mono">{lotFortuna.lord}</span>
              </div>
            </button>
          )}
          {lotSpirit && (
            <button onClick={() => handleLotClick(lotSpirit)} className="w-full text-left p-3 border border-slate-800 rounded-lg hover:border-amber-500/30 hover:bg-amber-500/5 cursor-pointer transition-colors">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-300 font-medium">{t.persianLotSpirit}</span>
                <span className="text-slate-200 font-mono">{lotSpirit.sign} {Math.floor(lotSpirit.degree)}°{lotSpirit.house ? ` · Casa ${lotSpirit.house}` : ""}</span>
              </div>
              <div className="flex justify-between items-center text-xs mt-1">
                <span className="text-slate-500">{t.persianLotLord}</span>
                <span className="text-amber-400 font-mono">{lotSpirit.lord}</span>
              </div>
            </button>
          )}
        </section>
      )}

      {/* ---------- LUNAR TRANSITS ---------- */}
      <section className="p-4 border border-slate-800 rounded-lg bg-[#080808]">
        <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">{t.persianLunarTransits}</h2>
        {!lunar ? (
          <p className="text-slate-500 text-sm">{t.persianNoLunar}</p>
        ) : (
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">{t.persianMoonPosition}</span>
              <span className="text-slate-200 font-mono">{moonPos}</span>
            </div>
            {lunarAspects.length > 0 && (
              <div className="space-y-1.5 mt-2 border-t border-slate-800/60 pt-2">
                {lunarAspects.map((a: any, i: number) => (
                  <div key={i} className="flex justify-between text-xs font-mono text-slate-400">
                    <span>{a.type} con {a.planet}</span>
                    <span className="text-slate-600">orb {a.orb.toFixed(2)}°</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {/* ---------- LIFE CYCLES ---------- */}
      <section className="p-4 border border-slate-800 rounded-lg bg-[#080808]">
        <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">{t.persianCycles}</h2>
        {cycles.length === 0 ? (
          <p className="text-slate-500 text-sm">{t.persianNoEvents}</p>
        ) : (
          <div className="space-y-2">
            {cycles.slice(0, 12).map((ev: any, idx: number) => (
              <div key={idx} className="flex justify-between items-start text-xs">
                <div>
                  <span className="text-slate-300 font-medium">{ev.cycle}</span>
                  <span className="text-slate-500 ml-2">{ev.planet} · {ev.angle}°</span>
                </div>
                <span className="text-slate-600 font-mono shrink-0 ml-3">
                  {new Date(ev.approx).toLocaleDateString("es-ES", { dateStyle: "medium" })}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

    </div>
  );
}
