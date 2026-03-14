"use client";

import { Trophy, MapPin } from "lucide-react";
import { UI, type Lang } from "@/lib/i18n";

type RankingEntry = {
  subject_id?: string;
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
};

export default function RankingTable({
  data,
  natalHf,
  lang = "es",
}: {
  data: RankingEntry[] | null;
  natalHf?: number;
  lang?: Lang;
}) {
  const t = UI[lang];

  if (!data || data.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic p-4">
        {t.selectSubject}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[11px] text-slate-400 uppercase tracking-wider border-b border-slate-700">
            <th className="py-2 px-3 w-8">#</th>
            <th className="py-2 px-3">{t.city}</th>
            <th className="py-2 px-3">{t.country}</th>
            <th className="py-2 px-3 text-right">{t.lat}</th>
            <th className="py-2 px-3 text-right">{t.lon}</th>
            <th className="py-2 px-3 text-right">{t.hfTotal}</th>
            <th className="py-2 px-3 text-right">{t.deltaNatal}</th>
            <th className="py-2 px-3 text-right">{t.aspects}</th>
            <th className="py-2 px-3 text-right">{t.angles}</th>
            <th className="py-2 px-3 text-right">{t.houses}</th>
            <th className="py-2 px-3 text-right">{t.distKm}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => {
            const delta = natalHf ? row.hf_total_v3 - natalHf : null;
            const isTop3 = i < 3;
            return (
              <tr
                key={i}
                className={`border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${
                  isTop3 ? "bg-amber-900/10" : ""
                }`}
              >
                <td className="py-2 px-3 text-slate-500 font-mono">
                  {i < 3 ? (
                    <Trophy
                      className={`w-3.5 h-3.5 inline ${
                        i === 0
                          ? "text-amber-400"
                          : i === 1
                          ? "text-slate-300"
                          : "text-amber-700"
                      }`}
                    />
                  ) : (
                    i + 1
                  )}
                </td>
                <td className="py-2 px-3 font-medium text-slate-200 flex items-center gap-1.5">
                  <MapPin className="w-3 h-3 text-slate-500" />
                  {row.city}
                </td>
                <td className="py-2 px-3 text-slate-400">{row.country}</td>
                <td className="py-2 px-3 text-right font-mono text-slate-500 text-xs">
                  {row.city_lat.toFixed(1)}
                </td>
                <td className="py-2 px-3 text-right font-mono text-slate-500 text-xs">
                  {row.city_lon.toFixed(1)}
                </td>
                <td className="py-2 px-3 text-right font-mono text-slate-200">
                  {row.hf_total_v3.toFixed(2)}
                </td>
                <td className="py-2 px-3 text-right font-mono">
                  {delta != null ? (
                    <span
                      className={
                        delta > 0 ? "text-green-400" : "text-red-400"
                      }
                    >
                      {delta > 0 ? "+" : ""}
                      {delta.toFixed(2)}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="py-2 px-3 text-right font-mono text-slate-400">
                  {row.hf_aspects.toFixed(2)}
                </td>
                <td className="py-2 px-3 text-right font-mono text-slate-400">
                  {row.hf_angles.toFixed(2)}
                </td>
                <td className="py-2 px-3 text-right font-mono text-slate-400">
                  {row.hf_houses.toFixed(1)}
                </td>
                <td className="py-2 px-3 text-right font-mono text-slate-400">
                  {row.distance_km.toFixed(0)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
