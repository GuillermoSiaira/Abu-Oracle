'use client'

import dynamic from "next/dynamic"
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent
} from "@/components/ui/simple-tabs"

import { NatalChartTab } from './natal-chart-tab'
import { PersianTechniquesTab } from './persian-techniques-tab'
import { TransitsTab } from './transits-tab'
import { useAppStore } from '@/lib/store'

const HFRelocationMap = dynamic(() => import("@/components/HFRelocationMap"), {
  ssr: false,
  loading: () => (
    <div className="text-center py-12 text-muted-foreground">Cargando mapa…</div>
  ),
})

export function ChartTabs() {
  const { abuData, includeTransits } = useAppStore()

  if (!abuData) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>Ingresa los datos natales y presiona "Calcular Carta Natal"</p>
      </div>
    )
  }

  const gridCols = includeTransits ? "grid-cols-4" : "grid-cols-3"

  return (
    <Tabs defaultValue="chart" className="w-full">
      <TabsList className={`grid w-full ${gridCols}`}>
        <TabsTrigger value="chart">Carta Natal</TabsTrigger>
        <TabsTrigger value="persian">Técnicas Persas</TabsTrigger>
        {includeTransits && (
          <TabsTrigger value="transits">Tránsitos</TabsTrigger>
        )}
        <TabsTrigger value="relocation">Relocation</TabsTrigger>
      </TabsList>

      <TabsContent value="chart" className="space-y-4">
        <NatalChartTab />
      </TabsContent>

      <TabsContent value="persian" className="space-y-4">
        <PersianTechniquesTab />
      </TabsContent>

      {includeTransits && (
        <TabsContent value="transits" className="space-y-4">
          <TransitsTab />
        </TabsContent>
      )}

      <TabsContent value="relocation" className="space-y-4">
        <HFRelocationMap geojsonUrl="/geojson/subject_1000_hf.geojson" rankingUrl="/rankings/subject_1000_ranking.json" />
      </TabsContent>
    </Tabs>
  )
}
