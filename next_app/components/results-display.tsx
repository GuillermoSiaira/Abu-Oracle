"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/simple-card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/simple-tabs"
import { Badge } from "@/components/ui/simple-badge"
import { Button } from "@/components/ui/simple-button"
import { Moon, Star, Sun, Sparkles, Activity, Calendar, Loader2, MessageSquare } from 'lucide-react'
import { ZodiacWheel } from "@/components/zodiac-wheel"

interface ResultsDisplayProps {
  results: any
  birthData?: {
    name: string
    city: string
    country: string
    date: string
    time: string
  }
  wheelOrientation?: "aries" | "ascendant"
}

const PLANET_ARCHETYPES: Record<
  string,
  {
    symbol: string
    archetype: string
    function: string
    polarity: string
    element: string
    color: string
    icon: string
    tone: string
  }
> = {
  Sun: {
    symbol: "☉",
    archetype: "El Rey / El Corazón",
    function: "Fuente de identidad, conciencia, propósito y vitalidad",
    polarity: "Activo",
    element: "Fuego",
    color: "#ffd700",
    icon: "☀️",
    tone: "Ilumina, dirige, da sentido",
  },
  Moon: {
    symbol: "☽",
    archetype: "La Reina / El Alma",
    function: "Emociones, memoria, hábitos, receptividad",
    polarity: "Receptiva",
    element: "Agua",
    color: "#c0c0c0",
    icon: "🌙",
    tone: "Nutre, protege, refleja",
  },
  Mercury: {
    symbol: "☿",
    archetype: "El Mensajero",
    function: "Intelecto, comunicación, pensamiento, lenguaje",
    polarity: "Mutable",
    element: "Aire",
    color: "#7ec8e3",
    icon: "☿",
    tone: "Interpreta, analiza, transmite",
  },
  Venus: {
    symbol: "♀",
    archetype: "La Musa",
    function: "Amor, armonía, placer, estética y deseo de unión",
    polarity: "Receptiva",
    element: "Agua",
    color: "#ff99cc",
    icon: "♀",
    tone: "Suaviza, conecta, embellece",
  },
  Mars: {
    symbol: "♂",
    archetype: "El Guerrero",
    function: "Acción, deseo, energía vital, coraje",
    polarity: "Activo",
    element: "Fuego",
    color: "#ff4444",
    icon: "♂",
    tone: "Afirma, lucha, protege",
  },
  Jupiter: {
    symbol: "♃",
    archetype: "El Sabio / Maestro",
    function: "Expansión, fe, filosofía, justicia y abundancia",
    polarity: "Activo",
    element: "Aire",
    color: "#3399ff",
    icon: "♃",
    tone: "Inspira, eleva, expande",
  },
  Saturn: {
    symbol: "♄",
    archetype: "El Guardián del Umbral",
    function: "Estructura, disciplina, tiempo, responsabilidad",
    polarity: "Receptivo",
    element: "Tierra",
    color: "#555555",
    icon: "♄",
    tone: "Consolida, exige, purifica",
  },
  Uranus: {
    symbol: "♅",
    archetype: "El Rebelde / Innovador",
    function: "Cambio súbito, libertad, intuición superior",
    polarity: "Activo",
    element: "Aire",
    color: "#00ffff",
    icon: "♅",
    tone: "Rompe moldes, libera",
  },
  Neptune: {
    symbol: "♆",
    archetype: "El Místico / Soñador",
    function: "Inspiración, empatía, fantasía, disolución del ego",
    polarity: "Receptivo",
    element: "Agua",
    color: "#cc99ff",
    icon: "♆",
    tone: "Transciende, disuelve, imagina",
  },
  Pluto: {
    symbol: "♇",
    archetype: "El Alquimista",
    function: "Transformación profunda, poder oculto, regeneración",
    polarity: "Activo",
    element: "Fuego / Agua",
    color: "#993399",
    icon: "♇",
    tone: "Destruye para renacer",
  },
}

