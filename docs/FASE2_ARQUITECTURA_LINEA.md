# Abu Oracle — Línea de arquitectura Fase 2 (Cognición + Memoria)

**Fecha de creación:** 2025-12-25

> **Referencia cruzada:** Este documento debe leerse junto con `FASE2_INTEGRACION_COGNITIVA_2025-12-23.md`, que contiene la visión y objetivos generales de la Fase 2. Aquí se detallan los contratos técnicos, payloads y criterios de éxito para la implementación.

## 1) Qué ya está resuelto (Fase 1)
- Frontend Next.js (next_app) renderiza el chat.
- Next.js route `/api/chat` actúa como adaptador de protocolo para Vercel AI SDK v3+ (Data Stream Protocol).
- Docker networking entre contenedores funciona.
- Abu Engine (abu_engine) calcula y devuelve JSON astrológico complejo.

**Invariante:** No se toca el frontend ni el adaptador salvo cambios estrictamente necesarios para pasar `session_id` y/o `abu_payload`.

## 2) Problema actual
- `lilly_swarm` devuelve respuestas hardcodeadas.
- No usa OpenAI.
- No consume Abu JSON.
- No tiene memoria.

## 3) Objetivo Fase 2
Convertir `lilly_swarm` en “capa cognitiva”:
- Recibe:
  - `message` del usuario (texto)
  - `abu_payload` (JSON calculado por Abu Engine) [Pendiente de implementar en route.ts]
  - `session_id` (para memoria)
- Produce:
  - `response` (texto para chat)

## 4) Contratos entre componentes

### 4.1 next_app -> lilly_swarm
**POST** `/api/chat` (interno Docker)

Payload objetivo (Meta):
```json
{
  "session_id": "uuid-temporal",
  "message": "texto del usuario",
  "context": { "abu_chart": "..." }
}
```

### 4.2 lilly_swarm -> OpenAI
Modo sugerido inicial: Chat Completions API (para velocidad y control directo del System Prompt). Motivo: Assistants API es más lenta y compleja para un MVP de streaming.

## 5) Memoria (MVP)
Archivo JSON local en contenedor Lilly: data/threads/{session_id}.json.

## 6) Criterio de Éxito
Escribir "interpreta la carta" y obtener una respuesta que mencione datos específicos (ej: "Tu Ascendente es Escorpio") extraídos del cálculo de Abu, no inventados.

---

**Este documento es técnico-operativo y debe ser consumido por humanos y agentes de IA. Marca el inicio de la Fase 2: creación de la memoria cognitiva y capacidad interpretativa de Abu Oracle.**
