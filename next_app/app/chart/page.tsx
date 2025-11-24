"use client"

import { useAppStore } from "@/lib/store"
import { ChartTabs } from "@/components/chart-tabs"
import { ChatPanel } from "@/components/chat-panel"

export default function ChartPage() {
  const birthData = useAppStore((s) => s.birthData)
  const abuData = useAppStore((s) => s.abuData)
  const lillyData = useAppStore((s) => s.lillyData)

  const ready = birthData && abuData && lillyData

  if (!ready) {
    return (
      <div className="p-10 text-center text-lg">
        Falta información para generar tu carta.
        <br />
        Por favor vuelve al inicio y completa el formulario.
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-8">
      <ChartTabs />
      <ChatPanel />
    </div>
  )
}
