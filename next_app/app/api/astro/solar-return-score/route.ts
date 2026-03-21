/**
 * /api/astro/solar-return-score
 *
 * HF escalar por ciudad modulado por Firdaria, para comparación de Retorno Solar.
 *
 * DISTINTO de:
 *   /api/astro/solar-return       → carta SR completa para una ciudad (planetas, casas, aspectos)
 *   /api/astro/sr-relocation-field → grilla global de heatmap (9425 puntos, sin filtro Firdaria)
 *
 * ESTE endpoint (Axioma 8.3 — dos dimensiones ortogonales):
 *   - Dimensión temporal: Firdaria activa en la fecha del SR (cuándo / con qué planetas)
 *   - Dimensión semántica: dominio elegido por el usuario (para qué propósito)
 *   - planet_subset = UNION(firdaria_planets, house_significators(natal, domain))
 *   - Devuelve un score HF escalar por ciudad para comparación directa
 *
 * Body:  { birthDate, birthLat, birthLon, sr_year?, domain?, cities: [{id, lat, lon}] }
 *   domain: 'h1'|'h2'|'h4'|'h5'|'h6'|'h7'|'h9'|'h10'|'global'
 * Response: { firdaria: {major, minor, major_dignity, major_dignity_score},
 *             sr_date, scores: [{id, hf_sr}] }
 */

import { NextResponse } from 'next/server';
import { getAbuAuthHeaders } from '@/lib/abu-auth';
import { ABU_BASE_URL } from '@/services/abu';

export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const headers = await getAbuAuthHeaders({ 'Content-Type': 'application/json' });
    const res = await fetch(`${ABU_BASE_URL}/api/astro/solar-return-score`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err: any) {
    console.error('[solar-return-score]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
