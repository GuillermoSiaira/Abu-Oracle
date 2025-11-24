'use client'

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/simple-card"
import { Input } from "@/components/ui/simple-input"
import { Button } from "@/components/ui/simple-button"
import { Send } from "lucide-react"
import type React from "react";


import {
  useAppStore,
  OnboardingStage
} from "@/lib/store"

import type { AbuAnalyzeResponse } from "@/lib/types"

import {
  runAbuAnalyze,
  runAbuSolarReturn,
  runAbuSolarReturnAI,
  runAbuOptimizeRS
} from "@/services/abu"

import { runLillyInterpret } from "@/services/lilly"

// ============================================
// GEOCODING SIMPLE (Nominatim)
// ============================================

async function geocodePlace(query: string) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(
    query
  )}`

  const res = await fetch(url)
  if (!res.ok) return null

  const data = await res.json()
  if (!Array.isArray(data) || data.length === 0) return null

  const item = data[0]
  const lat = parseFloat(item.lat)
  const lon = parseFloat(item.lon)

  if (Number.isNaN(lat) || Number.isNaN(lon)) return null

  return {
    lat,
    lon,
    displayName: item.display_name as string
  }
}

// ============================================
// MAPEO ABU → LILLY (hook para ajustes futuros)
// ============================================

function mapAbuToLillyAnalysis(abu: AbuAnalyzeResponse): AbuAnalyzeResponse {
  if (!abu) {
    throw new Error("No hay análisis de Abu disponible para Lilly.")
  }
  return abu
}

export function ChatPanel() {
  const {
    birthData,
    abuData,
    lillyData,
    chatHistory,
    addChatMessage,
    setBirthData,
    setAbuData,
    setLillyData,
    setIsLoading,
    setError,
    onboardingStage,
    onboardingData,
    setOnboardingStage,
    updateOnboardingData,
    resetOnboarding,
  } = useAppStore()

  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const hasChart = !!abuData
  const onboardingActive = !hasChart

  const isChatEnabled = onboardingActive || hasChart

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory, loading])

  // ==========================================
  // MENSAJE DE BIENVENIDA
  // ==========================================

  useEffect(() => {
    if (!hasChart && chatHistory.length === 0 && onboardingStage === "idle") {
      addChatMessage({
        role: "assistant",
        content:
          "Hola, soy el Agente Intérprete de AI Oracle. Para empezar necesito algunos datos de nacimiento. ¿Cuál es tu nombre completo (como quieras que aparezca en el informe)?",
        timestamp: new Date(),
      })
      setOnboardingStage("ask_name")
    }
  }, [
    hasChart,
    chatHistory.length,
    onboardingStage,
    addChatMessage,
    setOnboardingStage,
  ])

  const sendAssistantMessage = (content: string) => {
    addChatMessage({
      role: "assistant",
      content,
      timestamp: new Date(),
    })
  }

  // ==========================================
  // ONBOARDING FLOW
  // ==========================================

  const nextOnboardingStep = (current: OnboardingStage): OnboardingStage => {
    switch (current) {
      case "ask_name":
        return "ask_birthdate"
      case "ask_birthdate":
        return "ask_time"
      case "ask_time":
        return "ask_birthplace"
      case "ask_birthplace":
        return "ask_residence"
      case "ask_residence":
        return "ask_relocation"
      case "ask_relocation":
        return "completed"
      default:
        return "completed"
    }
  }

  const askQuestionForStage = (stage: OnboardingStage) => {
    switch (stage) {
      case "ask_birthdate":
        sendAssistantMessage(
          "Perfecto. Ahora dime tu fecha de nacimiento (AAAA-MM-DD). Ejemplo: 1991-04-12."
        )
        break
      case "ask_time":
        sendAssistantMessage(
          "Gracias. ¿A qué hora naciste? Usa formato 24 horas HH:MM. Ejemplo: 21:15."
        )
        break
      case "ask_birthplace":
        sendAssistantMessage(
          "¿En qué ciudad y país naciste? (Ejemplo: Balcarce, Argentina)."
        )
        break
      case "ask_residence":
        sendAssistantMessage(
          "¿Dónde vives actualmente? Ciudad y país. Ejemplo: Buenos Aires, Argentina."
        )
        break
      case "ask_relocation":
        sendAssistantMessage(
          "¿Querés un Retorno Solar reubicado en un lugar específico o que te sugiera los mejores lugares para pasar tu cumpleaños? Podés responder algo como “París, Francia” o “sugerime lugares”."
        )
        break
      default:
        break
    }
  }

  // ==========================================
  // ANÁLISIS NATAL DESDE ONBOARDING
  // ==========================================

  const runFullAnalysisFromOnboarding = async () => {
    const { name, birthDate, birthTime, birthPlaceText, residenceText } =
      onboardingData

    if (!birthDate || !birthTime || !birthPlaceText) {
      sendAssistantMessage(
        "Me falta alguna información clave (fecha, hora o lugar de nacimiento). Vamos de nuevo si querés."
      )
      return
    }

    try {
      setLoading(true)
      setIsLoading(true)
      setError(null)

      const birthPlaceGeo = await geocodePlace(birthPlaceText)
      if (!birthPlaceGeo) {
        sendAssistantMessage(
          "No pude encontrar la ciudad de nacimiento. ¿Podés verificarla o escribir una más conocida?"
        )
        return
      }

      let currentLat = birthPlaceGeo.lat
      let currentLon = birthPlaceGeo.lon

      if (residenceText) {
        const residenceGeo = await geocodePlace(residenceText)
        if (residenceGeo) {
          currentLat = residenceGeo.lat
          currentLon = residenceGeo.lon
        }
      }

      const isoDate = `${birthDate}T${birthTime}:00Z`

      const birthDataZustand = {
        birthDate: isoDate,
        lat: birthPlaceGeo.lat,
        lon: birthPlaceGeo.lon,
      }

      setBirthData(birthDataZustand)

      const payload = {
        person: {
          name: name ?? null,
          question: "",
        },
        birth: {
          date: isoDate,
          lat: birthPlaceGeo.lat,
          lon: birthPlaceGeo.lon,
        },
        current: {
          lat: currentLat,
          lon: currentLon,
        },
      }

      const abuRes = await runAbuAnalyze(payload)
      setAbuData(abuRes)

      const lillyRes = await runLillyInterpret({
        analysis: mapAbuToLillyAnalysis(abuRes),
        language: "es",
        question: "",
      })

      setLillyData(lillyRes)

      setOnboardingStage("completed")

      sendAssistantMessage(
        `Listo, ${name ?? "allí"}. Ya calculé tu carta natal y la interpretación inicial.`
      )

      sendAssistantMessage(
        "Si querés, también puedo analizar tu Retorno Solar para el próximo año. ¿Querés que te sugiera lugares o tenés alguno en mente?"
      )
    } catch (err: any) {
      console.error(err)
      setError(err.message || "Error inesperado.")
      sendAssistantMessage(
        "Hubo un error al generar tu carta. Probemos de nuevo en un momento."
      )
    } finally {
      setIsLoading(false)
      setLoading(false)
    }
  }

  // ==========================================
  // FUNCIÓN: RANKING IGP
  // ==========================================

  const handleOptimizeRS = async () => {
    if (!birthData) {
      sendAssistantMessage("Primero necesito tu carta natal.")
      return
    }

    try {
      setLoading(true)
      setIsLoading(true)

      const year = new Date().getFullYear() + 1

      const rankingRes = await runAbuOptimizeRS({
        birth: {
          date: birthData.birthDate,
          lat: birthData.lat,
          lon: birthData.lon,
        },
        target_year: year,
        intent: "general",
        preferences: {},
        refine: false,
        diversity: false,
        language: "es",
      })

      const results = rankingRes?.solar_return_ranking
      if (!results || !Array.isArray(results.top_places)) {
        sendAssistantMessage(
          "No pude obtener un ranking claro. Probemos otra vez más tarde."
        )
        return
      }

      let text = `✨ *Abu encontró los lugares más favorables para tu Retorno Solar ${year}:*\n\n`

      results.top_places.slice(0, 3).forEach((p: any, idx: number) => {
        text += `${idx + 1}. **${p.city}, ${p.country}**\n`
        if (p.reason) {
          text += `   — ${p.reason}\n`
        }
        text += "\n"
      })

      text += "¿Querés que calcule uno en particular?"

      sendAssistantMessage(text)
    } catch (err: any) {
      console.error(err)
      sendAssistantMessage(
        "Hubo un error al obtener los lugares óptimos para tu Retorno Solar."
      )
    } finally {
      setLoading(false)
      setIsLoading(false)
    }
  }

  // ==========================================
  // FUNCIÓN: RS EN CIUDAD ESPECÍFICA
  // ==========================================

  const handleSpecificRS = async (place: string) => {
    if (!birthData) {
      sendAssistantMessage("Primero necesito tu carta natal.")
      return
    }

    const geo = await geocodePlace(place)
    if (!geo) {
      sendAssistantMessage(
        "No pude encontrar ese lugar. ¿Querés probar con otra ciudad?"
      )
      return
    }

    try {
      setLoading(true)
      setIsLoading(true)

      const year = new Date().getFullYear() + 1

      const srChart = await runAbuSolarReturn({
        birthDate: birthData.birthDate,
        lat: geo.lat,
        lon: geo.lon,
        year,
      })

      const aiRes = await runAbuSolarReturnAI({
        natal_chart: abuData?.chart ?? {},
        solar_chart: srChart,
        language: "es",
      })

      let text = `✨ *Retorno Solar ${year} en ${geo.displayName}*\n\n`
      if (aiRes?.headline) text += `**${aiRes.headline}**\n\n`
      if (aiRes?.narrative) text += aiRes.narrative + "\n\n"

      if (aiRes?.actions?.length > 0) {
        text += "Sugerencias:\n"
        aiRes.actions.forEach((a: string) => {
          text += `- ${a}\n`
        })
      }

      sendAssistantMessage(text)
    } catch (err) {
      console.error(err)
      sendAssistantMessage(
        "Hubo un error al calcular el Retorno Solar en esa ciudad."
      )
    } finally {
      setLoading(false)
      setIsLoading(false)
    }
  }

  // ==========================================
  // DETECCIÓN DE INTENCIÓN RS
  // ==========================================

  const detectRSIntent = (text: string) => {
    const lower = text.toLowerCase()

    const keywordsRS = [
      "retorno solar",
      "rs",
      "solar return",
      "cumpleaños",
      "solar",
      "astrológico anual",
    ]

    const keywordsRanking = [
      "sugerime",
      "mejores lugares",
      "lugares",
      "ranking",
      "top lugares",
      "donde pasar mi cumpleaños",
    ]

    if (keywordsRanking.some((k) => lower.includes(k))) {
      return { type: "ranking" as const }
    }

    if (keywordsRS.some((k) => lower.includes(k))) {
      return { type: "specific" as const }
    }

    return null
  }

  // ==========================================
  // RESPUESTA DEL USUARIO (MAIN)
  // ==========================================

  const handleOnboardingAnswer = async (text: string) => {
    const stage = onboardingStage

    if (stage === "ask_name") {
      updateOnboardingData({ name: text.trim() })
    } else if (stage === "ask_birthdate") {
      updateOnboardingData({ birthDate: text.trim() })
    } else if (stage === "ask_time") {
      updateOnboardingData({ birthTime: text.trim() })
    } else if (stage === "ask_birthplace") {
      updateOnboardingData({ birthPlaceText: text.trim() })
    } else if (stage === "ask_residence") {
      updateOnboardingData({ residenceText: text.trim() })
    } else if (stage === "ask_relocation") {
      updateOnboardingData({ relocationPreference: text.trim() })
    }

    const next = nextOnboardingStep(stage)
    setOnboardingStage(next)

    if (next === "completed") {
      await runFullAnalysisFromOnboarding()
    } else {
      askQuestionForStage(next)
    }
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed) return

    addChatMessage({
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    })

    setInput("")

    if (!hasChart) {
      await handleOnboardingAnswer(trimmed)
      return
    }

    const rsIntent = detectRSIntent(trimmed)
    if (rsIntent) {
      if (rsIntent.type === "ranking") {
        await handleOptimizeRS()
        return
      }

      if (rsIntent.type === "specific") {
        await handleSpecificRS(trimmed)
        return
      }
    }

    try {
      setLoading(true)
      setIsLoading(true)
      setError(null)

      if (!abuData) {
        sendAssistantMessage(
          "Todavía no tengo tu carta calculada. Empecemos por tus datos de nacimiento."
        )
        resetOnboarding()
        setOnboardingStage("ask_name")
        sendAssistantMessage(
          "Para empezar, dime tu nombre completo (como quieras que aparezca en el informe)."
        )
        return
      }

      const lillyRes = await runLillyInterpret({
        analysis: mapAbuToLillyAnalysis(abuData),
        language: "es",
        question: trimmed,
      })

      setLillyData(lillyRes)

      let content = ""
      if (lillyRes.headline) content += `**${lillyRes.headline}**\n\n`
      if (lillyRes.narrative) content += `${lillyRes.narrative}\n\n`

      if (lillyRes.actions?.length) {
        content += "Sugerencias:\n"
        lillyRes.actions.forEach((a) => {
          content += `- ${a}\n`
        })
      }

      sendAssistantMessage(content || "Aquí tienes una lectura.")
    } catch (err) {
      console.error(err)
      sendAssistantMessage("Ocurrió un error al consultar a Lilly Engine.")
    } finally {
      setLoading(false)
      setIsLoading(false)
    }
  }

  // ==========================================
  // RENDER UI
  // ==========================================

  return (
    <Card className="h-[500px] flex flex-col">
      <CardHeader>
        <CardTitle className="font-serif">Agente Intérprete</CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {chatHistory.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <p>Haz una pregunta sobre tu carta natal</p>
              <p className="text-sm mt-2">
                {hasChart
                  ? "Escribe tu pregunta abajo"
                  : "Te voy a guiar para calcular tu carta primero"}
              </p>
            </div>
          )}

          {chatHistory.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 whitespace-pre-wrap ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg p-3">
                <p className="text-sm">Pensando...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" && !loading && isChatEnabled && handleSend()
            }
            placeholder={
              hasChart
                ? "Preguntá algo sobre tu carta…"
                : "Responde para comenzar"
            }
            disabled={loading || !isChatEnabled}
          />

          <Button
            onClick={handleSend}
            disabled={loading || !isChatEnabled}
            size="sm"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
