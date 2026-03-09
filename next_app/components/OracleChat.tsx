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
import { useAppStore } from "@/lib/store"; 
import { Send, Terminal } from "lucide-react";

/* ---------------------------------------------------------
   TerminalMessage
   ---------------------------------------------------------
   Renderiza la respuesta del LLM con efecto de tipeo
   estilo terminal (UX técnico / demo grant).
--------------------------------------------------------- */
const TerminalMessage = ({ content }: { content: string }) => {
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
   ORACLE CHAT – MAIN COMPONENT
--------------------------------------------------------- */
export default function OracleChat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Evita doble inicialización en React.StrictMode
  const initialized = useRef(false);

  // Store global (NO asumir tipos internos)
  // @ts-ignore
  const { abuData, birthData } = useAppStore();

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /* -----------------------------------------------------
     SYSTEM MESSAGE AUTOMÁTICO
     -----------------------------------------------------
     Se inyecta una sola vez cuando hay datos calculados.
     Evita UI vacía y comunica estado técnico al evaluador.
  ----------------------------------------------------- */
  useEffect(() => {
    if (!initialized.current && abuData) {
      initialized.current = true;

      setMessages([
        {
          id: 'sys-init',
          role: 'assistant',
          content:
`> SYSTEM_READY
> ABU ENGINE: CONNECTED
> DATA CONTEXT: ${birthData ? 'TEMPORAL + GEOSPATIAL ANCHOR LOADED' : 'NO INPUT DATA'}

Lilly is online.
You may query chart significance, planetary geometry,
or timing vectors derived from the current computation.`
        }
      ]);
    }
  }, [abuData, birthData]);

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
          session_id: "sidebar-session-v1"
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
      console.error(error);
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
        {messages.map((m) => (
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
