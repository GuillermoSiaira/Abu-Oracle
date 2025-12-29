# AI Oracle – Copilot Instructions for AI Agents

Use this guide to be productive immediately in this repo. Keep changes small, respect public contracts, and verify with quick runs.

## Big picture
- Three services orchestrated via Docker Compose (`docker-compose.yml`):
  - Abu Engine (FastAPI) → astrological data (chart, forecast, life cycles) on :8000
  - Lilly Engine (FastAPI + OpenAI) → interpretations on :8001
  - Next.js app (Next 15 + TS + Tailwind) → UI on :3000
- Data flow: Frontend → Abu (compute) → Lilly (interpret) → Frontend. Abu calls Lilly via `send_to_lilly()` (service DNS `http://lilly_engine:8001`).

## Key files / directories
- Abu: `abu_engine/main.py`, `abu_engine/core/*` (chart/aspects/forecast/houses/life_cycles/scoring)
- Lilly: `lilly_engine/main.py`, `lilly_engine/core/llm.py`, `lilly_engine/archetypes.json`, `lilly_engine/data/memory.json`
- Frontend: `next_app/app/(chart|forecast|interpret)`, `next_app/components/LillyPanel.tsx`

## Endpoints (contracts to preserve)
- Abu
  - GET `/api/astro/chart` → positions, aspects, houses. Params: `date`, `lat`, `lon`.
  - GET `/api/astro/forecast` → `{ timeseries, peaks }`. Params: `birthDate`, `lat`, `lon`, `start`, `end`, `step?`, `horizon?`.
  - GET `/api/astro/life-cycles` → `{ events:[{cycle, planet, angle, approx}] }`, Abu forwards to Lilly and returns `{ astro_data, interpretation }`.
  - GET `/api/astro/solar-return` → Solar Return chart. Params: `birthDate`, `lat`, `lon`, `year?`. Returns `{ solar_return_datetime, planets, aspects, score_summary }`.
  - POST `/api/ai/interpret` → `{ headline, narrative, actions[], astro_metadata{} }`.
    - Input: may include `events`, `transits`, `planets`, `aspects`, `timeseries`, `peaks`, `language`, `question`.
    - POST `/api/ai/solar-return` → `{ best_locations[], location_details[], reasoning, natal_ascendant{}, solar_ascendant{}, astro_metadata{} }`.
      - Input: `natal_chart`, `solar_chart`, `language?` (es/en/pt/fr). Analyzes Ascendant elements and suggests 2-3 favorable relocation cities.

## OpenAI usage (Lilly)
- API key: `OPENAI_API_KEY` env var.
- `lilly_engine/core/llm.py` builds a JSON-first prompt (ES by default) and calls GPT-4; falls back in `lilly_engine/main.py` to `archetypes.json` when key/mode fails.
- Conversation memory: `data/memory.json` stores last 5 entries per user; helpers `get_context(name)` and `save_context(name, data)` augment prompts with 1–2 prior entries.

## Local development workflows
- With Docker (recommended for all three):
  ```powershell
  docker compose up --build
  ```
- Run services locally (without Docker):
  ```powershell
  # Abu
  uvicorn abu_engine.main:app --reload --port 8000

  # Lilly (requires OPENAI_API_KEY for LLM path)
  uvicorn lilly_engine.main:app --reload --port 8001

  # Frontend
  cd next_app; npm install; npm run dev
  ```
- Frontend expects `NEXT_PUBLIC_ABU_URL` and `NEXT_PUBLIC_LILLY_URL` (Compose sets them to service DNS).

## Project conventions / patterns
- Language defaults to Spanish (`language: "es"`); keep content and prompts in ES unless explicitly overridden.
- Lilly responses must be valid JSON with keys: `headline`, `narrative`, `actions[]`, `astro_metadata{ source }`. Do not emit prose outside JSON.
- Prompt builder uses dataclasses (`Profile`, `Chart`, `Transit`, `Event`) and injects prior context; keep shape stable when extending.
- Abu→Lilly: use service name URLs in Docker; use `http://127.0.0.1` only for local, non-Compose runs.
- Frontend renders markdown via `react-markdown` + `remark-gfm` (install if missing).

## Examples
- Minimal Lilly request (events):
  ```json
  { "events": [{ "cycle": "Saturn Return", "planet": "Saturn" }], "language": "es" }
  ```
- Minimal Abu life-cycles call:
  ```text
  GET /api/astro/life-cycles?birthDate=1990-01-01T12:00:00Z
  ```

## Safe-change checklist for agents
- Preserve endpoint paths and response shapes shown above.
- If touching `llm.py`, keep JSON-only output contract and Spanish default; ensure memory helpers still cap 5 entries/user (FIFO).
- If adding endpoints, wire CORS for `http://localhost:3000` and update `next_app` fetchers accordingly.
- For Docker URLs, keep `lilly_engine` / `abu_engine` service DNS; don’t hardcode localhost in service-to-service calls.
- Large data (ephemeris) lives in `abu_engine/data/de440s.bsp`; don’t commit replacements.

## Quick troubleshooting
- Frontend ENOENT for package.json → run npm in `next_app/`.
- OpenAI failures: verify `OPENAI_API_KEY` and expect archetype fallback with `astro_metadata.source = "fallback"`.
- CORS errors: ensure origins include `http://localhost:3000` in both engines.
