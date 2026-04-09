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
import { getUserIdFromRequest } from '../../../../lib/get-user-id';
import { completeLilly } from '../../../../lib/lilly-complete';
import { logLillyUsage } from '../../../../lib/lilly-usage-logger';
import { selectModel } from '../../../../lib/selectModel';

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
      const orb = ''; // orb not in window shape — skipped
      const dir = t.ingress_date ? `ingresó ${t.ingress_date.slice(0, 10)}` : '';
      return `- ${t.transit_planet} ${t.aspect} ${t.natal_planet}${dir ? ' · ' + dir : ''}`;
    })
    .join('\n');
}

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
      lang,
      natalData,
      birthData,
      timeline,
      messages,
    } = body;

    const tl: BiographicalTimeline = timeline ?? EMPTY_TIMELINE;

    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:   new Date().toISOString(),
      activeTab:     'cielo_hoy',
      activeDomain:  null,
      activeCity:    null,
      lastEventType: 'sky_open',
      triggerData: {
        today: new Date().toISOString().slice(0, 10),
        fast_transits_active: _formatFastTransits(tl.transits_window),
      },
    });
    const block = assembleContextBlock(natal, tl, active, lang ?? 'es');

    const history: Anthropic.MessageParam[] = (messages ?? [])
      .filter((m: any) => m.role && m.content?.trim())
      .map((m: any) => ({ role: m.role as 'user' | 'assistant', content: m.content as string }));

    while (history.length > 0 && history[0].role !== 'user') {
      history.shift();
    }

    const { model } = selectModel('sky', 'genesis');
    const client = new Anthropic({ apiKey });
    const { text, usage } = await completeLilly(client, {
      model,
      max_tokens: 1536,
      system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
      messages: [...history, { role: 'user', content: block }],
    });
        logLillyUsage('sky', model, usage, await getUserIdFromRequest(req).catch(() => null));
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/sky]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
