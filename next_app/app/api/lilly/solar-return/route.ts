import type Anthropic from "@anthropic-ai/sdk";
import { NextResponse } from 'next/server';
import { getAnthropicClient } from '../../../../lib/anthropic-client';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';
import {
  buildNatalContext,
  buildActiveContext,
  assembleContextBlock,
  type BiographicalTimeline,
} from '../../../../lib/context-builder';

export const dynamic = 'force-dynamic';
import { completeLilly } from '../../../../lib/lilly-complete';
import { chartKeyFromBirthData, logInterpretation } from '../../../../lib/interpretation-logger';
import { logLillyUsage } from '../../../../lib/lilly-usage-logger';
import { getUserIdFromRequest } from '../../../../lib/get-user-id';
import { selectModel } from '../../../../lib/selectModel';
import { applyRateLimit } from '../../../../lib/usage-limiter';

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections: [],
  firdaria: [],
  transits_window: [],
};

export async function POST(req: Request) {
  try {
    const limitRes = await applyRateLimit(req);
    if (limitRes) return limitRes;

    const body = await req.json();
    const {
      domain,
      house_num,
      significators,
      hf_current,
      hf_max,
      best_city,
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
      activeCity:    null,
      lastEventType: 'sr_domain_select',
      triggerData:   { domain, house_num, significators, hf_current, hf_max, best_city, sr_year, active_domain, active_domain_house },
    });
    const block = assembleContextBlock(natal, timeline ?? EMPTY_TIMELINE, active, lang ?? 'es');

    const history: Anthropic.MessageParam[] = (messages ?? [])
      .filter((m: any) => m.role && m.content?.trim())
      .map((m: any) => ({ role: m.role as 'user' | 'assistant', content: m.content as string }));

    while (history.length > 0 && history[0].role !== 'user') {
      history.shift();
    }

    const { model } = selectModel('solar-return', 'genesis');
    const client = getAnthropicClient();
    const { text, usage } = await completeLilly(client, {
      model,
      max_tokens: 1024,
      system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
      messages: [...history, { role: 'user', content: block }],
    });
    const userId = await getUserIdFromRequest(req).catch(() => null);
    logLillyUsage('solar-return', model, usage, userId);
    logInterpretation({
      route: 'solar-return',
      eventType: body.eventType ?? 'sr_domain_select',
      inputTokens: usage.input_tokens,
      outputTokens: usage.output_tokens,
      costUsd: 0,
      continuations: usage.continuations,
      userId: userId ?? undefined,
      chartKey: chartKeyFromBirthData(birthData),
      lang: lang ?? 'es',
      condition: 'A',
    });
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/solar-return]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
