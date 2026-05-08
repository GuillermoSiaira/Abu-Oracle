import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { LILLY_SYSTEM_PROMPT } from '../../../../lib/lilly-prompt';
import {
  buildNatalContext,
  buildActiveContext,
  assembleContextBlock,
  formatLunarContext,
  type BiographicalTimeline,
} from '../../../../lib/context-builder';
import { getUserIdFromRequest } from '../../../../lib/get-user-id';
import { getRecentHistory, formatMemoryForPrompt } from '../../../../lib/chat-memory';
import { applyRateLimit } from '../../../../lib/usage-limiter';
import { completeLilly } from '../../../../lib/lilly-complete';
import { chartKeyFromBirthData, logInterpretation } from '../../../../lib/interpretation-logger';
import { logLillyUsage } from '../../../../lib/lilly-usage-logger';
import { selectModel } from '../../../../lib/selectModel';

export const dynamic = 'force-dynamic';

// ── Welcome message for first-time users (no LLM call) ───────────────────────

const WELCOME_COPY: Record<string, string> = {
  es: `Bienvenido a Abu Oracle. Tenés tres formas de explorar tu carta:\n— Hacé clic en cualquier planeta o casa de la rueda para que lo interprete\n— Abrí Técnicas Persas para ver el año astrológico que estás viviendo\n— Explorá el Mapa HF para descubrir dónde en el mundo resonás mejor\n\n¿Por dónde querés empezar?`,
  en: `Welcome to Abu Oracle. You have three ways to explore your chart:\n— Click any planet or house on the wheel to get an interpretation\n— Open Persian Techniques to see the astrological year you're living\n— Explore the HF Map to discover where in the world you resonate best\n\nWhere would you like to start?`,
  pt: `Bem-vindo ao Abu Oracle. Tens três formas de explorar o teu mapa:\n— Clica em qualquer planeta ou casa da roda para obter uma interpretação\n— Abre Técnicas Persas para ver o ano astrológico que estás a viver\n— Explora o Mapa HF para descobrir onde no mundo ressonas melhor\n\nPor onde queres começar?`,
  fr: `Bienvenue sur Abu Oracle. Vous avez trois façons d'explorer votre thème :\n— Cliquez sur une planète ou une maison du zodiaque pour l'interpréter\n— Ouvrez Techniques Persanes pour voir l'année astrologique que vous vivez\n— Explorez la Carte HF pour découvrir où dans le monde vous résonnez le mieux\n\nPar où voulez-vous commencer ?`,
};

const WELCOME_SUGGESTIONS: Record<string, Array<{ type: string; target: string; label: string }>> = {
  es: [
    { type: 'click_planet',    target: 'Sun',       label: '☀ Interpretar mi Sol natal' },
    { type: 'click_technique', target: 'profection', label: '↻ Ver mi año profeccional' },
    { type: 'click_domain',    target: 'h10',        label: '⬡ Campo HF Carrera' },
  ],
  en: [
    { type: 'click_planet',    target: 'Sun',       label: '☀ Interpret my natal Sun' },
    { type: 'click_technique', target: 'profection', label: '↻ See my profection year' },
    { type: 'click_domain',    target: 'h10',        label: '⬡ Career HF Map' },
  ],
  pt: [
    { type: 'click_planet',    target: 'Sun',       label: '☀ Interpretar o meu Sol natal' },
    { type: 'click_technique', target: 'profection', label: '↻ Ver o meu ano profeccional' },
    { type: 'click_domain',    target: 'h10',        label: '⬡ Mapa HF Carreira' },
  ],
  fr: [
    { type: 'click_planet',    target: 'Sun',       label: '☀ Interpréter mon Soleil natal' },
    { type: 'click_technique', target: 'profection', label: '↻ Voir mon année de profection' },
    { type: 'click_domain',    target: 'h10',        label: '⬡ Carte HF Carrière' },
  ],
};

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections: [],
  firdaria: [],
  transits_window: [],
};

const SUGGESTIONS_SUFFIX = [
  ``,
  `Al final de tu interpretación, añade exactamente este bloque sin modificarlo:`,
  ``,
  `[SUGERENCIAS]`,
  `{"suggestions": [`,
  `  {"type": "click_planet"|"click_technique"|"click_domain", "target": string, "label": string},`,
  `  ...`,
  `]}`,
  ``,
  `Elige los 3 elementos más significativos de esta carta para sugerir.`,
  `Priorizar: planetas angulares, planetas en domicilio/exaltación, señor del año, señor del ASC.`,
  `Para click_domain usar: h1, h2, h4, h5, h6, h7, h9, h10.`,
  `Para click_technique usar: sect, profection, firdaria, lot_fortuna, lot_spirit.`,
  `Para click_planet usar el nombre del planeta en inglés (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn).`,
].join('\n');

