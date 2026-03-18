# CLAUDE.md — AI Oracle / Abu Engine
> Leer este archivo antes de cualquier tarea. Contiene el estado actual del proyecto, arquitectura, convenciones y el plan de desarrollo activo.
> **Para tareas de integración Abu↔Lilly, leer también `ARCHITECTURE.md` (raíz del repo).**

---

## Proyecto

**AI Oracle** — motor astrológico computacional con campo escalar geográfico (Harmony Field) e interpretación por agentes LLM (Lilly Swarm). Stack: Python (backend / engine), TypeScript / Next.js (frontend), Docker, GCP.

Raíz del repo: `D:\projects\ai-oracle`

---

## Documentos de referencia obligatoria

| Documento | Cuándo leerlo |
|---|---|
| `CLAUDE.md` | Siempre — estado del proyecto y plan de desarrollo |
| `ARCHITECTURE.md` | Tareas que tocan la integración Abu↔Lilly, el Event System, el Context Builder o los endpoints que Lilly consume |
| `AXIOMATICS_OF_HEAVENS_v0_4.md` | Tareas que tocan scoring, dominios, HF o cualquier decisión doctrinal |

---

## Arquitectura en capas

```
Scientific Core → Intelligence → Applications → Agent Ecosystem
Abu Engine       Lilly Swarm    Relocation Atlas   Gresham / Oracle
```

### Componentes principales

| Componente | Ruta | Estado |
|---|---|---|
| Abu Engine (cómputo astronómico) | `abu_engine/` | ✅ funcional |
| Harmony Field v3 (campo escalar) | `abu_engine/harmony/field_v3.py` | ✅ producción |
| Grillas de relocalización | `output/relocation_fields_v3/` | ✅ 4,650 sujetos |
| GeoJSON dominios (2.5°, 9 dominios) | `next_app/public/geojson/*_domains.geojson` | ✅ 10 sujetos demo |
| Rankings top-20 ciudades | `output/rankings/` | ✅ 4,650 sujetos |
| Demo pack (10 sujetos curados) | `output/demo/` | ✅ completo |
| Frontend Next.js + MapLibre | `next_app/` | ✅ funcional |
| Mapa de relocalización | `next_app/components/HFRelocationMap.tsx` | ✅ funcional |
| Eventos biográficos | `data/biographical_events/` | ✅ 527 eventos |
| Correlator HF↔eventos | `scripts/hf_correlator/` | ✅ ejecutado |
| Domain Ranking (SR por dominio) | `abu_engine/core/domain_ranking.py` | ✅ producción |
| Lilly Agent (columna derecha) | `next_app/` Oracle Interface | ✅ online — sin Event System aún |

---

## Harmony Field — fórmula actual (v3)

```python
HF_v3(φ, λ) = HF_aspects + β * HF_angles(φ, λ) + γ * HF_houses(φ, λ)
# β = 0.6, γ = 0.3
```

- `HF_aspects` = suma de resonancias gaussianas entre pares de planetas (fijo por carta natal)
- `HF_angles` = angularidad a ASC/MC/DESC/IC (varía con lat/lon)
- `HF_houses` = ocupación de casas (varía con lat/lon)

Archivos clave:
- `abu_engine/harmony/resonance.py` — ASPECT_WEIGHTS, GROUP_WEIGHTS
- `abu_engine/harmony/field.py` — aggregate_field()
- `abu_engine/harmony/field_v3.py` — compute_hf_aspects(), compute_relocation_field()
- `abu_engine/harmony/houses.py` — house_significators(), asignación planeta→casa
- `abu_engine/harmony/angularity.py` — fuerza gaussiana a ángulos

### Resultado de optimización de pesos (grid search, 527 eventos, 9,261 combinaciones)

| Métrica | Pesos óptimos | Valor |
|---|---|---|
| Mejor corr_all | w_h=-0.75, w_t=-1.0, w_c=2.5 | corr=0.155, Cohen's d=0.441 |
| Mejor composite | w_h=-2.0, w_t=-2.0, w_c=3.0 | corr=0.148, separation=2.678 |

**Hallazgo clave**: los pesos óptimos son negativos para harmony y tension. La razón: HF global mezcla eventos de distintas casas. El filtrado por dominio mejora la señal (Fase 6).

---

## Dataset

| Archivo | Contenido |
|---|---|
| `data/raw/raw_birthdata.jsonl` | 5,359 cartas natales (5,348 geocodificadas, con Rodden rating) |
| `data/processed/hf_dataset_v2.parquet` | 4,650 embeddings HF 36D — input canónico para grillas |
| `data/biographical_events/*.json` | 527 eventos biográficos con transit_hf_weighted y valence |
| `data/external/worldcities.csv` | 144,563 ciudades GeoNames |
| `data/gold_standard/GS_00{1,2,3}.json` | 3 sujetos curados (Jung, Tesla, Turing) |

### Parquet de relocalización (por sujeto)
Columnas: `lat, lon, hf_total_v3, hf_aspects, hf_angles, hf_houses, delta_hf_total_v3, asc_lon, mc_lon`
Filas: 9,425 (grilla 2.5°×2.5°, lat∈[-70,70], lon∈[-180,175])

### GeoJSON multi-propiedad (generado) ✅
Cada Feature tiene: `hf_{domain}` y `delta_{domain}` para 9 dominios: `global, h1, h2, h4, h5, h6, h7, h9, h10`
Archivos: `next_app/public/geojson/{slug}_domains.geojson` (10 sujetos demo, 9425 pts, ~4.2 MB c/u)

---

## Endpoints disponibles (Abu Engine — producción)

| Endpoint | Descripción | Estado |
|---|---|---|
| `GET /api/astro/chart` | Carta natal base | ✅ |
| `GET /api/astro/chart/extended` | Carta + dignidades + lotes + fardars + profecciones + tránsitos | ✅ — fuente de AbuContext para Lilly |
| `GET /api/astro/solar-return` | SR para año y ciudad | ✅ |
| `GET /api/astro/domain-score` | Score ciudad puntual por dominio | ✅ |
| `POST /api/astro/domain-ranking` | Ranking lista de ciudades por dominio | ✅ |
| `GET /api/astro/relocation-field` | Campo HF natal on-demand con soporte `domain` (h1-h10) | ✅ |
| `GET /api/astro/sr-relocation-field` | Campo HF del Retorno Solar por grilla | ✅ |
| `GET /api/cities/search` | Búsqueda de ciudades | ✅ |
| `GET /api/astro/forecast` | Tránsitos activos | ✅ — timeout frecuente, optimización pendiente |

