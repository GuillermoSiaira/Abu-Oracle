"use client";

import { useChat } from 'ai/react';
import { useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';

export default function LillyPanel() {
  // --- EL FIX ESTÁ AQUÍ ---
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat', // <--- ESTA LÍNEA ES LA SOLUCIÓN AL ERROR 401
    onError: (error) => {
      console.error("❌ Error en el chat lateral:", error);
    }
  });

  // Auto-scroll al recibir mensajes
  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] border-l border-white/10 text-gray-100">
      {/* HEADER DEL SIDEBAR */}
      <div className="p-4 border-b border-white/10 flex items-center gap-2 bg-[#12121a]">
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        <h2 className="font-serif tracking-wider text-amber-500 font-bold text-sm">
          ORÁCULO VIVO
        </h2>
      </div>

      {/* ÁREA DE MENSAJES */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-xs text-gray-500 mt-10 px-4">
            <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-20" />
            <p>Lilly está escuchando.</p>
            <p className="mt-2">Pregunta sobre tus tránsitos o pide un consejo rápido.</p>
          </div>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[90%] rounded-lg px-3 py-2 text-xs md:text-sm ${
                m.role === 'user'
                  ? 'bg-amber-600/20 text-amber-100 border border-amber-500/30'
                  : 'bg-purple-900/20 text-purple-100 border border-purple-500/30'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="text-xs text-gray-500 italic animate-pulse">
              Consultando a los astros...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* INPUT AREA */}
      <div className="p-3 border-t border-white/10 bg-[#12121a]">
        <form onSubmit={handleSubmit} className="relative">
          <input
            className="w-full bg-black/30 border border-white/10 rounded-md pl-3 pr-10 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 placeholder:text-gray-600"
            value={input}
            onChange={handleInputChange}
            placeholder="Pregunta a los astros..."
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute right-2 top-1.5 text-gray-400 hover:text-amber-500 disabled:opacity-50 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