export async function POST(req: Request) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: 'ANTHROPIC_API_KEY not configured' },
      { status: 503 }
    );
  }

  try {
    const body = await req.json();
    const {
      name,
      sect,
      sect_master,
      lang,
      natalData,
      birthData,
      timeline,
      lunarData: clientLunarData,
      messages,
    } = body;

    // ── Memoria biográfica + detección de usuario nuevo ──────────────────────
    const userId = await getUserIdFromRequest(req);
    const memoryCtx = userId ? await getRecentHistory(userId) : null;
    const memoryBlock = memoryCtx ? formatMemoryForPrompt(memoryCtx) : '';

    // ── Welcome message for first-time users — no LLM call, no rate limit ────
    const isNewUser =
      !!userId && !!memoryCtx &&
      memoryCtx.exchanges.length === 0 && !memoryCtx.summary;
    if (isNewUser) {
      const resolvedLang = (lang as string) in WELCOME_COPY ? (lang as string) : 'es';
      return NextResponse.json({
        response:    WELCOME_COPY[resolvedLang],
        suggestions: WELCOME_SUGGESTIONS[resolvedLang],
      });
    }

    // ── Rate limit (solo si no es usuario nuevo — welcome es gratuito) ────────
    const limitRes = await applyRateLimit(req);
    if (limitRes) return limitRes;

    // ── Lunar data — usar el del cliente (fuente única de verdad) si viene en el body;
    //    solo hacer fetch server-side como fallback si no viene.
    let lunarBlock = '';
    if (clientLunarData) {
      lunarBlock = formatLunarContext(clientLunarData);
    } else {
      const abuUrl = process.env.ABU_ENGINE_URL || process.env.NEXT_PUBLIC_ABU_URL || '';
      const bDate = birthData?.birthDate;
      const bLat  = birthData?.lat;
      const bLon  = birthData?.lon;
      if (abuUrl && bDate && bLat != null && bLon != null) {
        try {
          const authHeader = req.headers.get('Authorization');
          const lunarUrl = new URL(`${abuUrl}/api/astro/lunar`);
          lunarUrl.searchParams.set('birthDate', bDate);
          lunarUrl.searchParams.set('lat',       String(bLat));
          lunarUrl.searchParams.set('lon',       String(bLon));
          const lunarRes = await fetch(lunarUrl.toString(), {
            headers: authHeader ? { Authorization: authHeader } : {},
          });
          if (lunarRes.ok) {
            lunarBlock = formatLunarContext(await lunarRes.json());
          }
        } catch {
          // non-fatal — Lilly procede sin sección CIELO ACTUAL
        }
      }
    }

    const natal  = buildNatalContext(natalData, birthData);
    const active = buildActiveContext({
      currentDate:     new Date().toISOString(),
      activeTab:       'persian_techniques',
      activeDomain:    null,
      activeCity:      null,
      lastEventType:   'screen_open',
      triggerData:     { name, sect, sect_master },
      utcOffsetHours:  (birthData as any)?.utcOffset ?? undefined,
    });
    const block =
      assembleContextBlock(natal, timeline ?? EMPTY_TIMELINE, active, lang ?? 'es', memoryBlock || undefined, lunarBlock || undefined)
      + '\n\n' + SUGGESTIONS_SUFFIX;

    const history: Anthropic.MessageParam[] = (messages ?? [])
      .filter((m: any) => m.role && m.content?.trim())
      .map((m: any) => ({ role: m.role as 'user' | 'assistant', content: m.content as string }));

    // Anthropic requires conversation to start with a user message
    while (history.length > 0 && history[0].role !== 'user') {
      history.shift();
    }

    const { model } = selectModel('screen-open', 'genesis');
    const client = new Anthropic({ apiKey });
    const { text: rawText, usage } = await completeLilly(client, {
      model,
      max_tokens: 1536,
      system: [{ type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
      messages: [...history, { role: 'user', content: block }],
    });

    // Parse [SUGERENCIAS] block from the end of the response
    let text = rawText;
    let suggestions: Array<{ type: string; target: string; label: string }> = [];
    const sugMarker = '[SUGERENCIAS]';
    const sugIdx = rawText.indexOf(sugMarker);
    if (sugIdx !== -1) {
      text = rawText.slice(0, sugIdx).trim();
      const jsonStr = rawText.slice(sugIdx + sugMarker.length).trim();
      try {
        const parsed = JSON.parse(jsonStr);
        if (Array.isArray(parsed.suggestions)) {
          suggestions = parsed.suggestions;
        }
      } catch {
        // If JSON is malformed, suggestions stay empty — not fatal
      }
    }

    logLillyUsage('screen-open', model, usage, userId ?? null);
    logInterpretation({
      route: 'screen-open',
      eventType: body.eventType ?? 'screen_open',
      inputTokens: usage.input_tokens,
      outputTokens: usage.output_tokens,
      costUsd: 0,
      continuations: usage.continuations,
      userId: userId ?? undefined,
      chartKey: chartKeyFromBirthData(birthData),
      lang: lang ?? 'es',
      condition: 'A',
    });
    return NextResponse.json({ response: text, suggestions });
  } catch (err: any) {
    console.error('[screen-open]', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
