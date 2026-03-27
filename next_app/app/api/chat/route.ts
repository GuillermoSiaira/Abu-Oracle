import { NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
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
import { checkAndIncrementDailyUsage, LIMIT_MESSAGE } from "@/lib/usage-limiter";

export const dynamic = "force-dynamic";

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

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
    const { messages, context, session_id, timeline, lang: bodyLang } = body;

    if (!messages?.length) {
      return NextResponse.json({ error: "No messages provided" }, { status: 400 });
    }

    // ── Auth + rate limit + memory ───────────────────────────────────────────
    const userId = await getUserIdFromRequest(reqClone);
    console.log("[chat-memory] userId:", userId);
    if (userId) {
      const allowed = await checkAndIncrementDailyUsage(userId);
      if (!allowed) {
        return NextResponse.json({ response: LIMIT_MESSAGE });
      }
    }
    const memoryCtx = userId ? await getRecentHistory(userId) : null;
    const memoryBlock = memoryCtx ? formatMemoryForPrompt(memoryCtx) : '';

    // Extract abuData and birthData from the existing context shape
    const abuData   = context?.calculations;
    const meta      = context?.meta;
    // Adapt meta shape { date, city } → buildNatalContext shape { birthDate, city }
    const birthData = meta ? { birthDate: meta.date, city: meta.city, utcOffset: meta.utcOffset } : undefined;
    const lang: string = bodyLang ?? "es";

    // ── Fetch lunar data from Abu Engine (non-fatal) ─────────────────────────
    let lunarBlock = '';
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

    // Build canonical context block — injected into system prompt (chat pattern)
    let systemPrompt = LILLY_SYSTEM_PROMPT;
    if (abuData) {
      const natal  = buildNatalContext(abuData, birthData);
      const active = buildActiveContext({
        currentDate:   new Date().toISOString(),
        activeTab:     "chat",
        activeDomain:  null,
        activeCity:    null,
        lastEventType: "chat",
        triggerData:   {},
      });
      const block = assembleContextBlock(
        natal,
        timeline ?? EMPTY_TIMELINE,
        active,
        lang,
        memoryBlock || undefined,
        lunarBlock || undefined,
      );
      systemPrompt = `${LILLY_SYSTEM_PROMPT}\n\n---\n${block}`;
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

    const response = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: parseInt(process.env.LILLY_CHAT_MAX_TOKENS ?? "2500"),
      system: systemPrompt,
      messages: anthropicMessages,
    });

    const text = response.content[0]?.type === "text" ? response.content[0].text : "";

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
