"use client";

import { useEffect, useState, useRef } from "react";
import { useAppStore } from "@/lib/store";
import { UI } from "@/lib/i18n";
import { ABU_BASE_URL } from "@/services/abu";
import RankingTable from "@/components/RankingTable";
import { LifeDomainSelector, type LifeDomain } from "@/components/LifeDomainSelector";
import { DomainSelector, type Domain } from "@/components/DomainSelector";
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

type DomainRankEntry = {
  rank: number;
  city: string;
  country: string;
  total_score: number;
  max_possible: number;
  grade: string;
  asc_sign: string;
  mc_sign: string;
  key_insight: string;
};

type DomainRankResult = {
  domain: string;
  domain_label: string;
  top_recommendations: DomainRankEntry[];
  errors: string[];
};

export function RelocationTab() {
  const { birthData, lang } = useAppStore();
  const t = UI[lang];
  const [data, setData] = useState<RelocationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Domain ranking state
  const [lifeDomain, setLifeDomain] = useState<LifeDomain | null>(null);
  const [domainRanking, setDomainRanking] = useState<DomainRankResult | null>(null);
  const [domainLoading, setDomainLoading] = useState(false);
  const [mode, setMode] = useState<'natal' | 'solar_return'>('natal');
  const [srYear, setSrYear] = useState<number>(new Date().getFullYear());

  // Blob URLs for map component
  const [geojsonUrl, setGeojsonUrl] = useState<string | null>(null);
  const [rankingUrl, setRankingUrl] = useState<string | null>(null);
  const blobUrlsRef = useRef<string[]>([]);

  // HF domain field for natal mode
  const [hfDomain, setHfDomain] = useState<Domain>("global");
  const [domainFieldLoading, setDomainFieldLoading] = useState(false);

  // Solar Return relocation field
  const [srGeojsonUrl, setSrGeojsonUrl] = useState<string | null>(null);
  const [srNatalHf, setSrNatalHf] = useState<number | null>(null);
  const [srDatetime, setSrDatetime] = useState<string | null>(null);
  const [srFieldLoading, setSrFieldLoading] = useState(false);

  // Cleanup blob URLs on unmount
  useEffect(() => {
    return () => {
      blobUrlsRef.current.forEach((u) => URL.revokeObjectURL(u));
    };
  }, []);

  // Fetch domain HF field when hfDomain changes (natal mode)
  useEffect(() => {
    if (!data || !birthData) return;
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

    fetch(`${ABU_BASE_URL}/api/astro/relocation-field?${params}`)
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
      .catch(() => {/* keep current map on error */})
      .finally(() => setDomainFieldLoading(false));
  }, [hfDomain, data, birthData]);

  // Fetch Solar Return field when switching to SR mode or changing year
  useEffect(() => {
    if (mode !== 'solar_return' || !data || !birthData) return;

    setSrFieldLoading(true);
    setSrGeojsonUrl(null);
    const params = new URLSearchParams({
      birthDate: birthData.birthDate,
      lat: String(birthData.lat),
      lon: String(birthData.lon),
      year: String(srYear),
      step: "2.5",
    });

    fetch(`${ABU_BASE_URL}/api/astro/sr-relocation-field?${params}`)
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
      .catch(() => {/* keep null — map won't render */})
      .finally(() => setSrFieldLoading(false));
  }, [mode, srYear, data, birthData]);

  // Fetch domain ranking when domain or base data changes
  useEffect(() => {
    if (!lifeDomain || !data || !birthData) {
      setDomainRanking(null);
      return;
    }

    const cities = data.rankings.slice(0, 20).map((r) => ({
      name: r.city,
      lat: r.city_lat,
      lon: r.city_lon,
      country: r.country,
    }));

    const params = new URLSearchParams({
      birthDate: birthData.birthDate,
      domain: lifeDomain,
      top_n: "5",
    });

    setDomainLoading(true);
    fetch(`${ABU_BASE_URL}/api/astro/domain-ranking?${params}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cities),
    })
      .then((r) => r.json())
      .then((result: DomainRankResult) => setDomainRanking(result))
      .catch(() => setDomainRanking(null))
      .finally(() => setDomainLoading(false));
  }, [lifeDomain, data, birthData]);

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
      const res = await fetch(`${ABU_BASE_URL}/api/astro/relocation?${params}`);
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

  if (!birthData) {
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
    return (
      <div className="text-center py-12 space-y-4">
        <Globe className="w-10 h-10 text-amber-400/50 mx-auto" />
        <p className="text-slate-400 text-sm">
          {t.calcDesc}
        </p>
        <button
          onClick={fetchRelocation}
          className="px-6 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          {t.calculate}
        </button>
        <p className="text-slate-600 text-xs">
          {t.demoLink}{" "}
          <a href="/relocation" className="text-amber-500 hover:text-amber-400 underline">
            Relocation Demo
          </a>.
        </p>
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
              />
            </div>
          )}

          {/* Ranking table */}
          <div className="rounded-lg border border-slate-700 p-3">
            <h3 className="text-sm font-medium text-slate-300 mb-2">{t.top20}</h3>
            <RankingTable data={data!.rankings} natalHf={data!.natal_hf} lang={lang} />
          </div>
        </>
      )}

      {mode === 'solar_return' && (
        <div className="space-y-3">
          {/* Year selector + SR datetime */}
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
            {srDatetime && !srFieldLoading && (
              <span className="text-xs text-slate-500 font-mono ml-auto">
                ☀ {new Date(srDatetime).toLocaleString(lang === 'es' ? 'es-AR' : 'en-US', {
                  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC'
                })} UTC
              </span>
            )}
          </div>

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
              />
            )}
          </div>

          {/* Domain ranking */}
          <div className="rounded-lg border border-slate-700 p-3 space-y-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="font-medium text-slate-300">Mejor ubicación por área de vida</span>
              <span className="text-slate-600">· Doctrina Abu Mashar · Solar Return {srYear}</span>
            </div>

          <LifeDomainSelector
            domain={lifeDomain}
            onDomainChange={setLifeDomain}
            disabled={domainLoading}
          />
          {domainLoading && (
            <div className="flex items-center gap-2 text-slate-500 text-xs py-2">
              <Loader2 className="w-3 h-3 animate-spin" />
              Calculando dominio {lifeDomain}…
            </div>
          )}
          {!domainLoading && domainRanking && domainRanking.top_recommendations.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs text-slate-500 font-mono">
                Top 5 · {domainRanking.domain_label}
              </p>
              {domainRanking.top_recommendations.map((r) => (
                <div
                  key={r.city}
                  className="flex items-center gap-3 text-xs bg-slate-800/50 rounded px-3 py-2"
                >
                  <span className="text-slate-500 font-mono w-4 shrink-0">#{r.rank}</span>
                  <span className="text-slate-200 flex-1 truncate">{r.city}</span>
                  <span
                    className="font-mono font-bold shrink-0"
                    style={{
                      color:
                        r.grade === "A" ? "#4ade80"
                        : r.grade === "B" ? "#fbbf24"
                        : r.grade === "C" ? "#94a3b8"
                        : "#f87171",
                    }}
                  >
                    {r.grade} · {r.total_score.toFixed(0)}
                  </span>
                  <span className="text-slate-600 text-[10px] truncate max-w-[120px]" title={r.key_insight}>
                    {r.key_insight}
                  </span>
                </div>
              ))}
            </div>
          )}
          {!domainLoading && lifeDomain === null && (
            <p className="text-xs text-slate-600 italic">
              Selecciona un dominio para ver que ciudades activan mejor ese area de tu vida.
            </p>
          )}
          </div>
        </div>
      )}
    </div>
  );
}