---

## Plan de desarrollo activo

### Fase 1 — Motor: planet_filter en field_v3.py ✅ `[COMPLETA]`
### Fase 2 — Data: etiquetar eventos por house_domain ✅ `[COMPLETA]`
### Fase 3 — Pipeline: grillas por dominio (demo pack) ✅ `[COMPLETA]`
### Fase 4 — Frontend: selector de dominio en el mapa ✅ `[COMPLETA]`
### Fase 5 — Domain Ranking por Solar Return ✅ `[COMPLETA 2026-03-13]`
### Fase 6 — Validación estadística ✅ `[COMPLETA 2026-03-13]`
### Fase 7 — Mejoras visuales del mapa HF ✅ `[COMPLETA 2026-03-14]`

Resultados Fase 6:

| Casa | N | corr_global | corr_domain | Δcorr | Resultado |
|------|---|-------------|-------------|-------|-----------|
| H04 Hogar | 34 | −0.001 | +0.305 | +0.306 | ✅ confirmado |
| H05 Creatividad | 57 | +0.198 | +0.353 | +0.155 | ✅ confirmado |
| H06 Trabajo/Salud | 18 | −0.317 | +0.051 | +0.369 | ✅ confirmado |
| H07 Amor | 93 | +0.098 | +0.088 | −0.010 | ❌ sin mejora |
| H09 Expansión | 56 | +0.014 | −0.123 | −0.138 | ❌ sin mejora |
| H10 Carrera | 226 | +0.090 | +0.033 | −0.057 | ❌ sin mejora (sesgo N+=208/N−=4) |

H10: Cohen's d_global=+0.871 — separación real pero desbalance de valencias limita Pearson. Ver Experimento 5 en `HF_EXPERIMENT_LOG.md`.

---

### Fase 8 — Paridad usuario/demo + Mapa Solar Return ✅ `[COMPLETA 2026-03-15]`

El mapa del usuario en `localhost:3000/chart` → "Mi Relocalización" ahora tiene
paridad visual con el demo y campos por dominio on-demand.

**Tarea 8.1** ✅ — Paridad visual: `step: "5"` → `step: "2.5"` en `relocation-tab.tsx`
- Root cause del mapa oscuro: 2409 pts (5°) → kernels de heatmap no se solapan a zoom 2
- Fix: 9425 pts (2.5°) = misma densidad que los GeoJSON del demo → colores cálidos visibles

**Tarea 8.2** ✅ — Dominio on-demand para el usuario
- `compute_field()` en `services/relocation.py` extendida con `planet_subset: List[str] | None`
- Endpoint `GET /api/astro/relocation-field` acepta `domain=h1|h2|h4|h5|h6|h7|h9|h10`
- Usa `house_significators()` para derivar el `planet_subset` del dominio pedido
- GeoJSON devuelto tiene propiedades `hf_total`/`delta_hf` (mismo formato que global)

**Tarea 8.3** ✅ — `DomainSelector` en modo natal del usuario
- `relocation-tab.tsx`: importa `DomainSelector` + estado `hfDomain: Domain`
- Al cambiar dominio: fetch `/api/astro/relocation-field?domain=hX` → nuevo blob URL → mapa actualiza
- Overlay de loading "Calculando campo de dominio…" mientras espera
- Al volver a "global": restaura GeoJSON original de `data.geojson` sin re-fetch

**Tarea 8.4** ✅ — Mapa de Retorno Solar (nueva)
- `compute_sr_field()` en `services/relocation.py`: encuentra SR datetime → usa esas posiciones planetarias en el grid. El SR datetime es independiente de la ubicación; solo cambia el ASC/MC local.
- Endpoint `GET /api/astro/sr-relocation-field?birthDate&lat&lon&year&step` — GeoJSON con `natal_latitude/natal_longitude/natal_hf/sr_datetime/year` en `properties`
- `relocation-tab.tsx` modo `solar_return`: fetch automático al activar el tab o cambiar `srYear`, mapa `HFRelocationMap` con `natalHf=srNatalHf`, SR datetime en header, ranking Abu Mashar por dominio debajo

**Concepto SR**: El mapa SR muestra qué ubicaciones activan mejor la configuración planetaria del año. A diferencia del mapa natal (blueprint permanente), el SR es el snapshot del cielo en el momento exacto que el Sol vuelve a su longitud natal — distinto cada año.

**Archivos modificados en Fase 8:**
- `next_app/components/relocation-tab.tsx`
- `abu_engine/services/relocation.py` — `compute_field(planet_subset)` + `compute_sr_field()`
- `abu_engine/main.py` — endpoints `relocation-field` + `sr-relocation-field`

Plan completo de la sesión en: `SESION_FE_PARIDAD_USUARIO.md`

---

### Fase 8.5 — Flujo demo + Lilly screen_open ✅ `[COMPLETA 2026-03-16]`

**Tarea 8.5.1** ✅ — CTA "Ver el motor en acción" → `/demo`
- `lib/i18n.ts`: `lillyCtaDemo` actualizado en 4 idiomas + strings `demoPageTitle/Subtitle/Loading` + export `DEMO_DESCRIPTIONS`
- `app/page.tsx`: href `/relocation` → `/demo`

**Tarea 8.5.2** ✅ — Página `/demo`: selector de celebridad
- `app/demo/page.tsx` — grid de 10 cards (todos los sujetos del demo pack)
- Cada card: nombre en serif, años de vida, ciudad natal, descripción i18n, badge Rodden rating
- Al click: `runAbuAnalyze` → `setBirthData` + `setAbuData` → `/chart` — mismo flujo que BirthDataPanel
- `lib/store.ts`: campo `isDemo: boolean` + `setIsDemo()` — no afecta renderización
- Sujetos: einstein, freud, jung, tesla, gandhi, frida, picasso, vangogh, borges, bowie

**Tarea 8.5.3** ✅ — Lilly screen_open (orientación inicial al cargar carta)
- `app/api/lilly/screen-open/route.ts` — POST route que llama a OpenAI (`LILLY_MODEL`, default `gpt-4o-mini`)
- System prompt fiel a `ARCHITECTURE.md §5`; context block: nombre, secta, maestro de secta, regentes ASC/MC + dignidades, firdaria, lang
- `components/OracleChat.tsx`: `useEffect` reemplazado — extrae contexto de `abuData`, llama al route, inyecta respuesta con typewriter; si falla → mensaje de "sin conexión" sin romper la UI
- `OPENAI_API_KEY` ya inyectada por `docker-compose.yml`; para dev local agregar en `next_app/.env.local`

