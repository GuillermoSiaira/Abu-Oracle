import { NextResponse } from 'next/server';
import { getAnthropicClient } from '../../../../lib/anthropic-client';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';
import {
  buildNatalContext,
  buildActiveContext,
  assembleContextBlock,
  type BiographicalTimeline,
} from '../../../../lib/context-builder';
import { applyRateLimit } from '../../../../lib/usage-limiter';
import { getUserIdFromRequest } from '../../../../lib/get-user-id';
import { completeLilly } from '../../../../lib/lilly-complete';
import { logLillyUsage } from '../../../../lib/lilly-usage-logger';
import { selectModel } from '../../../../lib/selectModel';

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
  try {
    const limitResponse = await applyRateLimit(req);
    if (limitResponse) return limitResponse;

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

    const { model } = selectModel('transit', 'genesis');
    const client = getAnthropicClient();
    const { text, usage } = await completeLilly(client, {
      model,
      max_tokens: 1024,
      system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
      messages: [...history, { role: 'user', content: block }],
    });
        logLillyUsage('transit', model, usage, await getUserIdFromRequest(req).catch(() => null));
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/transit]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
