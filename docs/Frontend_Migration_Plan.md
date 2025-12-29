# 📄 Frontend_Migration_Plan.md

# Migración de la UI Persa (v0-repo) al Repo Principal `ai-oracle`

**Versión:** 2025-03  
**Estado:** Aprobado  
**Autor:** Guillermo Siaira + ChatGPT  
**Objetivo:** Integrar la UI persa moderna (v0-repo) en el frontend real del proyecto `ai-oracle`, manteniendo 100% intactos los contratos, lógica y endpoints del backend Abu Engine y Lilly Engine.

---

# 🧩 1. Resumen Ejecutivo

Este documento especifica el plan de migración oficial para reemplazar la interfaz antigua del proyecto `ai-oracle` por la UI persa v0, desarrollada como prototipo interactivo.  
Los objetivos principales son:

* Unificar Abu Engine + Lilly Engine + UI persa.
* Mantener contratos del backend sin alteraciones.
* Introducir Zustand, servicios tipados y shadcn/ui.
* Establecer `/chart` como la página principal moderna.
* Dejar preparado el terreno para el próximo módulo: Chat Orquestador.

La migración se realiza sin romper el frontend actual y sin introducir deuda técnica innecesaria.

---

# 🟦 2. Estado Actual de los Repositorios

## Repo principal `ai-oracle`
* Contiene:
  * `/next_app` con el frontend anterior.
  * Páginas `/chart`, `/forecast`, `/interpret`, `/positions`.
  * Conexión directa a Abu/Lilly usando `fetch` + `useSWR`.
  * Sin Zustand.
  * Sin UI persa.
  * Tailwind básico, sin tema persa.
* Backend funcional, estable y desplegado:
  * Abu Engine (Cloud Run)
  * Lilly Engine (Cloud Run)
  * Contratos OpenAPI confirmados
  * JSON Maestro funcional

## Repo `ai-oracle-v0-repo`
* Contiene la UI persa completa:
  * BirthDataPanel
  * ChartTabs
  * ZodiacWheel persa
  * PersianTechniquesTab
  * InterpretationTab
  * MaestroTab
  * ChatPanel (UI)
  * tablas y vistas auxiliares
* Infraestructura moderna:
  * Zustand store (`lib/store.ts`)
  * Servicios tipados (`services/abu.ts`, `services/lilly.ts`)
  * UI shadcn (`components/ui/*`)
  * Variables CSS persas y utilidades
  * Tipos (`lib/types.ts`)

---

# 🟪 3. Problemas Detectados Durante Intentos de Migración

La migración directa falló por:

## ❌ 1. Falta de infraestructura en `next_app`
* No existían:
  * `/lib`
  * `/services`
  * `components/ui`
* No existía el store Zustand.

## ❌ 2. Tema Tailwind incompatible
* La UI persa usa utilidades:
  * `bg-background`
  * `text-muted-foreground`
  * `border-border`
* El tema actual no las define.

## ❌ 3. Imports y rutas incompatibles
* El v0 usa `@/lib/...`, `@/services/...`, `@/components/ui/...`.

## ❌ 4. Copilot trató de arreglar todo a la vez → caos
* Copilot mezcló mocks
* Rompió imports
* Intentó modificar contratos (no permitido)
* Se trabó por cantidad de errores simultáneos

---

# 🟩 4. Objetivos de la Migración

1. Establecer `/chart` como la interfaz principal del usuario.
2. Integrar:
   * BirthDataPanel → Abu Engine
   * ChartTabs → Carta + Técnicas Persas + Maestro
   * InterpretationTab → Lilly Engine
3. Instalar infraestructura moderna:
   * Zustand
   * Servicios tipados
   * UI shadcn
   * Tema persa (variables CSS + utilidades)
4. Mantener rutas clásicas (`/forecast`, `/interpret`) sin modificación.
5. Preparar UI para integrar Chat Orquestador en una fase posterior.

---

# 🟧 5. Plan de Migración (Orden Estricto)

## ✔️ FASE 1 — Preparación del Proyecto
Agregar infraestructura necesaria desde v0:
`/next_app/lib`  
  - types.ts  
  - store.ts
`/next_app/services`  
  - abu.ts  
  - lilly.ts
