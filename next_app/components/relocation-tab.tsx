"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { UI } from "@/lib/i18n";
import { ABU_BASE_URL } from "@/services/abu";
import { getAbuAuthHeaders } from "@/lib/abu-auth";
import RankingTable from "@/components/RankingTable";
import { DomainSelector, type Domain } from "@/components/DomainSelector";
import { LifeDomainSelector, type LifeDomain } from "@/components/LifeDomainSelector";
import { Globe, Loader2, AlertCircle, Star } from "lucide-react";
import dynamic from "next/dynamic";

const HFRelocationMap = dynamic(
  () => import("@/components/HFRelocationMap").then((m) => m.HFRelocationMap),
  { ssr: false }
);

type RelocationResult = {
  geojson: GeoJSON.FeatureCollection;
  rankings: Array<{
    relocation_latitude: number;
    relocation_longitude: number;
    hf_total_v3: number;
    hf_aspects: number;
    hf_angles: number;
    hf_houses: number;
    asc_lon: number;
    mc_lon: number;
    city: string;
    country: string;
    country_code?: string;
    city_lat: number;
    city_lon: number;
    distance_km: number;
  }>;
  natal_hf: number;
  max_hf: number;
  grid_points: number;
};


type SRCityEntry = {
  id: string;
  name: string;
  country?: string;
  lat: number;
  lon: number;
  hf_sr: number | null;
  isNatal?: boolean;
  isCurrent?: boolean;
};

type SRFirdaria = {
  major: string;
  minor: string;
  major_dignity: string;
  major_dignity_score: number;
};

const DOMAIN_HOUSE_NUM: Record<Domain, number> = {
  global: 0, h1: 1, h2: 2, h4: 4, h5: 5, h6: 6, h7: 7, h9: 9, h10: 10,
};

// LifeDomain (semántico) → Domain (formato hX para el backend) — Axioma 8.3
const LIFE_DOMAIN_TO_HX: Partial<Record<LifeDomain, Domain>> = {
  career: 'h10', love: 'h7', health: 'h1', family: 'h4',
  resources: 'h2', creativity: 'h5', expansion: 'h9',
};


function deriveSignificators(
  houseNum: number,
  planets: Array<{ name: string; house: number; sign?: string }>,
  houseCusps: Array<{ house: number; start: number }>
): string[] {
  const SIGN_LORDS: Record<string, string> = {
    Aries: 'Mars', Taurus: 'Venus', Gemini: 'Mercury', Cancer: 'Moon',
    Leo: 'Sun', Virgo: 'Mercury', Libra: 'Venus', Scorpio: 'Mars',
    Sagittarius: 'Jupiter', Capricorn: 'Saturn', Aquarius: 'Saturn',
    Pisces: 'Jupiter'
  };
  const SIGNS = [
    'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
    'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
  ];
  const cusp = houseCusps.find(h => h.house === houseNum);
  const cuspSign = cusp ? SIGNS[Math.floor(cusp.start / 30) % 12] : null;
  const lord = cuspSign ? SIGN_LORDS[cuspSign] : null;
  const occupants = planets.filter(p => p.house === houseNum).map(p => p.name);
  const result = lord ? [lord, ...occupants.filter(p => p !== lord)] : occupants;
  return result;
}

const DOMAIN_LABELS: Record<Domain, string> = {
  global: "Global", h1: "Identidad", h2: "Recursos", h4: "Hogar",
  h5: "Creatividad", h6: "Trabajo/Salud", h7: "Relaciones", h9: "Expansión", h10: "Carrera",
};

