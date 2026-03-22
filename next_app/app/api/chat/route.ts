import { NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { LILLY_SYSTEM_PROMPT } from "@/lib/lilly-prompt";
import {
  buildNatalContext,
  buildActiveContext,
  assembleContextBlock,
  type BiographicalTimeline,
} from "@/lib/context-builder";

export const dynamic = "force-dynamic";

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const EMPTY_TIMELINE: BiographicalTimeline = {
  profections: [],
  firdaria: [],
  transits_window: [],
};

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { messages, context, session_id, timeline } = body;

    if (!messages?.length) {
      return NextResponse.json({ error: "No messages provided" }, { status: 400 });
    }

    // Extract abuData and birthData from the existing context shape
    const abuData   = context?.calculations;
    const meta      = context?.meta;
    // Adapt meta shape { date, city } → buildNatalContext shape { birthDate, city }
    const birthData = meta ? { birthDate: meta.date, city: meta.city } : undefined;
    const lang: string = abuData?.lang ?? "es";

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
      const block = assembleContextBlock(natal, timeline ?? EMPTY_TIMELINE, active, lang);
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
    return NextResponse.json({ response: text });

  } catch (err: any) {
    console.error("🔴 /api/chat error:", err?.message ?? err);
    return NextResponse.json({ error: err?.message ?? "Internal error" }, { status: 500 });
  }
}
