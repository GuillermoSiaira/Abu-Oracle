/**
 * sonicMapping.ts — Abu Oracle Sonic Field
 * Tablas de mapeo astrológico → síntesis, según SONIC_FIELD_SPEC.md v0.1
 *
 * Fuente doctrinal: Hans Cousto, The Cosmic Octave (1978)
 * Principio: frecuencias orbitales trasladadas al rango audible via ley de octavas.
 */

// ---------------------------------------------------------------------------
// 1. Frecuencias base por planeta (tabla Cousto — octava audible)
// ---------------------------------------------------------------------------

export const PLANET_BASE_FREQ: Record<string, number> = {
  Sun:     126.22,
  Moon:    210.42,
  Mercury: 141.27,
  Venus:   221.23,
  Mars:    144.72,
  Jupiter: 183.58,
  Saturn:  147.85,
  Uranus:  207.36,
  Neptune: 211.44,
  Pluto:   140.25,
}

// Alias en español → inglés para normalizar keys que vengan del AbuContext
export const PLANET_NAME_MAP: Record<string, string> = {
  sol:       'Sun',
  luna:      'Moon',
  mercurio:  'Mercury',
  venus:     'Venus',
  marte:     'Mars',
  jupiter:   'Jupiter',
  'júpiter': 'Jupiter',
  saturno:   'Saturn',
  urano:     'Uranus',
  neptuno:   'Neptune',
  pluton:    'Pluto',
  'plutón':  'Pluto',
  // también acepta inglés directo (sin transformar)
  sun:       'Sun',
  moon:      'Moon',
  mercury:   'Mercury',
  mars:      'Mars',
  saturn:    'Saturn',
  uranus:    'Uranus',
  neptune:   'Neptune',
  pluto:     'Pluto',
}

/** Normaliza un nombre de planeta a la key canónica inglesa. */
export function normalizePlanetName(raw: string): string {
  const key = raw.toLowerCase().trim()
  return PLANET_NAME_MAP[key] ?? raw
}

/**
 * Frecuencia natal del planeta:
 * modula la base en ±1 semitono (±5.9%) según longitud eclíptica.
 *   freq_natal = freq_base * (1 + (lon / 360) * 0.059 * 2 - 0.059)
 * Rango: freq_base * 0.941 (lon=0°) → freq_base * 1.000 (lon=180°) → freq_base * 1.059 (lon=360°)
 */
export function natalFrequency(planetName: string, lonNatal: number): number {
  const canon = normalizePlanetName(planetName)
  const base = PLANET_BASE_FREQ[canon] ?? 220
  const mod = 1 + (lonNatal / 360) * 0.059 * 2 - 0.059
  return base * mod
}

// ---------------------------------------------------------------------------
// 2. Tipo de oscilador según dignidad esencial (timbre)
// ---------------------------------------------------------------------------

export type OscType = 'sine' | 'triangle' | 'sawtooth'
export type SynthType = 'Synth' | 'AMSynth' | 'FMSynth'

export interface OscConfig {
  synthType: SynthType
  oscType?: OscType   // solo para 'Synth'
}

/**
 * Mapeo dignidad → configuración de oscilador.
 * Las keys coinciden con los valores que devuelve Abu Engine en dignity_traditional.
 */
export const DIGNITY_OSC_MAP: Record<string, OscConfig> = {
  domicile:    { synthType: 'Synth', oscType: 'sine' },
  exaltation:  { synthType: 'Synth', oscType: 'triangle' },
  peregrine:   { synthType: 'Synth', oscType: 'sawtooth' },
  detriment:   { synthType: 'AMSynth' },
  fall:        { synthType: 'FMSynth' },
  // aliases que puede devolver el backend
  'in domicile':   { synthType: 'Synth', oscType: 'sine' },
  'in exaltation': { synthType: 'Synth', oscType: 'triangle' },
  'in detriment':  { synthType: 'AMSynth' },
  'in fall':       { synthType: 'FMSynth' },
}

/** Retorna config de oscilador para una dignidad dada; fallback: sawtooth (peregrine). */
export function getOscConfig(dignity: string): OscConfig {
  const key = dignity.toLowerCase().trim()
  return DIGNITY_OSC_MAP[key] ?? { synthType: 'Synth', oscType: 'sawtooth' }
}

// ---------------------------------------------------------------------------
// 3. Amplitud por angularidad
// ---------------------------------------------------------------------------

/**
 * Estima el score de angularidad de un planeta (0–1) basado en su distancia
 * al ASC, MC, DESC o IC más cercano.
 *
 *   minDist = distancia angular mínima a los 4 ángulos
 *   score   = max(0, 1 - minDist / 45)
 *
 * Fuente: SONIC_FIELD_SPEC.md §2.2
 */
