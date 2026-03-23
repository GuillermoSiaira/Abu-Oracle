/*
Abu Oracle – OracleChat.tsx
============================================================
Estado: CONSOLIDATED / GRANT-READY
Fecha: 2026-02-01

Objetivo:
---------
Este componente actúa como la interfaz conversacional técnica
entre el usuario y Lilly (LLM), con inyección explícita de contexto
astronómico y geoespacial calculado por Abu Engine.

Principios de diseño:
---------------------
1. NO asumir estructura interna de birthData (evita errores TS).
2. NO romper contratos existentes con backend (/api/chat).
3. UX tipo "terminal técnica", no chatbot genérico.
4. Inyección automática de System Message (evita pantalla vacía).
5. Compatible con React.StrictMode (doble render en dev).

Notas importantes:
------------------
- Este archivo ya causó errores críticos en el pasado.
- Cualquier cambio debe preservar la semántica del contexto enviado.
- El autocomplete de ciudad depende de otros componentes:
  ESTE ARCHIVO NO DEBE TOCAR ESA LÓGICA.
*/

'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAppStore } from "@/lib/store";
import { Send, Terminal } from "lucide-react";
import { UI } from '@/lib/i18n';
import { getAbuAuthHeaders } from '@/lib/abu-auth';
import { ABU_BASE_URL } from '@/services/abu';

/* ---------------------------------------------------------
   TerminalMessage
   ---------------------------------------------------------
   Renderiza la respuesta del LLM con efecto de tipeo
   estilo terminal (UX técnico / demo grant).
--------------------------------------------------------- */
export const TerminalMessage = ({ content }: { content: string }) => {
  const [displayedContent, setDisplayedContent] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (!content) return;

    setIsTyping(true);
    let i = 0;
    const speed = 1; // rápido, estilo consola técnica

    const timer = setInterval(() => {
      setDisplayedContent(content.slice(0, i + 1));
      i++;
      if (i >= content.length) {
        clearInterval(timer);
        setIsTyping(false);
      }
    }, speed);

    return () => clearInterval(timer);
  }, [content]);

  return (
    <div className="w-full overflow-hidden">
      <pre className="whitespace-pre-wrap break-words font-mono text-green-400/90 text-xs md:text-sm leading-relaxed">
        {displayedContent}
        {isTyping && (
          <span className="inline-block w-2 h-4 bg-green-500 ml-1 animate-pulse align-middle" />
        )}
      </pre>
    </div>
  );
};

