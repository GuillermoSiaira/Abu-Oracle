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
  profections: [],
  firdaria: [],
  transits_window: [],
};

export async function POST(req: Request) {
  let userId: string | null = null;
  let eventType = 'click_technique';

  try {
    const ctx = await getAccessContext(req);
    if (!ctx.allowed) return rateLimitResponse(ctx);
    userId = ctx.userId;

    const body = await req.json();
    eventType = body.eventType ?? body.data?.technique ?? eventType;
    const { technique, data, subject_name, lang, natalData, birthData, timeline, messages } = body;

    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:    new Date().toISOString(),
      activeTab:      'persian_techniques',
      activeDomain:   null,
      activeCity:     null,
      lastEventType:  'click_technique',
      triggerData:    { technique, ...data },
      utcOffsetHours: (birthData as any)?.utcOffset ?? undefined,
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
      : ['lot', 'firdaria'].includes(technique) ? 768
      : ['sect', 'profection'].includes(technique) ? 2048
      : 1024;

    let result: LillyResult;
    let model: string;

    if (ctx.provider === 'gemini') {
      model = GEMINI_FLASH_MODEL;
      const system = `${LILLY_SYSTEM_PROMPT}\n\n${block}`;
      result = await completeLillyGemini(
        system,
        toGeminiMessages(body.messages ?? [], ''),
        maxTokens,
      );
    } else {
      const decision = selectModel('technique', ctx.plan === 'monthly' || ctx.plan === 'annual' ? ctx.plan : 'genesis');
      model = decision.model;
      const client = getAnthropicClient();
      result = await completeLilly(client, {
        model,
        max_tokens: maxTokens,
        system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
        messages: [...history, { role: 'user', content: block }],
      });
    }

    const { text, usage } = result;
    logLillyUsage('technique', model, usage, ctx.userId);
    logInterpretation({
      route: 'technique',
      eventType: body.eventType ?? data?.technique ?? 'click_technique',
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
      route: 'technique',
      eventType,
      errorMessage,
      errorSource: classifyError(err),
      userId,
      stack: err instanceof Error ? err.stack ?? null : null,
    });
    console.error('[lilly/technique]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