const HOUSE_MEANINGS: Record<number, string> = {
  1: "Identidad, apariencia y comienzos",
  2: "Recursos, valores y posesiones",
  3: "Comunicación, hermanos y viajes cortos",
  4: "Hogar, familia y raíces",
  5: "Creatividad, romance y placer",
  6: "Trabajo, salud y servicio",
  7: "Relaciones, pareja y asociaciones",
  8: "Transformación, intimidad y recursos compartidos",
  9: "Filosofía, viajes largos y educación superior",
  10: "Carrera, estatus y logros públicos",
  11: "Amistades, grupos y aspiraciones",
  12: "Espiritualidad, retiro y lo oculto",
}

const DIGNITY_INFO: Record<string, { color: string; icon: string; description: string; bgClass: string }> = {
  Domicilio: {
    color: "#d4af37",
    icon: "🔆",
    description: "Fuerte, estable, actúa con naturalidad",
    bgClass: "bg-[#d4af37]/20 text-[#d4af37] border-[#d4af37]/40",
  },
  Exaltación: {
    color: "#ffd700",
    icon: "⭐",
    description: "Potencia elevada, inspiración, nobleza",
    bgClass: "bg-[#ffd700]/20 text-[#ffd700] border-[#ffd700]/40",
  },
  Peregrino: {
    color: "#66ccff",
    icon: "⚪",
    description: "Neutro, adaptabilidad, cambio",
    bgClass: "bg-[#66ccff]/20 text-[#66ccff] border-[#66ccff]/40",
  },
  Caída: {
    color: "#b5651d",
    icon: "🔻",
    description: "Debilidad, pérdida de dirección",
    bgClass: "bg-[#b5651d]/20 text-[#b5651d] border-[#b5651d]/40",
  },
  Exilio: {
    color: "#b22222",
    icon: "❌",
    description: "Tensión, desafíos, conflictos",
    bgClass: "bg-[#b22222]/20 text-[#b22222] border-[#b22222]/40",
  },
}

const ASPECT_INFO: Record<
  string,
  { color: string; icon: string; nature: string; description: string; bgClass: string }
> = {
  conjunction: {
    color: "#ffd700",
    icon: "☀️",
    nature: "Neutra (intensificadora)",
    description: "Unión de fuerzas. Los planetas actúan como uno solo.",
    bgClass: "bg-[#ffd700]/20 text-[#ffd700] border-[#ffd700]/40",
  },
  sextile: {
    color: "#00ff99",
    icon: "🔷",
    nature: "Benéfica",
    description: "Oportunidad, colaboración, aprendizaje fluido.",
    bgClass: "bg-[#00ff99]/20 text-[#00ff99] border-[#00ff99]/40",
  },
  square: {
    color: "#ff3333",
    icon: "❌",
    nature: "Tensa",
    description: "Choque de voluntades, desafío, necesidad de acción.",
    bgClass: "bg-[#ff3333]/20 text-[#ff3333] border-[#ff3333]/40",
  },
  trine: {
    color: "#66ccff",
    icon: "🔺",
    nature: "Benéfica",
    description: "Armonía natural, inspiración, dones innatos.",
    bgClass: "bg-[#66ccff]/20 text-[#66ccff] border-[#66ccff]/40",
  },
  opposition: {
    color: "#ff9900",
    icon: "⚖️",
    nature: "Tensa (polarizadora)",
    description: "Dualidad, tensión entre extremos. Enseña equilibrio.",
    bgClass: "bg-[#ff9900]/20 text-[#ff9900] border-[#ff9900]/40",
  },
}

