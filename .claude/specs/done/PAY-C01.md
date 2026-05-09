# PAY-C01 — Upgrade Flow: Modal + Pricing Page + Paddle Checkout

## Context

The Paddle webhook, `provisionUser`, and the 3 price IDs are already implemented and working
in production. One subscriber at $5/month confirms the backend works end-to-end.

What's missing: **the frontend funnel**. When a free user exhausts their 15 queries, the UI
shows a plain text error in the chat with no CTA, no button, no path to upgrade.

Price IDs (already in Cloud Run env vars):
- Genesis (one-time $100): `pri_01kmh442gtdnera4n0bzd2ndnn`
- Monthly ($5/mo):         `pri_01kmh4a00408wxpfvxqsn9faz0`
- Annual ($45/yr):         `pri_01kmh5g6hcn9kkq1r7g7cqdf40`

## Files to create / modify

```
next_app/app/pricing/page.tsx              NEW — /pricing page
next_app/components/UpgradeModal.tsx       NEW — modal shown on 429
next_app/components/OracleChat.tsx         MODIFY — detect 429 → show modal
next_app/lib/paddle.ts                     NEW — Paddle.js helpers
next_app/app/layout.tsx                    MODIFY — load Paddle.js script
```

## Spec

### 1. `lib/paddle.ts` — Paddle.js client helpers

```typescript
// Client-side only — safe to call in useEffect / onClick handlers

declare global {
  interface Window {
    Paddle?: {
      Initialize: (opts: { token: string }) => void;
      Checkout: {
        open: (opts: { items: Array<{ priceId: string; quantity: number }> }) => void;
      };
    };
  }
}

export const PADDLE_TOKEN = process.env.NEXT_PUBLIC_PADDLE_TOKEN ?? '';

export const PLANS = {
  genesis: {
    priceId:     'pri_01kmh442gtdnera4n0bzd2ndnn',
    label:       'Genesis',
    price:       '$100',
    period:      'pago único',
    description: 'Acceso de por vida · Sin límite diario',
    highlight:   true,
  },
  monthly: {
    priceId:     'pri_01kmh4a00408wxpfvxqsn9faz0',
    label:       'Mensual',
    price:       '$5',
    period:      'por mes',
    description: 'Hasta 50 consultas / día',
    highlight:   false,
  },
  annual: {
    priceId:     'pri_01kmh5g6hcn9kkq1r7g7cqdf40',
    label:       'Anual',
    price:       '$45',
    period:      'por año',
    description: 'Hasta 50 consultas / día · 25% descuento',
    highlight:   false,
  },
} as const;

export type PlanKey = keyof typeof PLANS;

export function openCheckout(priceId: string): void {
  if (typeof window === 'undefined' || !window.Paddle) {
    // Fallback: open pricing page
    window.location.href = '/pricing';
    return;
  }
  window.Paddle.Checkout.open({ items: [{ priceId, quantity: 1 }] });
}
```

### 2. `app/layout.tsx` — Load Paddle.js + initialize

Add inside the `<body>` **before** `</body>`:

```tsx
{/* Paddle.js — only loads in browser */}
<Script
  src="https://cdn.paddle.com/paddle/v2/paddle.js"
  strategy="afterInteractive"
  onLoad={() => {
    if (typeof window !== 'undefined' && window.Paddle && process.env.NEXT_PUBLIC_PADDLE_TOKEN) {
      window.Paddle.Initialize({ token: process.env.NEXT_PUBLIC_PADDLE_TOKEN });
    }
  }}
/>
```

Import `Script` from `'next/script'`.

### 3. `components/UpgradeModal.tsx` — Modal shown when free tier is exhausted

```tsx
'use client';

import { PLANS, openCheckout } from '@/lib/paddle';

interface UpgradeModalProps {
  open: boolean;
  onClose: () => void;
}

export function UpgradeModal({ open, onClose }: UpgradeModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="relative mx-4 w-full max-w-md rounded-xl border border-slate-700/60 bg-slate-900 p-6 shadow-2xl">
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-500 hover:text-slate-300"
        >
          ✕
        </button>

        {/* Header */}
        <div className="mb-6 text-center">
          <div className="mb-2 text-2xl">⟡</div>
          <h2 className="text-lg font-semibold text-slate-100">
            Consultas gratuitas agotadas
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Elegí un plan para continuar con Lilly
          </p>
        </div>

        {/* Plans */}
        <div className="space-y-3">
          {(Object.values(PLANS)).map((plan) => (
            <button
              key={plan.priceId}
              onClick={() => openCheckout(plan.priceId)}
              className={`w-full rounded-lg border px-4 py-3 text-left transition-all hover:border-amber-400/50 hover:bg-slate-800/80 ${
                plan.highlight
                  ? 'border-amber-400/40 bg-amber-400/5'
                  : 'border-slate-700/50 bg-slate-800/40'
              }`}
            >
              <div className="flex items-baseline justify-between">
                <span className="font-semibold text-slate-100">{plan.label}</span>
                <span className="text-amber-400 font-mono">
                  {plan.price}
                  <span className="ml-1 text-xs text-slate-500">{plan.period}</span>
                </span>
              </div>
              <p className="mt-0.5 text-xs text-slate-500">{plan.description}</p>
            </button>
          ))}
        </div>

        {/* Footer */}
        <p className="mt-4 text-center text-[11px] text-slate-600">
          Pago seguro via Paddle · Cancela cuando quieras
        </p>
      </div>
    </div>
  );
}
```

