'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/simple-card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/simple-table"

interface House {
  number: number
  cusp_longitude: number
  sign: string
  ruler: string
}

interface HousesTableProps {
  houses: House[]
}

const HOUSE_MEANINGS: Record<number, string> = {
  1: 'Identidad y apariencia',
  2: 'Recursos y valores',
  3: 'Comunicación y hermanos',
  4: 'Hogar y familia',
  5: 'Creatividad y placer',
  6: 'Salud y servicio',
  7: 'Relaciones y matrimonio',
  8: 'Transformación y legados',
  9: 'Filosofía y viajes',
  10: 'Carrera y reputación',
  11: 'Amistades y aspiraciones',
  12: 'Espiritualidad y reclusión',
}

export function HousesTable({ houses }: HousesTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-serif">Casas Astrológicas</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Casa</TableHead>
              <TableHead>Cúspide</TableHead>
              <TableHead>Signo</TableHead>
              <TableHead>Regente</TableHead>
              <TableHead>Significado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {houses.map((house) => (
              <TableRow key={house.number}>
                <TableCell className="font-bold">{house.number}</TableCell>
                <TableCell className="text-muted-foreground">{house.cusp_longitude.toFixed(2)}°</TableCell>
                <TableCell>{house.sign}</TableCell>
                <TableCell>{house.ruler}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {HOUSE_MEANINGS[house.number]}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
