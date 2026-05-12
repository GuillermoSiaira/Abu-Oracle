// next_app/app/chart/page.tsx
"use client";

import { useAppStore } from "@/lib/store";
import { ChartTabs } from "@/components/chart-tabs";
import { Calendar, MapPin, Sun, Moon } from "lucide-react";
import AuthGuard from "@/components/AuthGuard";
import Link from "next/link";
import dynamic from 'next/dynamic'
import { useMemo } from 'react'
import { buildSonicInput } from '@/components/sonic/sonicMapping'

const SonicField = dynamic(
  () => import('@/components/sonic/SonicField').then(m => ({ default: m.SonicField })),
  { ssr: false }
)

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
  const timeline = useAppStore((s) => s.timeline);
  const chartTab = useAppStore((s) => s.chartTab);
  const lang = useAppStore((s) => s.lang);

  const ready = !!abuData;

  if (!ready) {
    const emptyTitle: Record<string, string> = {
      es: 'Ingresá tus datos natales para comenzar',
      en: 'Enter your birth data to get started',
      pt: 'Insira seus dados natais para começar',
      fr: 'Entrez vos données natales pour commencer',
    };
    const emptyDemo: Record<string, string> = {
      es: 'O explorá una carta de demostración',
      en: 'Or explore a demo chart',
      pt: 'Ou explore um mapa de demonstração',
      fr: 'Ou explorez un thème de démonstration',
    };
    const resolvedLang = (lang as string) in emptyTitle ? (lang as string) : 'es';

    return (
      <AuthGuard>
        <div className="flex items-center justify-center h-full">
          <div className="text-center space-y-5 px-4">
            <div className="text-3xl text-amber-500/40">⟡</div>
            <p className="text-slate-400 text-sm max-w-xs">
              {emptyTitle[resolvedLang]}
            </p>
            <div className="flex flex-col gap-2 items-center">
              <Link
                href="/"
                className="text-sm font-mono text-amber-400 hover:text-amber-200 border border-amber-500/40 hover:border-amber-400/70 hover:bg-amber-500/5 rounded-sm px-5 py-2.5 transition-all"
              >
                → {resolvedLang === 'es' ? 'Ingresar mis datos' :
                   resolvedLang === 'en' ? 'Enter my data' :
                   resolvedLang === 'pt' ? 'Inserir meus dados' :
                   'Entrer mes données'}
              </Link>
              <Link
                href="/demo"
                className="text-xs font-mono text-slate-500 hover:text-slate-300 border border-slate-700/40 hover:border-slate-600/60 rounded-sm px-5 py-2 transition-all"
              >
                → {emptyDemo[resolvedLang]}
              </Link>
            </div>
          </div>
        </div>
      </AuthGuard>
    );
  }

  // ✅ FIX REAL
  const isDiurnal = abuData.derived?.sect === "diurnal";
  const SectIcon = isDiurnal ? Sun : Moon;

  // Sonic Field input — memoized from abuData
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const sonicInput = useMemo(() => buildSonicInput(abuData, timeline), [abuData, timeline])
  const subjectName = (birthData as any)?.userName || abuData.person?.name || 'Anónimo'

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
          {sonicInput && (
            <SonicField input={sonicInput} subjectName={subjectName} />
          )}
        </div>
      </header>

      <div
        className={`flex-1 px-4 py-6 space-y-6 ${
          chartTab === 'chart' ? 'overflow-hidden' : 'overflow-y-auto'
        }`}
      >
        <div className="w-full min-h-[520px] border border-slate-800/60 rounded-lg bg-slate-900/20 flex items-center justify-center">
          <ChartTabs />
        </div>
      </div>
      </div>
    </AuthGuard>
  );
}
