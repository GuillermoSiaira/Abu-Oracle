'use client';

import { useState, useRef, useEffect } from 'react';
import { useAppStore } from "@/lib/store"; 
import { Send, Terminal } from "lucide-react";

// --- COMPONENTE TERMINAL TYPER ---
const TerminalMessage = ({ content }: { content: string }) => {
  const [displayedContent, setDisplayedContent] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (!content) return;
    setIsTyping(true);
    let i = 0;
    const speed = 2; 
    
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
      <pre className="whitespace-pre-wrap break-words font-mono text-green-400 text-xs md:text-sm leading-relaxed">
        {displayedContent}
        {isTyping && (
          <span className="inline-block w-2 h-4 bg-green-400 ml-1 animate-pulse align-middle" />
        )}
      </pre>
    </div>
  );
};

// --- COMPONENTE PRINCIPAL: ORACLE CHAT (SIDEBAR) ---
export default function OracleChat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // @ts-ignore
  const abuData = useAppStore((state) => state.abuData);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput("");
    setIsLoading(true);

    const newMsg = { id: Date.now(), role: 'user', content: userText };
    setMessages(prev => [...prev, newMsg]);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, newMsg], 
          context: abuData,
          session_id: "sidebar-session-v1"
        })
      });

      if (!res.ok) throw new Error("Error en conexión");

      const data = await res.json();
      const aiText = data.response || "Sin respuesta.";

      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: 'assistant', 
        content: aiText 
      }]);

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: 'assistant', 
        content: "[ERROR DE CONEXIÓN] Lilly no responde." 
      }]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#050505] border-l border-green-900/30 font-mono">
      
      {/* HEADER SIDEBAR */}
      <div className="p-3 border-b border-green-900/30 bg-[#0a0a0a] flex items-center justify-between">
        <h2 className="text-xs font-bold text-green-500 uppercase tracking-widest flex items-center gap-2">
          <Terminal className="w-3 h-3" />
          Terminal Oráculo
        </h2>
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_#00ff00]"></div>
      </div>

      {/* LISTA DE MENSAJES */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-green-900 scrollbar-track-black">
        {messages.length === 0 && (
          <div className="text-center text-green-800 text-xs mt-10 select-none">
            {/* AQUÍ ESTABA EL ERROR: Usamos &gt; en lugar de > */}
            <p className="mb-2">&gt; ENLACE ESTABLECIDO</p>
            <p>&gt; ESPERANDO CONSULTA...</p>
          </div>
        )}
        
        {messages.map((m) => (
          <div key={m.id} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
            <span className="text-[10px] uppercase text-green-700 mb-1">
              {m.role === 'user' ? 'TÚ >>' : 'LILLY >>'}
            </span>
            
            <div className={`max-w-[95%] rounded-sm p-2 text-sm border ${
              m.role === 'user' 
                ? 'bg-yellow-900/10 border-yellow-600/30 text-yellow-100' 
                : 'bg-black border-green-900/50 w-full'
            }`}>
              {m.role === 'user' ? (
                <p className="whitespace-pre-wrap">{m.content}</p>
              ) : (
                <TerminalMessage content={m.content} />
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="text-xs text-green-500 animate-pulse pl-1">
            &gt; PROCESANDO...
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* INPUT FOOTER */}
      <form onSubmit={handleSubmit} className="p-3 bg-[#0a0a0a] border-t border-green-900/30 flex gap-2">
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Comando de entrada..."
          className="flex-1 bg-black/40 border border-green-900/50 rounded-sm py-2 px-3 text-sm text-green-400 focus:outline-none focus:border-green-500 placeholder-green-900"
          disabled={isLoading}
        />
        <button 
          type="submit" 
          disabled={isLoading || !input.trim()}
          className="text-xs bg-green-700 text-black font-bold px-3 py-2 rounded-sm hover:bg-green-600 disabled:opacity-50 disabled:bg-green-900 uppercase tracking-wider"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}