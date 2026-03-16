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
    const { technique, data, subject_name, lang } = body;

    let contextBlock = `Sujeto: ${subject_name ?? 'Anónimo'}\nIdioma de respuesta: ${lang ?? 'es'}\n\n`;

    if (technique === 'sect') {
      contextBlock += [
        `El usuario ha seleccionado la SECTA de la carta.`,
        `Secta: ${data.sect === 'diurnal' ? 'Diurna' : 'Nocturna'}`,
        `Maestro de secta: ${data.sect_master}`,
        `Dignidad del maestro: ${data.sect_master_dignity}`,
      ].join('\n');
    } else if (technique === 'profection') {
      contextBlock += [
        `El usuario ha seleccionado la PROFECCIÓN ANUAL.`,
        `Casa activada: Casa ${data.annual_house}`,
        `Signo de la cúspide: ${data.annual_sign}`,
        `Señor del año: ${data.annual_lord} (${data.annual_lord_dignity})`,
      ].join('\n');
    } else if (technique === 'firdaria') {
      contextBlock += [
        `El usuario ha seleccionado el FIRDARIA actual.`,
        `Período mayor: ${data.major_planet} (${data.major_dignity})`,
        `Sub-período: ${data.minor_planet} (${data.minor_dignity})`,
        `Período: ${data.start_date} → ${data.end_date}`,
      ].join('\n');
    } else if (technique === 'lot') {
      const lotDisplayName = data.lot_name === 'fortuna' ? 'FORTUNA' : 'ESPÍRITU';
      contextBlock += [
        `El usuario ha seleccionado la Parte de ${lotDisplayName} en la carta de ${subject_name ?? 'Anónimo'}.`,
        `Posición: ${data.sign} ${data.degree}°${data.house ? `, Casa ${data.house}` : ''}`,
        `Señor del Lote: ${data.lord} — ${data.lord_dignity}`,
      ].join('\n');
    } else if (technique === 'lunar_transit') {
      const aspectLines = Array.isArray(data.aspects) && data.aspects.length > 0
        ? data.aspects.map((a: any) => `  • ${a.type} con ${a.planet} (orbe ${a.orb?.toFixed?.(2) ?? a.orb}°)`).join('\n')
        : '  • Sin aspectos exactos';
      contextBlock += [
        `El usuario ha seleccionado el TRÁNSITO LUNAR actual.`,
        `La Luna transita en ${data.moon_position?.toFixed?.(2) ?? data.moon_position}° (${data.moon_sign ?? ''}).`,
        `Aspectos activos:`,
        aspectLines,
      ].join('\n');
    } else if (technique === 'planetary_cycle') {
      contextBlock += [
        `El usuario ha seleccionado un CICLO PLANETARIO.`,
        `Ciclo: ${data.cycle ?? data.aspect_type}`,
        `Planeta: ${data.planet} en ${data.angle}° natal`,
        `Fecha exacta: ${data.exact_date}`,
      ].join('\n');
    }

    const shortTechniques = ['lunar_transit', 'planetary_cycle'];
    const maxTokens = shortTechniques.includes(technique) ? 256 : 512;

    const client = new Anthropic({ apiKey });
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: maxTokens,
      system: LILLY_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: contextBlock }],
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/technique]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
