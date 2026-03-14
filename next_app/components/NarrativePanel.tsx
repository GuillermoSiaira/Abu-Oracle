"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { BookOpen, Lightbulb } from "lucide-react";

type NarrativeData = {
  headline: string;
  narrative: string;
  actions: string[];
  astro_metadata?: {
    source?: string;
    natal_hf?: number;
    max_hf?: number;
    gain_pct?: number;
    top_city?: string;
  };
};

export default function NarrativePanel({ data }: { data: NarrativeData | null }) {
  if (!data) {
    return (
      <div className="text-sm text-slate-500 italic p-4">
        Seleccioná un sujeto para ver la interpretación.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Headline */}
      <div className="flex items-start gap-2">
        <BookOpen className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
        <h3 className="text-lg font-semibold text-amber-300 leading-snug">
          {data.headline}
        </h3>
      </div>

      {/* Narrative */}
      <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {data.narrative}
        </ReactMarkdown>
      </div>

      {/* Actions */}
      {data.actions.length > 0 && (
        <div className="border-t border-slate-700 pt-3">
          <div className="flex items-center gap-1.5 mb-2">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
              Acciones
            </span>
          </div>
          <ul className="space-y-1.5">
            {data.actions.map((action, i) => (
              <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">▸</span>
                {action}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metadata badge */}
      {data.astro_metadata && (
        <div className="flex flex-wrap gap-2 pt-2 text-[10px] text-slate-500">
          {data.astro_metadata.source && (
            <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
              source: {data.astro_metadata.source}
            </span>
          )}
          {data.astro_metadata.gain_pct != null && (
            <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
              gain: +{data.astro_metadata.gain_pct.toFixed(1)}%
            </span>
          )}
        </div>
      )}
    </div>
  );
}
