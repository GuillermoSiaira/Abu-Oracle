# Marketing Agent Plan (Vertex AI Agent Builder)

Estado: Borrador (listo para ejecutar cuando finalicemos intérprete y FE)
Idioma: ES

## Objetivo
- Captar y convertir usuarios desde web/redes con un agente conversacional.
- Aumentar activaciones guiando onboarding y respuestas de soporte básicas.
- Mantener bajo costo y cero impacto en los servicios existentes (Abu/Lilly).

## Casos de uso
1) Captación en sitio (widget)
   - Saludo → Preguntas breves → CTA a “Quiero mi análisis completo”.
   - Recupera fecha/hora/lugar y sugiere features relevantes.
2) Onboarding / soporte
   - Guía por carta natal, pronóstico y relocación solar.
   - FAQ y resolución de dudas simples.
3) Contenido/SEO
   - Artículos con botón “Pregúntale al oráculo”.
   - Eleva engagement y tiempo en página.
4) Mensajería (futuro)
   - WhatsApp/Instagram Business → respuestas rápidas + CTA al sitio.

## Arquitectura (no invasiva)
Usuario ↔ Vertex AI Agent Builder ↔ (Tools) Abu/Lilly en Cloud Run
- Tools HTTP apuntan a:
  - Abu: GET /api/astro/chart, /forecast, /life-cycles, /solar-return
  - Lilly: POST /api/ai/interpret (y /api/ai/solar-return si aplica)
- El agente compone la conversación; Abu/Lilly siguen como fuentes de verdad.

## Alcance MVP (2–3 días)
- Agente único ES (tone amable, breve, enfocado a conversión).
- 3 Tools: chart, forecast, interpret.
- Widget embebible en Next.js (botón flotante; panel lateral simple).
- Métricas básicas: sesiones, captación de leads (evento de click a signup), 
  ratio de conversaciones→CTA.

## Prompt de sistema (borrador)
- Rol: Asistente de marketing de AI Oracle.
- Estilo: claro, empático, concreto. Español neutro.
- Objetivo: resolver dudas rápidas y derivar a análisis completo.
- Política: nunca inventar datos astrológicos; si necesita cálculo, usar tools.
- Secuencia típica:
  1. Saludo + pregunta de objetivo.
  2. Si hay datos de nacimiento, ofrecer resumen con tool(s).
  3. Cerrar con CTA (crear cuenta / ver análisis completo).

## Data & grounding
- Opcional: cargar axiomas/FAQ públicas como knowledge base.
- Mantener respuestas concisas y alineadas con nuestra terminología.

## KPIs
- Conversaciones iniciadas
- % usuarios que pasan a CTA (signup / análisis completo)
- Tiempo medio de interacción
- Preguntas más frecuentes (retroalimentan contenido del sitio)

## Costos (estimado)
- Agent Builder: bajo costo por conversación (Gemini flash es barato).
- Abu/Lilly: ya provisionados en Cloud Run (incremental por tráfico).

## Riesgos y mitigaciones
- Calidad vs. OpenAI: mantener Lilly para interpretaciones profundas.
- Lock-in GCP: capa solo de marketing; core sigue agnóstico.
- Privacidad: no guardar PII en el agente salvo consentimiento explícito.

## Checklist de implementación
- [ ] Crear agente en Vertex AI (us-central1)
- [ ] Configurar 3 tools HTTP a Cloud Run (chart, forecast, interpret)
- [ ] Prompt de sistema + ejemplos breves (ES)
- [ ] Probar 5 diálogos típicos (lead nuevo, usuario curioso, soporte simple)
- [ ] Generar embed code y montar `ChatWidget` en Next.js
- [ ] Eventos de analytics (conversación iniciada, CTA clickeada)
- [ ] Monitoreo y bucles de mejora (respuestas, caídas, latencia)

## Integración Next.js (borrador)
- Componente `components/ChatWidget.tsx` (botón + iframe/modal del agente).
- Evento `window.dataLayer.push({event: 'agent_cta'})` para medir conversión.

## Go/No-Go
- Go cuando:
  - [ ] Lilly devuelve interpretaciones con `source: "openai"` consistente.
  - [ ] FE pulido (loading, errores, copy final).
  - [ ] Orquestador migrado a Responses API o confirmado estable.

## Mantenimiento
- Revisar conversaciones semanales (Vertex AI analytics).
- Incorporar FAQs frecuentes al prompt/knowledge.
- Ajustar CTAs según campañas vigentes.
