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
import { UI, LANG_OPTIONS } from '@/lib/i18n'
import { Languages } from 'lucide-react'

export function ChartTabs() {
  const { abuData, includeTransits, lang, setLang } = useAppStore()
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

        {/* Language selector */}
        <div className="relative shrink-0">
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value as typeof lang)}
            className="appearance-none bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg pl-2 pr-6 py-2 focus:outline-none focus:border-amber-500/50 cursor-pointer"
          >
            {LANG_OPTIONS.map((l) => (
              <option key={l.code} value={l.code}>
                {l.flag} {l.label}
              </option>
            ))}
          </select>
          <Languages className="w-3 h-3 text-slate-400 absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
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
