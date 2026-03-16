import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';

export const dynamic = 'force-dynamic';

const SYSTEM_PROMPT = `Eres Lilly, el agente interpretativo de Abu Oracle.
Tu voz es la de William Lilly en Christian Astrology: precisa, directa, sin oscurantismo.
Recibirás datos sobre un dominio vital seleccionado en el mapa de relocalización.
Produce una interpretación en 3-4 líneas máximo.
No describas los hechos — el Context Builder ya lo hizo. Interpreta.
No uses disclaimers ni lenguaje de autoayuda.
Responde en el idioma del campo lang del contexto.

Marco doctrinal:
- Prioridad del señor de casa sobre planetas en casa (Abu Mashar)
- Angularidad como condición de activación (helenístico)
- Dignidades esenciales como calidad de expresión (persa medieval)
- HF como campo de resonancia geográfica, no de predicción`;

export async function POST(req: Request) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'ANTHROPIC_API_KEY not configured' }, { status: 503 });
  }

  try {
    const body = await req.json();
    const {
      domain,
      house_num,
      subject_name,
      significators,
      hf_current,
      hf_max,
      best_city,
      lang,
    } = body;

    const contextBlock = [
      `El usuario activó el dominio ${domain?.toUpperCase() ?? '—'} — Casa ${house_num ?? '—'}.`,
      `Sujeto: ${subject_name ?? 'Anónimo'}`,
      `Significadores de la casa: ${Array.isArray(significators) && significators.length ? significators.join(', ') : '—'}`,
      `HF del dominio en ubicación actual: ${hf_current != null ? hf_current.toFixed(3) : '—'}`,
      `HF máximo en la grilla: ${hf_max != null ? hf_max.toFixed(3) : '—'}`,
      `Mejor ciudad para este dominio: ${best_city ?? '—'}`,
      `Idioma de respuesta: ${lang ?? 'es'}`,
    ].join('\n');

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
    console.error('[lilly/domain]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
