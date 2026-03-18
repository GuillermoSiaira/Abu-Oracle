'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAppStore } from '@/lib/store';
import { UI } from '@/lib/i18n';
import BirthDataPanel from '@/components/birth-data-panel';
import AuthGuard from '@/components/AuthGuard';

export default function Home() {
  const { lang } = useAppStore();
  const t = UI[lang as keyof typeof UI] ?? UI.es;
  const [showForm, setShowForm] = useState(false);

  // Si el usuario pidió el formulario explícitamente
  if (showForm) {
    return (
      <AuthGuard>
        <main className="min-h-screen bg-gradient-to-b from-[#0b0b0b] to-[#050505]">
          <div className="container mx-auto py-16 space-y-14">
            <header className="text-center space-y-3">
              <h1 className="text-4xl md:text-5xl font-serif tracking-tight text-amber-500">
                ABU — Astrological Computation Engine
              </h1>
              <p className="text-slate-400 max-w-2xl mx-auto text-sm md:text-base">
                Deterministic astronomical computation using high-precision ephemerides,
                geospatial resolution (WGS84) and reproducible temporal anchors.
              </p>
            </header>
            <div className="max-w-2xl mx-auto">
              <BirthDataPanel />
            </div>
          </div>
        </main>
      </AuthGuard>
    );
  }

  // Estado inicial — identidad visual centrada en columna central
  return (
    <AuthGuard>
      <main className="h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-6 text-center px-4">
          {/* Title block */}
          <div className="space-y-2">
            <h1
              className="text-5xl md:text-6xl tracking-[0.15em] text-amber-400/90"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              ABU ORACLE
            </h1>
            <p className="text-[11px] font-mono tracking-[0.25em] uppercase text-slate-500">
              {t.homeSubtitle}
            </p>
          </div>

          {/* Separator */}
          <div className="w-24 h-px bg-amber-500/20" />

          {/* CTAs */}
          <div className="flex flex-col gap-2.5 items-center">
            <button
              onClick={() => setShowForm(true)}
              className="text-sm font-mono text-amber-400 hover:text-amber-200 border border-amber-500/40 hover:border-amber-400/70 hover:bg-amber-500/5 rounded-sm px-5 py-2.5 transition-all w-fit"
            >
              → {t.lillyCtaData}
            </button>
            <Link
              href="/demo"
              className="text-xs font-mono text-slate-500 hover:text-slate-300 border border-slate-700/40 hover:border-slate-600/60 rounded-sm px-5 py-2 transition-all w-fit"
            >
              → {t.lillyCtaDemo}
            </Link>
          </div>
        </div>
      </main>
    </AuthGuard>
  );
}
