import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';

export const dynamic = 'force-dynamic';

const ASPECT_ES: Record<string, string> = {
  conjunction: 'Conjunción',
  opposition: 'Oposición',
  square: 'Cuadratura',
  trine: 'Trígono',
  sextile: 'Sextil',
  semisextile: 'Semisextil',
  quincunx: 'Quincuncio',
};

export async function POST(req: Request) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'ANTHROPIC_API_KEY not configured' }, { status: 503 });
  }

  try {
    const body = await req.json();
    const {
      transit_planet,
      transit_sign,
      transit_deg,
      aspects,
      transit_date,
      subject_name,
      lang,
    } = body;

    const dateLabel = transit_date
      ? new Date(transit_date).toLocaleDateString('es-AR', {
          day: '2-digit', month: '2-digit', year: 'numeric',
        })
      : '—';

    const aspectLines = Array.isArray(aspects) && aspects.length
      ? aspects.map((a: any) => {
          const aspName = ASPECT_ES[a.aspect] ?? a.aspect;
          const orbStr = Math.abs(a.orb).toFixed(2) + '°';
          const appStr = a.applying ? 'aplicante' : 'separante';
          return `- ${aspName} a ${a.natal_planet} natal (orb ${orbStr}, ${appStr})`;
        }).join('\n')
      : '- Sin aspectos registrados';

    const contextBlock = [
      `El usuario seleccionó ${transit_planet?.toUpperCase() ?? '—'} en tránsito — actualmente en ${transit_sign ?? '—'} ${transit_deg != null ? transit_deg.toFixed(1) + '°' : ''}.`,
      `Aspectos activos de este tránsito:`,
      aspectLines,
      `Fecha de tránsito: ${dateLabel}`,
      `Sujeto: ${subject_name ?? 'Anónimo'}`,
      `Idioma de respuesta: ${lang ?? 'es'}`,
    ].join('\n');

    const client = new Anthropic({ apiKey });
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      system: LILLY_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: contextBlock }],
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/transit]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
