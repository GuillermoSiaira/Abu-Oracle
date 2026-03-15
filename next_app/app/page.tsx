'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAppStore } from '@/lib/store';
import { UI } from '@/lib/i18n';
import BirthDataPanel from '@/components/birth-data-panel';

export default function Home() {
  const { lang } = useAppStore();
  const t = UI[lang as keyof typeof UI] ?? UI.es;
  const [showForm, setShowForm] = useState(false);

  // Si el usuario pidió el formulario explícitamente
  if (showForm) {
    return (
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
    );
  }

  // Estado inicial — CTAs centrados. La columna derecha (OracleChat) habla por Lilly.
  return (
    <main className="h-full flex items-center justify-center">
      <LillyCtas
        ctaData={t.lillyCtaData}
        ctaDemo={t.lillyCtaDemo}
        onEnterData={() => setShowForm(true)}
      />
    </main>
  );
}

function LillyCtas({
  ctaData,
  ctaDemo,
  onEnterData,
}: {
  ctaData: string;
  ctaDemo: string;
  onEnterData: () => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <button
        onClick={onEnterData}
        className="text-sm font-mono text-amber-400 hover:text-amber-300 border border-amber-500/30 hover:border-amber-400/60 rounded-sm px-4 py-2.5 transition-colors text-left w-fit"
      >
        → {ctaData}
      </button>
      <Link
        href="/relocation"
        className="text-sm font-mono text-green-400/60 hover:text-green-300 border border-green-500/10 hover:border-green-400/30 rounded-sm px-4 py-2.5 transition-colors w-fit"
      >
        → {ctaDemo}
      </Link>
    </div>
  );
}
