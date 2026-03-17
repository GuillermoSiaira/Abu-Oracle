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
    <div className="p-4 space-y-3">

      {/* BLOQUE SUPERIOR — Sect / Profección / Firdaria */}
      <div className="grid grid-cols-3 divide-x divide-amber-400/20 border border-amber-400/20 rounded-lg">

        {/* Sect */}
        <button onClick={handleSectClick} className="px-4 py-3 text-left hover:bg-amber-500/5 transition-colors">
          <div className="text-[10px] text-amber-400/50 uppercase tracking-widest mb-1">{t.persianSect}</div>
          <div className="text-sm font-medium text-white">
            {sect === "diurnal" ? "☀ " + (t.persianSectDiurnal ?? "Diurna") : "☽ " + (t.persianSectNocturnal ?? "Nocturna")}
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">
            {sect === "diurnal" ? "Benéfico: Júpiter" : "Benéfico: Venus"}
          </div>
        </button>

        {/* Profección */}
        <button onClick={handleProfectionClick} className="px-4 py-3 text-left hover:bg-amber-500/5 transition-colors">
          <div className="text-[10px] text-amber-400/50 uppercase tracking-widest mb-1">{t.persianProfection}</div>
          <div className="text-sm font-medium text-white">
            {t.persianHouseLabel} {profectionHouse ?? "—"} · {profectionSign ?? "—"}
          </div>
          <div className="text-[11px] mt-0.5">
            <span className="text-gray-400">{t.persianAnnualLord}: </span>
            <span className="text-amber-400">{profectionLord ?? "—"}</span>
          </div>
        </button>

        {/* Firdaria */}
        <button onClick={handleFirdariaClick} className="px-4 py-3 text-left hover:bg-amber-500/5 transition-colors">
          <div className="text-[10px] text-amber-400/50 uppercase tracking-widest mb-1">
            {t.persianFirdaria}
            {isHistorical && (
              <span className="ml-1 normal-case text-[8px] text-slate-600 border border-slate-800 px-1 rounded">hist</span>
            )}
          </div>
          {firdariaValid ? (
            <>
              <div className="text-sm font-medium text-white">
                <span className="text-amber-400">{firdaria.major}</span>
                <span className="text-gray-500 mx-1">/</span>
                <span className="text-amber-300/70">{firdaria.sub ?? "—"}</span>
              </div>
              <div className="text-[11px] text-gray-400 mt-0.5">
                {firdaria.start?.slice(0, 10)} → {firdaria.end?.slice(0, 10)}
              </div>
            </>
          ) : (
            <div className="text-[11px] text-gray-500">{t.persianOutOfCycle}</div>
          )}
        </button>

      </div>

      {/* BLOQUE MEDIO — Partes Arábicas / Tránsitos Lunares */}
      <div className="grid grid-cols-2 gap-3">

        {/* Partes Arábicas */}
        <div className="border border-amber-400/20 rounded-lg p-3">
          <div className="text-[10px] text-amber-400/50 uppercase tracking-widest mb-2">{t.persianLotsTitle}</div>
          {[lotFortuna, lotSpirit].filter(Boolean).map((part: any) => (
            <button
              key={part.name}
              onClick={() => handleLotClick(part)}
              className="w-full text-left p-2 rounded hover:bg-amber-500/5 border border-transparent hover:border-amber-500/20 transition-colors mb-1 last:mb-0"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs text-white">
                  {part.name === "Fortuna" ? t.persianLotFortuna : t.persianLotSpirit}
                </span>
                <span className="text-[11px] text-amber-400">{part.lord}</span>
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">
                {part.sign} {Math.floor(part.degree)}°{part.house ? ` · ${t.persianHouseLabel} ${part.house}` : ""}
              </div>
            </button>
          ))}
          {!lotFortuna && !lotSpirit && (
            <p className="text-[11px] text-gray-500">{t.persianNoData}</p>
          )}
        </div>

        {/* Tránsitos Lunares */}
        <div className="border border-amber-400/20 rounded-lg p-3">
          <div className="text-[10px] text-amber-400/50 uppercase tracking-widest mb-2">{t.persianLunarTransits}</div>
          {!lunar ? (
            <p className="text-[11px] text-gray-500">{t.persianNoLunar}</p>
          ) : (
            <>
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-white/5">
                <span className="text-[11px] text-gray-400">Luna</span>
                <span className="text-xs text-white font-mono">{moonPos}</span>
              </div>
              {lunarAspects.map((asp: any, i: number) => (
                <button
                  key={i}
                  onClick={() => setPendingLillyEvent({
                    type: "click_technique",
                    payload: {
                      technique: "lunar_transit",
                      data: {
                        moon_position: lunar.moon_position,
                        moon_sign: lunar.moon_position != null ? getSignFromLongitude(lunar.moon_position) : null,
                        aspects: [asp],
                      },
                      subject_name: subjectName,
                      lang,
                    },
                  })}
                  className="w-full flex items-center justify-between p-1 rounded hover:bg-amber-500/5 border border-transparent hover:border-amber-500/20 transition-colors mb-1 last:mb-0"
                >
                  <span className="text-[11px] text-gray-400">{asp.type} {asp.planet}</span>
                  <span className="text-[11px] text-gray-500 font-mono">{asp.orb?.toFixed(2)}°</span>
                </button>
              ))}
            </>
          )}
        </div>

      </div>

      {/* BLOQUE INFERIOR — Ciclos Planetarios */}
      <div className="border border-amber-400/20 rounded-lg p-3">
        <div className="text-[10px] text-amber-400/50 uppercase tracking-widest mb-2">{t.persianCycles}</div>
        {cycles.length === 0 ? (
          <p className="text-[11px] text-gray-500">{t.persianNoEvents}</p>
        ) : (
          cycles.slice(0, 12).map((ev: any, idx: number) => (
            <button
              key={idx}
              onClick={() => setPendingLillyEvent({
                type: "click_technique",
                payload: {
                  technique: "planetary_cycle",
                  data: {
                    cycle: ev.cycle,
                    planet: ev.planet,
                    aspect_type: ev.cycle,
                    angle: ev.angle,
                    exact_date: ev.approx,
                  },
                  subject_name: subjectName,
                  lang,
                },
              })}
              className="w-full flex items-center justify-between py-1.5 border-b border-white/5 last:border-0 hover:bg-amber-500/5 px-1 rounded transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs text-white">{ev.planet}</span>
                <span className="text-[11px] text-gray-500">{ev.cycle}</span>
                <span className="text-[10px] text-gray-600 font-mono">{ev.angle}°</span>
              </div>
              <span className="text-[11px] text-gray-400 font-mono">
                {ev.approx?.slice(0, 10)}
              </span>
            </button>
          ))
        )}
      </div>

    </div>
  );
}
