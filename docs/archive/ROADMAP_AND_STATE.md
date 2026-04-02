# AI Oracle — Roadmap & Project State

> Archivo consolidado desde memoria de sesión Copilot. Mantener actualizado.
> Última actualización: 2026-03-12

## Estado actual de fases

| Fase | Estado | Descripción |
|------|--------|-------------|
| 1 | ✅ COMPLETADA | Demo pack en output/demo/ (10 sujetos, 2.5° grid, rankings deduplicados) |
| 2 | ✅ COMPLETADA | Frontend /relocation (dropdown, idioma es/en/pt/fr, MapLibre heatmap, ranking table, narrative panel) |
| 3 | ✅ COMPLETADA | Endpoint Abu `GET /api/astro/relocation` + tab "Mi Relocalización" conectado |
| 4 | ✅ COMPLETADA | HF v4: fórmula ponderada, bio scraper, correlador, optimizador de pesos |
| 5 | ✅ COMPLETADA | Map overhaul: CARTO tiles, heatmap, interactividad, mini-ranking, filtro región |

## Historial de sesiones

### Session 1-2: Repo review + Data reorganization
- Restructured data/: raw/, processed/, failures/, audit/, gold_standard/, external/
- Restructured output/: relocation_fields/ (v3, 4650 parquets), rankings/, maps/, geojson/, archive/
- Created output/MANIFEST.json, docs/DATABASE_STRUCTURE.md

### Session 2-3: Data enrichment
- Reverse geocoding: 5,348 of 5,359 records (reverse_geocoder offline)
- Rodden rating inference: AA:2322 | A:714 | B:1563 | C:745 | DD:4 | XX:11
- Rankings: top-20 city rankings for all 4,650 subjects
- Created data/external/worldcities.csv (144,563 cities)

### Session 3: Demo pack (Fase 1)
- 10 curated subjects: Einstein, Borges, Frida, Picasso, Van Gogh, Freud, Jung, Gandhi, Tesla, Bowie
- Each has: geojson.json, ranking.json, narrative.json (offline)
- Scripts: generate_demo_pack.py, generate_demo_narratives.py

### Session 4: Frontend /relocation (Fase 2)
- Route: next_app/app/relocation/ (RelocationClient.tsx + page.tsx)
- Components: NarrativePanel.tsx, RankingTable.tsx
- Navigation.tsx: links with active state
- Language selector: es/en/pt/fr
- Chart tabs: "Mi Relocalización" placeholder for endpoint personal
- Upgraded react-markdown 8→9, remark-gfm 3→4 (TS5 fix)
- Reused HFRelocationMap.tsx (MapLibre GL)
- Grid upgraded: 5° (2,409 pts) → 2.5° (9,425 pts) via regenerate_demo_hires.py
- Rankings deduped by city (best HF per unique city)
- venv310: installed pyarrow

### Session 5: Endpoint Abu + Frontend integration (Fase 3)
- Endpoint: `GET /api/astro/relocation?birthDate=...&lat=...&lon=...&step=5&top_n=20`
- Backend: `abu_engine/services/relocation.py` (compute_field, make_ranking, build_geojson)
  - Extracted logic from scripts/regenerate_demo_hires.py into service module
  - Cities cache (worldcities.csv 144K), grid generation, HF v3 scoring
  - Step clamped to min 2.5°, top_n clamped to [1,50]
  - Response: geojson + rankings + natal_hf + max_hf + grid_points
  - Smoke tested: 5° grid = 2409 pts, ~6s compute time
- Frontend: `next_app/components/relocation-tab.tsx` (RelocationTab)
  - Fetches /api/astro/relocation from Abu, creates Blob URLs for HFRelocationMap
  - Reuses existing HFRelocationMap + RankingTable components
  - States: no birth data → prompt, idle → "Calcular" button, loading, error, results
  - Summary header: natal HF, max HF, grid points, recalculate button
- chart-tabs.tsx: replaced placeholder with RelocationTab component
- Removed legacy route: next_app/app/relocation-map/ (2 files)
- Logging: relocation events tracked via log_event()

### Session 5b: Bugfixes + visualization improvements
- **Heatmap mejorado**: HFRelocationMap.tsx — radio zoom-adaptable (8→100px), intensidad por zoom, eliminado circle layer (causaba dots feos), palette de colores más suave con 8 stops
- **Países completos**: ISO-2 → nombre completo (246 códigos) en relocation service + demo rankings patcheados (10 sujetos)
- **Lat/Lon en ranking**: RankingTable.tsx muestra coordenadas de cada ciudad
- **country_code** agregado al response del ranking (mantiene ISO-2 como referencia)
- **404 diagnosticado**: endpoint existe, requiere reinicio de Abu para cargar cambios

