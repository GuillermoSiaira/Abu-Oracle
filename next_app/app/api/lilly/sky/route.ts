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
  firdaria:    [],
  transits_window: [],
};

/** Formatea tránsitos rápidos activos para el contextBlock del cielo de hoy. */
function _formatFastTransits(
  transits_window: BiographicalTimeline['transits_window']
): string {
  const fast = transits_window.filter(
    t => t.is_active && (t.speed_class === 'fast' || t.speed_class === 'lunar')
  );
  if (fast.length === 0) return 'Sin tránsitos rápidos activos en este momento.';
  return fast
    .map(t => {
      const dir = t.ingress_date ? `ingresó ${t.ingress_date.slice(0, 10)}` : '';
      return `- ${t.transit_planet} ${t.aspect} ${t.natal_planet}${dir ? ' · ' + dir : ''}`;
    })
    .join('\n');
}

/** Formatea tránsitos lentos activos de alta intensidad (conjunciones/oposiciones). */
function _formatSlowTransits(
  transits_window: BiographicalTimeline['transits_window']
): string {
  const slow = transits_window.filter(
    t => t.is_active && t.speed_class === 'slow' &&
         (t.aspect === 'conjunction' || t.aspect === 'opposition')
  );
  if (slow.length === 0) return '';
  return slow
    .map(t => {
      const exact = t.exact_date ? `exacto ${t.exact_date.slice(0, 10)}` : '';
      return `- ${t.transit_planet} ${t.aspect} ${t.natal_planet} [lento]${exact ? ' · ' + exact : ''}`;
    })
    .join('\n');
}

export async function POST(req: Request) {
  let userId: string | null = null;
  let eventType = 'sky_open';

  try {
    const ctx = await getAccessContext(req);
    if (!ctx.allowed) return rateLimitResponse(ctx);
    userId = ctx.userId;

    const body = await req.json();
    eventType = body.eventType ?? eventType;
    const {
      lang,
      natalData,
      birthData,
      timeline,
      messages,
    } = body;

    const tl: BiographicalTimeline = timeline ?? EMPTY_TIMELINE;

    const slowBlock = _formatSlowTransits(tl.transits_window);
    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:    new Date().toISOString(),
      activeTab:      'cielo_hoy',
      activeDomain:   null,
      activeCity:     null,
      lastEventType:  'sky_open',
      utcOffsetHours: (birthData as any)?.utcOffset ?? undefined,
      triggerData: {
        today: new Date().toISOString().slice(0, 10),
        fast_transits_active: _formatFastTransits(tl.transits_window),
        ...(slowBlock ? { slow_transits_active: slowBlock } : {}),
      },
    });
    const block = assembleContextBlock(natal, tl, active, lang ?? 'es');

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
        1536,
      );
    } else {
      const decision = selectModel('sky', ctx.plan === 'monthly' || ctx.plan === 'annual' ? ctx.plan : 'genesis');
      model = decision.model;
      const client = getAnthropicClient();
      result = await completeLilly(client, {
        model,
        max_tokens: 1536,
        system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
        messages: [...history, { role: 'user', content: block }],
      });
    }

    const { text, usage } = result;
    logLillyUsage('sky', model, usage, ctx.userId);
    logInterpretation({
      route: 'sky',
      eventType: body.eventType ?? 'sky_open',
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
      route: 'sky',
      eventType,
      errorMessage,
      errorSource: classifyError(err),
      userId,
      stack: err instanceof Error ? err.stack ?? null : null,
    });
    console.error('[lilly/sky]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