**Archivos modificados en Fase 8.5:**
- `next_app/app/page.tsx`
- `next_app/app/demo/page.tsx` — nuevo
- `next_app/app/api/lilly/screen-open/route.ts` — nuevo
- `next_app/lib/i18n.ts`
- `next_app/lib/store.ts`
- `next_app/components/OracleChat.tsx`

---

### Fase 8.6 — Fixes UI + click_planet ✅ `[COMPLETA 2026-03-16]`

Sesión de corrección y mejoras sobre el flujo demo. Lilly ahora responde, los nombres son correctos
y las tarjetas de posiciones planetarias son clickeables y disparan interpretación en tiempo real.

**Fix 1** ✅ — LILLY_UNREACHABLE resuelto
- Causa raíz: `OPENAI_API_KEY=` vacío en `next_app/.env.local` (Next.js no carga el `.env` raíz)
- Fix: clave copiada a `next_app/.env.local` — Lilly responde inmediatamente

**Fix 2** ✅ — Nombre en header de `/chart`
- `app/chart/page.tsx`: `?.name` → `?.userName || abuData.person?.name`
- `birthData.userName` es el campo correcto (establecido por demo y por el form del usuario)

**Fix 3** ✅ — Firdaria para sujetos históricos
- `abu_engine/main.py`: cuando `get_current_fardar` devuelve N/A (ciclo de 75 años superado), hace fallback con `birth_date + 74 años` para obtener el último período registrado
- Response incluye `historical_fallback: true` — la UI muestra badge "último período registrado"
- Tesla (1856), Freud (1856), Van Gogh (1853) ahora muestran su último período en lugar de N/A

**Fix 4** ✅ — Rueda zodiacal: anillos separados
- `natal-chart-tab.tsx`: el `ZodiacWheel` en el tab Carta Natal ya no recibe `transitPlanets`
- El anillo exterior de tránsitos solo aparece en el tab Tránsitos (que gestiona su propio feed)

**Fix 5** ✅ — Técnicas Persas completas
- `persian-techniques-tab.tsx` reescrito con diseño dark consistente
- **Sect**: label + descripción doctrinal (qué planeta benéfico/maléfico actúa en esta carta)
- **Profección**: casa + signo + **señor del año** (dato clave, en amber) derivado del signo de la cúspide
- **Firdaria**: mayor + sub + fechas formateadas + badge histórico cuando aplica
- **Ciclos/Luna**: misma info, layout limpio

**Fix 6** ✅ — Rediseño tarjetas de posiciones planetarias
- `natal-chart-tab.tsx`: nuevo `PlanetCard` con layout en 3 líneas:
  - Fila 1: Símbolo + Nombre | badge Dignidad + score
  - Fila 2: Grado°Min' Signo · Casa N | [℞] si retrógrado
  - Separador
  - Fila 3: aspecto más exacto (calculado client-side de longitudes natales), 5 aspectos mayores, orbes ≤ 8°
- Quita el bloque "Tránsito" de las tarjetas natales
- Cursor pointer, hover borde ámbar

**Fix 7** ✅ — click_planet (primer evento reactivo de Lilly)
- `lib/store.ts`: campo `pendingLillyEvent: Record<string,any> | null` + `setPendingLillyEvent()`
- `app/api/lilly/planet/route.ts` — nueva route POST: arma context block (posición, dignidad, aspecto, retrogradación) → OpenAI → respuesta Lilly
- `components/OracleChat.tsx`: `useEffect` que escucha `pendingLillyEvent`, llama `/api/lilly/planet`, inyecta respuesta con typewriter al array de mensajes
- `natal-chart-tab.tsx`: click en tarjeta → `setPendingLillyEvent({ type: 'click_planet', payload: {...} })`
- Patrón extensible: cualquier componente puede disparar un evento Lilly via store sin acoplarse a OracleChat

**Archivos modificados en Fase 8.6:**
- `next_app/.env.local` — OPENAI_API_KEY
- `next_app/app/chart/page.tsx`
- `next_app/app/api/lilly/planet/route.ts` — nuevo
- `next_app/lib/store.ts` — pendingLillyEvent
- `next_app/components/natal-chart-tab.tsx` — reescrito
- `next_app/components/persian-techniques-tab.tsx` — reescrito
- `next_app/components/OracleChat.tsx` — useEffect click_planet
- `abu_engine/main.py` — firdaria fallback histórico

---

### Fase 8.7 — Iteración 4: rueda + técnicas persas + transits + relocalización ✅ `[COMPLETA 2026-03-16]`

**Fix 1** ✅ — ZodiacWheel: separación de radios
- `numPos` de casa movido de `(houseRadius+signRadius)/2=200` a `innerRadius+20=160`
- Planetas quedan en 215 (signRadius+35), números de casa en 160 — sin superposición

**Fix 2a** ✅ — Persian Techniques: i18n completa (4 idiomas)
- 23 keys nuevas en `lib/i18n.ts`: persianSect, persianProfection, persianFirdaria, persianCycles, etc.
- `persian-techniques-tab.tsx` totalmente conectado a `t.*`

**Fix 2b** ✅ — Persian Techniques: reactividad Lilly
- Route `POST /api/lilly/technique` — interpreta sect, profección y firdaria con Claude Sonnet 4
- Secciones convertidas a `<button>` con hover borde ámbar (igual que PlanetCard)
- OracleChat.tsx refactorizado: routing table `type → route` en lugar de `if/else`

**Fix 3** ✅ — Forecast timeout: causa raíz identificada y corregida
- `get_planet_positions` llamaba `load.timescale()` en cada iteración del loop (~52 veces en 7d step)
- `load.timescale()` lee datos de disco (leap seconds) — 200-500ms por llamada → 10-25s total
- Fix: `_ts_cache` a nivel de módulo en `forecast.py` — primera llamada carga, resto usa cache

