// next_app/services/lilly.ts
// Servicio oficial para conectar el FE con Lilly Engine

export const LILLY_BASE_URL =
  process.env.NEXT_PUBLIC_LILLY_URL || "http://localhost:8001"

export type SupportedLanguage = "es" | "en" | "pt"

/**
 * NUEVA FORMA DEL REQUEST
 * Coincide EXACTO con MaestroRequest en el backend de Lilly.
 */
export interface LillyInterpretRequest {
  birthDate: string
  lat: number
  lon: number
  language: SupportedLanguage
  include_transits?: boolean
  include_solar_return?: boolean
}

/**
 * NUEVA FORMA DEL RESPONSE
 * Coincide con InterpretResponseMaestro / FullInterpretResponse
 */
export interface LillyInterpretation {
  maestro?: Record<string, any>
  narrative?: string
  ai?: {
    headline?: string
    narrative?: string
    actions?: string[]
  }
}

export class LillyApiError extends Error {
  status?: number
  constructor(message: string, status?: number) {
    super(message)
    this.name = "LillyApiError"
    this.status = status
  }
}

export async function runLillyInterpret(
  payload: LillyInterpretRequest
): Promise<LillyInterpretation> {

  const url = `${LILLY_BASE_URL}/api/ai/interpret`

  console.log("[Lilly] POST /api/ai/interpret")
  console.log("[Lilly] Payload:", payload)
  console.log("[Lilly] Payload JSON:", JSON.stringify(payload, null, 2))

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const text = await response.text().catch(() => "")
      throw new LillyApiError(
        `Lilly interpret failed (${response.status}): ${text || response.statusText}`,
        response.status
      )
    }

    const data = (await response.json()) as LillyInterpretation
    console.log("[Lilly] Response OK")

    return data
  } catch (err: any) {
    console.error("[Lilly] Network/Parse error", err)
    throw new LillyApiError(
      `Network or parsing error in Lilly interpret: ${String(
        err?.message || err
      )}`,
      0
    )
  }
}
