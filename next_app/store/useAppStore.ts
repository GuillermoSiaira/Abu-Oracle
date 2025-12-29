import { create } from 'zustand'
import { runAbuAnalyze } from '@/services/abu'
import type { AbuAnalyzeRequest, AbuAnalyzeResponse } from '@/lib/types'

/* ------------------------------------------------------------
   Tipos principales del estado global
------------------------------------------------------------- */

export interface BirthFormData {
  datetime: string    // ISO string
  lat: number
  lon: number
  timezone?: string
  name?: string
  gender?: 'male' | 'female' | 'other' | null
}

interface AppState {
  // Datos iniciales del usuario
  birthData: BirthFormData | null

  // Resultado completo del análisis Abu Engine
  analysis: AbuAnalyzeResponse | null

  // Estados de carga
  loadingAnalysis: boolean

  // Errores
  error: string | null

  /* -----------------------------
     Acciones del estado
  ------------------------------*/
  runAnalysis: (birth: BirthFormData) => Promise<void>
  reset: () => void
}

/* ------------------------------------------------------------
   IMPLEMENTACIÓN DEL STORE (Zustand)
------------------------------------------------------------- */

export const useAppStore = create<AppState>((set, get) => ({
  birthData: null,
  analysis: null,

  loadingAnalysis: false,

  error: null,

  /* --------------------------------------------------------
     ACCIÓN: Ejecutar análisis completo en Abu (/analyze)
  --------------------------------------------------------- */

  runAnalysis: async (birth) => {
    try {
      set({ loadingAnalysis: true, error: null })

      // Construimos el payload completo para Abu Engine
      const payload: AbuAnalyzeRequest = {
        person: {
          name: birth.name ?? null,
          question: "",
        },
        birth: {
          date: birth.datetime, // ISO string OK
          lat: birth.lat,
          lon: birth.lon,
        },
        current: {
          lat: birth.lat,
          lon: birth.lon,
          date: new Date().toISOString(),
        },
      }

      console.log('[Store] Calling Abu /analyze with:', payload)

      const analysis = await runAbuAnalyze(payload)

      set({
        birthData: birth,
        analysis,
      })
    } catch (err: any) {
      console.error('[Store] Abu /analyze error', err)
      set({ error: err?.message || 'Error al obtener análisis de Abu Engine' })
    } finally {
      set({ loadingAnalysis: false })
    }
  },

  /* --------------------------------------------------------
     ACCIÓN: reset — volver a estado inicial
  --------------------------------------------------------- */

  reset: () => {
    set({
      birthData: null,
      analysis: null,
      error: null,
      loadingAnalysis: false,
    })
  },
}))
