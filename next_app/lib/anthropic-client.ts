/**
 * anthropic-client.ts
 *
 * Factory centralizado para el cliente Anthropic.
 * Prioridad:
 *   1. ANTHROPIC_API_KEY presente → API directa (sin cuota Vertex)
 *   2. Sin API key → AnthropicVertex con ADC (Cloud Run)
 */

import Anthropic from '@anthropic-ai/sdk';
import { AnthropicVertex } from '@anthropic-ai/vertex-sdk';

export function getAnthropicClient(): Anthropic | AnthropicVertex {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (apiKey) {
    return new Anthropic({ apiKey });
  }
  return new AnthropicVertex({
    projectId: 'abu-oracle',
    region:    'us-central1',
  });
}
