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
      system: LILLY_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: contextBlock }],
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/domain]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
