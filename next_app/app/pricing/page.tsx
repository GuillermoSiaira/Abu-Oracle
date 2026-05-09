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
