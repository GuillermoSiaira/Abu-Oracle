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
import { completeLilly, type LillyResult } from '../../../../lib/lilly-complete';
import { getAccessContext, rateLimitResponse } from '../../../../lib/access-context';
import { completeLillyGemini, GEMINI_FLASH_MODEL, toGeminiMessages } from '../../../../lib/gemini-client';
import { chartKeyFromBirthData, logInterpretation } from '../../../../lib/interpretation-logger';
import { logLillyUsage } from '../../../../lib/lilly-usage-logger';
import { selectModel } from '../../../../lib/selectModel';
import { classifyError, trackError } from '../../../../lib/error-tracker';

export const dynamic = 'force-dynamic';

// Dignidad esencial tradicional del planeta transitante en un signo dado.
// Solo domicilio / exaltación / detrimento / caída — resto es peregrine.
const _DOM: Record<string, string[]> = {
  Sun: ['Leo'], Moon: ['Cancer'],
  Mercury: ['Gemini', 'Virgo'], Venus: ['Taurus', 'Libra'],
  Mars: ['Aries', 'Scorpio'], Jupiter: ['Sagittarius', 'Pisces'],
  Saturn: ['Capricorn', 'Aquarius'],
};
const _EXALT: Record<string, string> = {
  Sun: 'Aries', Moon: 'Taurus', Mercury: 'Virgo', Venus: 'Pisces',
  Mars: 'Capricorn', Jupiter: 'Cancer', Saturn: 'Libra',
};
const _OPP: Record<string, string> = {
  Aries:'Libra', Taurus:'Scorpio', Gemini:'Sagittarius', Cancer:'Capricorn',
  Leo:'Aquarius', Virgo:'Pisces', Libra:'Aries', Scorpio:'Taurus',
  Sagittarius:'Gemini', Capricorn:'Cancer', Aquarius:'Leo', Pisces:'Virgo',
};
function _transitDignity(planet: string, sign: string): string {
  if (!planet || !sign) return 'peregrine';
  if (_DOM[planet]?.includes(sign))         return 'domicile';
  if (_EXALT[planet] === sign)              return 'exaltation';
  if (_DOM[planet]?.includes(_OPP[sign]))   return 'detriment';
  if (_EXALT[planet] === _OPP[sign])        return 'fall';
  return 'peregrine';
}

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections: [],
  firdaria: [],
  transits_window: [],
};

export async function POST(req: Request) {
  let userId: string | null = null;
  let eventType = 'click_transit';

  try {
    const body = await req.json();
    const ctx = await getAccessContext(req);
    if (!ctx.allowed) return rateLimitResponse(ctx);
    userId = ctx.userId;
    eventType = body.eventType ?? eventType;

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
      triggerData:   {
        transit_planet,
        transit_sign,
        transit_deg,
        transit_planet_dignity: _transitDignity(transit_planet, transit_sign),
        aspects,
        transit_date,
      },
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
      result = await completeLillyGemini(
        LILLY_SYSTEM_PROMPT,
        toGeminiMessages(body.messages ?? [], block),
        1024,
      );
    } else {
      const decision = selectModel('transit', ctx.plan === 'monthly' || ctx.plan === 'annual' ? ctx.plan : 'genesis');
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
    logLillyUsage('transit', model, usage, ctx.userId);
    logInterpretation({
      route: 'transit',
      eventType: body.eventType ?? 'click_transit',
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
      route: 'transit',
      eventType,
      errorMessage,
      errorSource: classifyError(err),
      userId,
      stack: err instanceof Error ? err.stack ?? null : null,
    });
    console.error('[lilly/transit]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