export function RelocationTab() {
  const { birthData, lang, abuData, setPendingLillyEvent } = useAppStore();
  const t = UI[lang];
  const subjectName =
    (birthData as any)?.userName ||
    (abuData as any)?.person?.name ||
    "Anónimo";
  const [data, setData] = useState<RelocationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [mode, setMode] = useState<'natal' | 'solar_return'>('natal');
  const [srYear, setSrYear] = useState<number>(new Date().getFullYear());

  // Blob URLs for map component
  const [geojsonUrl, setGeojsonUrl] = useState<string | null>(null);
  const [rankingUrl, setRankingUrl] = useState<string | null>(null);
  const blobUrlsRef = useRef<string[]>([]);

  // HF domain field for natal mode
  const [hfDomain, setHfDomain] = useState<Domain>("global");
  const [domainFieldLoading, setDomainFieldLoading] = useState(false);
  const domainInitRef = useRef(false);

  // Pre-gate domain selection (Axioma 8.4 — selección obligatoria antes de calcular)
  const [natalPreDomain, setNatalPreDomain] = useState<LifeDomain | null>(null);

  // Solar Return relocation field
  const [srGeojsonUrl, setSrGeojsonUrl] = useState<string | null>(null);
  const [srNatalHf, setSrNatalHf] = useState<number | null>(null);
  const [srDatetime, setSrDatetime] = useState<string | null>(null);
  const [srFieldLoading, setSrFieldLoading] = useState(false);

  // Solar Return city comparison (per-city HF scores modulated by Firdaria + domain)
  const [srCities, setSrCities] = useState<SRCityEntry[]>([]);
  const [srFirdaria, setSrFirdaria] = useState<SRFirdaria | null>(null);
  const [srScoreLoading, setSrScoreLoading] = useState(false);
  const [srLifeDomain, setSrLifeDomain] = useState<LifeDomain | null>(null);

  // Fetch SR scores for a given city list (Firdaria + domain — Axioma 8.3)
  const fetchSRScores = useCallback(async (cities: SRCityEntry[]) => {
    if (!birthData || !cities.length) return;
    setSrScoreLoading(true);
    try {
      const domainHx = srLifeDomain ? (LIFE_DOMAIN_TO_HX[srLifeDomain] ?? 'global') : 'global';
      const authHeaders = await getAbuAuthHeaders({ 'Content-Type': 'application/json' });
      const res = await fetch(`${ABU_BASE_URL}/api/astro/solar-return-score`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          birthDate: birthData.birthDate,
          birthLat: birthData.lat,
          birthLon: birthData.lon,
          sr_year: srYear,
          domain: domainHx,
          cities: cities.map((c) => ({ id: c.id, lat: c.lat, lon: c.lon })),
        }),
      });
      if (!res.ok) {
        console.error(`[SR Scores] ${res.status} ${res.statusText}`, await res.text());
        return;
      }
      const result = await res.json();
      if (result.firdaria) setSrFirdaria(result.firdaria);
      if (Array.isArray(result.scores)) {
        setSrCities((prev) =>
          prev.map((c) => {
            const score = result.scores.find((s: { id: string; hf_sr: number }) => s.id === c.id);
            return score ? { ...c, hf_sr: score.hf_sr } : c;
          })
        );
      }
    } catch (e) {
      console.error('[SR Score]', e);
    } finally {
      setSrScoreLoading(false);
    }
  }, [birthData, srYear, srLifeDomain]);

  // Map click → nearest city → city_select a Lilly
  // mode y srYear en deps: onMapClickRef en HFRelocationMap garantiza que se llama la versión más reciente
  const isProcessingClick = useRef(false);
  const handleMapClick = useCallback(async ({ lat, lon, hfScore, deltaScore }: { lat: number; lon: number; hfScore: number; deltaScore: number }) => {
    if (isProcessingClick.current) return;
    isProcessingClick.current = true;
    try {
      const res = await fetch(`/api/cities/nearest?lat=${lat}&lon=${lon}`);
      if (!res.ok) {
        console.error(`[MapClick nearest] ${res.status} ${res.statusText}`);
        return;
      }
      const nearest = await res.json();
      if (!nearest.city) return;

      // Lilly event — city interpretation
      const srDomainHx = mode === 'solar_return' && srLifeDomain
        ? (LIFE_DOMAIN_TO_HX[srLifeDomain] ?? 'global')
        : undefined;
      setPendingLillyEvent({
        type: 'city_select',
        payload: {
          city_name: nearest.city,
          country: nearest.country,
          lat,
          lon,
          distance_km: nearest.distance_km,
          hf_score: hfScore,
          delta_natal: deltaScore,
          domain: hfDomain,
          subject_name: subjectName,
          mode,
          sr_year: mode === 'solar_return' ? srYear : undefined,
          active_domain: mode === 'solar_return' ? (srLifeDomain ?? 'global') : undefined,
          active_domain_house: srDomainHx,
          lang,
        },
      });

      // SR mode: add city to comparison list and re-score
      if (mode === 'solar_return') {
        const isDuplicate = srCities.some(
          (c) => c.name === nearest.city && c.country === nearest.country
        );
        if (!isDuplicate) {
          const newCity: SRCityEntry = {
            id: `${nearest.city}-${nearest.country}-${Date.now()}`,
            name: nearest.city,
            country: nearest.country,
            lat,
            lon,
            hf_sr: null,
          };
          const updatedCities = [...srCities, newCity];
          setSrCities(updatedCities);
          fetchSRScores(updatedCities);
        }
      }
    } catch (e) {
      console.error('[MapClick]', e);
    } finally {
      // Cooldown de 1s para prevenir doble-fire (StrictMode dev / handlers acumulados)
      setTimeout(() => { isProcessingClick.current = false; }, 1000);
    }
  }, [hfDomain, subjectName, mode, srYear, lang, setPendingLillyEvent, srCities, fetchSRScores, srLifeDomain]);

  // Cleanup blob URLs on unmount
  useEffect(() => {
    return () => {
      blobUrlsRef.current.forEach((u) => URL.revokeObjectURL(u));
    };
  }, []);

  // Initialize SR city list whenever mode or year changes
  useEffect(() => {
    if (mode !== 'solar_return' || !birthData) {
      if (mode !== 'solar_return') setSrCities([]);
      return;
    }
    const initCities: SRCityEntry[] = [
      {
        id: 'natal',
        name: birthData.city ?? 'Natal',
        lat: birthData.lat,
        lon: birthData.lon,
        hf_sr: null,
        isNatal: true,
      },
    ];
    const rLat = (birthData as any).residenceLat;
    const rLon = (birthData as any).residenceLon;
    if (rLat != null && rLon != null) {
      const diffDeg = Math.hypot(rLat - birthData.lat, rLon - birthData.lon);
      if (diffDeg > 0.5) {
        initCities.push({
          id: 'current',
          name: (birthData as any).residenceCity ?? 'Actual',
          lat: rLat,
          lon: rLon,
          hf_sr: null,
          isCurrent: true,
        });
      }
    }
    setSrCities(initCities);
    setSrLifeDomain(null);   // reset domain selection when mode/year changes
    fetchSRScores(initCities);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, srYear, birthData]);

  // Re-fetch SR scores when domain changes — cities stay accumulated
  useEffect(() => {
    if (mode !== 'solar_return' || srCities.length === 0) return;
    fetchSRScores(srCities);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [srLifeDomain]);

  // Fetch domain HF field when hfDomain changes (natal mode)
  useEffect(() => {
    if (!data || !birthData) return;

    // Fire domain_select Lilly event on user-initiated domain changes (skip first render)
    if (!domainInitRef.current) {
      domainInitRef.current = true;
    } else if (hfDomain !== "global") {
      const house_num = DOMAIN_HOUSE_NUM[hfDomain];
      const significators = abuData
        ? deriveSignificators(
            house_num,
            (abuData as any).chart.planets,
            (abuData as any).chart.houses.houses
          )
        : [];
      setPendingLillyEvent({
        type: "domain_select",
        payload: {
          domain: DOMAIN_LABELS[hfDomain],
          house_num,
          subject_name: subjectName,
          significators,
          hf_current: null,
          hf_max: null,
          best_city: null,
          lang,
        },
      });
    }

    if (hfDomain === "global") {
      // Restore the original global geojson blob URL
      const geoBlob = new Blob([JSON.stringify(data.geojson)], { type: "application/json" });
      const geoUrl = URL.createObjectURL(geoBlob);
      blobUrlsRef.current.push(geoUrl);
      setGeojsonUrl(geoUrl);
      return;
    }

    setDomainFieldLoading(true);
    const params = new URLSearchParams({
      birthDate: birthData.birthDate,
      lat: String(birthData.lat),
      lon: String(birthData.lon),
      domain: hfDomain,
      step: "2.5",
    });

    getAbuAuthHeaders()
      .then((headers) => fetch(`${ABU_BASE_URL}/api/astro/relocation-field?${params}`, { headers }))
      .then((r) => {
        if (!r.ok) throw new Error(`Error ${r.status}`);
        return r.json();
      })
      .then((geojson) => {
        const blob = new Blob([JSON.stringify(geojson)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        blobUrlsRef.current.push(url);
        setGeojsonUrl(url);
      })
      .catch((e) => console.error('[Domain Field]', e))
      .finally(() => setDomainFieldLoading(false));
  }, [hfDomain, data, birthData]);

  // Fetch Solar Return field when switching to SR mode, changing year, or changing domain
  // Axioma 8.4: el heatmap no carga hasta que hay un dominio seleccionado
  useEffect(() => {
    if (mode !== 'solar_return' || !data || !birthData || !srLifeDomain) return;

    setSrFieldLoading(true);
    setSrGeojsonUrl(null);
    const domainHx = srLifeDomain ? (LIFE_DOMAIN_TO_HX[srLifeDomain] ?? 'global') : 'global';
    const params = new URLSearchParams({
      birthDate: birthData.birthDate,
      lat: String(birthData.lat),
      lon: String(birthData.lon),
      year: String(srYear),
      step: "2.5",
      domain: domainHx,
    });

    getAbuAuthHeaders()
      .then((headers) => fetch(`${ABU_BASE_URL}/api/astro/sr-relocation-field?${params}`, { headers }))
      .then((r) => {
        if (!r.ok) throw new Error(`Error ${r.status}`);
        return r.json();
      })
      .then((geojson) => {
        const blob = new Blob([JSON.stringify(geojson)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        blobUrlsRef.current.push(url);
        setSrGeojsonUrl(url);
        setSrNatalHf(geojson.properties?.natal_hf ?? null);
        setSrDatetime(geojson.properties?.sr_datetime ?? null);
      })
      .catch((e) => console.error('[SR Field]', e))
      .finally(() => setSrFieldLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, srYear, data, birthData, srLifeDomain]);

  const fetchRelocation = async () => {
    if (!birthData) return;

    setLoading(true);
    setError(null);

    // Revoke previous blob URLs
    blobUrlsRef.current.forEach((u) => URL.revokeObjectURL(u));
    blobUrlsRef.current = [];

    const params = new URLSearchParams({
      birthDate: birthData.birthDate,
      lat: String(birthData.lat),
      lon: String(birthData.lon),
      step: "2.5",
      top_n: "20",
    });

    try {
      const headers = await getAbuAuthHeaders();
      const res = await fetch(`${ABU_BASE_URL}/api/astro/relocation?${params}`, { headers });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`Error ${res.status}: ${detail}`);
      }
      const result: RelocationResult = await res.json();
      setData(result);

      // Create blob URLs for map component
      const geoBlob = new Blob([JSON.stringify(result.geojson)], { type: "application/json" });
      const geoUrl = URL.createObjectURL(geoBlob);
      blobUrlsRef.current.push(geoUrl);
      setGeojsonUrl(geoUrl);

      const rankBlob = new Blob([JSON.stringify(result.rankings)], { type: "application/json" });
      const rankUrl = URL.createObjectURL(rankBlob);
      blobUrlsRef.current.push(rankUrl);
      setRankingUrl(rankUrl);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  };

  if (!abuData) {
    return (
      <div className="text-center py-12 space-y-3">
        <Globe className="w-10 h-10 text-amber-400/50 mx-auto" />
        <p className="text-slate-400 text-sm">
          {t.enterBirthData}
        </p>
      </div>
    );
  }

  if (!data && !loading && !error) {
    const preSelectedHx = natalPreDomain ? LIFE_DOMAIN_TO_HX[natalPreDomain] : undefined;
    const preSelectedLabel = preSelectedHx ? DOMAIN_LABELS[preSelectedHx as Domain] : '';
    return (
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-7 space-y-7">
        {/* Doctrine card — Axioma 8.4 */}
        <div className="space-y-4">
          <div className="flex items-center gap-2.5">
            <Globe className="w-4 h-4 text-amber-500/50 shrink-0" />
            <p className="text-[10px] tracking-[0.28em] text-amber-500/60 uppercase font-mono">
              Axioma 8.4 — Requisito epistémico
            </p>
          </div>
          <h3
            className="text-xl font-light text-slate-100 tracking-wide leading-snug"
            style={{ fontFamily: 'Georgia, "Times New Roman", serif', fontVariant: 'small-caps' }}
          >
            ¿Para qué aspecto de tu vida buscás ubicación?
          </h3>
          <div className="h-px bg-gradient-to-r from-amber-600/35 via-amber-600/10 to-transparent" />
          <p className="text-sm text-slate-400 leading-relaxed max-w-lg">
            El campo no puede responder{' '}
            <em className="text-slate-300 not-italic">"¿dónde es todo mejor?"</em>
            {' '}— esa pregunta no tiene respuesta útil. Elegí el dominio que te importa
            y el sistema calcula el campo específico para esa pregunta.
          </p>
        </div>

        {/* Domain selector */}
        <LifeDomainSelector domain={natalPreDomain} onDomainChange={setNatalPreDomain} />

        {/* Calculate button */}
        <div className="flex items-center gap-5">
          <button
            onClick={() => {
              if (natalPreDomain && preSelectedHx) {
                setHfDomain(preSelectedHx as Domain);
                fetchRelocation();
              }
            }}
            disabled={!natalPreDomain}
            title={!natalPreDomain ? "Elegí un dominio para activar el cálculo" : undefined}
            className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
              natalPreDomain
                ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-sm shadow-amber-900/20'
                : 'bg-slate-800/80 text-slate-600 cursor-not-allowed border border-slate-700/40'
            }`}
          >
            {natalPreDomain
              ? `Calcular campo · ${preSelectedLabel}`
              : 'Elegí un dominio para activar el cálculo'}
          </button>
          {!natalPreDomain && (
            <a href="/relocation" className="text-xs text-amber-600/50 hover:text-amber-500 underline">
              Ver demo
            </a>
          )}
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-12 space-y-3">
        <Loader2 className="w-8 h-8 text-amber-400 mx-auto animate-spin" />
        <p className="text-slate-400 text-sm">
          {t.computing}
        </p>
        <p className="text-slate-600 text-xs">{t.computingNote}</p>
        <p className="text-slate-700 text-xs">Calculando 9425 puntos · resolución 2.5°</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 space-y-3">
        <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
        <p className="text-red-400 text-sm">{error}</p>
        <button
          onClick={fetchRelocation}
          className="px-4 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm transition-colors"
        >
          {t.retry}
        </button>
      </div>
    );
  }

  const currentYear = new Date().getFullYear();

  return (
    <div className="space-y-4">
      {/* Summary header */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex gap-4 text-slate-400">
          <span>{t.natal}: <span className="text-white font-mono">{data!.natal_hf.toFixed(2)}</span></span>
          <span>{t.max}: <span className="text-amber-400 font-mono">{data!.max_hf.toFixed(2)}</span></span>
          <span>Grid: <span className="text-white font-mono">{data!.grid_points}</span> pts</span>
        </div>
        <button
          onClick={fetchRelocation}
          className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-xs transition-colors"
        >
          {t.recalculate}
        </button>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-2 p-1 bg-slate-800/50 rounded-xl border border-slate-700/50">
        <button
          onClick={() => setMode('natal')}
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 px-3 rounded-lg text-xs transition-colors ${
            mode === 'natal'
              ? 'bg-slate-700 text-amber-400 font-semibold'
              : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <span className="text-base">🏠</span>
          <span>¿Dónde vivir?</span>
          <span className="text-[10px] opacity-60">Carta natal · permanente</span>
        </button>
        <button
          onClick={() => setMode('solar_return')}
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 px-3 rounded-lg text-xs transition-colors ${
            mode === 'solar_return'
              ? 'bg-slate-700 text-amber-400 font-semibold'
              : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <span className="text-base">☀</span>
          <span>¿Dónde estar este año?</span>
          <span className="text-[10px] opacity-60">Retorno Solar · {currentYear}</span>
        </button>
      </div>

      {mode === 'natal' && (
        <>
          {/* Domain selector */}
          <DomainSelector domain={hfDomain} onDomainChange={setHfDomain} />

          {/* Map */}
          {geojsonUrl && (
            <div className="rounded-lg overflow-hidden border border-slate-700 relative">
              {domainFieldLoading && (
                <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-900/70 rounded-lg">
                  <div className="flex items-center gap-2 text-slate-300 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                    Calculando campo de dominio…
                  </div>
                </div>
              )}
              <HFRelocationMap
                geojsonUrl={geojsonUrl}
                rankingUrl={rankingUrl ?? undefined}
                natalHf={data!.natal_hf}
                initialZoom={2}
                mapHeight="55vh"
                legendLow={t.legendLow}
                legendHigh={t.legendHigh}
                onMapClick={handleMapClick}
              />
            </div>
          )}

          {/* Ranking table */}
          <div className="rounded-lg border border-slate-700 p-3">
            <h3 className="text-sm font-medium text-slate-300 mb-2">
              {t.top20}
              <span className="ml-2 text-[10px] text-slate-600 font-mono normal-case">— click para interpretar</span>
            </h3>
            <RankingTable
              data={data!.rankings}
              natalHf={data!.natal_hf}
              lang={lang}
              onCityClick={(row) => {
                const SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"];
                const ascLocal = row.asc_lon != null ? SIGNS[Math.floor(((row.asc_lon % 360) + 360) % 360 / 30)] : undefined;
                const mcLocal = row.mc_lon != null ? SIGNS[Math.floor(((row.mc_lon % 360) + 360) % 360 / 30)] : undefined;
                setPendingLillyEvent({
                  type: "city_select",
                  payload: {
                    city_name: row.city,
                    country: row.country,
                    lat: row.city_lat,
                    lon: row.city_lon,
                    hf_score: row.hf_total_v3,
                    delta_natal: row.hf_total_v3 - data!.natal_hf,
                    domain: DOMAIN_LABELS[hfDomain],
                    subject_name: subjectName,
                    asc_local: ascLocal,
                    mc_local: mcLocal,
                    lang,
                  },
                });
              }}
            />
          </div>
        </>
      )}

      {mode === 'solar_return' && (
        <div className="space-y-3">
          {/* Year selector + SR datetime — siempre visible */}
          <div className="flex items-center gap-3 text-sm">
            <Star className="w-4 h-4 text-amber-400 shrink-0" />
            <label className="text-slate-400">Retorno Solar</label>
            <select
              value={srYear}
              onChange={e => setSrYear(Number(e.target.value))}
              className="bg-slate-800 border border-slate-600 text-slate-200 rounded px-2 py-1 text-xs"
            >
              {[currentYear - 1, currentYear, currentYear + 1].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
            {srDatetime && !srFieldLoading && srLifeDomain && (
              <span className="text-xs text-slate-500 font-mono ml-auto">
                ☀ {new Date(srDatetime).toLocaleString(lang === 'es' ? 'es-AR' : 'en-US', {
                  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC'
                })} UTC
              </span>
            )}
          </div>

          {/* Gate: pre-screen cuando no hay dominio seleccionado (Axioma 8.4) */}
          {!srLifeDomain ? (
            <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-7 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center gap-2.5">
                  <Star className="w-4 h-4 text-amber-500/50 shrink-0" />
                  <p className="text-[10px] tracking-[0.28em] text-amber-500/60 uppercase font-mono">
                    Axiomas 8.3 + 8.4 — Requisito epistémico
                  </p>
                </div>
                <h3
                  className="text-xl font-light text-slate-100 tracking-wide leading-snug"
                  style={{ fontFamily: 'Georgia, "Times New Roman", serif', fontVariant: 'small-caps' }}
                >
                  ¿Qué aspecto de este año querés optimizar?
                </h3>
                <div className="h-px bg-gradient-to-r from-amber-600/35 via-amber-600/10 to-transparent" />
                <p className="text-sm text-slate-400 leading-relaxed max-w-lg">
                  Firdaria determina los planetas de este período.
                  El dominio determina para qué propósito.
                  Ambos son necesarios para que el mapa tenga sentido.
                </p>
              </div>
              <LifeDomainSelector
                domain={srLifeDomain}
                onDomainChange={setSrLifeDomain}
                disabled={srScoreLoading}
              />
            </div>
          ) : (
            <>
              {/* Domain selector — Axioma 8.3: requisito epistémico, no feature de navegación */}
              <LifeDomainSelector
                domain={srLifeDomain}
                onDomainChange={setSrLifeDomain}
                disabled={srScoreLoading}
              />

              {/* Firdaria activa — label informativo */}
              {srFirdaria && (
                <div className="flex items-center gap-2 text-xs bg-slate-800/50 rounded-lg px-3 py-2 border border-slate-700/50">
                  <span className="text-amber-400 font-mono">⊙</span>
                  <span className="text-slate-400">Firdaria activa:</span>
                  <span className="text-slate-200 font-medium">{srFirdaria.major} mayor</span>
                  <span className="text-slate-600">/</span>
                  <span className="text-slate-200 font-medium">{srFirdaria.minor} menor</span>
                  {srFirdaria.major_dignity !== 'peregrine' && (
                    <span
                      className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded"
                      style={{
                        color: srFirdaria.major_dignity_score > 0 ? '#4ade80' : '#f87171',
                        background: srFirdaria.major_dignity_score > 0 ? '#14532d40' : '#7f1d1d40',
                      }}
                    >
                      {srFirdaria.major} · {srFirdaria.major_dignity}
                    </span>
                  )}
                </div>
              )}
              {srScoreLoading && !srFirdaria && (
                <div className="flex items-center gap-2 text-xs text-slate-500 px-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Calculando Firdaria…
                </div>
              )}

              {/* SR Heatmap */}
              <div className="rounded-lg overflow-hidden border border-slate-700 relative">
                {srFieldLoading && (
                  <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-900/70 rounded-lg" style={{ minHeight: "55vh" }}>
                    <div className="flex flex-col items-center gap-2 text-slate-300 text-sm">
                      <Loader2 className="w-6 h-6 animate-spin text-amber-400" />
                      <span>Calculando Retorno Solar {srYear}…</span>
                      <span className="text-xs text-slate-500">9425 puntos · planetas del RS</span>
                    </div>
                  </div>
                )}
                {!srFieldLoading && !srGeojsonUrl && data && (
                  <div className="flex items-center justify-center bg-slate-900/50 rounded-lg" style={{ minHeight: "55vh" }}>
                    <p className="text-slate-600 text-xs">Cargando campo SR…</p>
                  </div>
                )}
                {srGeojsonUrl && (
                  <HFRelocationMap
                    geojsonUrl={srGeojsonUrl}
                    natalHf={srNatalHf ?? undefined}
                    initialZoom={2}
                    mapHeight="55vh"
                    legendLow={t.legendLow}
                    legendHigh={t.legendHigh}
                    onMapClick={handleMapClick}
                  />
                )}
              </div>

              {/* City comparison — scores filtrados por Firdaria */}
              {srCities.length > 0 && (
                <div className="rounded-lg border border-slate-700 p-3 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">Comparación de ciudades · HF SR</span>
                    <span className="text-slate-600 text-[10px]">
                      {(() => {
                        const hx = LIFE_DOMAIN_TO_HX[srLifeDomain] ?? 'global';
                        return `Firdaria · ${DOMAIN_LABELS[hx as Domain] ?? srLifeDomain} ${hx.toUpperCase()}`;
                      })()}
                    </span>
                  </div>
                  {srScoreLoading && (
                    <div className="flex items-center gap-2 text-slate-500 text-xs py-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Calculando scores…
                    </div>
                  )}
                  {(() => {
                    const maxScore = Math.max(...srCities.map((c) => c.hf_sr ?? -Infinity));
                    return srCities.map((city) => (
                      <div
                        key={city.id}
                        className="flex items-center gap-3 text-xs bg-slate-800/40 rounded px-3 py-2"
                      >
                        {city.isNatal && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 shrink-0">natal</span>
                        )}
                        {city.isCurrent && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 shrink-0">actual</span>
                        )}
                        {!city.isNatal && !city.isCurrent && (
                          <span className="w-10 shrink-0" />
                        )}
                        <span className="text-slate-200 flex-1 truncate">
                          {city.hf_sr === maxScore && maxScore > -Infinity && (
                            <span className="text-amber-400 mr-1">★</span>
                          )}
                          {city.name}
                          {city.country && (
                            <span className="text-slate-500 ml-1">{city.country}</span>
                          )}
                        </span>
                        <span className="font-mono text-amber-400 shrink-0">
                          {city.hf_sr !== null ? city.hf_sr.toFixed(3) : '—'}
                        </span>
                      </div>
                    ));
                  })()}
                  <p className="text-[10px] text-slate-600 pt-1">
                    Clickea el mapa para agregar ciudades · ★ mayor score con Firdaria activa
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
