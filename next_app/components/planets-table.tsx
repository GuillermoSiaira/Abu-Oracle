'use client'

import type { Planet } from '@/lib/types'
import { Badge } from "@/components/ui/simple-badge"

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: '☉',
  Moon: '☽',
  Mercury: '☿',
  Venus: '♀',
  Mars: '♂',
  Jupiter: '♃',
  Saturn: '♄',
  Uranus: '♅',
  Neptune: '♆',
  Pluto: '♇',
}

const DIGNITY_INFO = {
  domicile: { icon: '🔆', color: '#d4af37', label: 'Domicilio' },
  exaltation: { icon: '⭐', color: '#ffd700', label: 'Exaltación' },
  peregrine: { icon: '⚪', color: '#66ccff', label: 'Peregrino' },
  fall: { icon: '🔻', color: '#b5651d', label: 'Caída' },
  detriment: { icon: '❌', color: '#b22222', label: 'Exilio' },
}

export function PlanetsTable({ planets }: { planets: Planet[] }) {
  return (
    <div className="space-y-2">
      {planets.map((planet, idx) => (
        <div key={idx} className="flex justify-between items-center p-2 border-b border-border/50">
          <div className="flex items-center gap-2">
            <span className="text-lg">{PLANET_SYMBOLS[planet.name] || planet.name}</span>
            <span className="font-medium">{planet.name}</span>
          </div>
          <div className="flex gap-2 items-center">
            <span className="text-sm">{planet.degree.toFixed(2)}° {planet.sign}</span>
            <Badge variant="outline">Casa {planet.house}</Badge>
            <span style={{ color: DIGNITY_INFO[planet.dignity].color }}>
              {DIGNITY_INFO[planet.dignity].icon}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