**Fix 4** ✅ — My Relocation: reactividad Lilly completa
- Route `POST /api/lilly/domain` — interpreta dominio seleccionado
- Route `POST /api/lilly/city` — interpreta ciudad seleccionada (max 4-5 líneas, más rico)
- `RankingTable.tsx`: prop `onCityClick` + hover ámbar cuando tiene handler
- `relocation-tab.tsx`: `domainInitRef` para detectar cambios de dominio (skip first render), dispatch `domain_select`; `onCityClick` en RankingTable dispatch `city_select` con ASC/MC locales calculados

**Migración Anthropic API** ✅ — Todas las routes Lilly usan `@anthropic-ai/sdk`
- `screen-open`, `planet`, `technique`, `domain`, `city` → `claude-sonnet-4-6` (corregido en Fase 8.9)
- `ANTHROPIC_API_KEY` en `.env.local` (existía) y agregada en `docker-compose.yml`
- `openai` package queda como fallback para `lilly_swarm` chat (/api/chat proxy)

**Archivos modificados en Fase 8.7:**
- `next_app/components/zodiac-wheel.tsx` — radio numPos
- `next_app/lib/i18n.ts` — 23 keys persian* en 4 idiomas
- `next_app/components/persian-techniques-tab.tsx` — i18n + click handlers
- `next_app/components/OracleChat.tsx` — routing table de eventos Lilly
- `next_app/components/RankingTable.tsx` — onCityClick prop + hover ámbar
- `next_app/components/relocation-tab.tsx` — domain_select + city_select events
- `next_app/app/api/lilly/screen-open/route.ts` — migrado a Anthropic
- `next_app/app/api/lilly/planet/route.ts` — migrado a Anthropic
- `next_app/app/api/lilly/technique/route.ts` — nuevo, Anthropic
- `next_app/app/api/lilly/domain/route.ts` — nuevo, Anthropic
- `next_app/app/api/lilly/city/route.ts` — nuevo, Anthropic
- `abu_engine/core/forecast.py` — _ts_cache timescale singleton
- `docker-compose.yml` — ANTHROPIC_API_KEY

---

### Fase 8.8 — Partes Arábicas (Lotes) ✅ `[COMPLETA 2026-03-16]`

Diagnóstico previo: Abu Engine ya calculaba lotes en `GET /api/astro/chart/extended` (`extended.lots`)
pero el endpoint `/analyze` — fuente de `abuData` — no los incluía. Tampoco existía el campo `lord`.

**Tarea 8.8.1** ✅ — Backend: `lord` + lotes en `/analyze`
- `abu_engine/core/lots.py`: dict `SIGN_LORDS` con regencias tradicionales (Aries→Mars … Piscis→Júpiter)
- `calculate_all_lots()` ahora devuelve `lord` en cada lote: `{name, longitude, sign, degree, house, lord}`
- `abu_engine/main.py`: paso 6b en `/analyze` — calcula Fortuna/Espíritu/Eros/Necesidad con Sun/Moon/Venus/Mercury + ASC + cusps y los agrega como `derived.lots`

**Tarea 8.8.2** ✅ — Tipo `derived` actualizado
- `next_app/lib/types.ts`: campo `lots?` en `AbuAnalyzeResponse.derived` con tipo completo

**Tarea 8.8.3** ✅ — UI: sección "Partes Arábicas" en Técnicas Persas
- `components/persian-techniques-tab.tsx`: sección entre Firdaria y Tránsitos Lunares
- Muestra Parte de Fortuna y Parte del Espíritu (tarjetas clickeables, hover ámbar)
- Formato: `Signo Grado° · Casa N` + señor en amber
- Click → `click_technique` con `{ technique: 'lot', data: { lot_name, lon, sign, degree, house, lord, lord_dignity } }`

**Tarea 8.8.4** ✅ — Route Lilly: interpretación de lotes
- `app/api/lilly/technique/route.ts`: caso `lot` — context block con nombre del lote, posición, señor y dignidad → Lilly responde en 3-4 líneas

**Tarea 8.8.5** ✅ — i18n: 4 keys nuevas en 4 idiomas
- `persianLotsTitle`, `persianLotFortuna`, `persianLotSpirit`, `persianLotLord`

**Evento Lilly activo**: `click_technique` con `technique: 'lot'` — sigue el mismo patrón que sect/profección/firdaria.

**Pendiente**: `docker-compose build abu_engine` para que el endpoint `/analyze` incluya `derived.lots`.

**Archivos modificados en Fase 8.8:**
- `abu_engine/core/lots.py` — SIGN_LORDS + campo lord
- `abu_engine/main.py` — paso 6b lots en /analyze
- `next_app/lib/types.ts` — lots en tipo derived
- `next_app/lib/i18n.ts` — 4 keys persianLots* en 4 idiomas
- `next_app/components/persian-techniques-tab.tsx` — sección Partes Arábicas
- `next_app/app/api/lilly/technique/route.ts` — caso lot

---

### Fase 8.9 — Hotfix: model ID + tab rename + diagnóstico API ✅ `[COMPLETA 2026-03-16]`

**Fix 1** ✅ — Model ID corregido en todas las routes Lilly
- Root cause de LILLY_UNREACHABLE: `claude-sonnet-4-20250514` ya no es válido en `@anthropic-ai/sdk ^0.78.0`
- Fix: `claude-sonnet-4-20250514` → `claude-sonnet-4-6` en 5 routes (`screen-open`, `planet`, `technique`, `domain`, `city`)

**Fix 2** ✅ — OracleChat: error reporting mejorado
- `data.response || '> ERROR: LILLY_UNREACHABLE'` → `data.response || \`> ERROR: ${data.error ?? 'LILLY_UNREACHABLE'}\``
- Ahora muestra el mensaje exacto del SDK en lugar del genérico

**Fix 3** ✅ — Tab "Mapa HF" en i18n (4 idiomas)
- `tabRelocation`: "Mi Relocalización" → "Mapa HF" (ES, PT) / "HF Map" (EN) / "Carte HF" (FR)

**Pendiente post-Fase 8.9:**
- `lib/lilly-prompt.ts` — system prompt v1.0 compartido (ver prompt en historial de chat con Guillermo)
- Transits y Mapa HF no calculan en flujo demo (condición `!!birthData` debe ser `!!abuData`)
- `docker-compose build abu_engine` — activa `derived.lots` en `/analyze`

**Archivos modificados en Fase 8.9:**
- `next_app/app/api/lilly/screen-open/route.ts` — model ID
- `next_app/app/api/lilly/planet/route.ts` — model ID
- `next_app/app/api/lilly/technique/route.ts` — model ID
- `next_app/app/api/lilly/domain/route.ts` — model ID
- `next_app/app/api/lilly/city/route.ts` — model ID
- `next_app/components/OracleChat.tsx` — error reporting
- `next_app/lib/i18n.ts` — tabRelocation en 4 idiomas

