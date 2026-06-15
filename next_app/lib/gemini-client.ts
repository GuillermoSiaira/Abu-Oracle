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

  // Gemini necesita que `contents` TERMINE en un turno 'user' (si no, devuelve
  // vacío: no sabe a qué responder). En eventos reactivos tras una conversación,
  // messages termina en un turno 'model' (la última respuesta de Lilly) y el
  // mensaje final va vacío → habría que cerrar con un turno 'user'. También cubre
  // el caso sin mensajes. El contexto real (carta + selección) ya va en el system.
  const last = converted[converted.length - 1];
  if (!last || last.role !== 'user') {
    converted.push({
      role: 'user',
      content: 'Interpretá la selección actual del nativo descrita en el CONTEXTO ACTIVO, con precisión doctrinal.',
    });
  }

  return converted;
}

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function completeLillyGemini(
  system: string,
  messages: GeminiMessage[],
  maxTokens: number,
): Promise<LillyResult> {
  const client = getGeminiClient();

  let accumulatedText = '';
  let inputTokens = 0;
  let outputTokens = 0;
  let continuations = 0;
  const MAX_CONTINUATIONS = 3;
  let retryEmptyDone = false;

  const currentContents = messages.map((m) => ({
    role: m.role,
    parts: [{ text: m.content }],
  }));

  async function attemptCall(): Promise<any> {
    const backoff = [1000, 2000, 4000];
    for (let attempt = 0; attempt <= backoff.length; attempt++) {
      try {
        return await client.models.generateContent({
          model: GEMINI_FLASH_MODEL,
          config: {
            systemInstruction: system,
            maxOutputTokens: maxTokens,
            temperature: 0.7,
            thinkingConfig: { thinkingBudget: 0 },
          },
          contents: currentContents,
        });
      } catch (err: any) {
        if (attempt < backoff.length && (err?.status === 429 || err?.status === 503)) {
          await delay(backoff[attempt]);
          continue;
        }
        throw err;
      }
    }
  }

  while (continuations <= MAX_CONTINUATIONS) {
    const response = await attemptCall();
    
    const usage = response.usageMetadata ?? {};
    if (continuations === 0) {
      inputTokens = usage.promptTokenCount ?? 0;
    }
    outputTokens += usage.candidatesTokenCount ?? 0;

    const text = response.text ?? '';
    if (text) accumulatedText += text;

    const candidate = response.candidates?.[0];
    const finishReason = candidate?.finishReason;

    if (!accumulatedText) {
      if (finishReason === 'SAFETY' || finishReason === 'RECITATION') {
        accumulatedText = 'No puedo desarrollar esa lectura en este momento.';
        break;
      }
      if (!retryEmptyDone) {
        retryEmptyDone = true;
        continue;
      } else {
        accumulatedText = 'No puedo desarrollar esa lectura en este momento.';
        break;
      }
    }

    if (finishReason === 'MAX_TOKENS' && continuations < MAX_CONTINUATIONS && text) {
      currentContents.push({ role: 'model', parts: [{ text }] });
      currentContents.push({ role: 'user', parts: [{ text: 'Continúa.' }] });
      continuations++;
    } else {
      break;
    }
  }

  return {
    text: accumulatedText || 'No puedo desarrollar esa lectura en este momento.',
    usage: {
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      continuations: continuations,
    },
  };
}
