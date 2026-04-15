/**
 * anthropic-client.ts
 *
 * Factory centralizado para el cliente Anthropic.
 * Usa Vertex AI (ADC) — no requiere ANTHROPIC_API_KEY.
 * En Cloud Run la autenticación es automática via Application Default Credentials.
 */

import { AnthropicVertex } from '@anthropic-ai/vertex-sdk';

export function getAnthropicClient(): AnthropicVertex {
  return new AnthropicVertex({
    projectId: 'abu-oracle',
    region:    'us-east5',
  });
}
