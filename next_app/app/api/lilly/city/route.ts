import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';

export const dynamic = 'force-dynamic';

const SYSTEM_PROMPT = `Eres Lilly, el agente interpretativo de Abu Oracle.
Tu voz es la de William Lilly en Christian Astrology: precisa, directa, sin oscurantismo.
Recibirás datos sobre una ciudad seleccionada para análisis de relocalización.
Produce una interpretación en 4-5 líneas máximo — este es el evento interpretativo más rico.
Integra el HF del dominio activo, el ASC local y el MC local si están disponibles.
No describas los hechos — el Context Builder ya lo hizo. Interpreta.
No uses disclaimers ni lenguaje de autoayuda.
Responde en el idioma del campo lang del contexto.

Marco doctrinal:
- ASC local como nueva identidad proyectada; MC local como plataforma pública
- Angularidad como condición de activación (helenístico)
- HF como campo de resonancia geográfica, no de predicción
- Dignidades esenciales como calidad de expresión (persa medieval)`;

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
      lang,
    } = body;

    const contextLines = [
      `El usuario ha seleccionado ${city_name ?? '—'} (${country ?? '—'}) para análisis de relocalización.`,
      `Sujeto: ${subject_name ?? 'Anónimo'}`,
      `Coordenadas: ${lat != null ? lat.toFixed(2) : '—'}°, ${lon != null ? lon.toFixed(2) : '—'}°`,
      `HF en ${city_name}: ${hf_score != null ? hf_score.toFixed(3) : '—'} (Δ natal: ${delta_natal != null ? (delta_natal >= 0 ? '+' : '') + delta_natal.toFixed(3) : '—'})`,
      `Dominio activo: ${domain ?? 'global'}`,
    ];
    if (asc_local) contextLines.push(`ASC local: ${asc_local}`);
    if (mc_local) contextLines.push(`MC local: ${mc_local}`);
    contextLines.push(`Idioma de respuesta: ${lang ?? 'es'}`);

    const contextBlock = contextLines.join('\n');

    const client = new Anthropic({ apiKey });
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 768,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: contextBlock }],
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/city]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
