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
  if (typeof window === 'undefined') {
    return;
  }

  if (!window.Paddle) {
    // Fallback: open pricing page
    window.location.href = '/pricing';
    return;
  }

  window.Paddle.Checkout.open({ items: [{ priceId, quantity: 1 }] });
}