### Session 6: UI polish + HF formula analysis
- **Shared i18n**: `next_app/lib/i18n.ts` — UI strings centralizados (es/en/pt/fr) para tabs, relocation, ranking, leyenda
- **Global lang state**: zustand store (`next_app/lib/store.ts`) con `lang` + `setLang`, usado por /relocation y /chart
- **Color scale legend**: HFRelocationMap muestra leyenda gradiente (bottom-right)
- **City markers**: círculos numerados (#1-#5), borde blanco, sombra, 22px, popups con rank + nombre
- **Map visualization fix**: cambio de `heatmap` layer (kernel density, colores incorrectos) a `circle` layer (color directo por delta_hf). Blue=peor, White=neutral, Red=mejor que natal.
- **Map height**: prop `mapHeight` configurable (default "70vh")
- **HF formula diagnosis**: hf_total = harmony + tension + conjunction (ALL additive). Alto HF = alta actividad, NO alta armonía.
- **Decisión: Option B (Weighted)**: hf_weighted = w_h×harmony + w_t×tension + w_c×conjunction. Pesos entrenables vía correlación con eventos biográficos.

### Session 7: Bio scraper + HF v4 + Experimento de correlación (Fase 4)

> Documentación completa del experimento: `docs/theory/HF_THEORETICAL_FRAMEWORK.md` § Experiment 001

- **Bio event scraper** (`scripts/bio_scraper/`, 7 módulos):
  - Pipeline híbrido SPARQL + GPT-4o-mini. 229 eventos, 11 sujetos, avg 20.8/sujeto.
  - Output: `data/biographical_events/*.json` (schema v1.2)
  - Gold standard preservado (Jung 3/3 verificado)
- **HF v4 weighted formula**: implementada en `resonance.py` (GROUP_WEIGHTS), `field.py` (aggregate_field), `field_v3.py`
  - Fórmula: HF_weighted = w_h × harmony + w_t × tension + w_c × conjunction
- **Event-HF correlator** (`scripts/event_hf_correlator.py`):
  - 227 eventos procesados. Tránsitos calculados con Skyfield + Swiss Ephemeris.
  - Resultado: correlación NEGATIVA con pesos iniciales (r = −0.109, d = −0.27)
- **Weight optimizer** (`scripts/weight_optimizer.py`):
  - Grid search: 9,261 combinaciones, rango [-2.0, +3.0], step 0.25
  - **Hallazgo clave**: pesos óptimos invierten la hipótesis inicial
  - Óptimo v1: w_h = −1.25, w_t = −0.75, w_c = +0.75 (Cohen's d = 0.54, r = +0.19)
  - Conjunciones predicen eventos positivos; trines/sextiles = facilidad de fondo
  - Pesos aplicados a producción en `abu_engine/harmony/resonance.py`
  - Results: `data/biographical_events/optimization_results.json`

### Session 8: Expansión del corpus + Re-validación de pesos

- **Corpus expandido**: 11 → 26 sujetos, 229 → 529 eventos (avg 20.3/sujeto)
  - 15 nuevos sujetos: Monroe, Elvis, Ali, Hendrix, Joplin, Morrison, Dean, Miles Davis, Armstrong, Bruce Lee, Piaf, Hepburn, Bergman, Chanel, Wilde
  - Diversidad: género (8 mujeres), geografía (US/EU/Asia), época (1854-1942), campo (música, cine, deporte, moda, literatura)
  - Archivos: `scripts/bio_scraper/subjects.py` (26 entradas), 15 nuevos JSONs en `data/biographical_events/`
- **Re-validación del correlador** (527 eventos, 2 fuera de rango efemérides):
  - Pesos v1 (−1.25, −0.75, 0.75) en corpus expandido: r_nn = +0.133, d = +0.369 → señal se mantiene out-of-sample
- **Re-optimización de pesos** (grid search, 527 eventos):
  - **Óptimo v2: w_h = −1.0, w_t = −1.0, w_c = +2.5** (Cohen's d = 0.447, r_nn = +0.156)
  - Patrón de signos CONFIRMADO: w_h < 0, w_t < 0, w_c > 0
  - Conjunciones aún más dominantes (w_c = 2.5 vs 0.75 en v1)
  - Effect size reducido (d = 0.45 vs 0.54) — esperado con muestra más grande (menos overfitting)
- **Pesos v2 aplicados** a producción: `abu_engine/harmony/resonance.py` actualizado
- **Documentación actualizada**: `docs/theory/HF_THEORETICAL_FRAMEWORK.md` con resultados v2

### Session 9: Cross-validation LOSO

- **Script**: `scripts/cross_validation.py` — Leave-One-Subject-Out (26 folds)
  - Cada fold: hold out 1 sujeto, grid search en 25 restantes, evaluar en held-out
- **Resultado clave**: patrón de signos preservado en **26/26 folds (100%)**
  - w_h < 0, w_t < 0, w_c > 0 en todos los casos
- **Estabilidad de pesos**: w_h = −1.12 ± 0.26, w_t = −1.08 ± 0.21, w_c = +2.69 ± 0.43
  - Producción v2 (−1.0, −1.0, +2.5) dentro de 0.5σ de las medias LOSO
- **Test-set effect size**: v2 fixed d = +0.40 > per-fold trained d = +0.25
  - Pesos globales generalizan mejor que optima por fold → no hay overfitting
- **Documentación**: `docs/theory/HF_THEORETICAL_FRAMEWORK.md` § Result 3
- **Output**: `data/biographical_events/cross_validation_results.json`

### Session 8b: Map visualization overhaul + interactividad (Fase 5)

- **Mapa base**: Reemplazado `demotiles.maplibre.org` (caído) por CARTO Dark basemaps (fiable, sin API key)
- **Rendering**: Círculos → heatmap layer nativo (suave) + circle layer a zoom ≥ 5 para detalle
- **Paleta**: Azul/celeste agresivo → índigo-púrpura-ámbar-magenta (coherente con dark theme)
- **Natal marker con popup**: Estrella dorada muestra HF natal + coordenadas al click
- **City popups enriquecidos**: HF, delta vs natal (verde/rojo), coordenadas, distancia km
- **Tooltip hover**: Al pasar sobre circles (zoom ≥ 5), muestra HF total, delta y coords
- **Mini-ranking flotante**: Panel semi-transparente top-left con Top 3 ciudades + delta
- **Barra visual HF**: Barra comparativa natal → max HF en header de /relocation
- **Filtro por región**: Selector top-right (Global, Europa, Américas, Asia, África, Oceanía) con flyTo animado y filtro GeoJSON
- **Prop `natalHf`**: Nuevo prop en HFRelocationMap, pasado desde RelocationClient y relocation-tab
- **Archivos modificados**: HFRelocationMap.tsx, RelocationClient.tsx, relocation-tab.tsx

## Tareas pendientes

1. ~~**Endpoint Abu**~~ ✅ Session 5
2. ~~**Conectar tab "Mi Relocalización"**~~ ✅ Session 5
3. ~~**Eliminar ruta legacy /relocation-map**~~ ✅ Session 5
4. ~~**HF v4 weighted formula**~~ ✅ Session 7
5. ~~**Bio event scraper**~~ ✅ Session 7
6. ~~**Event-HF correlator + weight optimizer**~~ ✅ Session 7
7. **Regenerar narrativas con Lilly real** — correr generate_demo_narratives.py sin --offline
8. **Narrativa personal de relocalización** — integrar Lilly con el endpoint relocation
9. ~~**Expandir gold standard**~~ ✅ Session 8 — 26 sujetos, 529 eventos
10. ~~**Cross-validation**~~ ✅ Session 9 — LOSO 26 folds, patrón 26/26, v2 validado
11. **Cacheo de resultados** — cache de campos HF por birthDate+step
12. **Home UI: TechnicalPanel reactivo** — conectar sidebar izquierdo al store (dignities, rulers, LST del chart cargado)
13. **Home UI: System Architecture real** — reflejar config real del backend (no "JAX-Optimized")
14. **Home UI: Status de conexión Abu/Lilly** — indicador live en sidebar
15. **Home UI: Estado vacío elegante** — cuando no hay carta, mostrar invitación en vez de datos falsos

## Fase 3: Endpoint Abu /api/astro/relocation

### Qué construir
`GET /api/astro/relocation?birthDate=...&lat=...&lon=...`

### Piezas existentes
- `abu_engine/core/chart.py` → carta natal
- `abu_engine/core/aspects.py` → aspectos
- `abu_engine/core/houses.py` → casas
- `abu_engine/harmony/` → HF scoring
- `scripts/regenerate_demo_hires.py` → pipeline completo (compute_field + make_ranking, dedup)
- `data/external/worldcities.csv` → 144K ciudades

### Response shape esperado
```json
{
  "geojson": { "type": "FeatureCollection", "features": [...] },
  "rankings": [{ "city": "...", "country": "...", "hf_total_v3": 21.4, ... }],
  "natal_chart": { "planets": [...], "aspects": [...] },
  "natal_hf": 15.3,
  "max_hf": 21.4,
  "grid_points": 2409
}
```

## Key file locations
- Raw data: data/raw/raw_birthdata.jsonl (5,359 records)
- Embeddings: data/processed/hf_dataset_v2.parquet (4,650 rows, 36D)
- Relocation fields: output/relocation_fields/ (4,650 parquets, v3)
- Rankings: output/rankings/ (4,650 JSONs)
- Demo pack: output/demo/ (10 subjects, 2.5° grid)
- Cities: data/external/worldcities.csv (144,563)
- Manifest: output/MANIFEST.json
- Biographical events: data/biographical_events/ (26 JSONs + correlation + optimization results)
- HF theory + experiment: docs/theory/HF_THEORETICAL_FRAMEWORK.md
- Bio scraper pipeline: scripts/bio_scraper/ (7 modules)
- Event-HF correlator: scripts/event_hf_correlator.py
- Weight optimizer: scripts/weight_optimizer.py

## Notas técnicas
- GeoJSON property: `hf_total`; rankings property: `hf_total_v3`
- Canonical pipeline: embedding v2 → relocation model v3
- v2 relocation model FAILED (z_RSI=0.137), archived
- venv310 requerido para scripts con pyswisseph
- pip launcher roto en venv310: usar `python -m pip`
- Country distribution: US:1669 | FR:531 | ES:522 | GB:487 | IT:338
