# AI Oracle – Informe de Progreso 3

Fecha: 2025-11-01

## Resumen

En esta iteración incorporamos la interpretación de Revolución Solar con sugerencias de reubicación (Lilly), la API correspondiente, mejoras de frontend con mapa y gráficos multi-serie, y estabilizamos el arranque local (especialmente en Windows). También añadimos un warm-up en Abu para evitar errores 500 en el primer acceso a la Revolución Solar.

## Cambios principales

### Lilly Engine (interpretación)

- Nueva función `interpret_solar_return()` (heurística) que compara Ascendentes natal/solar por elemento y modalidad.
- Nuevo endpoint `POST /api/ai/solar-return`:
  - Entrada: `{ natal_chart, solar_chart, language? }` (ES por defecto).
  - Salida: `{ best_locations[], location_details[], reasoning, natal_ascendant{}, solar_ascendant{}, astro_metadata{} }`.
- Soporte multilingüe preservado; contrato JSON-only.
- Tests añadidos y pasando para lógica y endpoint.
- Documentación: `docs/Solar_Return_Relocation_API.md` y `docs/Solar_Return_Relocation_Examples.md`.

### Abu Engine (cómputo)

- Endpoint `GET /api/astro/solar-return` (ya existente) consolidado con cálculo binario del retorno solar y resumen de aspectos/puntaje.
- Warm-up de arranque para mitigar 500 iniciales:
  - Pre-carga de efemérides (`de440s.bsp`) y ejecución de cálculos ligeros (carta y revolución) en `@app.on_event("startup")`.
  - No modifica contratos ni respuestas; reduce latencia y errores de "cold start".

### Frontend (Next.js 15 + TS + Tailwind)

- Ruta `/interpret`:
  - Renderiza interpretación y recomendaciones geográficas (Lilly) sobre un mapa (Leaflet) y mini gráfico multi-serie.
  - Click en marcador agrega una nueva serie de pronóstico en la vista.
  - Persistencia de ciudades recomendadas en `localStorage`.
- Ruta `/forecast`:
  - Gráfico multi-serie (Recharts) con selector para añadir ciudades guardadas.
- Mapa (react-leaflet):
  - Carga dinámica para SSR, import de CSS global, fix de `invalidateSize` al montar/redimensionar.
  - Evitamos el mundo repetido al hacer zoom out (`noWrap` en `TileLayer`).
  - Strict Mode deshabilitado en dev para prevenir doble inicialización en Leaflet.

## Estabilidad y correcciones

- Corrigidos problemas de CSS (Leaflet), SSR, y error "Map container is already initialized".
- Mitigados errores 500 en el primer request de Revolución Solar con warm-up en Abu.
- Windows: se documentó la limpieza de `.next` y reinicios ordenados para evitar bloqueos de archivos.

## Cómo ejecutar (local)

- Docker Compose (recomendado):
  - `docker compose up --build`
- Sin Docker:
  - Abu: `uvicorn abu_engine.main:app --reload --port 8000`
  - Lilly: `uvicorn lilly_engine.main:app --reload --port 8001` (requiere `OPENAI_API_KEY` para ruta LLM)
  - Frontend: `cd next_app; npm install; npm run dev`

Asegurar variables `NEXT_PUBLIC_ABU_URL` y `NEXT_PUBLIC_LILLY_URL` para el frontend.

## Siguientes pasos

- Abu: monitoreo y consolidación del warm-up; manejo de errores más detallado en `/api/astro/solar-return`.
- Frontend: refinar UX del mapa (límites/zoom, tooltips), leyenda y colores para series múltiples.
- Datos: opción para centrar coordenadas de hogar/usuario; selección de idioma en UI.
- Pruebas: ampliar test de integración frontend-backend (mock endpoints) y snapshots de UI.

## Notas

- Mantener ES como idioma por defecto en prompts y respuestas de Lilly.
- Conservar URLs de servicio Docker (`http://lilly_engine:8001`) en comunicaciones Abu→Lilly.
- `archetypes.json` actúa como fallback cuando LLM no está disponible; `astro_metadata.source = "fallback"`.
