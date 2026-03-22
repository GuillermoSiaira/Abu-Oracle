import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT, buildBaseContext } from '../../../../lib/lilly-prompt';

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
      natalData,
    } = body;

    const baseCtx = buildBaseContext(natalData);

    const screenOpenBlock = [
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
      `Fecha actual: ${new Date().toISOString().split('T')[0]}`,
      `Idioma de respuesta: ${lang || 'es'}`,
      ``,
      `Al final de tu interpretación, añade exactamente este bloque sin modificarlo:`,
      ``,
      `[SUGERENCIAS]`,
      `{"suggestions": [`,
      `  {"type": "click_planet"|"click_technique"|"click_domain", "target": string, "label": string},`,
      `  ...`,
      `]}`,
      ``,
      `Elige los 3 elementos más significativos de esta carta para sugerir.`,
      `Priorizar: planetas angulares, planetas en domicilio/exaltación, señor del año, señor del ASC.`,
      `Para click_domain usar: h1, h2, h4, h5, h6, h7, h9, h10.`,
      `Para click_technique usar: sect, profection, firdaria, lot_fortuna, lot_spirit.`,
      `Para click_planet usar el nombre del planeta en inglés (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn).`,
    ].join('\n');

    const contextBlock = baseCtx
      ? `${baseCtx}\n\n---\n\n${screenOpenBlock}`
      : screenOpenBlock;

    const client = new Anthropic({ apiKey });
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      system: LILLY_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: contextBlock }],
    });

    const rawText = response.content[0].type === 'text' ? response.content[0].text : '';

    // Parse [SUGERENCIAS] block from the end of the response
    let text = rawText;
    let suggestions: Array<{ type: string; target: string; label: string }> = [];
    const sugMarker = '[SUGERENCIAS]';
    const sugIdx = rawText.indexOf(sugMarker);
    if (sugIdx !== -1) {
      text = rawText.slice(0, sugIdx).trim();
      const jsonStr = rawText.slice(sugIdx + sugMarker.length).trim();
      try {
        const parsed = JSON.parse(jsonStr);
        if (Array.isArray(parsed.suggestions)) {
          suggestions = parsed.suggestions;
        }
      } catch {
        // If JSON is malformed, suggestions stay empty — not fatal
      }
    }

    return NextResponse.json({ response: text, suggestions });
  } catch (err: any) {
    console.error('[screen-open]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
