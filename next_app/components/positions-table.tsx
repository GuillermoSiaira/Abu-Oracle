'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/simple-card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/simple-table"
import { Badge } from "@/components/ui/simple-badge"

interface Planet {
  name: string
  longitude: number
  sign: string
  house?: number
  dignity?: string
  dignity_score?: number
  retrograde?: boolean
}

interface PositionsTableProps {
  planets: Planet[]
}

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

const DIGNITY_INFO: Record<string, { icon: string; color: string; description: string }> = {
  Domicilio:   { icon: '🔆', color: 'text-yellow-600', description: 'Fuerte y coherente' },
  Exaltación:  { icon: '⭐', color: 'text-yellow-500', description: 'Potencia elevada' },
  Peregrino:   { icon: '⚪', color: 'text-blue-400', description: 'Neutral, adaptable' },
  Caída:       { icon: '🔻', color: 'text-orange-700', description: 'Debilidad' },
  Exilio:      { icon: '❌', color: 'text-red-600', description: 'Tensión, desafíos' },
}

export function PositionsTable({ planets }: PositionsTableProps) {
  const formatDegree = (longitude: number, sign: string) => {
    const degreeInSign = longitude % 30
    return `${Math.floor(degreeInSign)}° ${sign}`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-serif">Posiciones Planetarias</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Planeta</TableHead>
              <TableHead>Posición</TableHead>
              <TableHead>Longitud</TableHead>
              <TableHead>Casa</TableHead>
              <TableHead>Dignidad</TableHead>
              <TableHead>Score</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {planets.map((planet) => {
              const dignityInfo = planet.dignity ? DIGNITY_INFO[planet.dignity] : null

              return (
                <TableRow key={planet.name}>
                  <TableCell className="font-medium">
                    <span className="text-xl mr-2">{PLANET_SYMBOLS[planet.name]}</span>
                    {planet.name}
                    {planet.retrograde && <span className="ml-2 text-xs text-muted-foreground">℞</span>}
                  </TableCell>

                  <TableCell>{formatDegree(planet.longitude, planet.sign)}</TableCell>

                  <TableCell className="text-muted-foreground">
                    {planet.longitude.toFixed(2)}°
                  </TableCell>

                  <TableCell>{planet.house || '-'}</TableCell>

                  <TableCell>
                    {dignityInfo ? (
                      <Badge
                        variant="solid"
                        className={`border-0 ${dignityInfo.color}`}
                      >
                        {dignityInfo.icon} {planet.dignity}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>

                  <TableCell>
                    <span
                      className={
                        planet.dignity_score && planet.dignity_score > 0
                          ? "text-green-500"
                          : "text-muted-foreground"
                      }
                    >
                      {planet.dignity_score !== undefined
                        ? `+${planet.dignity_score}`
                        : '-'}
                    </span>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
