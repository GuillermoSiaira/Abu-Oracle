'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/simple-card"

interface Lot {
  name: string
  longitude: number
  sign: string
  house: number
  description: string
}

interface LotsViewProps {
  lots: Lot[]
}

export function LotsView({ lots }: LotsViewProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-serif">Partes Árabes</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {lots.map((lot) => (
          <div key={lot.name} className="border border-primary/20 rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-2xl">⊕</span>
              <h4 className="font-serif font-bold text-lg">Parte de {lot.name}</h4>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Posición</p>
                <p className="font-medium">{lot.longitude.toFixed(2)}° {lot.sign}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Casa</p>
                <p className="font-medium">Casa {lot.house}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Longitud</p>
                <p className="font-medium">{lot.longitude.toFixed(2)}°</p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground italic">{lot.description}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
