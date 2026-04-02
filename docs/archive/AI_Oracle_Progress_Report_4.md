# AI Oracle – Reporte de Cambios y Estado (2025-11-02)

## Resumen ejecutivo
Dejamos el stack estable y reproducible con tres frentes principales resueltos: (1) robustecimos la gestión de efemérides (auto-descarga y uso centralizado), (2) saneamos imports/URLs para que Docker + Next.js funcionen sin hacks, y (3) habilitamos el camino LLM real en Lilly con OpenAI, incluyendo mapeo de eventos y parsing más resiliente.

## Cambios clave (por área)

### Infraestructura y Compose
- `docker-compose.yml`
  - Añadido `environment` en `lilly_engine` para `OPENAI_API_KEY=${OPENAI_API_KEY}`.
  - Declaradas `NEXT_PUBLIC_ABU_URL` y `NEXT_PUBLIC_LILLY_URL` para el frontend (Next.js).

### Abu Engine (FastAPI, :8000)
- `abu_engine/core/chart.py`
  - Implementado `EphemerisSingleton` que:
    - Crea `data/` si no existe.
    - Descarga automáticamente `de440s.bsp` desde NAIF si falta.
    - Carga el kernel con Skyfield y lo comparte en toda la app.
  - Fix de zona horaria en `find_solar_return()` (usar datetimes con `tzinfo=UTC`).
- `abu_engine/core/forecast.py`
  - Reemplazo de carga hardcodeada del kernel por `EphemerisSingleton()`.
- `abu_engine/core/life_cycles.py`
  - Migrado a `EphemerisSingleton()` (eliminando path fijo a BSP).
- `abu_engine/main.py`
  - Imports relativos `from core.*` para layout flat en contenedor.
  - Warm-up no bloqueante que precalienta efemérides y rutas pesadas.

### Lilly Engine (FastAPI + OpenAI, :8001)
- `lilly_engine/main.py`
  - Mapeo automático de eventos de ciclos `{cycle, planet, angle, approx}` al esquema esperado por el LLM `{type, planet, to, angle?, peak?}`.
  - Mantiene fallback a arquetipos si falla OpenAI.
- `lilly_engine/core/llm.py`
  - `openai.api_key` lee `OPENAI_API_KEY` del entorno.
  - Parser mejorado para aceptar respuestas JSON del LLM aunque vengan en bloques ```json ... ```.
  - Modelo por defecto configurable vía `LILLY_MODEL` (default: `gpt-4o-mini`).

### Frontend (Next 15 + TS + Tailwind, :3000)
- Páginas `/chart`, `/forecast`, `/interpret` leen `NEXT_PUBLIC_*` y dejan de usar reescrituras de URLs.
- Dockerfile de Next.js simplificado (se quitaron sed/hacks que rompían en navegador).

## Verificaciones realizadas
- Abu
  - GET `/api/astro/chart` → 200 OK.
  - GET `/api/astro/forecast` → 200 OK, devuelve `{ timeseries, peaks }`.
  - GET `/api/astro/life-cycles` → 200 OK, `{ astro_data, interpretation }` (interpretation con `source=openai` si hay key, si no `fallback`).
  - GET `/api/astro/solar-return` → 200 OK tras fix de timezone; incluye `planets`, `aspects` y `score_summary`.
- Lilly
  - POST `/api/ai/interpret` → funciona con OpenAI si `OPENAI_API_KEY` está presente; `astro_metadata.source = "openai"`.
  - Parser tolera respuestas con bloques de código y extrae JSON válido.
- Frontend
  - `/` responde 200.
  - Páginas cableadas a envs; `/chart` verificada visualmente.

## Variables de entorno y `.env`
- Lugar: raíz del repo (junto a `docker-compose.yml`).
- Formato sugerido (sin comillas ni espacios alrededor de `=`):

```
OPENAI_API_KEY=sk-xxxx
LILLY_MODEL=gpt-4o-mini
NEXT_PUBLIC_ABU_URL=http://localhost:8000
NEXT_PUBLIC_LILLY_URL=http://localhost:8001
```

- Compose toma `OPENAI_API_KEY` y se la inyecta a `lilly_engine`.
- El frontend recibe `NEXT_PUBLIC_*` desde Compose.

## Cómo correr (local con Docker)

```powershell
# En la raíz del repo, con .env presente
docker compose up --build
```

- Abu: http://localhost:8000
- Lilly: http://localhost:8001
- Next: http://localhost:3000

## Pruebas rápidas (APIs)

```powershell
# Forecast (Abu)
Invoke-RestMethod "http://localhost:8000/api/astro/forecast?birthDate=1990-01-01T12:00:00Z&lat=-34.6&lon=-58.38&start=2025-01-01T00:00:00Z&end=2025-12-31T00:00:00Z&step=7d" | ConvertTo-Json -Depth 2

# Life-cycles (Abu → Lilly)
Invoke-RestMethod "http://localhost:8000/api/astro/life-cycles?birthDate=1990-01-01T12:00:00Z" | ConvertTo-Json -Depth 4

# Solar Return (Abu)
Invoke-RestMethod "http://localhost:8000/api/astro/solar-return?birthDate=1990-01-01T12:00:00Z&lat=-34.6&lon=-58.38&year=2025" | ConvertTo-Json -Depth 4

# Interpret (Lilly directo)
$body = '{"events":[{"cycle":"Saturn Return","planet":"Saturn","angle":0,"approx":"2019-08-01"}],"language":"es"}';
Invoke-RestMethod -Method Post -ContentType application/json -Body $body http://localhost:8001/api/ai/interpret | ConvertTo-Json -Depth 4
```

## Quality gates (esta sesión)
- Build: PASS (imágenes rebuild exitosas)
- Lint/Typecheck: no ejecutado
- Tests: no ejecutado (repos tienen tests pero no se ejecutaron en contenedor en esta sesión)

## Pendientes y próximos pasos
1. Tests automatizados
   - Añadir target de `pytest` para Abu/Lilly y job de CI.
2. Smoke test script
   - Script que llame a los 4 endpoints y valide shapes básicos tras cada build.
3. Elección de modelo LLM
   - Definir `LILLY_MODEL` por entorno (default `gpt-4o-mini`).
4. Observabilidad
   - Endpoints `/health` y logs más detallados de warm-up/fallbacks.
5. Ajustes de UI (opcional)
   - Revisión visual de `/forecast` y `/interpret` ahora que los endpoints están estables.

## Notas técnicas (mapa de cambios de código)
- Abu
  - `core/chart.py`, `core/forecast.py`, `core/life_cycles.py`, `main.py`.
- Lilly
  - `main.py`, `core/llm.py`.
- Frontend
  - Páginas en `next_app/app/(chart|forecast|interpret)` y Dockerfile.
- Compose
  - `docker-compose.yml` actualizado con envs.

---
Actualizado: 2025-11-02
