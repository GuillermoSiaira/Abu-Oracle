import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT, buildBaseContext } from '../../../../lib/lilly-prompt';

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
      natalData,
    } = body;

    const lines = [
      `El usuario activó el dominio ${domain?.toUpperCase() ?? '—'} — Casa ${house_num ?? '—'}.`,
      `Sujeto: ${subject_name ?? 'Anónimo'}`,
      Array.isArray(significators) && significators.length
        ? `Significadores de la casa: ${significators.join(', ')}`
        : null,
      hf_current != null
        ? `HF del dominio en lugar natal (proxy): ${hf_current.toFixed(3)}`
        : null,
      hf_max != null
        ? `HF máximo en la grilla para este dominio: ${hf_max.toFixed(3)}`
        : null,
      best_city
        ? `Mejor ciudad para este dominio: ${best_city}`
        : null,
      `Idioma de respuesta: ${lang ?? 'es'}`,
    ].filter(Boolean);
    const baseCtx = buildBaseContext(natalData);
    const contextBlock = baseCtx
      ? `${baseCtx}\n\n---\n\n${lines.join('\n')}`
      : lines.join('\n');

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
    console.error('[lilly/domain]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