---

### Fase 8.10 — Sesión CC: Layout + Panel Guía + Reactividad Completa ✅ `[COMPLETA 2026-03-16]`

**Tarea CC.1** ✅ — Proporciones de layout
- `DashboardLayout.tsx`: columna izquierda `280px → 180px`, columna derecha `350/400px → 380px` (fijo, sin breakpoint xl)

**Tarea CC.5** ✅ — Oracle Interface ancho ajustable (2026-03-16, commit `5098091`)
- Ancho default `440px` (era `380px`), rango `300–700px`, persiste en `localStorage('oracleWidth')`
- Divisor arrastrable (`w-1`, `cursor-col-resize`, hover `amber-400/30`, active `amber-400/50`) entre `<main>` y `<aside>` Oracle
- `widthRef` sincroniza el ancho durante el drag — evita closure stale en `mouseup` al escribir `localStorage`
- Handlers `mousemove`/`mouseup` en `useEffect(deps=[])` — montados una vez, leen refs no state

**Tarea CC.2** ✅ — Panel izquierdo: de datos estáticos a guía activa
- `TechnicalPanel.tsx` reescrito: cuando hay carta cargada muestra 3 secciones:
  - **LEYENDO AHORA** — refleja `lastLillyEvent.label` del store (actualizado en cada evento)
  - **SEÑOR DEL AÑO** — planeta de la profección + dignidad + casa activada (determinista, sin LLM)
  - **EXPLORAR** — 3 botones de `lillySuggestions` (del store) que disparan el evento correspondiente
- `screen-open/route.ts` modificado: incluye instrucción de sugerencias en el context block, parsea bloque `[SUGERENCIAS]` del raw text, devuelve `{ response, suggestions }`. `max_tokens` sube a 768
- `OracleChat.tsx`: al recibir respuesta de screen_open llama `setLillySuggestions(data.suggestions)`; al procesar cualquier evento deriva un label y llama `setLastLillyEvent({ type, label })`
- `store.ts`: campos nuevos `lastLillyEvent: { type, label } | null` + `lillySuggestions: Array<{type, target, label}> | null` (no persisten)
- `i18n.ts`: 5 keys nuevas en 4 idiomas — `tpReadingNow`, `tpNoSelection`, `tpYearLord`, `tpActivatedHouse`, `tpExplore`

**Tarea CC.3** ✅ — Técnicas Persas: tarjetas faltantes reactivas
- `persian-techniques-tab.tsx`: Tránsitos Lunares convertido a `<button>` con `click_technique / lunar_transit`; Ciclos Planetarios: cada fila es un `<button>` con `click_technique / planetary_cycle`
- `technique/route.ts`: casos `lunar_transit` (posición Luna + aspectos activos) y `planetary_cycle` (ciclo + planeta + ángulo + fecha) con `max_tokens: 256` (respuestas cortas 2-3 líneas)

**Tarea CC.4** ✅ — Forecast: vectorización + cap de rango (Fase 10)
- `forecast.py`: nueva función `get_planet_positions_batch()` — vectoriza skyfield: en lugar de `N_dates × N_planets` llamadas, hace `N_planets` llamadas con array de fechas (1 por planeta). `forecast_timeseries` usa batch. `_ts_cache` ya estaba.
- Cap `_MAX_FORECAST_DAYS = 90` — requests con rango > 90 días se truncan automáticamente

**Archivos modificados en Fase 8.10:**
- `next_app/components/DashboardLayout.tsx` — proporciones columnas
- `next_app/components/TechnicalPanel.tsx` — reescrito: panel guía activa
- `next_app/lib/store.ts` — lastLillyEvent + lillySuggestions
- `next_app/lib/i18n.ts` — 5 keys tpReadingNow/tpNoSelection/tpYearLord/tpActivatedHouse/tpExplore
- `next_app/app/api/lilly/screen-open/route.ts` — instrucción sugerencias + parsing
- `next_app/components/OracleChat.tsx` — setLillySuggestions + setLastLillyEvent
- `next_app/components/persian-techniques-tab.tsx` — lunar_transit + planetary_cycle click
- `next_app/app/api/lilly/technique/route.ts` — casos lunar_transit + planetary_cycle
- `abu_engine/core/forecast.py` — get_planet_positions_batch() + _MAX_FORECAST_DAYS cap

---

### Fase 9 — Lilly Event System `[PARCIAL]`

click_planet implementado en Fase 8.6 como route independiente.
Lo que resta es el sistema reactivo completo per ARCHITECTURE.md.

**Tarea 9.1** — Event System FE: emisores `LillyEvent` tipados para todas las pantallas
- `click_planet` ✅ funcional (Fase 8.6) — implementación directa, no via Context Builder
- `domain_select`, `click_house`, `click_transit`, `city_select` — pendientes
**Tarea 9.2** — Context Builder: traducción evento → prompt estructurado (determinista, sin LLM)
- Centraliza la construcción de context blocks (hoy cada route lo hace ad-hoc)
**Tarea 9.3** — System prompt completo: citas de Christian Astrology, casos edge, tono refinado
**Tarea 9.4** — RAG pipeline: chunking de Christian Astrology, recuperación por trigger
**Tarea 9.5** — Benchmark de modelo: GPT-4o-mini vs GPT-4o vs Claude Sonnet 4.6 en 5 casos representativos

**Prerequisito**: leer `ARCHITECTURE.md` completo antes de tocar cualquier tarea de esta fase.
El contrato LillyEvent, AbuContext schema y las plantillas del Context Builder están definidos ahí.

---

### Fase 10 — Optimización de tránsitos ✅ `[COMPLETA 2026-03-16]`

Vectorización aplicada en Fase 8.10 (CC.4). Ver detalle arriba.

---

## Convenciones del proyecto

