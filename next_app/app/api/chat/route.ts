import { NextResponse } from "next/server";
import { getAnthropicClient } from "@/lib/anthropic-client";
import { LILLY_SYSTEM_PROMPT } from "@/lib/lilly-prompt";
import {
  buildNatalContext,
  buildActiveContext,
  assembleContextBlock,
  formatLunarContext,
  type BiographicalTimeline,
} from "@/lib/context-builder";
import {
  getRecentHistory,
  formatMemoryForPrompt,
  saveExchange,
  summarizeIfNeeded,
} from "@/lib/chat-memory";
import { getAccessContext, rateLimitResponse } from "@/lib/access-context";
import { completeLilly, type LillyResult } from "@/lib/lilly-complete";
import { completeLillyGemini, GEMINI_FLASH_MODEL, toGeminiMessages } from "@/lib/gemini-client";
import type Anthropic from "@anthropic-ai/sdk";
import { logInterpretation } from "@/lib/interpretation-logger";
import { logLillyUsage } from "@/lib/lilly-usage-logger";
import { selectModel } from "@/lib/selectModel";
import { classifyError, trackError } from "@/lib/error-tracker";

export const dynamic = "force-dynamic";

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections: [],
  firdaria: [],
  transits_window: [],
};

export async function POST(req: Request) {
  let userId: string | null = null;
  let eventType = "chat";

  try {
    const body = await req.json();
    eventType = body.eventType ?? eventType;
    const { messages, context, session_id, timeline, lunarData: clientLunarData, lang: bodyLang } = body;

    if (!messages?.length) {
      return NextResponse.json({ error: "No messages provided" }, { status: 400 });
    }

    // ── Auth + rate limit + memory ───────────────────────────────────────────
    const ctx = await getAccessContext(req);
    if (!ctx.allowed) return rateLimitResponse(ctx);
    userId = ctx.userId ?? null;
    console.log("[chat-memory] userId:", userId);
    const memoryCtx = userId ? await getRecentHistory(userId) : null;
    const memoryBlock = memoryCtx ? formatMemoryForPrompt(memoryCtx) : '';

    // Extract abuData and birthData from the existing context shape
    const abuData   = context?.calculations;
    const meta      = context?.meta;
    // Adapt meta shape { date, city } → buildNatalContext shape { birthDate, city }
    const birthData = meta ? { birthDate: meta.date, city: meta.city, utcOffset: meta.utcOffset } : undefined;
    const lang: string = bodyLang ?? "es";

    // ── Lunar data — usar el del cliente si viene en el body; fallback a fetch server-side ─
    let lunarBlock = '';
    if (clientLunarData) {
      lunarBlock = formatLunarContext(clientLunarData);
    } else {
      const abuUrl = process.env.ABU_ENGINE_URL || process.env.NEXT_PUBLIC_ABU_URL || '';
      const bDate = meta?.date;
      const bLat  = meta?.lat;
      const bLon  = meta?.lon;
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
          // non-fatal — chat procede sin sección CIELO ACTUAL
        }
      }
    } // end else (fallback fetch)

    // Build canonical context block — injected as second cached system block (chat pattern)
    const systemBlocks: Array<{ type: 'text'; text: string; cache_control: { type: 'ephemeral' } }> = [
      { type: 'text', text: LILLY_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } },
    ];
    if (abuData) {
      const natal  = buildNatalContext(abuData, birthData);
      const active = buildActiveContext({
        currentDate:    new Date().toISOString(),
        activeTab:      "chat",
        activeDomain:   null,
        activeCity:     null,
        lastEventType:  "chat",
        triggerData:    {},
        utcOffsetHours: meta?.utcOffset ?? undefined,
      });
      const block = assembleContextBlock(
        natal,
        timeline ?? EMPTY_TIMELINE,
        active,
        lang,
        memoryBlock || undefined,
        lunarBlock || undefined,
      );
      systemBlocks.push({ type: 'text', text: block, cache_control: { type: 'ephemeral' } });
    }

    // Filter hidden messages (synthetic reactives) — they are noise in free chat
    const anthropicMessages = messages
      .filter((m: any) => !m.hidden && m.role && m.content?.trim())
      .map((m: any) => ({
        role: m.role === "user" ? "user" : "assistant",
        content: m.content,
      })) as Anthropic.MessageParam[];

    // Ensure conversation starts with user (Anthropic requirement)
    while (anthropicMessages.length > 0 && anthropicMessages[0].role !== "user") {
      anthropicMessages.shift();
    }

    if (!anthropicMessages.length) {
      return NextResponse.json({ error: "No valid messages" }, { status: 400 });
    }

    const MAX_TOKENS = parseInt(process.env.LILLY_CHAT_MAX_TOKENS ?? "2500");

    let result: LillyResult;
    let model: string;

    if (ctx.provider === 'gemini') {
      model = GEMINI_FLASH_MODEL;
      // For chat, the systemBlocks are already constructed; pass the last user message as block
      // toGeminiMessages handles the full messages array
      result = await completeLillyGemini(
        LILLY_SYSTEM_PROMPT,
        toGeminiMessages(messages, ''),
        MAX_TOKENS,
      );
    } else {
      const decision = selectModel('chat', ctx.plan === 'monthly' || ctx.plan === 'annual' ? ctx.plan : 'genesis');
      model = decision.model;
      const client = getAnthropicClient();
      result = await completeLilly(client, {
        model,
        max_tokens: MAX_TOKENS,
        system: systemBlocks,
        messages: anthropicMessages,
      });
    }

    const { text, usage } = result;

    logLillyUsage('chat', model, usage, userId ?? null);
    logInterpretation({
      route: 'chat',
      eventType: body.eventType ?? 'chat',
      provider: ctx.provider,
      model,
      inputTokens: usage.input_tokens,
      outputTokens: usage.output_tokens,
      costUsd: 0,
      continuations: usage.continuations,
      userId: userId ?? undefined,
      chartKey: meta?.date != null && meta?.lat != null && meta?.lon != null
        ? `${meta.date}|${meta.lat}|${meta.lon}`
        : undefined,
      lang,
      condition: 'A',
    });

    // ── Persist exchange to Firestore (fire-and-forget) ──────────────────────
    if (userId && text) {
      const resolvedUserId = userId;
      const lastUserMsg = [...anthropicMessages].reverse().find((m) => m.role === "user");
      const userText = typeof lastUserMsg?.content === "string" ? lastUserMsg.content : "";
      const subjectName =
        abuData?.person?.name ||
        meta?.userName ||
        "Anónimo";

      // Non-blocking — do not await
      saveExchange(userId, {
        user_message:       userText,
        assistant_response: text,
        event_type:         "chat",
        subject_name:       subjectName,
      }).then(() => summarizeIfNeeded(resolvedUserId));
    }

    return NextResponse.json({ response: text });

  } catch (err: any) {
    const errorMessage = err instanceof Error ? err.message : String(err);
    trackError({
      route: "chat",
      eventType,
      errorMessage,
      errorSource: classifyError(err),
      userId,
      stack: err instanceof Error ? err.stack ?? null : null,
    });
    console.error("🔴 /api/chat error:", err?.message ?? err);
    return NextResponse.json({ error: err?.message ?? "Internal error" }, { status: 500 });
  }
}
