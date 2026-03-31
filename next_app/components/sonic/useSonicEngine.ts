/**
 * useSonicEngine.ts — Abu Oracle Sonic Field
 * Hook principal que orquesta Tone.js para la Firma Sonora Natal (Capa 1).
 *
 * Diseño:
 * - Tone.js se importa dinámicamente dentro de useEffect (browser-only, evita SSR crash)
 * - Los synths se crean una sola vez en mount y viven en useRef (nunca se recrean en re-renders)
 * - Cada planeta es un Loop que dispara triggerAttackRelease cada LOOP_INTERVAL_S segundos
 * - start() requiere gesture del usuario (llama Tone.start() internamente)
 * - stop() hace fade-out de 2s sobre el Destination global
 */

'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import type * as ToneTypes from 'tone'
import {
  natalFrequency,
  getOscConfig,
  estimateAngularity,
  angularityToDb,
  applyAspectTuning,
  lunarPhaseEnvelope,
  normalizePlanetName,
  type SonicFieldInput,
} from './sonicMapping'

// SonicFieldInput is defined in sonicMapping.ts — re-export for consumers
export type { SonicFieldInput }

export interface SonicEngineReturn {
  isPlaying: boolean
  isReady: boolean
  start: () => Promise<void>
  stop: () => void
  setVolume: (db: number) => void
}

// ---------------------------------------------------------------------------
// Constantes internas
// ---------------------------------------------------------------------------

/** Duración base de cada nota natal (segundos). Variación aleatoria ±2s para textura viva. */
const NOTE_DURATION_S = 14

/** Intervalo del Loop natal (segundos). Más corto que NOTE_DURATION_S → notas solapadas. */
const LOOP_INTERVAL_S = 10

/** Duración de nota de tránsito (más corta — capa transitoria sobre el sustrato natal). */
const NOTE_DURATION_TRANSIT_S = 8

/** Intervalo del Loop de tránsito (más frecuente para dar sensación de movimiento). */
const LOOP_INTERVAL_TRANSIT_S = 6

/** Retardo en ms después del fade para detener el transport y resetear. */
const FADE_DURATION_MS = 2000
const STOP_BUFFER_MS   = 200

// ---------------------------------------------------------------------------
// Tipos internos
// ---------------------------------------------------------------------------

type AnyTone    = typeof ToneTypes
type AnySynth   = ToneTypes.Synth | ToneTypes.AMSynth | ToneTypes.FMSynth

interface PlanetVoice {
  name:  string
  synth: AnySynth
  loop:  ToneTypes.Loop
  freq:  number
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useSonicEngine(input: SonicFieldInput | null): SonicEngineReturn {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isReady,   setIsReady]   = useState(false)

  // Refs — sobreviven re-renders, nunca causan re-renders por sí solos
  const voicesRef      = useRef<PlanetVoice[]>([])
  const transportRef   = useRef<ReturnType<typeof ToneTypes.getTransport> | null>(null)
  const toneRef        = useRef<AnyTone | null>(null)
  const stopTimerRef   = useRef<ReturnType<typeof setTimeout> | null>(null)