- **Sistema de casas**: Placidus
- **Referencial**: Topocéntrico
- **Efemérides**: Swiss Ephemeris DE440s (rango 1849-12-26 a 2150-01-22)
- **Grilla relocalización**: 2.5°×2.5°, lat∈[-70,70], lon∈[-180,175], 9,425 puntos
- **Planetas activos**: Sol, Luna, Mercurio, Venus, Marte, Júpiter, Saturno, Urano, Neptuno, Plutón + ASC + MC
- **Aspectos**: conjunción 0°, sextil 60°, cuadratura 90°, trígono 120°, oposición 180°
- **Grupos de aspecto**: harmony = sextil+trígono, tension = cuadratura+oposición, conjunction = conjunción
- **Coordenada actual del usuario**: campo "Ciudad de residencia actual" del formulario Home → `current_lat/current_lon` en requests que la necesiten. Si no viene, usar birth_lat/birth_lon como fallback.

## Sujetos demo (output/demo/)

| Slug | ID | Rodden |
|---|---|---|
| einstein | 308660 | AA |
| freud | 337730 | AA |
| jung | 366580 | A |
| tesla | 357700 | B |
| gandhi | 61360 | A |
| frida | 35255 | AA |
| picasso | 76835 | AA |
| vangogh | 317785 | AA |
| borges | 12145 | AA |
| bowie | 232650 | A |

## Frontend

- URL local dev: `http://localhost:3001` (Docker ocupa :3000)
- Rutas activas:
  - `next_app/app/page.tsx` — Home: título `ABU ORACLE`, CTAs "Ingresar mis datos" (form on-demand) + "Ver el motor en acción" → `/demo`
  - `next_app/app/demo/page.tsx` — Selector de celebridad: grid 10 cards, llama `/analyze` on-demand → `/chart`
  - `next_app/app/chart/` — Carta natal (requiere `abuData`)
  - `next_app/app/relocation/RelocationClient.tsx` — Mapa relocalización (única consumer del mapa)
  - `next_app/app/relocation-map/` — ELIMINADA
- Componentes UI clave:
  - `next_app/components/Navigation.tsx` — Top bar global con selector de idioma conectado a `setLang` del store (visible en todas las páginas)
  - `next_app/components/TechnicalPanel.tsx` — Panel guía activa (desde Fase 8.10): LEYENDO AHORA (`lastLillyEvent`), SEÑOR DEL AÑO (profección), EXPLORAR (sugerencias de Lilly). Sección `tpSysArch` colapsable + status dots siempre visibles
  - `next_app/components/OracleChat.tsx` — Cuando `abuData && birthData`: llama `/api/lilly/screen-open` → typewriter + guarda suggestions en store. Escucha `pendingLillyEvent` → llama route, inyecta respuesta, actualiza `lastLillyEvent`. Sin datos: bloque `SYSTEM_READY / AWAITING INPUT`
  - `next_app/components/natal-chart-tab.tsx` — Rueda zodiacal (sin tránsitos) + tarjetas planetarias clickeables. Click → `setPendingLillyEvent` → Lilly responde
  - `next_app/components/persian-techniques-tab.tsx` — Sect + Profección + Firdaria + Partes Arábicas + **Tránsitos Lunares** (clickeable, `lunar_transit`) + **Ciclos Planetarios** (cada fila clickeable, `planetary_cycle`)
  - `next_app/components/HFRelocationMap.tsx` — Mapa MapLibre GL heatmap
- API routes internas (Next.js):
  - `next_app/app/api/chat/route.ts` — proxy a lilly_swarm para chat conversacional
  - `next_app/app/api/lilly/screen-open/route.ts` — llama Anthropic (`claude-sonnet-4-6`) con contexto mínimo AbuContext (screen_open)
  - `next_app/app/api/lilly/planet/route.ts` — click_planet: context block planeta → Anthropic → interpretación
  - `next_app/app/api/lilly/technique/route.ts` — click_technique: sect/profección/firdaria/lot → Anthropic → interpretación
  - `next_app/app/api/lilly/domain/route.ts` — domain_select: dominio HF → Anthropic → interpretación
  - `next_app/app/api/lilly/city/route.ts` — city_select: ciudad relocalización → Anthropic → interpretación (max_tokens=768)
- `next_app/app/api/cities/nearest/route.ts` — GET `?lat&lon` → ciudad más cercana por haversine sobre `data/external/worldcities.csv` (144k filas, cache en memoria). Path con fallback dev/Docker via `fs.existsSync`.
- GeoJSON públicos: `next_app/public/geojson/` — formato legacy `subject_*_hf.geojson` + dominios `*_domains.geojson`
- Rankings públicos: `next_app/public/rankings/`

---

## Cómo trabajar con este repo

Cuando Claude Code retome una sesión, leer este archivo primero y preguntar por la fase activa.
La próxima tarea es siempre la primera sin tilde `✅` en el plan de desarrollo — actualmente **Fase 9 (Lilly Event System completo)**.

**Estado Lilly al 2026-03-16 (Fase 8.10)**: screen_open ✅, click_planet ✅, click_technique (sect/profección/firdaria/lot/**lunar_transit**/**planetary_cycle**) ✅, domain_select ✅, city_select ✅. Todas las routes usan `claude-sonnet-4-6` via `@anthropic-ai/sdk`. System prompt v1.0 en `lib/lilly-prompt.ts` ✅. Pendiente: click_house, click_transit, Context Builder centralizado (Fase 9).

**Estado panel guía al 2026-03-16**: TechnicalPanel reescrito — LEYENDO AHORA + SEÑOR DEL AÑO + EXPLORAR operativos. `screen-open` devuelve `{ response, suggestions }`. `store.ts` mantiene `lastLillyEvent` y `lillySuggestions` en memoria (no persisten).

---

### Features y fixes — sesión post Fase 8.10

#### ZodiacWheel — tooltip hover + click_planet desde la rueda (`4d2cc3f`)
- `PlanetPosition` exportado con `deg`, `dignity`, `retrograde`
- `onPlanetClick?: (planet: PlanetPosition) => void` en props
- `hoveredPlanet` state local — tooltip `foreignObject` con nombre, signo, grado, casa, dignidad, retrógrado
- Borde amber en planeta hovered (`stroke #fbbf24`, `strokeWidth 4`)
- Tránsitos: solo hover informativo, sin disparo Lilly
- `natal-chart-tab`: pasa `dignity` + `retrograde` en `natalPlanets`, conecta `onPlanetClick` a `handlePlanetClick` existente

#### DashboardLayout — Oracle panel resizable (`5098091`, `eb4e704`)
- `oracleWidth` en state (300–700px, default 440px), persiste en `localStorage('oracleWidth')`
- Divisor arrastrable `w-1` entre `<main>` y `<aside>` Oracle — `cursor-col-resize`, hover amber
- `widthRef` + handlers en `useEffect(deps=[])` — evita closure stale en `mouseup`

