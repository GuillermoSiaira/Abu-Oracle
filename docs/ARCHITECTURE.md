# AI Oracle — Arquitectura y Decisiones Técnicas

## 1. Objetivo del sistema

AI Oracle es una aplicación compuesta por múltiples servicios cuyo objetivo es:

* Realizar **cálculos astrológicos de alta complejidad** (Abu Engine)
* Interpretarlos mediante **razonamiento simbólico + LLM** (Lilly Swarm)
* Exponerlos a un usuario final vía **interfaz conversacional** (Next.js)

El sistema está diseñado para evolucionar hacia:

* Memoria persistente por usuario
* Asistentes LLM especializados
* Streaming real
* Escalabilidad modular

---

## 2. Componentes principales (AS-IS)

### 2.1 Abu Engine (Python — puerto 8000)

**Responsabilidad**

* Cálculo determinista y matemático:

  * cartas
  * ciclos
  * firdarias
  * profecciones
  * retornos solares
  * etc.

**Características**

* No depende de LLM
* Es puro dominio
* Stateless (por ahora)
* API HTTP JSON

**Estado**

* ✅ Funcional
* ✅ Validado por logs
* ❌ No debe tocarse en esta fase

---

### 2.2 Lilly Swarm (Python — puerto 8001)

**Responsabilidad**

* Orquestación cognitiva
* Interpretación semántica
* Uso de LLM (OpenAI u otros)
* Coordinación con Abu

**Características**

* Produce respuestas completas en **JSON**
* Actualmente **NO hace streaming**
* Endpoint principal:

  * `POST /api/chat`

**Estado**

* ✅ Funcional
* ✅ Recibe mensajes
* ✅ Usa LLM
* ❌ No habla SSE / streaming todavía

---

### 2.3 Next.js App (Frontend + API Gateway — puerto 3000)

**Responsabilidad**

* UI (React)
* Chat (`useChat` del AI SDK)
* Gateway de comunicación entre frontend y backend Python

**Restricción clave**

* `useChat` **exige** respuestas en formato **streaming / SSE**

**Estado**

* UI funcional
* Chat roto **por incompatibilidad de protocolo**, no por lógica

---

## 3. El problema real (diagnóstico final)

> **NO es un problema de LLM**
> **NO es un problema de OpenAI**
> **NO es un problema de Abu ni de Lilly**

### El problema es de **contrato de transporte**

* El frontend espera: **Server-Sent Events (stream)**
* El backend entrega: **JSON completo**
* Resultado:
  `Failed to parse stream string`
  o mensajes que nunca aparecen en pantalla

Esto es un **mismatch de protocolo**, no un error conceptual.

---

## 4. Decisión arquitectónica clave (DECISIÓN #1)

### Implementar un **Adapter SSE en Next.js**

**Qué hace**

* Recibe JSON completo desde Lilly
* Lo transforma en un stream SSE mínimo
* Engaña legítimamente a `useChat`
* NO altera la inteligencia
* NO mueve lógica
* NO hardcodea respuestas

**Patrón aplicado**

* Adapter Pattern
* Gateway Pattern
* Boundary Translation

**Dónde vive**

* `next_app/app/api/chat/route.ts`

---

## 5. Qué NO se hace (decisiones explícitas)

❌ No se elimina Assistants
❌ No se quita OpenAI
❌ No se mueve lógica cognitiva a Next
❌ No se reescribe Abu
❌ No se reescribe Lilly hoy
❌ No se hardcodean respuestas

Estas decisiones son **conscientes y documentadas**.

---

## 6. Estado actual de la arquitectura (TO-BE inmediato)

```
[ Browser / useChat ]
          |
          |  (SSE / Streaming)
          v
[ Next.js API Gateway ]
          |
          |  (JSON HTTP)
          v
[ Lilly Swarm (LLM + Orquestación) ]
          |
          |  (JSON HTTP)
          v
[ Abu Engine (Cálculo puro) ]
```

---

## 7. Roadmap técnico (orden obligatorio)

### Fase 1 — 🔓 Desbloqueo (ACTUAL)

* ✅ Adapter SSE en Next.js
* Resultado: el chat **responde en pantalla**

---

### Fase 2 — 🧠 Memoria

Decidir dónde vive el `thread_id`:

* Frontend: `localStorage`
* Backend: archivo JSON (`threads.json`) o similar

Objetivo:

* Persistencia de contexto por usuario

---

### Fase 3 — ⚡ Streaming real (opcional)

* Reescribir Lilly para usar:

  * generators
  * async yield
  * SSE real desde Python

**No es bloqueante**, solo mejora UX.

---

### Fase 4 — 🤖 Assistants avanzados

* Especialización de agentes
* Herramientas
* Memoria larga
* Multimodalidad

---

## 8. Principio rector (regla de oro)

> **Nunca volver a romper la arquitectura por confundir transporte con inteligencia**

Si algo no funciona:

1. Revisar logs
2. Ver contratos
3. Ver protocolos
4. Adaptar fronteras
   👉 **No mover cerebros**

---

## 9. Estado emocional del proyecto (nota humana)

Este bloqueo fue costoso **porque el sistema es bueno**.
No es un proyecto frágil: es uno **exigente**.

Resolver este punto:

* desbloquea todo
* valida la arquitectura
* permite avanzar sin volver atrás

---

## 10. Estado actual

🟡 Contenedores reconstruyéndose
🟢 Decisión arquitectónica cerrada
🟢 Documento base establecido

---

Cuando termine el build y pruebes el chat, decime simplemente:

> **“Ya aparece texto en pantalla.”**

Con eso:

* cerramos definitivamente este incidente
* pasamos a **memoria** y **producto**, no más infraestructura reactiva.
