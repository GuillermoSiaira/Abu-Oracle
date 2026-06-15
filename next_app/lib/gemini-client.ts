import { GoogleGenAI } from '@google/genai';
import type { LillyResult } from './lilly-complete';

// Vertex (us-central1) solo tiene la familia 2.5 habilitada en este proyecto;
// gemini-2.0-flash da 404. Env-var-driven para cambiar sin rebuild.
export const GEMINI_FLASH_MODEL = process.env.LILLY_GEMINI_MODEL || 'gemini-2.5-flash';

type GeminiMessage = {
  role: 'user' | 'model';
  content: string;
};

function getGeminiClient(): GoogleGenAI {
  const apiKey = process.env.GEMINI_API_KEY;
  if (apiKey) {
    return new GoogleGenAI({ apiKey });
  }
  // Fallback: Vertex AI with Application Default Credentials.
  // In Cloud Run, ADC is provided automatically via the service account.
  // No GEMINI_API_KEY needed — uses the GCP project billing already active.
  return new GoogleGenAI({
    vertexai: true,
    project: process.env.GOOGLE_CLOUD_PROJECT || 'abu-oracle',
    location: 'us-central1',
  } as any);
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

  // Solo agregar el mensaje final si tiene contenido (evita input vacío).
  if (finalUserMessage && finalUserMessage.trim()) {
    converted.push({ role: 'user', content: finalUserMessage });
  }

  // Gemini rechaza input vacío ("Model input cannot be empty"). En eventos
  // reactivos sin mensajes previos, garantizar un turno de usuario mínimo;
  // el contexto real (carta + memoria) ya va en el system prompt.
  if (converted.length === 0) {
    converted.push({
      role: 'user',
      content: 'Interpretá el contexto astrológico provisto con precisión doctrinal.',
    });
  }

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
