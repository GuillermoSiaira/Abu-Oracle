import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';
import {
  buildNatalContext,
  buildActiveContext,
  assembleContextBlock,
  type BiographicalTimeline,
} from '../../../../lib/context-builder';
import { applyRateLimit } from '../../../../lib/usage-limiter';
import { completeLilly } from '../../../../lib/lilly-complete';

export const dynamic = 'force-dynamic';

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections: [],
  firdaria: [],
  transits_window: [],
};

export async function POST(req: Request) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'ANTHROPIC_API_KEY not configured' }, { status: 503 });
  }

  try {
    const limitResponse = await applyRateLimit(req);
    if (limitResponse) return limitResponse;

    const body = await req.json();
    const { technique, data, subject_name, lang, natalData, birthData, timeline, messages } = body;

    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:   new Date().toISOString(),
      activeTab:     'persian_techniques',
      activeDomain:  null,
      activeCity:    null,
      lastEventType: 'click_technique',
      triggerData:   { technique, ...data },
    });
    const block = assembleContextBlock(natal, timeline ?? EMPTY_TIMELINE, active, lang ?? 'es');

    const history: Anthropic.MessageParam[] = (messages ?? [])
      .filter((m: any) => m.role && m.content?.trim())
      .map((m: any) => ({ role: m.role as 'user' | 'assistant', content: m.content as string }));

    while (history.length > 0 && history[0].role !== 'user') {
      history.shift();
    }

    const maxTokens =
      ['lunar_transit', 'planetary_cycle'].includes(technique) ? 1536
      : ['lot', 'sect', 'profection', 'firdaria'].includes(technique) ? 2048
      : 1024;

    const client = new Anthropic({ apiKey });
    const text = await completeLilly(client, {
      model: 'claude-haiku-4-5-20251001',
      max_tokens: maxTokens,
      system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
      messages: [...history, { role: 'user', content: block }],
    });
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/technique]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
