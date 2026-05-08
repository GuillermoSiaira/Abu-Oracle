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
import { getUserIdFromRequest } from "@/lib/get-user-id";
import {
  getRecentHistory,
  formatMemoryForPrompt,
  saveExchange,
  summarizeIfNeeded,
} from "@/lib/chat-memory";
import { applyRateLimit } from "@/lib/usage-limiter";
import { completeLilly } from "@/lib/lilly-complete";
import type Anthropic from "@anthropic-ai/sdk";
import { logInterpretation } from "@/lib/interpretation-logger";
import { logLillyUsage } from "@/lib/lilly-usage-logger";
import { selectModel } from "@/lib/selectModel";

export const dynamic = "force-dynamic";

const client = getAnthropicClient();

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections: [],
  firdaria: [],
  transits_window: [],
};

export async function POST(req: Request) {
  try {
    // Clone request so we can read body AND headers (getUserIdFromRequest reads headers)
    const reqClone = req.clone();
    const body = await req.json();
    const { messages, context, session_id, timeline, lunarData: clientLunarData, lang: bodyLang } = body;

    if (!messages?.length) {
      return NextResponse.json({ error: "No messages provided" }, { status: 400 });
    }

    // ── Auth + rate limit + memory ───────────────────────────────────────────
    const limitRes = await applyRateLimit(reqClone);
    if (limitRes) return limitRes;
    const userId = await getUserIdFromRequest(reqClone);
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

    const { model } = selectModel('chat', 'genesis');
    const { text, usage } = await completeLilly(client, {
      model,
      max_tokens: parseInt(process.env.LILLY_CHAT_MAX_TOKENS ?? "2500"),
      system: systemBlocks,
      messages: anthropicMessages,
    });

    logLillyUsage('chat', model, usage, userId ?? null);
    logInterpretation({
      route: 'chat',
      eventType: body.eventType ?? 'chat',
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
      }).then(() => summarizeIfNeeded(userId));
    }

    return NextResponse.json({ response: text });

  } catch (err: any) {
    console.error("🔴 /api/chat error:", err?.message ?? err);
    return NextResponse.json({ error: err?.message ?? "Internal error" }, { status: 500 });
  }
}