export function estimateAngularity(
  planetLon: number,
  ascLon: number,
  mcLon: number,
): number {
  const desc = (ascLon + 180) % 360
  const ic   = (mcLon  + 180) % 360
  const angles = [ascLon, mcLon, desc, ic]

  const minDist = Math.min(
    ...angles.map(a => Math.abs(((planetLon - a + 180) % 360) - 180))
  )

  return Math.max(0, 1 - minDist / 45)
}

/**
 * Convierte angularity_score (0–1) a dB de ganancia.
 *   volumen_db = -30 + (score * 24)
 *   Rango: -30 dB (cadente) → -6 dB (angular)
 */
export function angularityToDb(score: number): number {
  return -30 + score * 24
}

// ---------------------------------------------------------------------------
// 4. Aspectos como relaciones armónicas
// ---------------------------------------------------------------------------

export type AspectType = 'conjunction' | 'sextile' | 'square' | 'trine' | 'opposition'

/**
 * Relación de frecuencias que representa cada aspecto.
 * Cuando dos planetas forman aspecto, sus frecuencias se ajustan mutuamente
 * para aproximarse a esta razón, ponderada por el orb.
 */
export const ASPECT_HARMONIC: Record<AspectType, number> = {
  conjunction: 1.0,          // unísono 1:1
  trine:       1.5,          // quinta justa 3:2
  sextile:     1.25,         // tercera mayor 5:4
  square:      1.0594631,    // semitono (segunda menor ≈ 2^(1/12))
  opposition:  1.4142136,    // tritono (√2 ≈ triton)
}

/**
 * Dado un orb (0–8°), retorna el factor de ajuste de frecuencia relativo
 * al intervalo armónico del aspecto. A orb=0: ajuste máximo. A orb=8: ajuste mínimo.
 * El ajuste se interpola linealmente.
 *
 * @param baseFreq     frecuencia natal del planeta receptor
 * @param aspectType   tipo de aspecto
 * @param orb          orb en grados (0–8)
 * @returns            frecuencia ajustada
 */
export function applyAspectTuning(
  baseFreq: number,
  targetFreq: number,
  aspectType: AspectType,
  orb: number,
): number {
  const maxOrb = 8
  const clampedOrb = Math.min(Math.max(orb, 0), maxOrb)
  const weight = 1 - clampedOrb / maxOrb   // 1.0 at orb=0, 0.0 at orb=8

  const ratio = ASPECT_HARMONIC[aspectType] ?? 1
  // Frecuencia ideal = targetFreq * ratio (el planeta A suena a ratio * freq_B)
  const idealFreq = targetFreq * ratio

  // Interpolación: la frecuencia se "atrae" hacia el ideal ponderada por el weight
  return baseFreq + (idealFreq - baseFreq) * weight * 0.3 // 0.3 = profundidad máxima de detune
}

// ---------------------------------------------------------------------------
// 5. Fase lunar natal como envolvente ADSR global
// ---------------------------------------------------------------------------

export interface ADSREnvelope {
  attack: number    // segundos
  decay: number     // segundos
  sustain: number   // 0–1
  release: number   // segundos
  label: string
}

/**
 * Determina la envolvente ADSR global según la separación Sol-Luna natal.
 * @param moonPhaseDeg  separación Sol→Luna en grados (0–360)
 */
export function lunarPhaseEnvelope(moonPhaseDeg: number): ADSREnvelope {
  const deg = ((moonPhaseDeg % 360) + 360) % 360

  if (deg < 45 || deg >= 315) {
    // Luna Nueva / Balsámica — introspectivo
    return { attack: 3.0, decay: 1.5, sustain: 0.7, release: 4.0, label: 'Nueva/Balsámica' }
  } else if (deg < 135) {
    // Creciente — emergente
    return { attack: 1.5, decay: 0.8, sustain: 0.75, release: 2.0, label: 'Creciente' }
  } else if (deg < 225) {
    // Luna Llena — pleno, abierto
    return { attack: 0.5, decay: 0.5, sustain: 0.9, release: 1.5, label: 'Llena' }
  } else {
    // Menguante — reflexivo
    return { attack: 1.5, decay: 1.0, sustain: 0.65, release: 2.5, label: 'Menguante' }
  }
}

// ---------------------------------------------------------------------------
// 6. Parámetros Tone.js por tipo de sintetizador
// ---------------------------------------------------------------------------

/**
 * Opciones de construcción para cada tipo de synth.
 * Estas son las propiedades que se pasan al constructor de Tone.js.
 * Se inyectan junto con la envolvente ADSR calculada por lunarPhaseEnvelope().
 */
export const SYNTH_DEFAULTS = {
  Synth: {
    volume: -12,
    oscillator: { type: 'sine' as OscType },
    envelope: { attack: 1.5, decay: 0.8, sustain: 0.75, release: 2.0 },
  },
  AMSynth: {
    volume: -12,
    harmonicity: 2.5,
    detune: 0,
    oscillator: { type: 'sawtooth' as const },
    envelope: { attack: 1.5, decay: 0.8, sustain: 0.75, release: 2.0 },
    modulation: { type: 'square' as const },
    modulationEnvelope: { attack: 0.5, decay: 0, sustain: 1, release: 0.5 },
  },
  FMSynth: {
    volume: -12,
    harmonicity: 3,
    modulationIndex: 10,
    detune: 0,
    oscillator: { type: 'sine' as const },
    envelope: { attack: 1.5, decay: 0.8, sustain: 0.75, release: 2.0 },
    modulation: { type: 'triangle' as const },
    modulationEnvelope: { attack: 0.5, decay: 0, sustain: 1, release: 0.5 },
  },
}

