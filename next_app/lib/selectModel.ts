// Única función de selección de modelo en todo el proyecto.
// Hoy implementa política estática. En el futuro será el punto
// de entrada del optimizador MILP (Fase E).

export type Route =
  | 'screen-open'
  | 'transit'
  | 'domain'
  | 'chat'
  | 'solar-return'
  | 'planet'
  | 'technique'
  | 'city'
  | 'sky'
  | 'house'
  | 'mundana'

export type Plan = 'genesis' | 'monthly' | 'annual' | 'free'

export interface ModelDecision {
  model: string
  routing_reason: string
}

// Estimated input tokens per route (COST_OPTIMIZATION.md: 3,500–5,000 input typical)
const INPUT_TOKENS_EST: Record<Route, number> = {
  'screen-open':  4500,
  'planet':       4000,
  'transit':      4000,
  'domain':       3800,
  'city':         3800,
  'technique':    4000,
  'solar-return': 4000,
  'house':        4000,
  'mundana':      4500,
  'sky':          4500,
  'chat':         5000,
}

const OUTPUT_TOKENS_EST = 300

// Claude pricing per 1M tokens (USD). Source: Anthropic pricing page.
const PRICING: Record<string, { input: number; output: number }> = {
  'claude-sonnet-4-6':       { input: 3.00, output: 15.00 },
  'claude-haiku-4-5-20251001': { input: 0.80, output:  4.00 },
}

export function selectModel(route: Route, plan: Plan): ModelDecision {
  let model: string
  let routing_reason: string

  // Static policy: all doctrinal routes use Sonnet.
  // Haiku is reserved for the MILP optimizer (Fase E) — not active yet.
  model = 'claude-sonnet-4-6'
  routing_reason = 'all routes → Sonnet; Haiku reserved for MILP optimizer'

  const inputEst = INPUT_TOKENS_EST[route] ?? 4000
  const pricing  = PRICING[model] ?? PRICING['claude-sonnet-4-6']
  const costEst  =
    (inputEst / 1_000_000) * pricing.input +
    (OUTPUT_TOKENS_EST / 1_000_000) * pricing.output

  console.log(
    JSON.stringify({
      ts:                new Date().toISOString(),
      route,
      plan,
      model_selected:    model,
      routing_reason,
      tokens_input_est:  inputEst,
      tokens_output_est: OUTPUT_TOKENS_EST,
      cost_est_usd:      parseFloat(costEst.toFixed(6)),
    })
  )

  return { model, routing_reason }
}
