// next_app/services/abu.ts
// Servicio oficial para conectar el Frontend con Abu Engine

import type { AbuAnalyzeRequest, AbuAnalyzeResponse } from "@/lib/types";
import { getAbuAuthHeaders } from "@/lib/abu-auth";

export const ABU_BASE_URL =
  process.env.NEXT_PUBLIC_ABU_URL ||
  "https://abu-engine-503488473965.us-central1.run.app";

/* ------------------------------------------------------------
   Error especializado
------------------------------------------------------------- */

export class AbuApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "AbuApiError";
    this.status = status;
  }
}

/* ------------------------------------------------------------
   1) Carta Natal — POST /analyze
------------------------------------------------------------- */

export async function runAbuAnalyze(
  payload: AbuAnalyzeRequest
): Promise<AbuAnalyzeResponse> {
  const url = `${ABU_BASE_URL}/analyze`;

  console.log("[Abu] POST /analyze");
  console.log("[Abu] Payload:", payload);

  try {
    const headers = await getAbuAuthHeaders({ "Content-Type": "application/json" });
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new AbuApiError(
        `Abu /analyze failed (${response.status}): ${text || response.statusText}`,
        response.status
      );
    }

    const data = (await response.json()) as AbuAnalyzeResponse;
    console.log("[Abu] Response OK");
    return data;
  } catch (err: any) {
    console.error("[Abu] Network/Parse error", err);
    throw new AbuApiError(
      `Network or parsing error in Abu /analyze: ${String(
        err?.message || err
      )}`,
      0
    );
  }
}

/* ------------------------------------------------------------
   2) Retorno Solar — GET /api/astro/solar-return
------------------------------------------------------------- */

export async function runAbuSolarReturn(params: {
  birthDate: string;
  lat: number;
  lon: number;
  year?: number;
}) {
  const url = new URL(`${ABU_BASE_URL}/api/astro/solar-return`);

  url.searchParams.set("birthDate", params.birthDate);
  url.searchParams.set("lat", String(params.lat));
  url.searchParams.set("lon", String(params.lon));
  if (params.year) url.searchParams.set("year", String(params.year));

  console.log("[Abu] GET /api/astro/solar-return =>", url.toString());

  try {
    const headers = await getAbuAuthHeaders();
    const res = await fetch(url.toString(), { headers });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new AbuApiError(
        `Abu /solar-return failed (${res.status}): ${text}`,
        res.status
      );
    }

    return await res.json();
  } catch (err: any) {
    console.error("[Abu] SR error", err);
    throw new AbuApiError(
      `Network error in Solar Return: ${String(err?.message || err)}`,
      0
    );
  }
}

/* ------------------------------------------------------------
   3) Retorno Solar — Análisis AI /api/ai/solar-return (POST)
------------------------------------------------------------- */

export async function runAbuSolarReturnAI(payload: {
  natal_chart: any;
  solar_chart: any;
  language: "es" | "en" | "pt";
}) {
  const url = `${ABU_BASE_URL}/api/ai/solar-return`;

  console.log("[Abu] POST /api/ai/solar-return", payload);

  try {
    const headers = await getAbuAuthHeaders({ "Content-Type": "application/json" });
    const res = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new AbuApiError(
        `Abu /ai/solar-return failed (${res.status}): ${text}`,
        res.status
      );
    }

    return await res.json();
  } catch (err: any) {
    console.error("[Abu] SR AI error", err);
    throw new AbuApiError(
      `Network error in AI Solar Return: ${String(err?.message || err)}`,
      0
    );
  }
}

/* ------------------------------------------------------------
   4) Ranking / Optimización — POST /api/rs/optimize
------------------------------------------------------------- */

export async function runAbuOptimizeRS(payload: {
  birth: { date: string; lat: number; lon: number };
  target_year: number;
  intent?: string;
  preferences?: any;
  refine?: boolean;
  diversity?: boolean;
  language?: "es" | "en" | "pt";
}) {
  const url = `${ABU_BASE_URL}/api/rs/optimize`;

  console.log("[Abu] POST /api/rs/optimize", payload);

  try {
    const headers = await getAbuAuthHeaders({ "Content-Type": "application/json" });
    const res = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new AbuApiError(
        `Abu /rs/optimize failed (${res.status}): ${text}`,
        res.status
      );
    }

    return await res.json();
  } catch (err: any) {
    console.error("[Abu] RS optimize error", err);
    throw new AbuApiError(
      `Network error in RS Optimize: ${String(err?.message || err)}`,
      0
    );
  }
}
