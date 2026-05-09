import { GoogleGenAI } from '@google/genai';
import type { LillyResult } from './lilly-complete';

export const GEMINI_FLASH_MODEL = 'gemini-2.0-flash';

type GeminiMessage = {
  role: 'user' | 'model';
  content: string;
};

function getGeminiClient(): GoogleGenAI {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error('GEMINI_API_KEY not set');
  return new GoogleGenAI({ apiKey });
}

export function toGeminiMessages(
  messages: Array<{ role: string; content: unknown; hidden?: boolean }>,
  finalUserMessage: string,
): GeminiMessage[] {
  const converted = messages
    .filter((m) => !m.hidden && m.role && String(m.content ?? '').trim())
    .map((m) => ({
      role: m.role === 'assistant' ? 'model' as const : 'user' as const,
      content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
    }));

  converted.push({ role: 'user', content: finalUserMessage });
  return converted;
}

export async function completeLillyGemini(
  system: string,
  messages: GeminiMessage[],
  maxTokens: number,
): Promise<LillyResult> {
  const client = getGeminiClient();

  const response = await client.models.generateContent({
    model: GEMINI_FLASH_MODEL,
    config: {
      systemInstruction: system,
      maxOutputTokens: maxTokens,
      temperature: 0.7,
    },
    contents: messages.map((m) => ({
      role: m.role,
      parts: [{ text: m.content }],
    })),
  });

  const usage = response.usageMetadata ?? {};

  return {
    text: response.text ?? '',
    usage: {
      input_tokens: usage.promptTokenCount ?? 0,
      output_tokens: usage.candidatesTokenCount ?? 0,
      continuations: 0,
    },
  };
}
