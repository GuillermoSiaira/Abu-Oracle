# AI Oracle — Troubleshooting de Protocolo de Chat y Comparativa de Diagnóstico IA

## Resumen del Incidente

Durante la integración del chat entre el frontend (Next.js + AI SDK v3+) y el backend (Lilly Swarm), se detectó un bug crítico: el chat no mostraba mensajes y arrojaba el error:

```
Failed to parse stream string. Invalid code data.
```

Tras análisis con Gemini y ChatGPT, se identificó que el problema era de **protocolo de transporte** entre el adaptador de Next.js (`route.ts`) y el hook `useChat` del frontend.

---

## Diagnóstico y Solución

- **NO** es un bug de Abu, Lilly, Docker, ni de lógica de backend.
- El bug es de **idioma/protocolo** entre el adaptador y el frontend.
- El frontend espera el **Data Stream Protocol (DSP)** (formato `0:"texto"` y header `X-Vercel-AI-Data-Stream: v1`), pero el backend enviaba **Server-Sent Events clásico** (formato `data: ...`).

### Solución correcta (DSP):
```typescript
const stream = new ReadableStream<Uint8Array>({
  start(controller) {
    controller.enqueue(encoder.encode(`0:${text}\n`));
    controller.close();
  },
});

return new Response(stream, {
  headers: {
    "Content-Type": "text/plain; charset=utf-8",
    "X-Vercel-AI-Data-Stream": "v1",
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
  },
});
```

---

## Tablas Comparativas de Diagnóstico

### Tabla 1 — Análisis de Gemini

| Componente                | Función en tu App                                   | Estado Actual | ¿Dónde estaba el Bug?         |
|--------------------------|-----------------------------------------------------|---------------|-------------------------------|
| Usuario                  | Escribe "Hola" en el navegador.                     | ✅ OK         | N/A                           |
| Frontend (Next.js)       | useChat recibe el input y hace POST a /api/chat.     | ✅ OK         | N/A                           |
| API Route (Next.js)      | Recibe el POST y se conecta con Docker.              | ✅ OK         | N/A                           |
| Red Docker               | Resuelve http://lilly_swarm:8001.                    | ✅ OK         | N/A                           |
| Lilly (Python)           | Procesa el mensaje y genera respuesta.               | ✅ OK         | N/A                           |
| Lilly (Python)           | Devuelve JSON: {"response": "Hola..."} a Next.js.   | ✅ OK         | N/A                           |
| API Route (Adaptador)    | Transforma el JSON de Python en un Stream.           | ⚠️            | AQUÍ FALLABA                  |
| Frontend (Parser)        | Recibe el Stream y lo escribe en pantalla.           | ❌ CRASH      | Mismatch de protocolo         |

### Tabla 2 — Comparativa Técnica ChatGPT vs Gemini

| Capa                        | Estado real del sistema   | Propuesta ChatGPT (anterior) | Propuesta Gemini           | Veredicto   |
|-----------------------------|--------------------------|------------------------------|----------------------------|-------------|
| Frontend (useChat, AI SDK)  | Usa AI SDK v3.4+         | SSE clásico                  | Data Stream Protocol (DSP) | ✅ Gemini    |
| Protocolo esperado          | 0:"texto" (DSP)          | data: "texto" (SSE)          | 0:"texto"                 | ✅ Gemini    |
| Error visible               | Failed to parse stream    | Error genérico de stream     | Mismatch de protocolo      | ✅ Gemini    |
| Backend Python (Lilly)      | Devuelve JSON completo    | Correcto                     | Correcto                   | ✅ Ambos     |
| Next.js route.ts            | Debe traducir protocolo   | JSON → SSE                   | JSON → DSP                 | ✅ Gemini    |
| Formato de salida           | Texto fragmentado         | text/event-stream con data:  | text/plain + 0: + header   | ✅ Gemini    |
| Header clave                | X-Vercel-AI-Data-Stream   | ❌ ausente                   | ✅ presente                 | ✅ Gemini    |
| Compatibilidad futura       | AI SDK v3+                | ❌ se rompe                   | ✅ alineada                 | ✅ Gemini    |
| Naturaleza de la solución   | Adaptador legítimo        | Adaptador incompleto         | Adaptador correcto         | ✅ Gemini    |

---

## Conclusión

- **La arquitectura es correcta.**
- **El bug es de “idioma” entre componentes, no de lógica.**
- **La solución de Gemini es la adecuada para AI SDK v3+.**
- **Con este fix, el chat aparecerá en pantalla y el ciclo estará cerrado.**

---

## Estado actual del proyecto

- Abu calcula ✔
- Lilly razona ✔
- Next conecta ✔
- Chat aparece en pantalla ❗ (último paso)

---

## Referencias
- [AI SDK Data Stream Protocol](https://sdk.vercel.ai/docs/guides/data-stream-protocol)
- [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

**Este documento debe usarse como referencia para troubleshooting de integración FE/BE y para onboarding de nuevos desarrolladores en AI Oracle.**