/* ---------------------------------------------------------
   LillyWelcome
   ---------------------------------------------------------
   Empty-state block shown when no chart is loaded.
   Reuses TerminalMessage for typewriter effect.
   CTAs appear after the typewriter finishes (~text.length ms).
--------------------------------------------------------- */
function LillyWelcome({ t }: { t: (typeof UI)[keyof typeof UI] }) {
  const [showCtas, setShowCtas] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowCtas(true), t.lillyWelcome.length + 500);
    return () => clearTimeout(timer);
  }, [t.lillyWelcome.length]);

  return (
    <div className="p-4 space-y-5 mt-6">
      <TerminalMessage content={t.lillyWelcome} />
      {showCtas && (
        <div className="flex flex-col gap-2 pl-1">
          <Link
            href="/"
            className="text-xs font-mono text-amber-400/80 hover:text-amber-300 border border-amber-500/20 hover:border-amber-400/40 rounded-sm px-3 py-1.5 transition-colors w-fit"
          >
            → {t.lillyCtaData}
          </Link>
          <Link
            href="/relocation"
            className="text-xs font-mono text-green-400/60 hover:text-green-300 border border-green-500/10 hover:border-green-400/30 rounded-sm px-3 py-1.5 transition-colors w-fit"
          >
            → {t.lillyCtaDemo}
          </Link>
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------
   ORACLE CHAT – MAIN COMPONENT
--------------------------------------------------------- */
export default function OracleChat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Evita doble inicialización en React.StrictMode
  const initialized = useRef(false);
  // Detecta cambio de sujeto para resetear el chat
  const prevAbuRef = useRef<any>(undefined);

  // Store global (NO asumir tipos internos)
  // @ts-ignore
  const { abuData, birthData, lang, pendingLillyEvent, setPendingLillyEvent, setLastLillyEvent, setLillySuggestions, setTimeline, timeline } = useAppStore();
  const t = UI[lang as keyof typeof UI] ?? UI.es;
  const pathname = usePathname();
  const isChartPage = pathname === '/chart';

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /* -----------------------------------------------------
     SCREEN_OPEN — LILLY INITIAL ORIENTATION
     -----------------------------------------------------
     Fires once when abuData + birthData are available.
     Calls /api/lilly/screen-open with minimal AbuContext
     and injects the LLM response with typewriter effect.
  ----------------------------------------------------- */
  useEffect(() => {
    // Reset chat when subject changes (new abuData object)
    if (prevAbuRef.current !== undefined && prevAbuRef.current !== abuData) {
      initialized.current = false;
      setMessages([]);
      setLastLillyEvent(null);
      setLillySuggestions(null);
      setTimeline(null);
    }
    prevAbuRef.current = abuData;

    const isComplete = (d: any) => Array.isArray(d?.chart?.planets) && d.chart.planets.length > 0;
    if (!initialized.current && isChartPage && isComplete(abuData) && birthData) {
      initialized.current = true;

      // --- Fetch biography (timeline) — una vez por sujeto ---
      const bDate = (birthData as any).birthDate;
      const bLat  = (birthData as any).lat;
      const bLon  = (birthData as any).lon;
      if (bDate && bLat != null && bLon != null) {
        const bioUrl = new URL(`${ABU_BASE_URL}/api/astro/biography`);
        bioUrl.searchParams.set('birthDate', bDate);
        bioUrl.searchParams.set('birthLat',  String(bLat));
        bioUrl.searchParams.set('birthLon',  String(bLon));
        bioUrl.searchParams.set('window_months', '18');
        getAbuAuthHeaders()
          .then(headers => fetch(bioUrl.toString(), { headers }))
          .then(res => res.ok ? res.json() : Promise.reject(res.status))
          .then(data => setTimeline(data))
          .catch(err => console.error('[biography]', err));
      }

      // --- Build minimal context from abuData ---
      const name =
        (birthData as any)?.userName ||
        (abuData as any)?.person?.name ||
        'Anónimo';

      const sect = (abuData as any)?.derived?.sect ?? null;
      const sectMaster = sect === 'diurnal' ? 'Jupiter' : 'Venus';

      const SIGNS = [
        'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
        'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces',
      ];
      const RULERSHIPS: Record<string, string> = {
        Aries: 'Mars', Taurus: 'Venus', Gemini: 'Mercury', Cancer: 'Moon',
        Leo: 'Sun', Virgo: 'Mercury', Libra: 'Venus', Scorpio: 'Mars',
        Sagittarius: 'Jupiter', Capricorn: 'Saturn', Aquarius: 'Saturn', Pisces: 'Jupiter',
      };

      const houses = (abuData as any)?.chart?.houses;
      const ascLon: number | null = houses?.asc ?? null;
      const mcLon: number | null = houses?.mc ?? null;
      const ascSign = ascLon != null ? SIGNS[Math.floor(ascLon / 30) % 12] : null;
      const mcSign = mcLon != null ? SIGNS[Math.floor(mcLon / 30) % 12] : null;
      const ascRuler = ascSign ? (RULERSHIPS[ascSign] ?? null) : null;
      const mcRuler = mcSign ? (RULERSHIPS[mcSign] ?? null) : null;

      const planets: any[] = (abuData as any)?.chart?.planets ?? [];

      const dignityKind = (d: any): string | null => {
        if (!d) return null;
        if (d.domicile || d.kind === 'domicile') return 'Domicile';
        if (d.exaltation || d.kind === 'exaltation') return 'Exaltation';
        return null;
      };
      const planetDignity = (pName: string): string => {
        const p = planets.find((pl: any) => pl.name === pName);
        if (!p?.dignity) return 'Peregrine';
        const d = p.dignity;
        if (d.domicile || d.kind === 'domicile') return 'Domicile';
        if (d.exaltation || d.kind === 'exaltation') return 'Exaltation';
        if (d.detriment || d.kind === 'detriment') return 'Detriment';
        if (d.fall || d.kind === 'fall') return 'Fall';
        return 'Peregrine';
      };

      const strongDignities = planets
        .filter((p: any) => dignityKind(p.dignity) !== null)
        .slice(0, 2)
        .map((p: any) => ({ planet: p.name, dignity: dignityKind(p.dignity)! }));

      const firdaria = (abuData as any)?.derived?.firdaria?.current ?? null;

      // Show loading indicator immediately
      setIsLoading(true);

      fetch('/api/lilly/screen-open', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          sect,
          sect_master: sectMaster,
          asc_ruler: ascRuler,
          asc_ruler_dignity: ascRuler ? planetDignity(ascRuler) : null,
          mc_ruler: mcRuler,
          mc_ruler_dignity: mcRuler ? planetDignity(mcRuler) : null,
          strong_dignities: strongDignities,
          firdaria_major: firdaria?.major ?? null,
          firdaria_minor: firdaria?.sub ?? null,
          lang,
          natalData: abuData,
          birthData: birthData ?? undefined,
          timeline:  timeline ?? undefined,
          messages,
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          const text: string = data.response || `> ERROR: ${data.error ?? 'LILLY_UNREACHABLE'}`;
          setMessages([
            { id: `screen-open-user-${Date.now()}`, role: 'user', content: '[carta_cargada]', hidden: true },
            { id: 'screen-open', role: 'assistant', content: text },
          ]);
          if (Array.isArray(data.suggestions) && data.suggestions.length > 0) {
            setLillySuggestions(data.suggestions);
          }
        })
        .catch(() => {
          setMessages([{
            id: 'screen-open',
            role: 'assistant',
            content: '> LILLY_AI: Sin conexión.\n> Configura ANTHROPIC_API_KEY para activar la interpretación.',
          }]);
        })
        .finally(() => setIsLoading(false));
    }
  }, [abuData, birthData, lang, isChartPage]);

  /* -----------------------------------------------------
     LILLY EVENT — REACTIVE (click_planet, etc.)
     -----------------------------------------------------
     Fires whenever natal-chart-tab (or any component) sets
     pendingLillyEvent in the store.
  ----------------------------------------------------- */
  useEffect(() => {
    if (!pendingLillyEvent) return;

    const { type, payload } = pendingLillyEvent as { type: string; payload: any };
    // Clear immediately to avoid re-fire
    setPendingLillyEvent(null);

    // Track last event for TechnicalPanel "Leyendo Ahora"
    const deriveLabel = (t: string, p: any): string => {
      if (t === 'click_planet') return p?.planet_name || p?.name || 'Planeta';
      if (t === 'click_technique') {
        const tech = p?.technique ?? '';
        if (tech === 'sect') return 'Secta';
        if (tech === 'profection') return 'Profección';
        if (tech === 'firdaria') return 'Firdaria';
        if (tech === 'lot_fortuna' || (tech === 'lot' && p?.data?.lot_name === 'fortuna')) return 'Parte de Fortuna';
        if (tech === 'lot_spirit' || (tech === 'lot' && p?.data?.lot_name === 'spirit')) return 'Parte del Espíritu';
        if (tech === 'lunar_transit') return 'Tránsito Lunar';
        if (tech === 'planetary_cycle') return p?.data?.planet ?? 'Ciclo Planetario';
        return tech;
      }
      if (t === 'domain_select') return `Dominio ${p?.domain ?? ''}`;
      if (t === 'sr_domain_select') return `SR ${p?.sr_year ?? ''} · ${p?.domain ?? ''}`;
      if (t === 'click_transit') return `${p?.transit_planet ?? 'Tránsito'} en ${p?.transit_sign ?? ''}`;

      if (t === 'city_select') return p?.city_name || 'Ciudad';
      return t;
    };
    setLastLillyEvent({ type, label: deriveLabel(type, payload) });

    const routeMap: Record<string, string> = {
      click_planet: '/api/lilly/planet',
      click_technique: '/api/lilly/technique',
      domain_select: '/api/lilly/domain',
      sr_domain_select: '/api/lilly/solar-return',
      click_transit: '/api/lilly/transit',
      city_select: '/api/lilly/city',
    };
    const route = routeMap[type];
    if (!route) return;

    setIsLoading(true);
    fetch(route, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        natalData: abuData,
        birthData: birthData ?? undefined,
        timeline:  timeline ?? undefined,
        messages,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        const text: string = data.response || `> ERROR: ${data.error ?? 'LILLY_UNREACHABLE'}`;
        const ts = Date.now();
        setMessages((prev) => [
          ...prev,
          { id: `${type}-user-${ts}`, role: 'user', content: `[${type}]`, hidden: true },
          { id: `${type}-${ts}`, role: 'assistant', content: text },
        ]);
      })
      .catch(() => {
        setMessages((prev) => [
          ...prev,
          {
            id: `${type}-err-${Date.now()}`,
            role: 'assistant',
            content: '> LILLY_AI: Sin conexión.',
          },
        ]);
      })
      .finally(() => setIsLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingLillyEvent]);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  /* -----------------------------------------------------
     HANDLE SUBMIT
     -----------------------------------------------------
     Envia:
     - Historial de mensajes
     - Contexto estructurado (meta + cálculos)
     - Sin suposiciones de campos opcionales
  ----------------------------------------------------- */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput("");
    setIsLoading(true);

    const newMsg = { id: Date.now(), role: 'user', content: userText };
    setMessages(prev => [...prev, newMsg]);

    try {
      const sessionContext = {
        meta: birthData ? {
          date: birthData.birthDate,
          // city puede no existir tipado → defensive access
          city: (birthData as any)?.city || "Unknown",
          lat: birthData.lat,
          lon: birthData.lon
        } : "No temporal context",
        calculations: abuData
      };

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, newMsg],
          context: sessionContext,
          session_id: "sidebar-session-v1",
          timeline: timeline ?? undefined,
        })
      });

      if (!res.ok) throw new Error("Connection error");

      const data = await res.json();
      const aiText = data.response || "No response vector.";

      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: aiText
        }
      ]);

    } catch (error) {
      console.warn('[handleSubmit]', error);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: "> ERROR: LINK_LOST. Lilly is unreachable."
        }
      ]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  /* -----------------------------------------------------
     RENDER
  ----------------------------------------------------- */
  return (
    <div className="flex flex-col h-full bg-[#080808] text-slate-300 font-sans">

      {/* HEADER */}
      <div className="p-3 border-b border-slate-800 bg-[#050505] flex items-center justify-between shrink-0">
        <h2 className="text-[10px] font-bold text-green-500 uppercase tracking-widest flex items-center gap-2">
          <Terminal className="w-3 h-3" />
          Oracle Interface
        </h2>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-green-900/20 px-1.5 py-0.5 rounded border border-green-900/30">
            <div className="w-1 h-1 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-[9px] text-green-400 font-mono">ONLINE</span>
          </div>
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.length === 0 && (
          <div className="p-4 mt-4 font-mono text-xs text-green-500/70 space-y-1">
            <p>&gt; SYSTEM_READY</p>
            <p>&gt; ABU ENGINE: CONNECTED</p>
            <p>&gt; AWAITING INPUT</p>
          </div>
        )}
        {messages.filter(m => !m.hidden).map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <span className="text-[9px] uppercase text-slate-600 mb-1 px-1 font-mono">
              {m.role === 'user' ? 'OPERATOR' : 'LILLY_AI'}
            </span>

            <div
              className={`max-w-[90%] rounded-sm p-3 text-sm shadow-sm border ${
                m.role === 'user'
                  ? 'bg-slate-800/60 border-slate-700 text-slate-200 font-sans'
                  : 'bg-[#0a0a0a] border-green-900/20 w-full font-mono shadow-inner'
              }`}
            >
              {m.role === 'user'
                ? <p className="whitespace-pre-wrap">{m.content}</p>
                : <TerminalMessage content={m.content} />
              }
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="text-xs text-green-500/70 animate-pulse pl-1 font-mono mt-2">
            &gt; PROCESSING VECTOR...
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* INPUT */}
      <form
        onSubmit={handleSubmit}
        className="p-3 bg-[#050505] border-t border-slate-800 shrink-0 flex gap-2"
      >
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter command or query..."
          className="flex-1 bg-slate-900/30 border border-slate-800 rounded-sm px-3 py-2 text-sm text-green-400 focus:outline-none focus:border-green-600/50 placeholder-slate-700 font-mono"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="bg-slate-900 text-green-500 hover:bg-green-900/20 hover:text-green-400 disabled:opacity-30 rounded-sm px-3 border border-slate-800 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

    </div>
  );
}