export function ResultsDisplay({ results, birthData, wheelOrientation = "aries" }: ResultsDisplayProps) {
  const [interpretation, setInterpretation] = useState<any>(null)
  const [interpretLoading, setInterpretLoading] = useState(false)
  const [interpretError, setInterpretError] = useState<string | null>(null)

  const chart = results.chart || {}
  const extended = results.extended || {}
  
  const planets = chart.planets || []
  const houses = chart.houses || []
  const aspects = chart.aspects || []
  
  const profections = extended.profections || null
  const lots = extended.lots || null
  const fixed_stars = extended.fixed_stars || null
  const lunar_mansion = extended.lunar_mansion || null
  const fardars = extended.fardars || null

  const sect = results.derived.sect || null
  const firdaria = results.life_cycles?.firdaria
  const arabicParts = results.derived.arabic_parts
  const lifeCycles = results.life_cycles?.natal_periods || []
  const forecast = results.forecast

  const formatDignity = (dignity: any): string => {
    if (!dignity) return "Sin datos"
    if (dignity.domicile || dignity.essential === "Domicilio") return "Domicilio"
    if (dignity.exaltation || dignity.essential === "Exaltación") return "Exaltación"
    if (dignity.detriment || dignity.essential === "Exilio") return "Exilio"
    if (dignity.fall || dignity.essential === "Caída") return "Caída"
    if (dignity.peregrine || dignity.essential === "Peregrino") return "Peregrino"
    return "Sin datos"
  }

  const getDignityInfo = (dignity: any) => {
    const dignityName = formatDignity(dignity)
    return (
      DIGNITY_INFO[dignityName] || {
        color: "#6b7280",
        icon: "—",
        description: "Sin dignidad especial",
        bgClass: "bg-muted/20 text-muted-foreground border-muted",
      }
    )
  }

  const getAspectInfo = (aspectType: string) => {
    const normalizedType = aspectType.toLowerCase()
    return (
      ASPECT_INFO[normalizedType] || {
        color: "#6b7280",
        icon: "⭕",
        nature: "Desconocida",
        description: "Aspecto no catalogado",
        bgClass: "bg-muted/20 text-muted-foreground border-muted",
      }
    )
  }

  const getOrbIntensity = (orb: number | undefined): string => {
    if (!orb) return "opacity-60"
    if (orb < 1) return "opacity-100 font-bold"
    if (orb < 3) return "opacity-90"
    if (orb < 5) return "opacity-75"
    return "opacity-60"
  }

  const formatPlanetName = (name: string) => {
    const archetype = PLANET_ARCHETYPES[name]
    if (!archetype) {
      return <span>{name}</span>
    }

    return (
      <div className="group relative inline-flex items-center gap-2">
        <span className="text-2xl" style={{ color: archetype.color }} aria-hidden="true">
          {archetype.symbol}
        </span>
        <span className="font-semibold">{name}</span>
        {/* Tooltip on hover */}
        <div className="absolute left-0 top-full mt-2 z-50 hidden group-hover:block w-80 p-4 rounded-lg border-2 bg-card shadow-2xl animate-in fade-in duration-200">
          <div className="space-y-2">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-3xl">{archetype.icon}</span>
              <div>
                <p className="font-serif font-bold text-lg" style={{ color: archetype.color }}>
                  {archetype.archetype}
                </p>
                <p className="text-xs text-muted-foreground italic">{archetype.tone}</p>
              </div>
            </div>
            <p className="text-sm leading-relaxed">{archetype.function}</p>
            <div className="flex gap-3 text-xs text-muted-foreground mt-2">
              <span>
                <strong>Polaridad:</strong> {archetype.polarity}
              </span>
              <span>•</span>
              <span>
                <strong>Elemento:</strong> {archetype.element}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const getPlanetSymbol = (name: string) => {
    return PLANET_ARCHETYPES[name]?.symbol || ""
  }

  const chartBirthData = birthData
    ? {
        name: birthData.name || "Carta Natal",
        date: `${birthData.date}T${birthData.time}:00Z`,
        location: birthData.city && birthData.country ? `${birthData.city}, ${birthData.country}` : undefined,
        lat: undefined,
        lon: undefined,
      }
    : results.birth
      ? {
          name: results.person?.name || results.name || "Carta Natal",
          date: results.birth.date,
          location:
            results.person?.birth_city && results.person?.birth_country
              ? `${results.person.birth_city}, ${results.person.birth_country}`
              : results.birth.location,
          lat: results.birth.lat,
          lon: results.birth.lon,
        }
      : undefined

  const sunPlanet = planets.find((p: any) => p.name === "Sun")
  const moonPlanet = planets.find((p: any) => p.name === "Moon")
  const ascendantSign = houses?.[0]?.sign

  const handleInterpret = async () => {
    if (!results.birth) return

    setInterpretLoading(true)
    setInterpretError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_ABU_API_URL || "http://localhost:8000"
      
      const payload = {
        birthDate: results.birth.date,
        lat: results.birth.lat,
        lon: results.birth.lon,
        language: "es",
        include_narrative: true,
      }

      console.log("[v0] Calling POST /api/ai/interpret with payload:", payload)

      const response = await fetch(`${backendUrl}/api/ai/interpret`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })

      if (response.status === 502) {
        setInterpretError("Error en Abu Engine. El servicio de interpretación no está disponible.")
        return
      }

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      console.log("[v0] Received interpretation data:", data)
      setInterpretation(data)
    } catch (err) {
      console.error("[v0] Error calling /api/ai/interpret:", err)
      setInterpretError(err instanceof Error ? err.message : "Error desconocido al obtener interpretación")
    } finally {
      setInterpretLoading(false)
    }
  }

  return (
    <div className="space-y-12 animate-in fade-in duration-700">
      <div className="text-center space-y-4">
        <h2 className="text-4xl font-serif text-balance">Tu Configuración Celeste</h2>
        <p className="text-muted-foreground text-lg">Revelada a través de la sabiduría antigua</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-2 border-primary/40 shadow-lg hover-lift bg-card/50 backdrop-blur">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
              <Sun className="w-5 h-5 text-primary" />
              Secta
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-serif font-bold text-primary tracking-tight">
              {sect === "diurnal" ? "Diurna" : sect === "nocturnal" ? "Nocturna" : "Sin datos disponibles"}
            </div>
            <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
              {sect === "diurnal"
                ? "Carta del día"
                : sect === "nocturnal"
                  ? "Carta de la noche"
                  : "Determina si pertenece al día o la noche"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-primary/40 shadow-lg hover-lift bg-card/50 backdrop-blur">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
              <Sparkles className="w-5 h-5 text-primary" />
              Firdaria Actual
            </CardTitle>
          </CardHeader>
          <CardContent>
            {firdaria ? (
              <>
                <div className="text-2xl font-serif font-bold tracking-tight">
                  <span className="text-xl">{getPlanetSymbol(firdaria.main?.ruler)}</span> {firdaria.main?.ruler}{" "}
                  (Mayor)
                </div>
                <div className="text-lg text-muted-foreground mt-1">
                  → <span className="text-lg">{getPlanetSymbol(firdaria.sub?.ruler)}</span> {firdaria.sub?.ruler} (Sub)
                </div>
                <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                  {firdaria.sub?.period_start ? new Date(firdaria.sub.period_start).toLocaleDateString() : ""} -{" "}
                  {firdaria.sub?.period_end ? new Date(firdaria.sub.period_end).toLocaleDateString() : ""}
                </p>
              </>
            ) : (
              <div className="text-base text-muted-foreground">Sin datos disponibles</div>
            )}
          </CardContent>
        </Card>

        <Card className="border-2 border-primary/40 shadow-lg hover-lift bg-card/50 backdrop-blur">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
              <Star className="w-5 h-5 text-primary" />
              Casa de Profección
            </CardTitle>
          </CardHeader>
          <CardContent>
            {profections?.house ? (
              <>
                <div className="text-3xl font-serif font-bold tracking-tight">Casa {profections.house}</div>
                <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                  {HOUSE_MEANINGS[profections.house] || "Sin descripción"}
                </p>
              </>
            ) : (
              <div className="text-base text-muted-foreground">Sin datos disponibles</div>
            )}
          </CardContent>
        </Card>

        <Card className="border-2 border-primary/40 shadow-lg hover-lift bg-card/50 backdrop-blur">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
              <Moon className="w-5 h-5 text-primary" />
              Tránsito Lunar
            </CardTitle>
          </CardHeader>
          <CardContent>
            {results.derived.lunar_transit?.moon_position ? (
              <>
                <div className="text-3xl font-serif font-bold tracking-tight">
                  {Math.floor(results.derived.lunar_transit.moon_position)}°
                </div>
                <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                  {results.derived.lunar_transit.aspects?.length
                    ? `${results.derived.lunar_transit.aspects.length} aspecto${results.derived.lunar_transit.aspects.length > 1 ? "s" : ""}`
                    : "Sin aspectos mayores"}
                </p>
              </>
            ) : (
              <div className="text-base text-muted-foreground">Sin datos disponibles</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-2 border-primary/30 shadow-2xl bg-card/50 backdrop-blur">
        <CardHeader className="space-y-3">
          <CardTitle className="text-3xl font-serif text-center">Carta Natal</CardTitle>
          <CardDescription className="text-base leading-relaxed text-center">
            Configuración celeste completa
            <span className="block mt-2 text-sm">
              Orientación: {wheelOrientation === "aries" ? "Aries arriba (tradicional)" : "Ascendente arriba (personal)"}
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent className="py-8">
          <ZodiacWheel
            planets={planets}
            houses={{ houses, asc: houses?.[0]?.cusp, mc: houses?.[9]?.cusp }}
            birthData={chartBirthData}
            sunSign={sunPlanet?.sign}
            moonSign={moonPlanet?.sign}
            ascendantSign={ascendantSign}
            orientation={wheelOrientation}
          />
        </CardContent>
      </Card>

      <Card className="border-2 border-primary/30 shadow-2xl bg-card/50 backdrop-blur">
        <CardHeader className="space-y-3">
          <CardTitle className="text-3xl font-serif">Análisis Completo</CardTitle>
          <CardDescription className="text-base leading-relaxed">
            Explorar posiciones planetarias y técnicas persas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="planets" className="w-full">
            <TabsList className="grid w-full grid-cols-7 h-12">
              <TabsTrigger value="planets" className="text-sm">
                Planetas
              </TabsTrigger>
              <TabsTrigger value="houses" className="text-sm">
                Casas
              </TabsTrigger>
              <TabsTrigger value="aspects" className="text-sm">
                Aspectos
              </TabsTrigger>
              <TabsTrigger value="profections" className="text-sm">
                Profecciones
              </TabsTrigger>
              <TabsTrigger value="lots" className="text-sm">
                Lotes
              </TabsTrigger>
              <TabsTrigger value="stars" className="text-sm">
                Estrellas
              </TabsTrigger>
              <TabsTrigger value="interpret" className="text-sm">
                Interpretación
              </TabsTrigger>
            </TabsList>

            <TabsContent value="planets" className="mt-8">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b-2 border-primary/30">
                      <th className="text-left p-4 font-serif text-lg">Planeta</th>
                      <th className="text-left p-4 font-serif text-lg">Signo</th>
                      <th className="text-left p-4 font-serif text-lg">Grado</th>
                      <th className="text-left p-4 font-serif text-lg">Casa</th>
                      <th className="text-left p-4 font-serif text-lg">Dignidad</th>
                      <th className="text-right p-4 font-serif text-lg">Puntaje</th>
                    </tr>
                  </thead>
                  <tbody>
                    {planets.map((planet: any, index: number) => {
                      const dignityInfo = getDignityInfo(planet.dignity)
                      const dignityName = formatDignity(planet.dignity)

                      return (
                        <tr key={index} className="border-b border-border hover:bg-primary/5 transition-colors">
                          <td className="p-4 font-semibold">{formatPlanetName(planet.name)}</td>
                          <td className="p-4">{planet.sign || "Sin datos"}</td>
                          <td className="p-4 text-muted-foreground">
                            {planet.degree ? `${planet.degree.toFixed(2)}°` : "Sin datos"}
                          </td>
                          <td className="p-4">{planet.house || "Sin datos"}</td>
                          <td className="p-4">
                            <div className="flex flex-col gap-1">
                              <Badge className={`${dignityInfo.bgClass} border-2 font-semibold`}>
                                <span className="mr-1">{dignityInfo.icon}</span>
                                {dignityName}
                              </Badge>
                              <span className="text-xs text-muted-foreground italic">{dignityInfo.description}</span>
                            </div>
                          </td>
                          <td className="p-4 text-right font-semibold">
                            {planet.dignity?.score !== undefined ? (
                              <>
                                {planet.dignity.score > 0 ? "+" : ""}
                                {planet.dignity.score}
                              </>
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </TabsContent>

            <TabsContent value="houses" className="mt-8">
              {houses.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {houses.map((house: any, index: number) => (
                    <Card key={index} className="hover-lift border-2 bg-card/30">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-serif">Casa {house.number || house.house}</CardTitle>
                        <CardDescription className="text-sm leading-relaxed">
                          {HOUSE_MEANINGS[house.number || house.house] || ""}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <p className="text-sm leading-relaxed">
                          <span className="text-muted-foreground">Signo:</span>{" "}
                          <span className="font-semibold text-base">{house.sign || "Sin datos"}</span>
                        </p>
                        <p className="text-sm leading-relaxed">
                          <span className="text-muted-foreground">Cúspide:</span>{" "}
                          <span className="font-semibold text-base">
                            {house.cusp
                              ? `${house.cusp.toFixed(2)}°`
                              : house.degree
                                ? `${house.degree.toFixed(2)}°`
                                : "Sin datos"}
                          </span>
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Star className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground text-lg leading-relaxed">Sin datos de casas disponibles</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="aspects" className="space-y-4 mt-8">
              {aspects && aspects.length > 0 ? (
                <div className="space-y-3">
                  {aspects.map((aspect: any, index: number) => {
                    const aspectInfo = getAspectInfo(aspect.type)
                    const intensityClass = getOrbIntensity(aspect.orb)

                    return (
                      <div
                        key={index}
                        className={`flex items-start justify-between p-5 rounded-lg border-2 transition-all hover-lift bg-card/30 ${intensityClass}`}
                        style={{ borderColor: aspectInfo.color + "60" }}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-2xl" aria-hidden="true">
                              {aspectInfo.icon}
                            </span>
                            <h4 className="font-serif font-semibold text-lg">
                              <span className="text-xl">{getPlanetSymbol(aspect.planet_a)}</span> {aspect.planet_a}{" "}
                              <span className="text-primary mx-2">{aspect.type}</span>{" "}
                              <span className="text-xl">{getPlanetSymbol(aspect.planet_b)}</span> {aspect.planet_b}
                            </h4>
                          </div>
                          <div className="ml-11 space-y-1">
                            <p className="text-sm italic leading-relaxed" style={{ color: aspectInfo.color }}>
                              {aspectInfo.description}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Orbe: {aspect.orb ? `${aspect.orb.toFixed(2)}°` : "Sin datos"} • Naturaleza:{" "}
                              {aspectInfo.nature}
                            </p>
                          </div>
                        </div>
                        <Badge className={`${aspectInfo.bgClass} border-2 font-semibold text-sm px-3 py-1`}>
                          {aspectInfo.icon} {aspect.type}
                        </Badge>
                      </div>
                    )
                  })}
                </div>
              ) : results.derived.lunar_transit?.aspects && results.derived.lunar_transit.aspects.length > 0 ? (
                <div className="space-y-3">
                  <h3 className="text-xl font-serif mb-4">Aspectos Lunares</h3>
                  {results.derived.lunar_transit.aspects.map((aspect: any, index: number) => {
                    const aspectInfo = getAspectInfo(aspect.type)
                    const intensityClass = getOrbIntensity(aspect.orb)

                    return (
                      <div
                        key={index}
                        className={`flex items-start justify-between p-5 rounded-lg border-2 transition-all hover-lift bg-card/30 ${intensityClass}`}
                        style={{ borderColor: aspectInfo.color + "60" }}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-2xl" aria-hidden="true">
                              {aspectInfo.icon}
                            </span>
                            <h4 className="font-serif font-semibold text-lg">
                              <span className="text-xl">☽</span> Luna{" "}
                              <span className="text-primary mx-2">{aspect.type}</span>{" "}
                              <span className="text-xl">{getPlanetSymbol(aspect.planet)}</span> {aspect.planet}
                            </h4>
                          </div>
                          <div className="ml-11 space-y-1">
                            <p className="text-sm italic leading-relaxed" style={{ color: aspectInfo.color }}>
                              {aspectInfo.description}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Orbe: {aspect.orb ? `${aspect.orb.toFixed(2)}°` : "Sin datos"} • Naturaleza:{" "}
                              {aspectInfo.nature}
                            </p>
                          </div>
                        </div>
                        <Badge className={`${aspectInfo.bgClass} border-2 font-semibold text-sm px-3 py-1`}>
                          {aspectInfo.icon} {aspect.type}
                        </Badge>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Moon className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground text-lg leading-relaxed">Sin aspectos disponibles</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="profections" className="mt-8">
              {profections ? (
                <div className="space-y-4">
                  <p className="text-muted-foreground leading-relaxed">
                    Las profecciones anuales muestran qué casa está activada cada año de vida.
                  </p>
                  <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                    {JSON.stringify(profections, null, 2)}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Calendar className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground text-lg leading-relaxed">Sin datos de profecciones disponibles</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="lots" className="mt-8">
              {lots ? (
                <div className="space-y-4">
                  <p className="text-muted-foreground leading-relaxed">
                    Los lotes o partes arábicas son puntos calculados de la carta natal.
                  </p>
                  <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                    {JSON.stringify(lots, null, 2)}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Sparkles className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground text-lg leading-relaxed">Sin datos de lotes disponibles</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="stars" className="mt-8">
              {fixed_stars ? (
                <div className="space-y-4">
                  <p className="text-muted-foreground leading-relaxed">
                    Las estrellas fijas tienen influencia cuando están en conjunción con planetas o ángulos.
                  </p>
                  <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                    {JSON.stringify(fixed_stars, null, 2)}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Star className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground text-lg leading-relaxed">Sin datos de estrellas fijas disponibles</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="interpret" className="mt-8">
              {!interpretation ? (
                <div className="text-center py-12 space-y-6">
                  <MessageSquare className="w-16 h-16 text-primary/50 mx-auto mb-4" />
                  <div className="space-y-3">
                    <h3 className="text-2xl font-serif">Interpretación con Lilly</h3>
                    <p className="text-muted-foreground text-lg leading-relaxed max-w-2xl mx-auto">
                      Obtén una interpretación narrativa completa de tu carta natal usando inteligencia artificial
                    </p>
                  </div>
                  <Button
                    onClick={handleInterpret}
                    disabled={interpretLoading}
                    size="md"  
                    className="h-12 px-8"
                  >
                    {interpretLoading ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Generando interpretación...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-5 w-5" />
                        Generar Interpretación
                      </>
                    )}
                  </Button>
                  {interpretError && (
                    <div className="mt-4 p-4 bg-destructive/10 border-2 border-destructive/30 rounded-lg max-w-2xl mx-auto">
                      <p className="text-destructive font-medium">{interpretError}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-6">
                  {interpretation.narrative ? (
                    <div className="prose prose-invert max-w-none">
                      <div className="p-6 rounded-lg bg-card/50 border-2 border-primary/30">
                        <h3 className="text-2xl font-serif mb-4">Narrativa</h3>
                        <p className="text-base leading-relaxed whitespace-pre-wrap">{interpretation.narrative}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-6">
                      <p className="text-muted-foreground">Narrativa no disponible</p>
                    </div>
                  )}
                  
                  {interpretation.maestro && (
                    <div className="space-y-4">
                      <h3 className="text-2xl font-serif">JSON Maestro</h3>
                      <pre className="bg-muted p-6 rounded-lg overflow-x-auto text-sm">
                        {JSON.stringify(interpretation.maestro, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
