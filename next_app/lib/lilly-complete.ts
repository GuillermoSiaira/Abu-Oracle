/**
 * lilly-complete.ts
 *
 * Wrapper sobre Anthropic messages.create con loop de continuación automático.
 * Garantiza que la respuesta nunca quede truncada en medio de una oración.
 *
 * Mecanismo:
 *   Si stop_reason === 'max_tokens', el fragmento parcial se agrega como turno
 *   'assistant' seguido de un turno 'user: Continúa.' — claude-sonnet-4-6 no
 *   acepta que el array termine en assistant (no soporta prefill).
 *   Se repite hasta stop_reason === 'end_turn' o MAX_CONTINUATIONS.
 *
 * Costo: 1 llamada adicional de ~100-300 tokens de input en el caso raro de
 * truncación. Cero overhead cuando la respuesta entra dentro de max_tokens.
 */

import Anthropic from '@anthropic-ai/sdk';

type CreateParams = Anthropic.MessageCreateParamsNonStreaming;

const MAX_CONTINUATIONS = 3;

export interface LillyUsage {
  input_tokens:  number;
  output_tokens: number;
  continuations: number; // 0 = respuesta en un solo turno
}

export interface LillyResult {
  text:  string;
  usage: LillyUsage;
}

export async function completeLilly(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  client: any,
  params: CreateParams,
): Promise<LillyResult> {
  // Shallow-copy messages array so el caller no es mutado
  const messages: Anthropic.MessageParam[] = [
    ...(params.messages as Anthropic.MessageParam[]),
  ];

  let fullText = '';
  let totalInput  = 0;
  let totalOutput = 0;
  let continuations = 0;

  for (let i = 0; i <= MAX_CONTINUATIONS; i++) {
    const response = await client.messages.create({ ...params, messages });

    const chunk = (response.content as Anthropic.ContentBlock[])
      .filter((b): b is Anthropic.TextBlock => b.type === 'text')
      .map(b => b.text)
      .join('');

    fullText      += chunk;
    totalInput    += response.usage.input_tokens;
    totalOutput   += response.usage.output_tokens;

    if (response.stop_reason !== 'max_tokens') break;
    if (i === MAX_CONTINUATIONS) break;

    continuations++;
    // claude-sonnet-4-6 no soporta prefill (array terminando en assistant).
    // Patrón correcto: assistant partial → user 'Continúa.' → el modelo retoma.
    messages.push({ role: 'assistant', content: chunk });
    messages.push({ role: 'user',      content: 'Continúa.' });
  }

  return {
    text:  fullText,
    usage: { input_tokens: totalInput, output_tokens: totalOutput, continuations },
  };
}
