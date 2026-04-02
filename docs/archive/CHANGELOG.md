# AI Oracle – Changelog

All notable changes to this project will be documented in this file.
This project loosely follows Keep a Changelog and uses date-based versions.

## [Unreleased]
- **User Profile System**: Name, birth city/country selector, residence selector with autocomplete, localStorage persistence.
- **CitySelector Component**: Typeahead search using Abu's `/api/cities/search` endpoint (58 cities database).
- **Multi-location Forecast**: Integrated user profile in `/interpret` and `/positions`; forecast now compares natal + residence automatically.
- **Chart Wheel MVP**: Added `components/ChartWheel.tsx` (SVG natal wheel) lazy-loaded in `/interpret`.
- **Extended Calculations**: New `core/extended_calc.py` with dignities, Arabic parts, lunar nodes; new endpoint `/api/astro/chart-detailed`.
- **Planets Expanded**: Uranus, Neptune, Pluto now included in all chart calculations.
- Production build for Next.js containers (npm run build + start)
- LocalStorage cache for life-cycles and chart responses
- Prefetch of critical data from Portal (hover/idle)
- SSR/SSG exploration for faster TTFB
- GZip/Brotli compression in Abu/Lilly (FastAPI middleware)
- Classical corpus ingestion (William Lilly) and embeddings generation
- Advanced axioms: dignities/debilities, applicative vs. separative, sect, velocity
- **Houses System** (pyswisseph): Placidus/Koch cusps, Ascendant, MC (HIGH PRIORITY - needed for accurate Part of Fortune and house placements)
- **Transits Endpoint**: Compare natal vs current/future positions
- **Progressions**: Secondary progressions calculation
- **UI: Advanced Forecast Comparison**: Add/remove up to 5 cities in chart, persist selection

---

## [v2.1] – 2025-11-03 — Reasoning layer + UX pass + perf boost

### Added
- Lilly reasoning field (JSON key: `reasoning`) with env flag `LILLY_INCLUDE_REASONING` (default true).
- Dual dialogue fields in Lilly responses: `abu_line` (voz técnica) y `lilly_line` (voz intuitiva).
- Axioms layer: `lilly_engine/data/axioms/astrological_axioms.md` + loader en `core/llm.py`.
- Knowledge layer scaffold: `core/knowledge.py` con búsqueda semántica; script `scripts/generate_embeddings.py`.
- UX Portal del Oráculo (`next_app/app/page.tsx`) con presentación de Abu y Lilly.
- DialogueBubble component (`next_app/components/DialogueBubble.tsx`) y mejoras en `LillyPanel.tsx` (burbujas + reasoning colapsable).
- Documentation: `docs/AI_Oracle_UX_Vision_and_Dialogue_Design.md`, `docs/AI_Oracle_Performance_Optimizations.md`, `docs/AI_Oracle_Progress_Report_5.md`.

### Changed
- Prompt builder (`lilly_engine/core/llm.py`): inyecta axioms, referencias clásicas y tarea de razonamiento; formato actualizado para pedir `abu_line`/`lilly_line`.
- API contract de interpretación (Lilly): `main.py` ahora expone opcionalmente `abu_line`, `lilly_line` y `reasoning` junto a `headline`, `narrative`, `actions`, `astro_metadata` (compatibilidad preservada).
- Interpret UI (`/interpret`):
  - Desacople de estado (edición vs. committed) para evitar fetch por tecla.
  - Lazy loading de mapa/forecast con botón "Ver Recomendaciones Geográficas y Forecast".
  - Skeleton screens y mejores contenedores (overflow, break-words, scroll horizontal en metadata).
- Navigation: menú simplificado; en páginas internas solo "← Volver al Portal".

### Fixed
- Input bug en `/interpret`: escribir una letra ya no dispara fetch automático.
- Texto desbordado en interpretación: estilos `break-words`, `overflow-hidden`, `overflow-x-auto`.
- OPENAI_API_KEY no inyectada: agregado en `docker-compose.yml` para `lilly_engine`.
- Life-cycle events → LLM schema: mapeo `{cycle, planet, angle, approx}` a `{type, planet, to, angle?, peak?}`.
- Parsing de JSON con code fences (```json ... ```): extractor robusto en `llm.py`.
- Rutas absolutas para axioms y numpy agregado a `requirements.txt`.

### Performance
- `/interpret`: requests iniciales reducidos 6 → 2 (life-cycles + interpret); mapa/forecast on-demand.
- Skeletons en `/interpret`, `/chart` y `/forecast` para mejorar percepción de velocidad.

### Notes
- Spanish is default language across prompts and UI unless overridden.
- If classical corpus is empty, knowledge layer gracefully degrades (sin referencias, solo axiomas).

---

## Older
- See previous progress reports in `docs/` for historical context.

[Unreleased]: https://github.com/your-org/AI_Oracle/compare/v2.1...HEAD
[v2.1]: https://github.com/your-org/AI_Oracle/releases/tag/v2.1
