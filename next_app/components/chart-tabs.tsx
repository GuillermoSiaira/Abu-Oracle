'use client'

import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent
} from "@/components/ui/simple-tabs"
import { NatalChartTab } from './natal-chart-tab'
import { PersianTechniquesTab } from './persian-techniques-tab'
import { InterpretationTab } from './interpretation-tab'
import { TransitsTab } from './transits-tab'
import { MaestroTab } from './maestro-tab'
import { useAppStore } from '@/lib/store'

export function ChartTabs() {
  const { abuData, lillyData, includeTransits } = useAppStore()

  if (!abuData) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>Ingresa los datos natales y presiona "Calcular Carta Natal"</p>
      </div>
    )
  }

  return (
    <Tabs defaultValue="chart" className="w-full">
      <TabsList className="grid w-full grid-cols-5">
        <TabsTrigger value="chart">Carta Natal</TabsTrigger>
        <TabsTrigger value="persian">Técnicas Persas</TabsTrigger>

        {/* SOLO RENDERIZAMOS LAS TABS SI LILLY YA RESPONDIÓ */}
        {lillyData && (
          <TabsTrigger value="interpretation">Interpretación</TabsTrigger>
        )}

        {lillyData && (
          <TabsTrigger value="maestro">Análisis Maestro</TabsTrigger>
        )}

        {includeTransits && (
          <TabsTrigger value="transits">Tránsitos</TabsTrigger>
        )}
      </TabsList>

      <TabsContent value="chart" className="space-y-4">
        <NatalChartTab />
      </TabsContent>

      <TabsContent value="persian" className="space-y-4">
        <PersianTechniquesTab />
      </TabsContent>

      <TabsContent value="interpretation" className="space-y-4">
        <InterpretationTab />
      </TabsContent>

      <TabsContent value="maestro" className="space-y-4">
        <MaestroTab />
      </TabsContent>

      {includeTransits && (
        <TabsContent value="transits" className="space-y-4">
          <TransitsTab />
        </TabsContent>
      )}
    </Tabs>
  )
}
