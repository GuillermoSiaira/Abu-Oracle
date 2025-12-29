'use client';

import Navigation from './Navigation';
import OracleChat from './OracleChat';
import { ReactNode } from 'react';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200 overflow-hidden">
      
      {/* NAVBAR SUPERIOR */}
      <div className="shrink-0 z-20">
        <Navigation />
      </div>

      {/* SPLIT VIEW */}
      <div className="flex flex-1 overflow-hidden relative">

        {/* MAIN */}
        <main className="flex-1 overflow-y-auto p-4 md:mr-[350px]">
          <div className="max-w-6xl mx-auto h-full">
            {children}
          </div>
        </main>

        {/* SIDEBAR ORACLE */}
        <aside
          className="
            hidden md:flex flex-col
            fixed right-0 inset-y-0
            w-[350px]
            bg-slate-900 border-l border-slate-800
            z-30
          "
        >
          <OracleChat />
        </aside>

      </div>
    </div>
  );
}
