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
    const {
      city_name,
      country,
      lat,
      lon,
      hf_score,
      delta_natal,
      domain,
      asc_local,
      mc_local,
      mode,
      sr_year,
      active_domain,
      active_domain_house,
      lang,
      natalData,
      birthData,
      timeline,
      messages,
    } = body;

    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:   new Date().toISOString(),
      activeTab:     'hf_map',
      activeDomain:  active_domain ?? domain ?? null,
      activeCity:    city_name && lat != null && lon != null && hf_score != null
        ? { name: city_name, lat, lon, hf_score }
        : null,
      lastEventType: 'city_select',
      triggerData:   {
        city_name, country, lat, lon, hf_score, delta_natal,
        domain, asc_local, mc_local, mode, sr_year,
        active_domain, active_domain_house,
      },
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
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 1024,
      system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
      messages: [...history, { role: 'user', content: block }],
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/city]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
