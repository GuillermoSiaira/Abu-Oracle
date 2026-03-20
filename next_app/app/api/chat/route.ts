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
      const profectionHouse: number | null = abuData?.derived?.profection?.house ?? null;

      // Derive profection lord from house cusp → sign → traditional ruler
      const CHAT_SIGNS = [
        "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
      ];
      const CHAT_RULERS: Record<string, string> = {
        Aries: "Mars", Taurus: "Venus", Gemini: "Mercury", Cancer: "Moon",
        Leo: "Sun", Virgo: "Mercury", Libra: "Venus", Scorpio: "Mars",
        Sagittarius: "Jupiter", Capricorn: "Saturn", Aquarius: "Saturn", Pisces: "Jupiter",
      };
      let profLord = "?";
      if (profectionHouse != null) {
        const cusps: any[] = houses?.houses ?? [];
        const cusp = cusps.find((h: any) => h.house === profectionHouse);
        if (cusp) {
          const signIdx = Math.floor(((cusp.start % 360) + 360) % 360 / 30);
          profLord = CHAT_RULERS[CHAT_SIGNS[signIdx]] ?? "?";
        }
      }

      contextBlock = `
CHART CONTEXT
Name: ${name}
Birth: ${meta.date ?? ""} · ${meta.city ?? ""}
Sect: ${sect}
Planets: ${planets}
ASC: ${houses?.asc?.toFixed(1) ?? "?"} | MC: ${houses?.mc?.toFixed(1) ?? "?"}
Profection lord: ${profLord} (House ${profectionHouse ?? "?"})
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
