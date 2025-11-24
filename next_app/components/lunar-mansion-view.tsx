'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/simple-card"

interface LunarMansion {
  mansion_number: number
  mansion_name: string
  degree_range: string
  description: string
}

interface LunarMansionViewProps {
  lunarMansion?: LunarMansion
}

export function LunarMansionView({ lunarMansion }: LunarMansionViewProps) {
  if (!lunarMansion) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="font-serif">Mansión Lunar</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No hay datos de mansión lunar disponibles</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-serif">Mansión Lunar</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Mansión #{lunarMansion.mansion_number}</p>
            <h3 className="text-2xl font-serif font-bold text-primary">{lunarMansion.mansion_name}</h3>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Rango</p>
            <p className="font-medium">{lunarMansion.degree_range}</p>
          </div>
        </div>
        <div className="p-4 bg-muted rounded-lg">
          <p className="text-sm leading-relaxed">{lunarMansion.description}</p>
        </div>
      </CardContent>
    </Card>
  )
}
