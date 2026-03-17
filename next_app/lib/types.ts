// ======================================================
//  NATAL / BASE TYPES
// ======================================================

export interface Planet {
  name: string
  sign: string
  degree: number
  longitude: number
  house: number
  dignity: 'domicile' | 'exaltation' | 'peregrine' | 'fall' | 'detriment'
  score?: number
}

export interface House {
  number: number
  sign: string
  degree: number
  longitude: number
}

export interface Aspect {
  planet1: string
  planet2: string
  type:
    | 'conjunction'
    | 'opposition'
    | 'trine'
    | 'square'
    | 'sextile'
    | 'semisextile'
    | 'quincunx'
    | 'semisquare'
    | 'sesquiquadrate'
  orb: number
  applying: boolean
}

export interface Chart {
  planets: Planet[]
  houses: House[]
  aspects: Aspect[]
  ascendantDegree: number
  mcDegree: number
}

export interface Lot {
  name: string
  degree: number
  sign: string
  house: number
}

export interface Profection {
  year: number
  sign: string
  lord: string
  house: number
}

export interface Fardar {
  planet: string
  startDate: string
  endDate: string
  years: number
}

export interface LunarMansion {
  name: string
  degree: number
  nature: string
}

export interface FixedStar {
  name: string
  longitude: number
  conjunctPlanet?: string
  orb?: number
}

export interface Extended {
  lots: Lot[]
  profections: Profection[]
  fardars: Fardar[]
  lunar_mansion: LunarMansion
  fixed_stars: FixedStar[]
  solar_return?: Record<string, any>
  solar_return_ranking?: Record<string, any>
  transits?: Record<string, any> // legacy / experimental
}

export interface AbuResponse {
  chart: Chart
  extended: Extended
}

// ======================================================
//  ABU /analyze REQUEST REAL
// ======================================================

export interface AbuAnalyzeRequest {
  person?: {
    name?: string | null
    question?: string
  }
  birth: {
    date: string
    lat: number
    lon: number
  }
  current: {
    lat: number
    lon: number
    date?: string
  }
}

// ======================================================
//  ABU /analyze RESPONSE REAL (ACTUALIZADO)
// ======================================================

// 🔹 Planeta en tránsito (misma semántica que natal, sin casa)
export interface TransitPlanet {
  name: string
  longitude: number
  sign: string
  degree_in_sign?: number
  formatted?: string
}

export interface AbuAnalyzeResponse {
  person: {
    name?: string | null
    question?: string
  }

  chart: {
    planets: any[]
    houses: {
      houses: { house: number; start: number; end: number }[]
      asc: number | null
      mc: number | null
    }
  }

  derived: {
    sect: 'diurnal' | 'nocturnal' | null

    firdaria: {
      current: {
        major: string | null
        sub?: string | null
        start: string | null
        end: string | null
      } | null
    }

    profection: {
      house: number | null
    }

    lunar_transit: {
      moon_position?: number | null
      aspects: { planet: string; type: string; orb: number }[]
    }

    solar_return?: any

    lots?: Array<{
      name: string
      longitude: number
      sign: string
      degree: number
      house?: number
      lord: string
    }>
  }

  life_cycles: any

  forecast: {
    timeseries: Array<{ date: string; score: number }>
    peaks: Array<{ date: string; score: number; is_peak: boolean }>
  }

  // ✅ NUEVO — tránsitos planetarios completos
  transits?: {
    planets: TransitPlanet[]
  }

  question?: string
}

// ======================================================
//  LILLY ENGINE — CONTRATO REAL (ACTUALIZADO)
// ======================================================

export interface LillyResponse {
  maestro?: Record<string, any>
  narrative?: string
  ai?: {
    headline?: string
    narrative?: string
    actions?: string[]
  }
}

// ======================================================
//  CHAT UI
// ======================================================

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// ======================================================
//  FRONTEND — BirthData (Zustand)
// ======================================================

export interface BirthData {
  birthDate: string
  utcOffset?: number
  lat: number
  lon: number
  city?: string | null
  userName?: string | null
  residenceCity?: string | null
  residenceLat?: number | null
  residenceLon?: number | null
  futureCity?: string | null
  futureLat?: number | null
  futureLon?: number | null
  futureDate?: string | null
}
