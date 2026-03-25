import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';
import {
  buildNatalContext,
  buildActiveContext,
  assembleContextBlock,
  type BiographicalTimeline,
} from '../../../../lib/context-builder';
import { getUserIdFromRequest } from '../../../../lib/get-user-id';
import { getRecentHistory, formatMemoryForPrompt } from '../../../../lib/chat-memory';

export const dynamic = 'force-dynamic';

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections: [],
  firdaria: [],
  transits_window: [],
};

const SUGGESTIONS_SUFFIX = [
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
      lang,
      natalData,
      birthData,
      timeline,
      messages,
    } = body;

    // ── Memoria biográfica (si el usuario está autenticado) ──────────────────
    const userId = await getUserIdFromRequest(req);
    const memoryCtx = userId ? await getRecentHistory(userId) : null;
    const memoryBlock = memoryCtx ? formatMemoryForPrompt(memoryCtx) : '';

    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:   new Date().toISOString(),
      activeTab:     'persian_techniques',
      activeDomain:  null,
      activeCity:    null,
      lastEventType: 'screen_open',
      triggerData:   { name, sect, sect_master },
    });
    const block =
      assembleContextBlock(natal, timeline ?? EMPTY_TIMELINE, active, lang ?? 'es', memoryBlock || undefined)
      + '\n\n' + SUGGESTIONS_SUFFIX;

    const history: Anthropic.MessageParam[] = (messages ?? [])
      .filter((m: any) => m.role && m.content?.trim())
      .map((m: any) => ({ role: m.role as 'user' | 'assistant', content: m.content as string }));

    // Anthropic requires conversation to start with a user message
    while (history.length > 0 && history[0].role !== 'user') {
      history.shift();
    }

    const client = new Anthropic({ apiKey });
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      system: LILLY_SYSTEM_PROMPT,
      messages: [...history, { role: 'user', content: block }],
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
