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
