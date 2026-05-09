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
import { logLillyUsage } from '../../../../lib/lilly-usage-logger';
import { selectModel } from '../../../../lib/selectModel';

export const dynamic = 'force-dynamic';

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections:     [],
  firdaria:        [],
  transits_window: [],
};

/** Formatea una configuración mundana para el contextBlock de Lilly. */
function _formatConfig(config: {
  type: string;
  label: string;
  planets: string[];
  orb: number;
  exact_date: string | null;
  p_value: number | null;
  density_ratio: number | null;
  significance: string;
}): string {
  const lines: string[] = [];
  lines.push(`Configuración: ${config.label}`);
  lines.push(`Planetas: ${config.planets.join(', ')}`);
  if (config.orb != null) lines.push(`Orbe actual: ${config.orb.toFixed(2)}°`);
  if (config.exact_date)  lines.push(`Exactitud: ${config.exact_date}`);
  if (config.p_value != null)       lines.push(`p-value (H_mundana_A): ${config.p_value}`);
  if (config.density_ratio != null) lines.push(`Densidad histórica: ${config.density_ratio}x el baseline`);
  lines.push(`Significancia: ${config.significance}`);
  return lines.join('\n');
}

/** Formatea eventos históricos de muestra. */
function _formatHistory(sampleEvents: Array<{ date: string; description: string; category: string }>): string {
  if (!sampleEvents || sampleEvents.length === 0) return '';
  return sampleEvents
    .map(ev => `- ${ev.date}: ${ev.description}${ev.category ? ` [${ev.category}]` : ''}`)
    .join('\n');
}

export async function POST(req: Request) {
  try {
    const ctx = await getAccessContext(req);
    if (!ctx.allowed) return rateLimitResponse(ctx);

    const body = await req.json();
    const {
      config,          // objeto de configuración mundana activa
      historyContext,  // { sample_events, density_ratio, p_value }
      lang,
      natalData,
      birthData,
      timeline,
      messages,
    } = body;

    // Context natal (puede estar ausente si el usuario va directo a mundana sin carta)
    const natal  = natalData ? buildNatalContext(natalData, birthData) : null;

    // Context block mundano
    const configBlock = config ? _formatConfig(config) : 'Sin configuración mundana específica.';
    const historyBlock = historyContext?.sample_events?.length
      ? `\nContexto histórico (eventos similares del corpus):\n${_formatHistory(historyContext.sample_events)}`
      : '';

    const mundanaContext = [
      '═══ CONFIGURACIÓN MUNDANA ACTIVA ═══',
      configBlock,
      historyBlock,
      '═══════════════════════════════════',
    ].filter(Boolean).join('\n');

    // Si hay carta natal, usar el context builder completo
    // Si no, construir un bloque mínimo con solo la configuración mundana
    let block: string;
    if (natal) {
      const active = buildActiveContext({
        currentDate:   new Date().toISOString(),
        activeTab:     'mundana',
        activeDomain:  null,
        activeCity:    null,
        lastEventType: 'mundana_config',
        triggerData: {
          mundana_config: config?.type ?? 'unknown',
          mundana_label:  config?.label ?? '',
          lang,
        },
      });
      const tl: BiographicalTimeline = timeline ?? EMPTY_TIMELINE;
      block = assembleContextBlock(natal, tl, active, lang ?? 'es') + '\n\n' + mundanaContext;
    } else {
      block = [
        `Idioma de respuesta: ${lang ?? 'es'}`,
        '',
        mundanaContext,
        '',
        'Interpreta esta configuración mundana según la doctrina de Abu Mashar.',
        'Relaciona con el contexto histórico si está disponible.',
        'Responde en el idioma indicado.',
      ].join('\n');
    }

    const history: Array<{ role: 'user' | 'assistant'; content: string }> = (messages ?? [])
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
        toGeminiMessages(messages ?? [], block),
        2048,
      );
    } else {
      const decision = selectModel('mundana', ctx.plan === 'monthly' || ctx.plan === 'annual' ? ctx.plan : 'genesis');
      model = decision.model;
      const client = getAnthropicClient();
      result = await completeLilly(client, {
        model,
        max_tokens: 2048,
        system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
        messages: [...history, { role: 'user', content: block }],
      });
    }

    const { text, usage } = result;
    logLillyUsage('mundana', model, usage, ctx.userId);
    return NextResponse.json({ response: text });
  } catch (err: any) {
    console.error('[lilly/mundana]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
