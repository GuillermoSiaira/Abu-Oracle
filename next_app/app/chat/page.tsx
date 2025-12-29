"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Terminal, Cpu, Activity } from "lucide-react";
import { useAppStore } from "@/lib/store";

// --- SUB-COMPONENTE: TERMINAL TYPER (CORREGIDO) ---
// Maneja la estética de escritura y asegura que el texto sea visible
const TerminalMessage = ({ content }: { content: string }) => {
  const [displayedContent, setDisplayedContent] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (!content) return;
    
    setIsTyping(true);
    let i = 0;
    // Velocidad un poco más rápida para UX fluida
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

  // Si no hay contenido, mostramos un placeholder para debug visual
  if (!content) return <div className="text-gray-600 text-xs font-mono animate-pulse">[Esperando datos del flujo...]</div>;

  return (
    <div className="w-full bg-black/40 p-3 rounded border border-green-900/30 overflow-hidden">
      {/* FIX VISUAL: 
         - whitespace-pre-wrap: Respeta los espacios de tus tablas ASCII.
         - break-words: Evita que líneas muy largas rompan el layout horizontal.
      */}
      <pre className="whitespace-pre-wrap break-words font-mono text-green-400 text-sm md:text-base leading-relaxed">
        {displayedContent}
        {isTyping && (
          <span className="inline-block w-2 h-4 bg-green-400 ml-1 animate-pulse align-middle" />
        )}
      </pre>
    </div>
  );
};

// --- COMPONENTE PRINCIPAL: CHAT PAGE ---

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // @ts-ignore
  const abuData = useAppStore((state) => state.abuData);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || isLoading) return;

    // 1. Mensaje Usuario
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      timestamp: new Date().toLocaleTimeString(),
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      console.log("🚀 Enviando a Lilly. Contexto activo:", !!abuData);

      // 2. Fetch al backend
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [
            ...messages.map(m => ({ role: m.role, content: m.content })),
            { role: "user", content: question }
          ],
          context: abuData, 
          session_id: "user-session-v1"
        })
      });

      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);

      const data = await res.json();
      
      // DEBUG LOG: Esto aparecerá en la consola del navegador (F12)
      console.log("✅ RESPUESTA RECIBIDA:", data);

      // 3. Procesar respuesta
      const aiText = data.response || "Error: El oráculo devolvió una respuesta vacía.";

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: aiText,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

    } catch (err) {
      console.error("🔴 Error en el frontend:", err);
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `[SYSTEM ERROR] Fallo en el enlace neural.\n${err}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#050505] text-green-500 font-mono selection:bg-green-900/50 overflow-hidden">
      
      {/* HEADER */}
      <header className="px-4 py-3 bg-[#0a0a0a] border-b border-green-900/30 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Terminal className="w-5 h-5 text-green-600" />
          <h1 className="text-sm md:text-base tracking-widest text-green-400 font-bold uppercase">
            Abu Oracle <span className="text-green-800">::</span> Lilly Swarm Uplink
          </h1>
        </div>
        <div className="flex items-center gap-4 text-xs text-green-700">
          <div className="flex items-center gap-1">
            <Cpu className="w-3 h-3" />
            <span>CORE: ONLINE</span>
          </div>
          <div className="flex items-center gap-1">
            <Activity className="w-3 h-3" />
            <span>NET: STABLE</span>
          </div>
        </div>
      </header>

      {/* MAIN CHAT AREA */}
      <main className="flex-1 overflow-y-auto p-4 md:p-6 scroll-smooth scrollbar-thin scrollbar-thumb-green-900 scrollbar-track-black">
        
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center opacity-40 select-none">
            <div className="border border-green-800 p-8 rounded bg-[#0a0a0a]">
              <p className="mb-2">&gt; INICIANDO PROTOCOLO ABU...</p>
              <p className="mb-2">&gt; CARGANDO EFEMÉRIDES...</p>
              <p className="animate-pulse">&gt; ESPERANDO INPUT DEL USUARIO_</p>
            </div>
          </div>
        )}

        <div className="space-y-6 max-w-5xl mx-auto">
          {messages.map((m) => (
            <div key={m.id} className="flex flex-col gap-1">
              
              <div className="flex items-center gap-2 text-xs uppercase tracking-wider opacity-70 mb-1 border-b border-green-900/20 pb-1 w-full">
                <span className={m.role === 'user' ? "text-yellow-500" : "text-green-600"}>
                  {m.role === 'user' ? "USER >>" : "LILLY >>"}
                </span>
                <span className="text-green-900 ml-auto">{m.timestamp}</span>
              </div>

              <div className={`rounded-sm border-l-2 ${
                m.role === 'user' 
                  ? "border-yellow-600/50 bg-yellow-900/10 text-yellow-100 p-3" 
                  : "border-green-600/50 bg-transparent pl-0"
              }`}>
                {m.role === 'user' ? (
                  <p className="whitespace-pre-wrap break-words">{m.content}</p>
                ) : (
                  <TerminalMessage content={m.content} />
                )}
              </div>

            </div>
          ))}

          {isLoading && (
            <div className="text-green-700 text-sm animate-pulse font-mono pl-2">
              &gt; PROCESANDO CÁLCULOS EN EL VECTOR ESPACIAL...
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* INPUT AREA */}
      <div className="p-4 bg-[#0a0a0a] border-t border-green-900/30 shrink-0">
        <form
          onSubmit={handleSubmit}
          className="max-w-5xl mx-auto flex items-center gap-3 bg-black border border-green-800/50 p-2 rounded-sm focus-within:border-green-500 transition-colors"
        >
          <span className="text-green-600 pl-2 animate-pulse">&gt;</span>
          <input
            ref={inputRef}
            className="flex-1 bg-transparent border-none text-green-400 placeholder-green-900 focus:ring-0 focus:outline-none font-mono"
            value={input}
            onChange={handleInputChange}
            placeholder="Ingrese comando o pregunta..."
            disabled={isLoading}
            autoComplete="off"
            autoFocus
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 text-black bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:bg-green-900 transition-colors rounded-sm uppercase font-bold text-xs tracking-wider px-4"
          >
            <span className="hidden md:inline">Transmitir</span>
            <Send className="w-4 h-4 md:hidden" />
          </button>
        </form>
      </div>
    </div>
  );
}