### 4. `components/OracleChat.tsx` — Detect 429 → show modal

Add state near the top of the component:
```tsx
const [showUpgrade, setShowUpgrade] = useState(false);
```

In every fetch call that receives a Lilly response, after getting the response JSON:
```tsx
// Existing pattern in handleSubmit and the pendingLillyEvent useEffect:
if (res.status === 429) {
  setShowUpgrade(true);
  return; // don't add the error text to messages
}
```

Specifically, wrap the existing `data.response || '> ERROR...'` check:
```tsx
if (!res.ok) {
  if (res.status === 429) { setShowUpgrade(true); return; }
  // existing error handling
}
```

Add at the bottom of the OracleChat JSX (before closing tag):
```tsx
<UpgradeModal open={showUpgrade} onClose={() => setShowUpgrade(false)} />
```

### 5. `app/pricing/page.tsx` — Standalone pricing page

```tsx
'use client';

import { PLANS, openCheckout } from '@/lib/paddle';

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold text-slate-100">Abu Oracle</h1>
        <p className="mt-2 text-slate-400">
          Motor de astrología computacional con interpretación doctrinal
        </p>
      </div>

      <div className="grid w-full max-w-2xl gap-4 md:grid-cols-3">
        {/* Free tier card — read only */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="text-sm font-semibold text-slate-400">Gratis</div>
          <div className="mt-2 text-2xl font-bold text-slate-100">$0</div>
          <p className="mt-1 text-xs text-slate-500">15 consultas de por vida</p>
          <ul className="mt-4 space-y-1 text-xs text-slate-500">
            <li>✓ Carta natal completa</li>
            <li>✓ Mapa HF relocalización</li>
            <li>✓ 15 interpretaciones Lilly</li>
          </ul>
        </div>

        {/* Paid plans */}
        {(Object.values(PLANS)).map((plan) => (
          <div
            key={plan.priceId}
            className={`rounded-xl border p-5 ${
              plan.highlight
                ? 'border-amber-400/40 bg-amber-400/5'
                : 'border-slate-700/50 bg-slate-900/60'
            }`}
          >
            {plan.highlight && (
              <div className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-amber-400">
                Recomendado
              </div>
            )}
            <div className="text-sm font-semibold text-slate-300">{plan.label}</div>
            <div className="mt-2 text-2xl font-bold text-slate-100">
              {plan.price}
              <span className="ml-1 text-sm font-normal text-slate-500">{plan.period}</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">{plan.description}</p>
            <ul className="mt-4 space-y-1 text-xs text-slate-400">
              <li>✓ Hasta 50 consultas / día</li>
              <li>✓ Claude Sonnet (mejor calidad)</li>
              <li>✓ Memoria entre sesiones</li>
              <li>✓ Todos los módulos</li>
            </ul>
            <button
              onClick={() => openCheckout(plan.priceId)}
              className="mt-5 w-full rounded-lg bg-amber-500 py-2 text-sm font-semibold text-slate-900 transition hover:bg-amber-400"
            >
              Comenzar
            </button>
          </div>
        ))}
      </div>

      <p className="mt-6 text-center text-xs text-slate-600">
        Pago seguro via Paddle · Acceso inmediato tras el pago
      </p>
    </main>
  );
}
```

### 6. New env var required

Add to Cloud Run (Next.js app) and `.env.local`:
```
NEXT_PUBLIC_PADDLE_TOKEN=live_xxxxxxxxxxxxx
```

Found in Paddle dashboard → **Developer** → **Authentication** → **Client-side token**.

Also add a link to the pricing page in the Navigation bar:
```tsx
// In next_app/components/Navigation.tsx — add alongside existing nav items:
<Link href="/pricing" className="text-sm text-slate-400 hover:text-amber-400">
  Planes
</Link>
```

## Acceptance criteria

- [ ] `lib/paddle.ts` exports `PLANS`, `openCheckout`, `PADDLE_TOKEN`
- [ ] Paddle.js loads via `next/script` in layout, initialized with `NEXT_PUBLIC_PADDLE_TOKEN`
- [ ] `UpgradeModal` renders correctly and clicking any plan calls `openCheckout(priceId)`
- [ ] `OracleChat` detects `status === 429` → opens `UpgradeModal` instead of showing error text
- [ ] `/pricing` page renders all 3 plans + free tier card, each paid plan has "Comenzar" button
- [ ] `npx tsc --noEmit` passes
- [ ] Navigation bar has "Planes" link pointing to `/pricing`

## Env var needed before deploy

`NEXT_PUBLIC_PADDLE_TOKEN` — get from Paddle dashboard → Developer → Authentication → Client-side token.
Add to Cloud Run **before** deploying this spec.
