/**
 * lilly-complete.ts
 *
 * Wrapper sobre Anthropic messages.create con loop de continuación automático.
 * Garantiza que la respuesta nunca quede truncada en medio de una oración.
 *
 * Mecanismo:
 *   Si stop_reason === 'max_tokens', el texto parcial se agrega como turno
 *   'assistant' y se llama de nuevo — el modelo retoma exactamente donde quedó.
 *   Se repite hasta stop_reason === 'end_turn' o MAX_CONTINUATIONS.
 *
 * Costo: 1 llamada adicional de ~100-300 tokens de input en el caso raro de
 * truncación. Cero overhead cuando la respuesta entra dentro de max_tokens.
 */

import Anthropic from '@anthropic-ai/sdk';

type CreateParams = Anthropic.MessageCreateParamsNonStreaming;

const MAX_CONTINUATIONS = 3;

export async function completeLilly(
  client: Anthropic,
  params: CreateParams,
): Promise<string> {
  // Shallow-copy messages array so el caller no es mutado
  const messages: Anthropic.MessageParam[] = [
    ...(params.messages as Anthropic.MessageParam[]),
  ];

  let fullText = '';

  for (let i = 0; i <= MAX_CONTINUATIONS; i++) {
    const response = await client.messages.create({ ...params, messages });

    const chunk = response.content
      .filter((b): b is Anthropic.TextBlock => b.type === 'text')
      .map(b => b.text)
      .join('');

    fullText += chunk;

    if (response.stop_reason !== 'max_tokens') break;
    if (i === MAX_CONTINUATIONS) break;

    // Agrega el fragmento parcial como turno assistant → el modelo continúa
    messages.push({ role: 'assistant', content: chunk });
  }

  return fullText;
}
