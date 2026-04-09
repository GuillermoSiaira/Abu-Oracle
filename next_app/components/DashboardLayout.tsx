'use client';

import { ReactNode, useState, useRef, useEffect } from 'react';
import Navigation from './Navigation';
import OracleChat from './OracleChat';
import TechnicalPanel from './TechnicalPanel';
import { useAppStore } from '@/lib/store';

const MIN_WIDTH = 300;
const MAX_WIDTH = 700;
const DEFAULT_WIDTH = 440;

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const chartSidebarExpanded = useAppStore((s) => s.chartSidebarExpanded);
  const [oracleWidth, setOracleWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      return parseInt(localStorage.getItem('oracleWidth') ?? String(DEFAULT_WIDTH));
    }
    return DEFAULT_WIDTH;
  });

  // Ref para el ancho durante el drag — evita closures stale en los event listeners
  const isDragging = useRef(false);
  const widthRef = useRef(oracleWidth);

  const handleMouseDown = () => {
    isDragging.current = true;
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return;
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        widthRef.current = newWidth;
        setOracleWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      if (isDragging.current) {
        isDragging.current = false;
        localStorage.setItem('oracleWidth', String(widthRef.current));
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []); // sin deps — handlers leen refs, no state

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200 overflow-hidden font-sans">

      {/* 1. TOP BAR (Navigation) */}
      <div className="shrink-0 z-20 border-b border-slate-800 bg-[#0a0a0a]">
        <Navigation />
      </div>

      {/* 2. MAIN WORKSPACE (Split View) */}
      <div className="flex flex-1 overflow-hidden relative">

        {/* COLUMNA IZQUIERDA: Contexto Técnico */}
        <aside
          className={`hidden lg:flex flex-col shrink-0 bg-[#050505] border-r border-slate-800
            transition-all duration-200 z-10
            ${chartSidebarExpanded ? 'w-[220px]' : 'w-[48px]'}
          `}
        >
          <TechnicalPanel />
        </aside>

        {/* COLUMNA CENTRAL: Visualización Principal */}
        <main className="flex-1 overflow-y-auto relative bg-slate-950">
          {children}
        </main>

        {/* DIVISOR ARRASTRABLE */}
        <div
          onMouseDown={handleMouseDown}
          className="hidden md:block w-1 shrink-0 cursor-col-resize bg-transparent hover:bg-amber-400/30 active:bg-amber-400/50 transition-colors z-40"
        />

        {/* COLUMNA DERECHA: Oracle Chat — ancho dinámico */}
        <aside
          className="hidden md:flex flex-col shrink-0 bg-[#050505] border-l border-slate-800 z-30 shadow-[0_0_15px_rgba(0,0,0,0.5)]"
          style={{ width: oracleWidth }}
        >
          <OracleChat />
        </aside>

      </div>
    </div>
  );
}
