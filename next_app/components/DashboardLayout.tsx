'use client';

import { ReactNode } from 'react';
import Navigation from './Navigation';
import OracleChat from './OracleChat';
import TechnicalPanel from './TechnicalPanel'; 

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200 overflow-hidden font-sans">
      
      {/* 1. TOP BAR (Navigation) */}
      <div className="shrink-0 z-20 border-b border-slate-800 bg-[#0a0a0a]">
        <Navigation />
      </div>

      {/* 2. MAIN WORKSPACE (Split View) */}
      <div className="flex flex-1 overflow-hidden relative">

        {/* COLUMNA IZQUIERDA: Contexto Técnico */}
        <aside className="
            hidden lg:flex flex-col 
            w-[280px] shrink-0
            bg-[#050505] border-r border-slate-800 
            z-10
        ">
           <TechnicalPanel /> 
        </aside>

        {/* COLUMNA CENTRAL: Visualización Principal */}
        <main className="flex-1 overflow-y-auto relative bg-slate-950">
          {children}
        </main>

        {/* COLUMNA DERECHA: Oracle Chat */}
        <aside className="
            hidden md:flex flex-col
            w-[350px] xl:w-[400px] shrink-0
            bg-[#050505] border-l border-slate-800
            z-30 shadow-[0_0_15px_rgba(0,0,0,0.5)]
          "
        >
          <OracleChat />
        </aside>

      </div>
    </div>
  );
}