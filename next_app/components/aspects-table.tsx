'use client'

import type { Aspect } from '@/lib/types'
import { Badge } from "@/components/ui/simple-badge"

const ASPECT_INFO = {
  conjunction: { icon: '☌', color: '#ffd700', label: 'Conjunción' },
  opposition: { icon: '☍', color: '#ff4444', label: 'Oposición' },
  trine: { icon: '△', color: '#44ff44', label: 'Trígono' },
  square: { icon: '□', color: '#ff8844', label: 'Cuadratura' },
  sextile: { icon: '⚹', color: '#44ffff', label: 'Sextil' },
  semisextile: { icon: '⚺', color: '#aaaaaa', label: 'Semisextil' },
  quincunx: { icon: '⚻', color: '#ff88ff', label: 'Quincuncio' },
  semisquare: { icon: '∠', color: '#ffaa44', label: 'Semicuadratura' },
  sesquiquadrate: { icon: '⚼', color: '#ff6644', label: 'Sesquicuadratura' },
}

export function AspectsTable({ aspects }: { aspects: Aspect[] }) {
  return (
    <div className="space-y-2">
      {aspects.map((aspect, idx) => (
        <div key={idx} className="flex justify-between items-center p-2 border-b border-border/50">
          <div className="flex items-center gap-2">
            <span>{aspect.planet1}</span>
            <span style={{ color: ASPECT_INFO[aspect.type].color }}>
              {ASPECT_INFO[aspect.type].icon}
            </span>
            <span>{aspect.planet2}</span>
          </div>
          <div className="flex gap-2 items-center">
            <span className="text-xs text-muted-foreground">orbe {aspect.orb.toFixed(2)}°</span>
            {aspect.applying && <Badge variant="outline" className="text-xs">Aplicativo</Badge>}
          </div>
        </div>
      ))}
    </div>
  )
}
