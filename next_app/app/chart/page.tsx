// next_app/app/chart/page.tsx
"use client";

import { useAppStore } from "@/lib/store";
import { ChartTabs } from "@/components/chart-tabs";
import { Calendar, MapPin, Sun, Moon } from "lucide-react";
import AuthGuard from "@/components/AuthGuard";

function formatLocalDate(utcStr: string, utcOffset?: number): string {
  if (!utcStr) return "—";
  const utcMs = new Date(utcStr).getTime();
  if (isNaN(utcMs)) return utcStr;
  const offsetMs = (utcOffset ?? 0) * 3600000;
  const local = new Date(utcMs + offsetMs);
  const yyyy = local.getUTCFullYear();
  const mm = String(local.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(local.getUTCDate()).padStart(2, "0");
  const hh = String(local.getUTCHours()).padStart(2, "0");
  const min = String(local.getUTCMinutes()).padStart(2, "0");
  const sign = utcOffset == null ? "" : utcOffset >= 0 ? `+${utcOffset}` : `${utcOffset}`;
  const suffix = utcOffset != null ? ` (UTC${sign})` : "";
  return `${yyyy}-${mm}-${dd} · ${hh}:${min}${suffix}`;
}

export default function ChartPage() {
  const birthData = useAppStore((s) => s.birthData);
  const abuData = useAppStore((s) => s.abuData);

  const ready = !!abuData;

  if (!ready) {
    return (
      <AuthGuard>
        <div className="flex items-center justify-center h-full text-slate-500">
          <div className="text-center space-y-2">
            <p className="text-lg">No chart data loaded</p>
            <p className="text-sm opacity-70">
              Initialize Abu Engine from the start page.
            </p>
          </div>
        </div>
      </AuthGuard>
    );
  }

  // ✅ FIX REAL
  const isDiurnal = abuData.derived?.sect === "diurnal";
  const SectIcon = isDiurnal ? Sun : Moon;

  return (
    <AuthGuard>
      <div className="flex flex-col h-full w-full bg-[#050505] overflow-hidden">

      <header className="shrink-0 px-6 py-4 border-b border-slate-800 bg-[#080808] flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100 tracking-tight mb-1">
            {(birthData as any)?.userName || abuData.person?.name || "Anonymous Subject"}
          </h1>

          <div className="flex items-center gap-4 text-xs text-slate-400 font-mono">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {formatLocalDate(
                birthData?.birthDate || (abuData as any).birth?.date || "",
                (birthData as any)?.utcOffset
              )}
            </span>

            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {(birthData as any)?.city || "—"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded text-xs text-slate-300">
            <SectIcon
              className={`w-3 h-3 ${
                isDiurnal ? "text-yellow-500" : "text-blue-300"
              }`}
            />
            <span className="uppercase tracking-wider font-semibold">
              {abuData.derived?.sect || "unknown"} sect
            </span>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        <div className="w-full min-h-[520px] border border-slate-800/60 rounded-lg bg-slate-900/20 flex items-center justify-center">
          <ChartTabs />
        </div>
      </div>
      </div>
    </AuthGuard>
  );
}
