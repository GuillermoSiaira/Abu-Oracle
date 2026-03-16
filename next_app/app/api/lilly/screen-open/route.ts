import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';

export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: 'ANTHROPIC_API_KEY not configured' },
      { status: 503 }
    );
  }

  try {
    const body = await req.json();
    const {
      name,
      sect,
      sect_master,
      asc_ruler,
      asc_ruler_dignity,
      mc_ruler,
      mc_ruler_dignity,
      strong_dignities,
      firdaria_major,
      firdaria_minor,
      lang,
    } = body;

    const contextBlock = [
      `Sujeto: ${name || 'Anónimo'}`,
      `Secta: ${sect || '—'}`,
      `Maestro de secta: ${sect_master || '—'}`,
      `Regente ASC: ${asc_ruler || '—'} (${asc_ruler_dignity || 'Peregrine'})`,
      `Regente MC: ${mc_ruler || '—'} (${mc_ruler_dignity || 'Peregrine'})`,
      `Dignidades fuertes: ${
        Array.isArray(strong_dignities) && strong_dignities.length
          ? strong_dignities
              .map((d: { planet: string; dignity: string }) => `${d.planet} en ${d.dignity}`)
              .join(', ')
          : 'ninguna destacada'
      }`,
      `Firdaria actual: mayor ${firdaria_major || '—'} · menor ${firdaria_minor || '—'}`,
      `Idioma de respuesta: ${lang || 'es'}`,
    ].join('\n');

    const client = new Anthropic({ apiKey });
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 512,
      system: LILLY_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: contextBlock }],
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[screen-open]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
