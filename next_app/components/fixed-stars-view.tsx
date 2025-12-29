'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/simple-card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/simple-table"

interface FixedStar {
  name: string
  longitude: number
  latitude: number
  magnitude: number
  nature: string
  conjunct_planet?: string
  orb?: number
}

interface FixedStarsViewProps {
  fixedStars?: FixedStar[]
}

export function FixedStarsView({ fixedStars }: FixedStarsViewProps) {
  if (!fixedStars || fixedStars.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="font-serif">Estrellas Fijas</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No hay conjunciones con estrellas fijas significativas</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-serif">Estrellas Fijas</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Estrella</TableHead>
              <TableHead>Longitud</TableHead>
              <TableHead>Magnitud</TableHead>
              <TableHead>Naturaleza</TableHead>
              <TableHead>Conjunción</TableHead>
              <TableHead>Orbe</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {fixedStars.map((star) => (
              <TableRow key={star.name}>
                <TableCell className="font-medium">{star.name}</TableCell>
                <TableCell>{star.longitude.toFixed(2)}°</TableCell>
                <TableCell>{star.magnitude.toFixed(1)}</TableCell>
                <TableCell className="text-sm">{star.nature}</TableCell>
                <TableCell>{star.conjunct_planet || '-'}</TableCell>
                <TableCell>{star.orb ? `${star.orb.toFixed(2)}°` : '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
