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
import { getAccessContext, rateLimitResponse } from '../../../../lib/access-context';
import { completeLilly, type LillyResult } from '../../../../lib/lilly-complete';
import { completeLillyGemini, GEMINI_FLASH_MODEL, toGeminiMessages } from '../../../../lib/gemini-client';
import { chartKeyFromBirthData, logInterpretation } from '../../../../lib/interpretation-logger';
import { logLillyUsage } from '../../../../lib/lilly-usage-logger';
import { selectModel } from '../../../../lib/selectModel';
import { classifyError, trackError } from '../../../../lib/error-tracker';

export const dynamic = 'force-dynamic';

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections:     [],
  firdaria:        [],
  transits_window: [],
};

export async function POST(req: Request) {
  let userId: string | null = null;
  let eventType = 'click_house';

  try {
    const ctx = await getAccessContext(req);
    if (!ctx.allowed) return rateLimitResponse(ctx);
    userId = ctx.userId;

    const body = await req.json();
    eventType = body.eventType ?? eventType;
    const {
      house_num,
      cusp_sign,
      house_lord,
      occupants,
      subject_name,
      lang,
      natalData,
      birthData,
      timeline,
      messages,
    } = body;

    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:   new Date().toISOString(),
      activeTab:     'natal_chart',
      activeDomain:  null,
      activeCity:    null,
      lastEventType: 'click_house',
      triggerData:   { house_num, cusp_sign, house_lord, occupants, subject_name },
    });
    const block = assembleContextBlock(natal, timeline ?? EMPTY_TIMELINE, active, lang ?? 'es');

    const history: Anthropic.MessageParam[] = (messages ?? [])
      .filter((m: any) => m.role && m.content?.trim())
      .map((m: any) => ({ role: m.role as 'user' | 'assistant', content: m.content as string }));

    while (history.length > 0 && history[0].role !== 'user') {
      history.shift();
    }

    let result: LillyResult;
    let model: string;

    if (ctx.provider === 'gemini') {
      model = GEMINI_FLASH_MODEL;
      const system = `${LILLY_SYSTEM_PROMPT}\n\n${block}`;
      result = await completeLillyGemini(
        system,
        toGeminiMessages(body.messages ?? [], ''),
        1024,
      );
    } else {
      const decision = selectModel('house', ctx.plan === 'monthly' || ctx.plan === 'annual' ? ctx.plan : 'genesis');
      model = decision.model;
      const client = getAnthropicClient();
      result = await completeLilly(client, {
        model,
        max_tokens: 1024,
        system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
        messages: [...history, { role: 'user', content: block }],
      });
    }

    const { text, usage } = result;
    logLillyUsage('house', model, usage, ctx.userId);
    logInterpretation({
      route: 'house',
      eventType: body.eventType ?? 'click_house',
      provider: ctx.provider,
      model,
      inputTokens: usage.input_tokens,
      outputTokens: usage.output_tokens,
      costUsd: 0,
      continuations: usage.continuations,
      userId: ctx.userId ?? undefined,
      chartKey: chartKeyFromBirthData(birthData),
      lang: lang ?? 'es',
      condition: 'A',
    });
    return NextResponse.json({ response: text });
  } catch (err: any) {
    const errorMessage = err instanceof Error ? err.message : String(err);
    trackError({
      route: 'house',
      eventType,
      errorMessage,
      errorSource: classifyError(err),
      userId,
      stack: err instanceof Error ? err.stack ?? null : null,
    });
    console.error('[lilly/house]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
