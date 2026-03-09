'use client';

import { Activity, Shield, Cpu, Database, Globe, Clock } from 'lucide-react';

export default function TechnicalPanel() {
// DEMO DATA (Grant Scope):
// These values are static placeholders to expose the system architecture
// and computational semantics. Live binding will be enabled post-grant.

  
  const dignities = [
    { planet: 'Sun', status: 'Peregrine', score: '-2' },
    { planet: 'Moon', status: 'Domicile', score: '+5', positive: true },
    { planet: 'Mars', status: 'Exaltation', score: '+4', positive: true },
    { planet: 'Venus', status: 'Detriment', score: '-5', negative: true },
    { planet: 'Jupiter', status: 'Term', score: '+2', positive: true },
  ];

  return (
    <div className="h-full bg-[#050505] text-slate-400 p-3 font-mono text-xs overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800">
      
      {/* SECCIÓN 1: SYSTEM ARCHITECTURE */}
      <div className="mb-6 border-b border-slate-900 pb-4">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2">
          <Cpu className="w-3 h-3" /> System Architecture
        </h3>
        <div className="space-y-2 text-[11px]">
          <div className="flex justify-between items-center">
            <span>Core Kernel:</span> 
            <span className="text-green-500 font-bold">JAX-Optimized</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Ephemeris Lib:</span> 
            <span className="text-slate-300">SWISS_EPH_2.10</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Geo-Resolver:</span> 
            <span className="text-blue-400">WGS84 / OSRM</span>
          </div>
           <div className="flex justify-between items-center">
            <span>Precision:</span> 
            <span className="text-slate-300">64-bit float</span>
          </div>
        </div>
      </div>

      {/* SECCIÓN 2: COMPUTATION CONTEXT (NUEVO) */}
      <div className="mb-6 border-b border-slate-900 pb-4">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2">
          <Clock className="w-3 h-3" /> Computation Context
        </h3>
        <div className="space-y-2 text-[11px]">
          <div className="flex justify-between">
            <span>Ref. Frame:</span> <span className="text-slate-200">Topocentric</span>
          </div>
          <div className="flex justify-between">
            <span>House Sys:</span> <span className="text-slate-200">Whole Sign (Hellenistic)</span>
          </div>
          <div className="flex justify-between">
            <span>Sidereal Time:</span> <span className="text-slate-500 font-mono">18:42:11 LST</span>
          </div>
           <div className="flex justify-between">
            <span>Ayanamsha:</span> <span className="text-slate-500">N/A (Tropical)</span>
          </div>
        </div>
      </div>

      {/* SECCIÓN 3: ESSENTIAL DIGNITIES */}
      <div className="mb-6 border-b border-slate-900 pb-4">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2">
          <Shield className="w-3 h-3" /> Essential Dignities
        </h3>
        <div className="space-y-1">
          {dignities.map((d) => (
            <div key={d.planet} className="flex justify-between items-center py-1 border-b border-slate-900/50 last:border-0">
              <span className="text-slate-300">{d.planet}</span>
              <div className="flex items-center gap-2">
                <span className={`
                  px-1 rounded text-[10px]
                  ${d.positive ? 'bg-green-900/20 text-green-400' : ''}
                  ${d.negative ? 'bg-red-900/20 text-red-400' : ''}
                  ${!d.positive && !d.negative ? 'text-slate-500' : ''}
                `}>
                  {d.status}
                </span>
                <span className="w-4 text-right text-slate-500">{d.score}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SECCIÓN 4: SCHEME RULERS */}
      <div className="mb-6">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2">
          <Database className="w-3 h-3" /> Scheme Controllers
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-slate-900/30 p-2 rounded border border-slate-800">
            <div className="text-[9px] text-slate-500 mb-1">ASC RULER</div>
            <div className="text-sm text-yellow-500 font-semibold">Saturn</div>
          </div>
          <div className="bg-slate-900/30 p-2 rounded border border-slate-800">
            <div className="text-[9px] text-slate-500 mb-1">MC RULER</div>
            <div className="text-sm text-slate-200 font-semibold">Mars</div>
          </div>
          <div className="bg-slate-900/30 p-2 rounded border border-slate-800 col-span-2">
            <div className="text-[9px] text-slate-500 mb-1">SECT MASTER</div>
            <div className="text-sm text-slate-200 flex justify-between items-center">
              <span>Jupiter</span>
              <span className="text-slate-500 text-[10px] bg-slate-800 px-1 rounded">DIURNAL</span>
            </div>
          </div>
        </div>
      </div>
      
    </div>
  );
}