`/next_app/components/ui`  
  - alert.tsx  
  - badge.tsx  
  - button.tsx  
  - card.tsx  
  - input.tsx  
  - label.tsx  
  - switch.tsx  
  - tabs.tsx  
  - table.tsx
Agregar variables CSS persas al final de `styles/globals.css`, junto a utilidades:
.bg-background  
.bg-card  
.text-primary  
.text-muted-foreground  
.border-border
💡 Esto resuelve el 90% de los errores.

---

## ✔️ FASE 2 — Migración de Componentes
Copiar desde el v0 a `next_app/components`:
* birth-data-panel.tsx
* chart-tabs.tsx
* chat-panel.tsx
* natal-chart-tab.tsx
* persian-techniques-tab.tsx
* interpretation-tab.tsx
* maestro-tab.tsx
* zodiac-wheel.tsx
* tablas auxiliares:
  * houses-table.tsx
  * planets-table.tsx
  * positions-table.tsx
  * lots-view.tsx
  * profections-view.tsx
  * lunar-mansion-view.tsx
  * fixed-stars-view.tsx

---

## ✔️ FASE 3 — Página `/chart` (remplazo total)
Nuevo contenido:
* "use client"
* <BirthDataPanel />
* <ChartTabs />
* <ChatPanel /> (UI; backend vendrá luego)
`/forecast`, `/interpret`, `/positions` permanecen intactas.

---

## ✔️ FASE 4 — Conexión con Abu Engine y Lilly Engine
* BirthDataPanel → abu.getChartExtended()
* InterpretationTab → lilly.interpretMaestro()
* El resultado se guarda en Zustand.
* Los tabs leen el estado.

---

## ✔️ FASE 5 — Validación Final
Luego de la migración, validar:
### Carta natal
* Rueda zodiacal
* Posiciones planetarias
* Casas
* Aspectos
### Técnicas persas
* Profecciones
* Lotes
* Mansión lunar
* Estrellas fijas
### Interpretación
* Narrativa
* JSON Maestro completo
Nada del backend se modifica.

---

# 🧪 6. Pruebas Automatizadas y Validación Visual

## Pruebas Automatizadas
* Implementar y/o ejecutar pruebas unitarias para los servicios tipados (`abu.ts`, `lilly.ts`).
* Ejecutar pruebas de integración para los componentes principales migrados.
* Validar que los endpoints y contratos se respetan en las llamadas frontend-backend.

## Validación Visual y Responsive
* Revisar la UI persa en desktop y dispositivos móviles.
* Confirmar que el tema, colores y utilidades CSS se aplican correctamente en todos los componentes.
* Validar que la experiencia de usuario y la accesibilidad se mantienen.

---

# 🔮 7. Fase Posterior: Chat Orquestador
Una vez estable:
* Crear `app/api/orchestrate/route.ts`
* Conectar con Assistant (orquestador)
* ChatPanel envía preguntas y muestra:
  * headline
  * narrative
  * actions
  * astro_metadata
Esta fase se implementa después de la migración principal.

---

# 🧠 8. Roles Claros
## ChatGPT (arquitectura)
* Define el plan
* Asegura que no se rompa backend
* Garantiza que el frontend se monte correctamente
* Verifica cada fase antes de ejecutar la siguiente
## Copilot (operativo)
* Copia archivos
* Ajusta imports
* Inserta CSS
* Reemplaza contenido de páginas
* Resuelve errores sintácticos
Copilot no debe:
* cambiar contratos
* inventar endpoints
* refactorizar Zustand
* modificar lógica

---

# 🏁 9. Resultado Esperado
Una UI que:
✔️ Usa la estética persa
✔️ Conecta Abu Engine + Lilly Engine
✔️ Maneja JSON Maestro
✔️ Muestra carta, técnicas persas y narrativa
✔️ Tiene ChatPanel listo para conectar
✔️ Mantiene backend intacto
✔️ Permite escalar hacia el orquestador

---

# 📌 10. Notas Finales
* Ambos repos deben estar presentes en tu máquina local para copiar componentes.
* La migración NO afecta el backend.
* `/forecast` no se modifica en esta fase.
* El chat LLM se agrega después.

---

# ✔️ FIN DEL DOCUMENTO
