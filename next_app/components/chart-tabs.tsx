'use client'

import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent
} from "@/components/ui/simple-tabs"

import { NatalChartTab } from './natal-chart-tab'
import { PersianTechniquesTab } from './persian-techniques-tab'
import { TransitsTab } from './transits-tab'
import { RelocationTab } from './relocation-tab'
import { useAppStore } from '@/lib/store'
import { UI } from '@/lib/i18n'

export function ChartTabs() {
  const { abuData, includeTransits, lang } = useAppStore()
  const t = UI[lang]

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
      <div className="flex items-center gap-2 mb-1">
        <TabsList className={`grid flex-1 ${gridCols}`}>
          <TabsTrigger value="chart">{t.tabChart}</TabsTrigger>
          <TabsTrigger value="persian">{t.tabPersian}</TabsTrigger>
          {includeTransits && (
            <TabsTrigger value="transits">{t.tabTransits}</TabsTrigger>
          )}
          <TabsTrigger value="relocation">{t.tabRelocation}</TabsTrigger>
        </TabsList>

      </div>

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
        <RelocationTab />
      </TabsContent>
    </Tabs>
  )
}
