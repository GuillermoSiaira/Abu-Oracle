"use client";

import { useAppStore } from "@/lib/store";
import { runLillyInterpret } from "@/services/lilly";
import { useState } from "react";

// Saneador ultra básico para evitar tags peligrosos
function sanitizeMarkdown(md: string): string {
  return md
    .replace(/<script.*?>.*?<\/script>/gi, "")
    .replace(/on\w+=".*?"/g, "")
    .replace(/javascript:/gi, "");
}

export function InterpretationTab() {
  const birthData = useAppStore((s) => s.birthData);
  const lillyData = useAppStore((s) => s.lillyData);
  const setLillyData = useAppStore((s) => s.setLillyData);
  const isLoading = useAppStore((s) => s.isLoading);
  const setIsLoading = useAppStore((s) => s.setIsLoading);

  const [error, setError] = useState<string | null>(null);

  async function handleInterpret() {
    if (!birthData) return;

    try {
      setIsLoading(true);
      setError(null);

      const result = await runLillyInterpret({
        birthDate: birthData.birthDate,
        lat: birthData.lat,
        lon: birthData.lon,
        language: "es",
        include_transits: useAppStore.getState().includeTransits,
      });

      setLillyData(result);
    } catch (err: any) {
      setError("Hubo un error generando la interpretación.");
      console.error("Error interpretando:", err);
    } finally {
      setIsLoading(false);
    }
  }

  const safeMarkdown = lillyData?.narrative
    ? sanitizeMarkdown(lillyData.narrative)
        .replace(/\n\n/g, "<br/><br/>")
        .replace(/\n/g, "<br/>")
    : "";

  const aiHeadline = lillyData?.ai?.headline;
  const aiNarrative = lillyData?.ai?.narrative;
  const aiActions = lillyData?.ai?.actions || [];

  return (
    <div className="max-w-3xl mx-auto py-8 space-y-8">

      {/* BOTÓN PREMIUM */}
      <div className="flex justify-center">
        <button
          onClick={handleInterpret}
          disabled={isLoading}
          className={`px-6 py-3 rounded-xl font-medium shadow-lg transition-all
            ${
              isLoading
                ? "bg-primary/40 text-primary-foreground/60"
                : "bg-primary text-primary-foreground hover:shadow-xl hover:scale-[1.02]"
            }
          `}
        >
          {isLoading ? "Interpretando…" : "Generar interpretación"}
        </button>
      </div>

      {/* MENSAJE DE ERROR */}
      {error && (
        <div className="text-red-600 text-center text-sm">{error}</div>
      )}

      {/* CONTENIDO */}
      {lillyData && (
        <div
          className="
            p-8 rounded-2xl border bg-card/70 shadow-sm
            backdrop-blur-sm space-y-6
          "
        >
          {/* TITULAR PRINCIPAL (AI) */}
          {aiHeadline && (
            <h2
              className="
                text-3xl font-serif font-bold tracking-wide text-center mb-4
              "
            >
              {aiHeadline}
            </h2>
          )}

          {/* NARRATIVA HEURÍSTICA */}
          {safeMarkdown && (
            <div
              className="
                text-lg leading-relaxed tracking-wide
                font-serif opacity-90 whitespace-pre-line
              "
              dangerouslySetInnerHTML={{ __html: safeMarkdown }}
            />
          )}

          {/* NARRATIVA AI */}
          {aiNarrative && (
            <div className="pt-4 border-t mt-6 text-base opacity-90 leading-relaxed">
              {aiNarrative}
            </div>
          )}

          {/* BLOQUE DE ACCIONES (AI) */}
          {aiActions.length > 0 && (
            <div className="pt-4 border-t mt-6 space-y-2">
              <h3 className="text-lg font-semibold">Sugerencias</h3>
              <ul className="list-disc pl-6 text-sm opacity-80">
                {aiActions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!lillyData && !isLoading && (
        <div className="text-center opacity-60 text-sm">
          Obtén tu interpretación para ver el análisis.
        </div>
      )}
    </div>
  );
}