  // --- initEngine — una sola vez en mount ------------------------------
  useEffect(() => {
    if (!input || input.planets.length === 0) return

    let cancelled = false

    async function initEngine() {
      // Importación dinámica — Web Audio API solo en browser
      const ToneModule = await import('tone')
      if (cancelled) return

      toneRef.current    = ToneModule
      transportRef.current = ToneModule.getTransport()

      // 1. Frecuencias natales iniciales (una por planeta)
      const freqMap: Record<string, number> = {}
      for (const p of input!.planets) {
        const canon = normalizePlanetName(p.name)
        freqMap[canon] = natalFrequency(p.name, p.lon)
      }

      // 2. Ajuste de frecuencias por aspectos natales (applyAspectTuning sobre planet_a)
      for (const asp of input!.aspects) {
        const nameA = normalizePlanetName(asp.planet_a)
        const nameB = normalizePlanetName(asp.planet_b)
        const fa = freqMap[nameA]
        const fb = freqMap[nameB]
        if (fa !== undefined && fb !== undefined) {
          freqMap[nameA] = applyAspectTuning(fa, fb, asp.type, asp.orb)
        }
      }

      // 3. Envolvente ADSR global desde fase lunar natal
      const env = lunarPhaseEnvelope(input!.moon_phase_deg)
      const envOpts = {
        attack:  env.attack,
        decay:   env.decay,
        sustain: env.sustain,
        release: env.release,
      }

      // 4. Crear synths y loops por planeta
      const voices: PlanetVoice[] = []

      for (let i = 0; i < input!.planets.length; i++) {
        const p      = input!.planets[i]
        const canon  = normalizePlanetName(p.name)
        const freq   = freqMap[canon] ?? natalFrequency(p.name, p.lon)

        // Angularidad → volumen en dB
        const angScore = p.angularity_score
          ?? estimateAngularity(p.lon, input!.asc_lon, input!.mc_lon)
        const volumeDb = angularityToDb(angScore)

        // Tipo de oscilador según dignidad
        const oscConfig = getOscConfig(p.dignity_traditional)

        // Construir el synth apropiado
        let synth: AnySynth

        if (oscConfig.synthType === 'AMSynth') {
          synth = new ToneModule.AMSynth({
            volume:   volumeDb,
            envelope: envOpts,
          })
        } else if (oscConfig.synthType === 'FMSynth') {
          synth = new ToneModule.FMSynth({
            volume:   volumeDb,
            envelope: envOpts,
          })
        } else {
          // 'Synth' con tipo de onda según dignidad
          synth = new ToneModule.Synth({
            oscillator: { type: oscConfig.oscType ?? 'sine' },
            volume:     volumeDb,
            envelope:   envOpts,
          })
        }

        // Conectar al Destination global
        synth.toDestination()

        // Capturar en closure para el callback del Loop
        const capturedFreq  = freq
        const capturedSynth = synth

        // Loop que dispara la nota cada LOOP_INTERVAL_S segundos
        const loop = new ToneModule.Loop((time: number) => {
          // Variación aleatoria leve en la duración para textura orgánica
          const noteDur = NOTE_DURATION_S + (Math.random() * 4 - 2)
          capturedSynth.triggerAttackRelease(capturedFreq, noteDur, time)
        }, LOOP_INTERVAL_S)

        // Stagger de arranque: cada planeta empieza 400ms después del anterior
        loop.start(i * 0.4)

        voices.push({ name: canon, synth, loop, freq })
      }

      // 5. Capa 2 — Transit voices (additive layer sobre la firma natal)
      //    Cada tránsito activo con transit_lon conocido agrega una voz efímera.
      //    - Frecuencia: posición eclíptica actual del planeta transitante
      //    - Volumen: −24 dB (orb=8°) a −12 dB (orb=0°) — siempre más suave que los natales
      //    - Timbre: trine/sextile=sine (consonante) | square/opposition=FMSynth (disonante) | conjunction/resto=AMSynth
      //    - Loop más rápido y notas más cortas → textura en movimiento sobre el sustrato natal
      const natalStartOffset = input!.planets.length * 0.4  // offset inicial para no pisar arranque natal

      if (input!.active_transits?.length) {
        let transitIdx = 0
        for (const tr of input!.active_transits) {
          if (tr.transit_lon == null) continue  // sin posición actual → omitir

          // Frecuencia desde la posición actual del planeta transitante
          const transitFreq = natalFrequency(tr.transit_planet, tr.transit_lon)

          // Volumen proporcional al orb — más ajustado = más audible
          const orbClamped = Math.min(Math.max(tr.orb, 0), 8)
          const transitVolumeDb = -24 + (1 - orbClamped / 8) * 12

          // Timbre según carácter del aspecto
          const aspKey = tr.type?.toLowerCase().trim() ?? ''
          let transitSynth: AnySynth

          if (aspKey === 'trine' || aspKey === 'sextile') {
            // Consonante — flujo suave
            transitSynth = new ToneModule.Synth({
              oscillator: { type: 'sine' },
              volume:     transitVolumeDb,
              envelope:   { attack: 2.0, decay: 0.5, sustain: 0.8, release: 3.0 },
            })
          } else if (aspKey === 'square' || aspKey === 'opposition') {
            // Disonante — tensión armónica compleja
            transitSynth = new ToneModule.FMSynth({
              volume:          transitVolumeDb,
              harmonicity:     3,
              modulationIndex: 8,
              envelope:        { attack: 2.0, decay: 0.5, sustain: 0.8, release: 3.0 },
            })
          } else {
            // Conjunción / desconocido — fusión AM
            transitSynth = new ToneModule.AMSynth({
              volume:       transitVolumeDb,
              harmonicity:  1.5,
              envelope:     { attack: 2.0, decay: 0.5, sustain: 0.8, release: 3.0 },
            })
          }

          transitSynth.toDestination()

          const capturedTransitFreq  = transitFreq
          const capturedTransitSynth = transitSynth

          const transitLoop = new ToneModule.Loop((time: number) => {
            const noteDur = NOTE_DURATION_TRANSIT_S + (Math.random() * 4 - 2)
            capturedTransitSynth.triggerAttackRelease(capturedTransitFreq, noteDur, time)
          }, LOOP_INTERVAL_TRANSIT_S)

          // Stagger: arrancan después de todos los natales, separados 300ms entre sí
          transitLoop.start(natalStartOffset + transitIdx * 0.3)

          voices.push({
            name:  normalizePlanetName(tr.transit_planet),
            synth: transitSynth,
            loop:  transitLoop,
            freq:  transitFreq,
          })

          transitIdx++
        }
      }

      if (!cancelled) {
        voicesRef.current = voices
        setIsReady(true)
      }
    }

    initEngine()

    // Cleanup al desmontar
    return () => {
      cancelled = true

      if (stopTimerRef.current) clearTimeout(stopTimerRef.current)

      for (const voice of voicesRef.current) {
        try { voice.loop.stop() }  catch (_) { /* ignore */ }
        try { voice.loop.dispose() } catch (_) { /* ignore */ }
        try { voice.synth.dispose() } catch (_) { /* ignore */ }
      }
      voicesRef.current = []

      try { transportRef.current?.stop() } catch (_) { /* ignore */ }

      setIsReady(false)
      setIsPlaying(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Intencional: solo en mount. Input no cambia sin un remount del componente padre.

  // --- start -----------------------------------------------------------
  const start = useCallback(async () => {
    const ToneModule = toneRef.current
    if (!ToneModule || !isReady || isPlaying) return

    // Tone.start() solo puede llamarse desde un evento de usuario (click)
    await ToneModule.start()

    // Resetear volumen por si venía de un fade-out previo
    ToneModule.getDestination().volume.value = 0

    // Arrancar el Transport → todos los Loops empiezan a disparar
    transportRef.current?.start()

    setIsPlaying(true)
  }, [isReady, isPlaying])

  // --- stop ------------------------------------------------------------
  const stop = useCallback(() => {
    const ToneModule = toneRef.current
    if (!ToneModule || !isPlaying) return

    // Fade-out suave de 2s sobre el Destination global
    ToneModule.getDestination().volume.rampTo(-60, FADE_DURATION_MS / 1000)

    if (stopTimerRef.current) clearTimeout(stopTimerRef.current)

    stopTimerRef.current = setTimeout(() => {
      try { transportRef.current?.stop() } catch (_) { /* ignore */ }

      // Detener loops sin disposerarlos (el synth sigue vivo para reproducir de nuevo)
      for (const voice of voicesRef.current) {
        try { voice.loop.stop(0) } catch (_) { /* ignore */ }
      }

      // Resetear volumen para el próximo start()
      try {
        if (toneRef.current) toneRef.current.getDestination().volume.value = 0
      } catch (_) { /* ignore */ }

      setIsPlaying(false)
    }, FADE_DURATION_MS + STOP_BUFFER_MS)
  }, [isPlaying])

  // --- setVolume -------------------------------------------------------
  const setVolume = useCallback((db: number) => {
    try {
      toneRef.current?.getDestination().volume.rampTo(db, 0.1)
    } catch (_) { /* ignore if not initialized */ }
  }, [])

  return { isPlaying, isReady, start, stop, setVolume }
}
