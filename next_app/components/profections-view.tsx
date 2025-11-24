'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/simple-card"

interface Profection {
  current_year: number
  profected_house: number
  profected_sign: string
  lord_of_year: string
  description: string
}

interface ProfectionsViewProps {
  profections: Profection
}

export function ProfectionsView({ profections }: ProfectionsViewProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-serif">Profecciones Anuales</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 border border-primary/20 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Año Actual</p>
            <p className="text-2xl font-bold text-primary">{profections.current_year}</p>
          </div>
          <div className="text-center p-4 border border-primary/20 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Casa Profectada</p>
            <p className="text-2xl font-bold text-primary">{profections.profected_house}</p>
          </div>
          <div className="text-center p-4 border border-primary/20 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Signo Profectado</p>
            <p className="text-2xl font-bold text-primary">{profections.profected_sign}</p>
          </div>
          <div className="text-center p-4 border border-primary/20 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Señor del Año</p>
            <p className="text-2xl font-bold text-primary">{profections.lord_of_year}</p>
          </div>
        </div>
        <div className="p-4 bg-muted rounded-lg">
          <p className="text-sm leading-relaxed">{profections.description}</p>
        </div>
      </CardContent>
    </Card>
  )
}
