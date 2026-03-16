import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';

export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'ANTHROPIC_API_KEY not configured' }, { status: 503 });
  }

  try {
    const body = await req.json();
    const {
      planet_name,
      lon,
      sign,
      house,
      dignity,
      dignity_score,
      retrograde,
      subject_name,
      closest_aspect,
      lang,
    } = body;

    const degInSign = ((lon % 360) + 360) % 360 % 30;
    const deg = Math.floor(degInSign);
    const min = Math.round((degInSign - deg) * 60);
    const scoreStr = dignity_score > 0 ? `+${dignity_score}` : `${dignity_score}`;

    const contextLines = [
      `El usuario ha seleccionado ${planet_name} en la carta natal de ${subject_name ?? 'Anónimo'}.`,
      `Posición: ${sign} ${deg}°${String(min).padStart(2,'0')}', Casa ${house ?? '—'}`,
      `Dignidad: ${dignity} (score: ${scoreStr})`,
    ];
    if (retrograde) contextLines.push(`${planet_name} está retrógrado.`);
    if (closest_aspect) {
      contextLines.push(
        `Aspecto más exacto: ${closest_aspect.type} con ${closest_aspect.planet} (orb ${closest_aspect.orb.toFixed(1)}°)`
      );
    }
    contextLines.push(`Idioma de respuesta: ${lang ?? 'es'}`);

    const contextBlock = contextLines.join('\n');

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
    console.error('[lilly/planet]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
