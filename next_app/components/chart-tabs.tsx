'use client'

import { NatalChartTab } from './natal-chart-tab'
import { PersianTechniquesTab } from './persian-techniques-tab'
import { TransitsTab } from './transits-tab'
import { RelocationTab } from './relocation-tab'
import { CieloHoyTab } from './cielo-hoy-tab'
import { useAppStore } from '@/lib/store'
import { useEffect } from 'react'

export function ChartTabs() {
  const { abuData, includeTransits, chartTab, setChartTab } = useAppStore()

  if (!abuData) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>Ingresa los datos natales y presiona "Calcular Carta Natal"</p>
      </div>
    )
  }

  const activeTab = chartTab ?? 'persian'

  useEffect(() => {
    if (!includeTransits && activeTab === 'transits') {
      setChartTab('persian')
    }
  }, [includeTransits, activeTab, setChartTab])

  return (
    <div className="h-full w-full">
      {activeTab === 'chart'      && <NatalChartTab />}
      {activeTab === 'persian'    && <PersianTechniquesTab />}
      {activeTab === 'transits'   && includeTransits && <TransitsTab />}
      {activeTab === 'relocation' && <RelocationTab />}
      {activeTab === 'sky'        && <CieloHoyTab />}
    </div>
  )
}
