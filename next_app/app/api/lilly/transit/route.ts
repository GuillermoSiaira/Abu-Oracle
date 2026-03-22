import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';
import {
  buildNatalContext,
  buildActiveContext,
  assembleContextBlock,
  type BiographicalTimeline,
} from '../../../../lib/context-builder';

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
    const body = await req.json();
    const {
      transit_planet,
      transit_sign,
      transit_deg,
      aspects,
      transit_date,
      lang,
      natalData,
      birthData,
      timeline,
      messages,
    } = body;

    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:   transit_date ?? new Date().toISOString(),
      activeTab:     'transits',
      activeDomain:  null,
      activeCity:    null,
      lastEventType: 'click_transit',
      triggerData:   { transit_planet, transit_sign, transit_deg, aspects, transit_date },
    });
    const block = assembleContextBlock(natal, timeline ?? EMPTY_TIMELINE, active, lang ?? 'es');

    const history: Anthropic.MessageParam[] = (messages ?? [])
      .filter((m: any) => m.role && m.content?.trim())
      .map((m: any) => ({ role: m.role as 'user' | 'assistant', content: m.content as string }));

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

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/transit]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
