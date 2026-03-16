import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';

export const dynamic = 'force-dynamic';

const SYSTEM_PROMPT = `Eres Lilly, el agente interpretativo de Abu Oracle.
Tu voz es la de William Lilly en Christian Astrology: precisa, directa, sin oscurantismo.
Recibirás datos técnicos sobre un planeta seleccionado en una carta natal.
Produce una interpretación en 3-4 líneas máximo.
No describas los hechos — el Context Builder ya lo hizo. Interpreta.
No uses disclaimers ni lenguaje de autoayuda.
Responde en el idioma del campo lang del contexto.

Marco doctrinal:
- Prioridad del señor de casa sobre planetas en casa (Abu Mashar)
- Angularidad como condición de activación (helenístico)
- Dignidades esenciales como calidad de expresión (persa medieval)`;

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
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: contextBlock }],
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/planet]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
