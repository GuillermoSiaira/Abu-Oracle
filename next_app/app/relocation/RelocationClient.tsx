"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import NarrativePanel from "@/components/NarrativePanel";
import RankingTable from "@/components/RankingTable";
import { DomainSelector, type Domain } from "@/components/DomainSelector";
import { Globe, ChevronDown, BarChart3, BookOpen, Map, Languages } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { UI, LANG_OPTIONS, type Lang } from "@/lib/i18n";

// Lazy-load the map to avoid SSR issues with MapLibre
const HFRelocationMap = dynamic(() => import("@/components/HFRelocationMap"), {
  ssr: false,
  loading: () => (
    <div className="h-[60vh] rounded-xl bg-slate-900 animate-pulse flex items-center justify-center text-slate-500">
      Cargando mapa…
    </div>
  ),
});

type SubjectMeta = {
  id: number;
  slug: string;
  display_name: string;
  rodden_rating: string;
  birth_datetime: string;
  natal_lat: number;
  natal_lon: number;
  natal_hf: number;
  max_hf: number;
  min_hf: number;
  grid_points: number;
  has_geojson: boolean;
  has_ranking: boolean;
  has_narrative: boolean;
};

type DemoIndex = {
  subjects: SubjectMeta[];
};

type NarrativeData = {
  headline: string;
  narrative: string;
  actions: string[];
  astro_metadata?: Record<string, unknown>;
};

type RankingEntry = {
  subject_id: string;
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
  city_lat: number;
  city_lon: number;
  distance_km: number;
};

type ActiveTab = "map" | "ranking" | "narrative";