#### Click en mapa HF → reverse geocoding → city_select (`e5b0f16`, `119e713`, `45aac70`)
- `GET /api/cities/nearest?lat&lon` — haversine sobre 144k ciudades, cache en memoria al primer request
- CSV path: `fs.existsSync` prueba `process.cwd()/data/external/` (Docker) y `../data/external/` (dev)
- `docker-compose.yml`: volume `./data/external:/app/data/external:ro`
- `HFRelocationMap`: prop `onMapClick`, click handler en `useEffect` separado con `map.off` en cleanup
- `relocation-tab`: `handleMapClick` con `useCallback` + `isProcessingClick` ref (cooldown 1s)
- Conectado en mapa natal y mapa SR

#### Fixes OracleChat — sesión 2026-03-16 (post Fase 8.10)

Tres bugs corregidos en `next_app/components/OracleChat.tsx`. Commits: `854b83e`, `24b6929`, `07b201b`.

**Fix 1 — Reset al cambiar sujeto** (`854b83e`)
- Causa: `initialized.current` (useRef) nunca se reseteaba → al cambiar de carta `screen_open` no re-disparaba y los mensajes del sujeto anterior persistían en el array local `messages`.
- Fix: `prevAbuRef` compara la referencia del objeto `abuData`. Si cambia → reset `initialized + messages + lastLillyEvent + lillySuggestions`.
- Patrón: `prevAbuRef.current !== undefined && prevAbuRef.current !== abuData` → reset.

**Fix 2 — Guard `isComplete`** (`24b6929`)
- Causa: `abuData && birthData` acepta cualquier objeto truthy, incluso localStorage corrupto o respuesta parcial.
- Fix: `const isComplete = (d) => Array.isArray(d?.chart?.planets) && d.chart.planets.length > 0` como condición adicional antes de disparar.

**Fix 3 — `screen_open` solo en `/chart`** (`07b201b`)
- Causa: `OracleChat` vive en `DashboardLayout` (todas las rutas). Al recargar `/`, `abuData` se rehidrata desde localStorage → `isComplete` pasa → Lilly disparaba en Home sin que el usuario hiciera nada.
- Fix: `usePathname()` de `next/navigation` → `isChartPage = pathname === '/chart'` → guard completo: `!initialized.current && isChartPage && isComplete(abuData) && birthData`.
- `isChartPage` agregado a deps del useEffect.

Para tareas que toquen la integración con Lilly (Fase 9 en adelante), leer `ARCHITECTURE.md` antes de escribir código.

Al completar una tarea, marcarla con `✅` en este archivo y hacer commit.

## Fase 10 — Multi-usuario (EN PROGRESO)

Ver `MULTIUSER_ARCHITECTURE.md` para arquitectura completa.

Stack: Firebase Auth + Firestore + Resend + **Paddle** webhook
Proyecto GCP: `abu-oracle`

### Estado
- [x] Firebase Auth habilitado
- [x] Firestore habilitado
- [x] auth middleware en abu-engine
- [x] Login/Register en Next.js ✅ `[COMPLETA 2026-03-17]`
- [x] AuthGuard en /chart ✅ `[COMPLETA 2026-03-17]`
- [x] AuthGuard en / (Home) ✅ `[COMPLETA 2026-03-18]`
- [x] Páginas legales (Privacy + Terms) en landing page ✅ `[COMPLETA 2026-03-18]`
- [ ] Webhook de pago **Paddle** (ubicación TBD — ver nota abajo)
- [ ] Email bienvenida con Resend
- [x] Deploy backend GCP (Cloud Run + SA)
- [x] Testing end-to-end (auth frontend + flujo pago) ✅ `[VALIDADO 2026-03-17]`
- [ ] LANZAMIENTO

### Avance confirmado (2026-03-17)

- GCP provisioning completado:
  - `identitytoolkit.googleapis.com` habilitada
  - `firestore.googleapis.com` habilitada
  - Firestore Native creada en `us-central1`
- Seguridad/IAM:
  - Service Account `abu-engine-sa@abu-oracle.iam.gserviceaccount.com` creada
  - Rol `roles/datastore.user` asignado
- Backend auth desplegado:
  - Nuevo módulo `abu_engine/core/auth.py` (Firebase JWT verify + quota check Firestore)
  - `firebase-admin==6.5.0` agregado en `abu_engine/requirements.txt`
  - 12 endpoints de Abu protegidos con `Depends(verify_token)`
- Deploy y validación en producción:
  - `abu-engine` deployado en Cloud Run con SA adjunta
  - Smoke tests OK: `/health` 200, endpoint protegido sin token 401, token falso 401

### Avance confirmado (2026-03-17) — Frontend auth completo

Implementado por Codex, validado en esta sesión:

- `next_app/lib/firebase.ts` — inicialización condicional Firebase (no rompe si faltan vars)
- `next_app/lib/auth-context.tsx` — AuthProvider: login/register/logout/getIdToken vía Firebase Auth
- `next_app/components/AuthGuard.tsx` — guard que redirige a `/auth/login?next=` si no hay sesión
- `next_app/lib/abu-auth.ts` — `getAbuAuthHeaders()`: inyecta Bearer token JWT en requests al backend
- `next_app/app/auth/login/page.tsx` — página login/register con toggle, manejo de errores, redirect post-auth
- `next_app/app/layout.tsx` — `<AuthProvider>` wrappea toda la app
- `next_app/app/chart/page.tsx` — envuelto en `<AuthGuard>`

**Fixes de configuración detectados y resueltos:**
- API key de Firebase tenía `1` (número) en lugar de `l` (letra) → corregido en `.env.local`
- Email/Password provider no estaba activado en Firebase Console → activado en Authentication → Sign-in method
- Dev server tenía procesos zombie en puertos 3001 y 3002 (35 KB y 90 KB de memoria = muertos) → matados con PowerShell `Stop-Process`
- Webpack cache corrupto → regenerado automáticamente al reiniciar

**Validación E2E (2026-03-17):**
- `/auth/login` → formulario carga ✅
- Register con guillemosiaira@gmail.com → redirige a `/chart` ✅
- `/chart` carga carta natal ✅
- Abu Engine: `GET /health` → 200 desde browser ✅
- `[Abu] POST /analyze` → `Response OK` en consola ✅

### Avance confirmado (2026-03-18) — Landing page legal + Paddle