// ---------------------------------------------------------------------------
// 8. Factory — construye SonicFieldInput desde abuData (forma canónica del store)
// ---------------------------------------------------------------------------

export interface SonicFieldInput {
  planets: Array<{
    name: string
    lon: number
    dignity_traditional: string
    angularity_score?: number
    house: number
  }>
  aspects: Array<{
    planet_a: string
    planet_b: string
    type: AspectType
    orb: number
  }>
  moon_phase_deg: number
  asc_lon: number
  mc_lon: number
  /** Tránsitos activos — usados por Capa 2 para añadir voces dinámicas */
  active_transits?: Array<{
    transit_planet: string
    natal_planet:   string
    type:           string
    orb:            number
    transit_lon?:   number   // longitud eclíptica actual del planeta transitante
  }>
}

const NATAL_ASPECTS_CONFIG = [
  { type: 'conjunction' as AspectType, angle: 0,   orb: 8 },
  { type: 'sextile'     as AspectType, angle: 60,  orb: 6 },
  { type: 'square'      as AspectType, angle: 90,  orb: 8 },
  { type: 'trine'       as AspectType, angle: 120, orb: 8 },
  { type: 'opposition'  as AspectType, angle: 180, orb: 8 },
]

/**
 * Deriva los aspectos natales client-side desde el array de planetas.
 * Mismo algoritmo que natal-chart-tab.tsx::natalAspectLines.
 */
function deriveAspects(planets: any[]): SonicFieldInput['aspects'] {
  const results: SonicFieldInput['aspects'] = []
  for (let i = 0; i < planets.length; i++) {
    for (let j = i + 1; j < planets.length; j++) {
      const lonA = planets[i].longitude
      const lonB = planets[j].longitude
      const diff = Math.abs(((Math.abs(lonA - lonB) % 360) + 360) % 360)
      const norm = diff > 180 ? 360 - diff : diff
      let bestOrb = Infinity
      let bestType: AspectType | null = null
      for (const asp of NATAL_ASPECTS_CONFIG) {
        const orb = Math.abs(norm - asp.angle)
        if (orb <= asp.orb && orb < bestOrb) {
          bestOrb = orb
          bestType = asp.type
        }
      }
      if (bestType && bestOrb <= 8) {
        results.push({ planet_a: planets[i].name, planet_b: planets[j].name, type: bestType, orb: bestOrb })
      }
    }
  }
  return results
}

/**
 * Construye un SonicFieldInput completo desde el objeto abuData del store.
 * Acepta opcionalmente el timeline (biography) para poblar active_transits (Capa 2).
 * Retorna null si los datos mínimos no están disponibles.
 */
export function buildSonicInput(abuData: any, timeline?: any): SonicFieldInput | null {
  const planets: any[] = abuData?.chart?.planets
  const asc: number    = abuData?.chart?.houses?.asc
  const mc: number     = abuData?.chart?.houses?.mc
  if (!planets?.length || asc == null || mc == null) return null

  const sun  = planets.find((p: any) => p.name === 'Sun')
  const moon = planets.find((p: any) => p.name === 'Moon')
  const moonPhaseDeg = ((moon?.longitude ?? 0) - (sun?.longitude ?? 0) + 360) % 360

  // Tránsitos activos desde el timeline (biography) — Capa 2
  const activeTransits = timeline?.transits_window
    ?.filter((t: any) => t.is_active)
    .map((t: any) => ({
      transit_planet: t.transit_planet,
      natal_planet:   t.natal_planet,
      type:           t.aspect,
      orb:            t.orb ?? 0,
      transit_lon:    t.transit_lon,
    }))

  return {
    planets: planets.map((p: any) => {
      const d = p.dignity
      let dignityStr = 'peregrine'
      if (d) {
        if (d.domicile   || d.kind === 'domicile')   dignityStr = 'domicile'
        else if (d.exaltation || d.kind === 'exaltation') dignityStr = 'exaltation'
        else if (d.detriment  || d.kind === 'detriment')  dignityStr = 'detriment'
        else if (d.fall       || d.kind === 'fall')        dignityStr = 'fall'
      }
      return { name: p.name, lon: p.longitude, dignity_traditional: dignityStr, house: p.house ?? 1 }
    }),
    aspects:          deriveAspects(planets),
    moon_phase_deg:   moonPhaseDeg,
    asc_lon:          asc,
    mc_lon:           mc,
    active_transits:  activeTransits?.length ? activeTransits : undefined,
  }
}
