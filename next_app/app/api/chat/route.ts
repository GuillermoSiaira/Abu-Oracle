import { NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { LILLY_SYSTEM_PROMPT } from "@/lib/lilly-prompt";

export const dynamic = "force-dynamic";

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { messages, context, session_id } = body;

    if (!messages?.length) {
      return NextResponse.json({ error: "No messages provided" }, { status: 400 });
    }

    // Build a compact context block from the astrological data
    const abuData = context?.calculations;
    const meta = context?.meta;

    let contextBlock = "";
    if (abuData && meta) {
      const name = abuData?.person?.name ?? "Unknown";
      const planets = (abuData?.chart?.planets ?? [])
        .slice(0, 12)
        .map((p: any) => `${p.name} ${p.sign} H${p.house}${p.dignity?.kind ? ` (${p.dignity.kind})` : ""}`)
        .join(", ");
      const houses = abuData?.chart?.houses;
      const sect = abuData?.derived?.sect ?? "unknown";
      const firdaria = abuData?.derived?.firdaria?.current;
      const profection = abuData?.derived?.profection;

      contextBlock = `
CHART CONTEXT
Name: ${name}
Birth: ${meta.date ?? ""} · ${meta.city ?? ""}
Sect: ${sect}
Planets: ${planets}
ASC: ${houses?.asc?.toFixed(1) ?? "?"} | MC: ${houses?.mc?.toFixed(1) ?? "?"}
Profection lord: ${profection?.lord ?? "?"} (House ${profection?.house_number ?? "?"})
Firdaria: ${firdaria?.major ?? "?"} / ${firdaria?.sub ?? "?"}
Lang: ${abuData?.lang ?? "es"}
`;
    }

    const systemPrompt = contextBlock
      ? `${LILLY_SYSTEM_PROMPT}\n\n---\n${contextBlock}`
      : LILLY_SYSTEM_PROMPT;

    // Convert messages to Anthropic format, filtering out any with empty content
    const anthropicMessages = messages
      .filter((m: any) => m.content?.trim())
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
      max_tokens: parseInt(process.env.LILLY_CHAT_MAX_TOKENS ?? "1500"),
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