**Distinción de repos (crítica):**
| Repo | URL pública | Stack | Hosting |
|---|---|---|---|
| `Abu-Oracle` | `app.abu-oracle.com` | Next.js + Python | Cloud Run (GCP) + Cloudflare Worker |
| `abu-oracle-landingpage` | `abu-oracle.com` | HTML estático | Vercel (Hobby) |

**Landing page (`abu-oracle-landingpage`) — cambios:**
- `privacy.html` → `abu-oracle.com/privacy` — bilingüe ES/EN, toggle en esquina superior derecha
- `terms-and-conditions.html` → `abu-oracle.com/terms-and-conditions` — idem
- `index.html` — footer con links a privacy y terms; 20 spots → **100 spots** Genesis
- `vercel.json` — `cleanUrls: true` para servir sin extensión `.html`
- Git global configurado `guillermosiaira@gmail.com` / `GuillermoSiaira` — Vercel Hobby bloquea commits de autores no asociados a la cuenta GitHub. **No usar Co-Authored-By en commits de este repo.**

**Webhook de pago — decisión de procesador:**
- Procesador cambiado de **Lemon Squeezy → Paddle**
- Lógica escrita: verifica `Paddle-Signature` (HMAC-SHA256 sobre `ts:body`), procesa evento `transaction.completed`, extrae email de `data.customer.email`, crea usuario Firebase Auth + doc Firestore, envía email Resend
- **Ubicación TBD**: la landing es HTML estático (no puede tener API routes). Opciones: Vercel serverless separado o Next.js app Abu Oracle.
- Variables requeridas cuando se implemente: `PADDLE_WEBHOOK_SECRET`, `RESEND_API_KEY`, `FIREBASE_SERVICE_ACCOUNT_JSON` (o ADC en Cloud Run)

### Avance confirmado (2026-03-18) — AuthGuard Home + infra Cloudflare Worker

- `next_app/app/page.tsx` — `<AuthGuard>` en ambos returns (Home inicial + showForm). Commit `209da3c`.
- Deploy Next.js → Cloud Run revision `abu-oracle-app-00002-6n8` ✅

**Infraestructura `app.abu-oracle.com` — Cloudflare Worker como reverse proxy:**
- Cloud Run no acepta hostname custom sin `gcloud beta run domain-mappings` (requiere dominio verificado en Google).
- Solución: Worker `abu-oracle-proxy` en Cloudflare que reescribe el hostname a `abu-oracle-app-503488473965.us-central1.run.app`.
- Custom domain `app.abu-oracle.com` asignado al Worker en Cloudflare Workers & Pages.
- DNS: el CNAME anterior fue reemplazado por el registro gestionado por el Worker.
- Validado: `https://app.abu-oracle.com` → redirige a `/auth/login` ✅

**Worker code** (Cloudflare Workers & Pages → `abu-oracle-proxy`):
```javascript
export default {
  async fetch(request) {
    const url = new URL(request.url);
    url.hostname = "abu-oracle-app-503488473965.us-central1.run.app";
    url.protocol = "https:";
    url.port = "";
    const newRequest = new Request(url.toString(), {
      method: request.method,
      headers: request.headers,
      body: ["GET", "HEAD"].includes(request.method) ? null : request.body,
      redirect: "follow",
    });
    return fetch(newRequest);
  },
};
```

### Avance confirmado (2026-03-18) — Fixes producción + Webhook crypto

**Fixes producción (todos en Cloud Run):**
- `abu_engine/core/auth.py`: `_get_firebase_app()` antes de `auth.verify_id_token()` — el SDK no se inicializaba al primer request → 401 en todos los endpoints. Commit `4d05a19`.
- `next_app/lib/abu-auth.ts`: `await firebaseAuth.authStateReady()` antes de `getIdToken()` — Firebase restora sesión async, `currentUser` era null en el primer render. Commit `58c202b`.
- `next_app/Dockerfile`: `COPY --from=builder /app/data ./data` en runner stage — `worldcities.csv` no llegaba al container → `/api/cities/nearest` fallaba → HF map click sin respuesta.
- `next_app/data/external/worldcities.csv`: incluido en build context (no en git — gitignored en raíz).

**Firestore usuario de prueba:**
- UID `xJhOVmVFRUXoRBRGK6mJWyMeZOu1` (`guillermosiaira@gmail.com`) con `payment_verified: true`, `plan: genesis`, `quota_limit: 99999`.
- Creado via Firestore REST API con gcloud ADC (quota project: `abu-oracle`).

**Webhook crypto-payment (Alchemy + Arbitrum):**
- `next_app/app/api/webhook/crypto-payment/route.ts` — verifica `x-alchemy-signature` HMAC-SHA256, filtra transfers ETH a Safe wallet `0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82`, provisiona usuario Genesis en Firebase Auth + Firestore, envía email Resend.
- `next_app/lib/firebase-admin.ts` — init Firebase Admin SDK con ADC (Cloud Run) o `FIREBASE_SERVICE_ACCOUNT_JSON` (local).
- Deps nuevas: `firebase-admin ^13.7.0`, `resend ^6.9.4`, `uuid ^13.0.0`.
- `GENESIS_PRICE_ETH=0.001` en Cloud Run (test) → cambiar a `0.19` para producción.
- Safe wallet: `0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82` (Arbitrum).

**Cloud Run env vars actualizadas (abu-oracle-app, revision 00005-2cb):**
- Agregadas: `RESEND_API_KEY`, `ALCHEMY_WEBHOOK_SECRET`, `GENESIS_PRICE_ETH=0.001`, `LILLY_MODEL=gpt-4o-mini`
- `PADDLE_WEBHOOK_SECRET` vacío — pendiente aprobación Paddle

**Archivos nuevos en esta sesión:**
- `next_app/app/api/webhook/crypto-payment/route.ts`
- `next_app/lib/firebase-admin.ts`

### Siguiente bloque operativo

1. Configurar Alchemy Notify webhook apuntando a `https://app.abu-oracle.com/api/webhook/crypto-payment` → probar E2E con envío de `0.001 ETH` a la Safe wallet
2. Verificar email de bienvenida (Resend → `noreply@abu-oracle.com`)
3. Cambiar `GENESIS_PRICE_ETH=0.19` en Cloud Run cuando test pase
4. Webhook Paddle → `next_app/app/api/webhook/payment/route.ts` (cuando aprueben)
5. LANZAMIENTO