export default function RelocationClient() {
  const [subjects, setSubjects] = useState<SubjectMeta[]>([]);
  const [selected, setSelected] = useState<SubjectMeta | null>(null);
  const [ranking, setRanking] = useState<RankingEntry[] | null>(null);
  const [narrative, setNarrative] = useState<NarrativeData | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("map");
  const [loading, setLoading] = useState(false);
  const [domain, setDomain] = useState<Domain>("global");
  const { lang, setLang } = useAppStore();

  const t = UI[lang];

  // Load demo index
  useEffect(() => {
    fetch("/demo/index.json")
      .then((r) => r.json())
      .then((data: DemoIndex) => {
        setSubjects(data.subjects);
        if (data.subjects.length > 0) {
          setSelected(data.subjects[0]);
        }
      });
  }, []);

  // Load ranking + narrative when subject changes
  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    const slug = selected.slug;

    Promise.all([
      fetch(`/demo/${slug}/ranking.json`).then((r) => r.json()),
      fetch(`/demo/${slug}/narrative.json`).then((r) => r.json()),
    ])
      .then(([rankData, narrData]) => {
        setRanking(rankData);
        setNarrative(narrData);
      })
      .finally(() => setLoading(false));
  }, [selected]);

  const gainPct = selected
    ? (((selected.max_hf - selected.natal_hf) / selected.natal_hf) * 100).toFixed(1)
    : null;

  const tabs: { key: ActiveTab; label: string; icon: React.ReactNode }[] = [
    { key: "map", label: t.tabMap, icon: <Map className="w-4 h-4" /> },
    { key: "ranking", label: t.tabRanking, icon: <BarChart3 className="w-4 h-4" /> },
    { key: "narrative", label: t.tabNarrative, icon: <BookOpen className="w-4 h-4" /> },
  ];

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <header className="shrink-0 px-6 py-4 border-b border-slate-800 bg-[#080808]">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-100 tracking-tight flex items-center gap-2">
              <Globe className="w-6 h-6 text-amber-400" />
              {t.relTitle}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              {t.relSubtitle}
            </p>
          </div>

          {/* Language + Subject selectors */}
          <div className="flex items-center gap-2">
            {/* Language selector */}
            <div className="relative">
              <select
                value={lang}
                onChange={(e) => setLang(e.target.value as Lang)}
                className="appearance-none bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg pl-3 pr-7 py-2 focus:outline-none focus:border-amber-500/50 cursor-pointer"
              >
                {LANG_OPTIONS.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.flag} {l.label}
                  </option>
                ))}
              </select>
              <Languages className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Subject selector */}
            <div className="relative">
            <select
              value={selected?.slug ?? ""}
              onChange={(e) => {
                const s = subjects.find((s) => s.slug === e.target.value);
                if (s) setSelected(s);
              }}
              className="appearance-none bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg pl-3 pr-8 py-2 focus:outline-none focus:border-amber-500/50 cursor-pointer min-w-[220px]"
            >
              {subjects.map((s) => (
                <option key={s.slug} value={s.slug}>
                  {s.display_name} ({s.rodden_rating})
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
          </div>
        </div>

        {/* Stats bar */}
        {selected && (
          <div className="flex flex-wrap gap-4 mt-3 text-xs font-mono">
            <Stat label={t.natal} value={selected.natal_hf.toFixed(2)} />
            <Stat label={t.max} value={selected.max_hf.toFixed(2)} color="text-green-400" />
            <Stat label={t.min} value={selected.min_hf.toFixed(2)} color="text-red-400" />
            <Stat label={t.gain} value={`+${gainPct}%`} color="text-amber-400" />
            <Stat label={t.points} value={String(selected.grid_points)} />
          </div>
        )}
        {/* HF comparison bar */}
        {selected && (
          <div className="flex flex-wrap items-center gap-3 mt-3">
            <div className="flex-1 min-w-[200px]">
              <div className="relative h-5 bg-slate-800 rounded-full overflow-hidden">
                {/* Natal bar */}
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-slate-600 transition-all duration-500"
                  style={{ width: `${Math.min((selected.natal_hf / selected.max_hf) * 100, 100)}%` }}
                />
                {/* Max bar (full) */}
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-amber-500/30 border-r-2 border-amber-400 transition-all duration-500"
                  style={{ width: "100%" }}
                />
                {/* Natal label */}
                <span
                  className="absolute top-0 h-full flex items-center text-[10px] font-mono text-slate-200 pl-2 font-bold"
                  style={{ left: 0 }}
                >
                  {selected.natal_hf.toFixed(1)}
                </span>
                {/* Max label */}
                <span
                  className="absolute top-0 h-full flex items-center text-[10px] font-mono text-amber-400 pr-2 font-bold"
                  style={{ right: 0 }}
                >
                  {selected.max_hf.toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Tab bar */}
      <div className="shrink-0 flex border-b border-slate-800 bg-[#0a0a0a]">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm transition-colors border-b-2 ${
              activeTab === t.key
                ? "border-amber-500 text-amber-400"
                : "border-transparent text-slate-500 hover:text-slate-300"
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center py-12 text-slate-500 text-sm animate-pulse">
            {t.loading} {selected?.display_name}…
          </div>
        )}

        {!loading && activeTab === "map" && selected && (
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <DomainSelector domain={domain} onDomainChange={setDomain} />
              <span className="text-[10px] text-slate-600 font-mono bg-slate-900/50 px-2 py-1 rounded border border-slate-800">
                Campo HF · Carta Natal
              </span>
            </div>
            <HFRelocationMap
              geojsonUrl={`/geojson/${selected.slug}_domains.geojson`}
              rankingUrl={`/demo/${selected.slug}/ranking.json`}
              natalHf={selected.natal_hf}
              domain={domain}
              className="rounded-xl overflow-hidden border border-slate-800"
              legendLow={t.legendLow}
              legendHigh={t.legendHigh}
            />
          </div>
        )}

        {!loading && activeTab === "ranking" && (
          <div className="p-4">
            <div className="bg-slate-900/50 rounded-xl border border-slate-800 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-amber-400" />
                <span className="text-sm font-semibold text-slate-200">
                  {t.top20}
                </span>
                {selected && (
                  <span className="text-xs text-slate-500 ml-auto">
                    HF Natal: {selected.natal_hf.toFixed(2)}
                  </span>
                )}
              </div>
              <RankingTable data={ranking} natalHf={selected?.natal_hf} lang={lang} />
            </div>
          </div>
        )}

        {!loading && activeTab === "narrative" && (
          <div className="p-4">
            <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-5">
              <NarrativePanel data={narrative} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  color = "text-slate-200",
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-slate-500">{label}:</span>
      <span className={color}>{value}</span>
    </div>
  );
}
