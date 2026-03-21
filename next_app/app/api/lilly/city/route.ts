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
      city_name,
      country,
      lat,
      lon,
      hf_score,
      delta_natal,
      domain,
      subject_name,
      asc_local,
      mc_local,
      mode,
      sr_year,
      lang,
      natalData,
    } = body;

    const isSR = mode === 'solar_return';
    const contextLines = [
      isSR
        ? `El usuario ha seleccionado ${city_name ?? '—'} (${country ?? '—'}) en el mapa de Retorno Solar ${sr_year ?? '—'}.`
        : `El usuario ha seleccionado ${city_name ?? '—'} (${country ?? '—'}) para análisis de relocalización.`,
      `Sujeto: ${subject_name ?? 'Anónimo'}`,
      `Coordenadas: ${lat != null ? lat.toFixed(2) : '—'}°, ${lon != null ? lon.toFixed(2) : '—'}°`,
      `HF en ${city_name}: ${hf_score != null ? hf_score.toFixed(3) : '—'} (Δ natal: ${delta_natal != null ? (delta_natal >= 0 ? '+' : '') + delta_natal.toFixed(3) : '—'})`,
      `Dominio activo: ${domain ?? 'global'}`,
    ];
    if (asc_local) contextLines.push(`ASC local: ${asc_local}`);
    if (mc_local) contextLines.push(`MC local: ${mc_local}`);
    contextLines.push(`Idioma de respuesta: ${lang ?? 'es'}`);

    const baseCtx = buildBaseContext(natalData);
    const contextBlock = baseCtx
      ? `${baseCtx}\n\n---\n\n${contextLines.join('\n')}`
      : contextLines.join('\n');

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
    console.error('[lilly/city]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
