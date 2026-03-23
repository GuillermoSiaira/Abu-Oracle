# CLAUDE.md — AI Oracle / Abu Engine
> Leer este archivo antes de cualquier tarea. Contiene el estado actual del proyecto, arquitectura, convenciones y el plan de desarrollo activo.
> **Para tareas de integración Abu↔Lilly, leer también `ARCHITECTURE.md` (raíz del repo).**

---

## 🚀 LANZAMIENTO PÚBLICO — 19 de marzo de 2026

**Abu Oracle se lanzó públicamente el 19 de marzo de 2026.**

- URL: `https://app.abu-oracle.com`
- Landing: `https://abu-oracle.com`
- Modelo de acceso: Genesis Member — 100 slots · 500 USDC · acceso de por vida
- Pago: USDC en Arbitrum One → Safe wallet `0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82`
- Stack en producción: Next.js + Python/FastAPI → Cloud Run (GCP) · Firebase Auth · Firestore · Alchemy webhook · Resend
- Revisión inicial: `abu-oracle-app-00016-xqp`

### Gantt de Tránsitos — sesión 2026-03-22 (E2E pass session 2)

**`next_app/components/transits-tab.tsx` — reescritura completa**

La pestaña Tránsitos fue reemplazada por un Gantt interactivo. Los datos vienen de `useAppStore(s => s.timeline?.transits_window)` (ya cargado por OracleChat al montar la carta) — sin fetch adicional.

| Feature | Descripción |
|---|---|
| Gantt CSS | Barras `position:absolute` con `left%` + `width%` calculados desde fechas reales. Contenedor: header fijo 56px + área scrolleable `height: calc(100vh - 220px)` |
| Eje temporal | Labels de meses rotados verticalmente (`writing-mode: vertical-rl; transform: rotate(180deg)`), centrados con `justifyContent: center` |
| Selector ventana | Botones ± 6m / 12m / 18m (default 18) — recalcula bounds del Gantt |
| Bandas Firdaria | Overlay `position:absolute; z-index:-1` con `isolation:isolate` en contenedor → Mayor: púrpura `rgba(127,119,221,0.13)` · Menor: teal `rgba(29,158,117,0.10/0.22)`. Labels bajo el header (`top:60/78px`). Tooltip interactivo en banda mayor: planeta mayor/menor, fechas, badge activo |
| Barras de tránsito | Coloreadas por tipo de aspecto (ASPECT_META). Marcador blanco en `exact_date`. Línea naranja = hoy |
| Filtro "Solo activos" | Botón toggle — filtra `transits_window` a `is_active: true`. Muestra contador `N/Total` |
| Tooltip global | `position:fixed` con `getBoundingClientRect()` — escapa cualquier `overflow` del scroll container. Clamped al viewport. Muestra: `{sym} {planet} {symbol} {natSym} {natalPlanet}` + tipo aspecto + exacto/ingreso/egreso + badge activo |
| Click en barra | `setPendingLillyEvent({ type: 'click_transit', payload: { transit_planet, natal_planet, aspect, exact_date } })` → Lilly interpreta |

**Decisiones técnicas:**
- Overlay Firdaria fuera del div scrolleable → `position:absolute` en el outer container → persiste al hacer scroll
- `isolation:isolate` en outer container → `z-index:-1` en overlay queda sobre el background pero bajo las filas
- Tooltip con `position:fixed` (no `absolute`) → no se clipea por `overflow-y:auto` del scroll container
- Header separado del scroll container → no usa `sticky` (evita duplicación) — el único elemento que scrollea es el div de filas

---

### Fixes UI/SVG — sesión 2026-03-22 (post Context Builder)

| Fix | Archivos | Descripción |
|---|---|---|
| Sidebar ancho + font | `DashboardLayout.tsx`, `TechnicalPanel.tsx` | `180px→220px`, `text-xs→text-sm`, `p-3→p-4` |
| Layout dos columnas Carta Natal | `natal-chart-tab.tsx` | Rueda 60% + posiciones planetarias 40% en `lg+`, scroll interno |
| Líneas de aspecto en SVG | `zodiac-wheel.tsx`, `natal-chart-tab.tsx` | Prop `natalAspects`, líneas SVG calculadas client-side sobre pares de planetas, radio 130, opacidad 0.7 |
| Bug casas↔signo | `zodiac-wheel.tsx` | Bloque `SIGNOS` derivado de `houseCusps` reales (antes usaba `ZODIAC_SIGNS` fijo en 0°/30°/60°…) |
| max_tokens técnicas | `lilly/technique/route.ts` | `lot`/`sect`/`profection`/`firdaria` → 2048 tokens |

---

### ⚠️ PENDIENTE DE DEPLOY A PRODUCCIÓN (commit `8092fdf` + sesión 2026-03-22)

**No deployar parcialmente. Deploy conjunto cuando E2E pass esté completo.**

Los siguientes cambios están en `main` pero **no han sido desplegados** a Cloud Run:

**Abu Engine** — requiere `docker build` + `docker push` + `gcloud run deploy abu-engine`:
- `GET /api/astro/sr-relocation-field` acepta param `domain`
- `POST /api/astro/solar-return-score` (nuevo endpoint)
- `compute_point_hf()` en `services/relocation.py`

**Next.js app** — requiere build con NEXT_PUBLIC_* args + `docker push` + `gcloud run deploy abu-oracle-app`:
- `app/api/astro/solar-return-score/route.ts` (nuevo proxy)
- `components/relocation-tab.tsx` (SR domain heatmap + scores + logging)
- **Context Builder canónico (sesión 2026-03-22)** — ver sección completa abajo
- FIX 1/2/3 de sesión 2026-03-22 (ancla ASC, header fecha, house_system)

**Nota**: `docker-compose.yml` con `AUTH_ENABLED=false` + `ENV=development` es **solo para dev local**.
En Cloud Run abu_engine ya tiene `AUTH_ENABLED=true` por defecto — no tocar esa variable en producción.

---

### Fixes post-lanzamiento (2026-03-21) — SR domain heatmap + scores + auth local dev

**Axioma 8.3 — SR heatmap domain-aware** (`main.py`, `relocation-tab.tsx`)
- `GET /api/astro/sr-relocation-field` acepta nuevo param `domain` opcional.
- Backend: `planet_subset = UNION(firdaria_planets, house_significators(natal, domain))` — misma lógica que `solar-return-score`.
- Frontend: `srLifeDomain` en deps del SR field useEffect → cambio de dominio re-fetcha el heatmap con el nuevo `domain` param.

**Nuevo endpoint `POST /api/astro/solar-return-score`** (`main.py`, `services/relocation.py`)
- Computa HF escalar por lista de ciudades usando posiciones del SR + `planet_subset` Firdaria+dominio.
- Helper `compute_point_hf()` en `services/relocation.py` — HF para un punto sin grid completo.
- Proxy Next.js en `app/api/astro/solar-return-score/route.ts`.

**Fix scores SR mostraban "—" siempre** (`relocation-tab.tsx`)
- Causa raíz 1: `fetchSRScores` llamaba al proxy Next.js → `getAbuAuthHeaders()` server-side → sin `currentUser` → sin token → Abu Engine 401 → silent return.
- Fix: `fetchSRScores` llama `getAbuAuthHeaders()` client-side y va directo a `ABU_BASE_URL` — igual que todos los otros fetches Abu Engine del archivo.
- Causa raíz 2: Abu Engine en Docker local no tiene credenciales Firebase para `ApplicationDefault()` → `auth.verify_id_token()` lanza excepción → 401 "Error de autenticación".
- Fix: `docker-compose.yml` agrega `AUTH_ENABLED=false` + `ENV=development` al servicio `abu_engine` → activa el bypass dev en `auth.py`. Fail-closed en Cloud Run: `K_SERVICE` presente → `sys.exit(1)` si `AUTH_ENABLED=false`.

**Bugs visuales modo SR** (`relocation-tab.tsx`, `lilly/city/route.ts`)
- Badge "filtrando por Firdaria": ahora muestra `"Firdaria · Carrera H10"` cuando hay dominio activo, `"filtrando por Firdaria"` cuando global.
- Lilly city_select en SR: payload incluye `active_domain` (LifeDomain key) y `active_domain_house` (hX). Route `/api/lilly/city` construye `domainLabel` diferenciado por modo.
- Logging: todos los fetches silenciosos en `relocation-tab.tsx` ahora loggean con `console.error`.

### Fixes post-lanzamiento (2026-03-21) — Mapa HF: click handler + SR context + layout

**Fix 1 — Click handler roto tras cambio de dominio** (`HFRelocationMap.tsx`)
- Causa raíz: useEffect del click handler tenía `mapInstance.current` (ref) en sus deps → React no re-ejecuta effects cuando cambia una ref → al cambiar dominio el mapa se destruía/recrea pero el handler no se re-registraba.
- Fix: click handler movido directamente dentro del callback `map.on('load', ...)` del useEffect principal. `map.remove()` en cleanup destruye todos los listeners automáticamente. Zero estados extra, zero useEffects extra.

**Fix 2 — `sr_domain_select` sin route** → ya estaba implementado desde sesión anterior. `routeMap` y `/api/lilly/solar-return/route.ts` existían.

**Fix 3 — Payload incorrecto en click de mapa SR** (`relocation-tab.tsx`, `city/route.ts`)
- Causa raíz: `handleMapClick` siempre enviaba `domain: hfDomain` (selector del modo natal) sin incluir `mode` ni `sr_year`. Lilly recibía contexto natal cuando el usuario estaba en el mapa SR.
- Fix: `mode` y `sr_year` en deps del `useCallback` y en el payload. `/api/lilly/city` diferencia primera línea del contextBlock según `mode === 'solar_return'`.

**Fix 4 — Layout inconsistente entre pestañas** (`relocation-tab.tsx`)
- Causa raíz: `LifeDomainSelector` aparecía debajo del mapa en modo `solar_return`, arriba en modo `natal`.
- Fix: `LifeDomainSelector` movido antes del `<HFRelocationMap>` en el bloque SR — consistente con modo natal.

**Dev: caché `.next` corrupta por case-mismatch en Windows**
- Causa: servidor iniciado desde `next_App` (mayúscula) vs ruta real `next_app` (minúscula) → webpack cachea rutas absolutas → mismatch causa `invariant expected layout router to be mounted`.
- Fix: `Remove-Item -Recurse -Force .next` + reiniciar siempre desde `D:\projects\ai-oracle\next_app` (minúscula).

### Fixes post-lanzamiento (2026-03-20)

**Fix: Chat conversacional Lilly — LINK_LOST eliminado** (`3999611`)
- Causa raíz: `/api/chat` hacía proxy a lilly_swarm (`LILLY_ENGINE_URL`) que no está desplegado en Cloud Run → siempre fallaba con `LINK_LOST`.
- Fix: route reescrita para usar Anthropic SDK (`claude-sonnet-4-6`) directamente, igual que las routes reactivas. Inyecta `LILLY_SYSTEM_PROMPT` completo + bloque compacto con datos de carta (nombre, planetas, sect, profección, firdaria).
- Revisión: `abu-oracle-app-00017-z26`

**Fix: Lecturas truncadas en chat** (`7f1f6c7`)
- Causa: `max_tokens: 512` insuficiente para lecturas natales completas.
- Fix: `max_tokens: 1500` por defecto, configurable via env var `LILLY_CHAT_MAX_TOKENS`.
- Revisión: `abu-oracle-app-00018-7j2`

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

### Fase 4 — Correlación segmentada por dominio ✅ `[COMPLETA 2026-03-21]`

Script: `scripts/correlate_by_domain.py` — z-score por sujeto, Pearson + Cohen's d + Mann-Whitney U + rank-biserial.
Reporte: `analysis/domain_correlation_report.md` · `analysis/domain_correlation_results.json`

| Casa | N | delta_corr | delta_rb | Resultado |
|------|---|------------|----------|-----------|
| H05 Creatividad | 57 | +0.150 | n/a (N−=1) | ✅ confirmado |
| H09 Expansión | 66 | +0.017 | +0.107 | señal débil positiva |
| H10 Carrera | 250 | −0.061 | +0.249 | rank-biserial mejora; Pearson limitado por N−=4 |
| H07 Relaciones | 93 | +0.017 | +0.214 | neutro — sin mejora ni degradación clara |
| H01/H02/H06/H08/H12 | <12 | — | — | N insuficiente |

**Diagnóstico H10**: rb_global=−0.315 → rb_domain=−0.066. El filtrado por dominio reduce el error del global en 0.249 puntos. Límite: significadores de H10 incluyen Neptuno y Plutón (planetas lentos — baja varianza temporal). Veredicto: hipótesis parcialmente confirmada y no refutada; el límite es el corpus, no el modelo.

**GS_004 — Guillermo Siaira** (nuevo Gold Standard, `data/biographical_events/GS_004_siaira.json`):
- 26 eventos con `lat`/`lon` por evento — único corpus con ubicación real en el dataset
- Balance: 11 negativos / 14 positivos / 1 neutro (mejor balance del corpus)
- Límite estructural: movilidad geográfica baja (Buenos Aires 1997–2021) → HF natal en ubicación del evento es constante para H10; el test espacial queda vacío por construcción

**Pendiente Fase 5 — HF SR con Firdaria** (no iniciar hasta nueva sesión):
- Especificación: `compute_relocation_field(reference_date, planet_subset=[firdaria_major, firdaria_minor])`
- Hipótesis: el campo de relocalización calculado con los planetas del período firdaria activo predice mejor la geografía de eventos del período que el campo global

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

## Estrategia Comercial

**Principio rector**: el sistema vende, el fundador crea.

El fundador tiene dificultad constitutiva para sostener el intercambio
mercantil directo. La solución es arquitectónica, no psicológica.

### Modelo faceless + agente autónomo

El Genesis launch es el prototipo funcional:
- Pago USDC on-chain → Arbitrum One, Safe multisig
- Webhook Alchemy → validación HMAC-SHA256
- Firebase Auth → creación automática de usuario
- Resend → email de bienvenida automático
- Flujo completo sin intervención manual del fundador

Horizonte: agente autónomo on-chain (ERC-8004) que opere, cobre,
entregue acceso y reinvierta en infraestructura sin intervención humana.

### Pricing Genesis (activo)
- 100 slots · 500 USDC · acceso de por vida
- Safe multisig: 0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82

### Ideas post-lanzamiento
1. Pronóstico largo plazo: Gantt tránsitos + Firdaria + Lilly reactiva
2. Reporte audio+visual cobrable: ElevenLabs + PDF — pago via Paddle
3. Agente autónomo ERC-8004: flujo comercial completamente on-chain

### Canales de distribución (faceless)
Mostrar el output del sistema, no al fundador.
El HF map, las lecturas de Lilly, los rankings de ciudades — eso es
el contenido. Guillermo no tiene que aparecer.

| Canal | Formato |
|---|---|
| Twitter/X | Thread técnico-astrológico |
| Instagram | Visual HF map + lectura corta |
| Landing page | Demo interactivo público |

---

## Bugs Pendientes

Esta sección es la fuente de verdad de bugs abiertos.
Marcar con ✅ al resolver. No eliminar — mover a historial abajo.

| # | Bug | Archivo | Prioridad | Estado |
|---|---|---|---|---|
| BUG-01 | Dignidades: rulerships modernos en lugar de tradicionales (Urano→Acuario, Plutón→Escorpio, Neptuno→Piscis). Impacto confirmado: Saturno en Leo devuelve peregrine en lugar de detriment | extended_calc.py | Alta — riesgo de impactar HF | 🔴 Abierto |
| BUG-02 | birth_dt no emitido en contextBlock — Lilly no calcula edad del nativo. Fix: agregar línea en context-builder.ts:~284 bajo header CARTA NATAL | context-builder.ts | Alta — fix trivial | 🟢 Resuelto · commit fix-bug02 |
| BUG-03 | UTC vs hora local en profecciones — birth_dt en UTC corre el aniversario profeccional 1 día. Fix: usar fecha local del nacimiento, no UTC | profections.py | Alta — afecta todos UTC± | 🟢 Resuelto · limitación: abu-analyzer.tsx usa GET /chart/extended — BUG-03 no corregido en ese flujo legacy. Pendiente. |
| BUG-04 | LINK_LOST intermitente en /api/chat — posible cold start Cloud Run + timeout Vercel edge (>25s con max_tokens:2500). Requiere reproducir + logs Cloud Run | next_app/api/chat | Media — requiere diagnóstico | 🔴 Abierto |

### Historial bugs resueltos
(vacío por ahora)

---

## Cómo trabajar con este repo

Leer CLAUDE.md al inicio de cada sesión (sección "## Bugs Pendientes" incluida). Los bugs documentados son issues conocidos — no investigarlos de nuevo, solo tenerlos presentes como contexto.

Cuando Claude Code retome una sesión, leer este archivo primero y preguntar por la fase activa.
La próxima tarea es siempre la primera sin tilde `✅` en el plan de desarrollo — actualmente **Fase 9 (Lilly Event System completo)**.

**Estado Lilly al 2026-03-16 (Fase 8.10)**: screen_open ✅, click_planet ✅, click_technique (sect/profección/firdaria/lot/**lunar_transit**/**planetary_cycle**) ✅, domain_select ✅, city_select ✅. Todas las routes usan `claude-sonnet-4-6` via `@anthropic-ai/sdk`. System prompt v1.0 en `lib/lilly-prompt.ts` ✅. Pendiente: click_house, click_transit, Context Builder centralizado (Fase 9).

**Estado panel guía al 2026-03-16**: TechnicalPanel reescrito — LEYENDO AHORA + SEÑOR DEL AÑO + EXPLORAR operativos. `screen-open` devuelve `{ response, suggestions }`. `store.ts` mantiene `lastLillyEvent` y `lillySuggestions` en memoria (no persisten).

### Context Builder canónico — sesión 2026-03-22 ✅ `[COMPLETO]`

**`/api/astro/biography`** — endpoint verificado ✅
- Devuelve profections (90 años) + firdaria (75 años aplanada) + transits_window (±18 meses, planetas lentos).
- Requiere auth (`verify_token`). En dev local: accesible sin auth solo si `AUTH_ENABLED=false` en Docker.

**`next_app/lib/context-builder.ts`** — creado, compila limpio ✅
- Exporta: `buildNatalContext()`, `buildActiveContext()`, `assembleContextBlock()`, `PlanetPosition`, `NatalContext`, `BiographicalTimeline`, `ActiveContext`.
- `assembleContextBlock()` produce bloque estructurado: CARTA NATAL · LÍNEA DE TIEMPO (profección activa+siguiente, firdaria activa+siguiente, tránsitos ±18m) · CONTEXTO ACTIVO (trigger_data específico del evento).

**Timeline en Zustand store + fetch en OracleChat** ✅
- `lib/store.ts`: campo `timeline: BiographicalTimeline | null` + `setTimeline()`. NO persiste en localStorage.
- `OracleChat.tsx`: fetch a `/api/astro/biography` al detectar cambio de `abuData` (una vez por sujeto). `setTimeline(null)` en reset al cambiar sujeto.
- `handleSubmit` (chat libre) envía `timeline` a `/api/chat`.

**8 routes Lilly migradas a `assembleContextBlock()`** ✅

| Route | `activeTab` | `lastEventType` | Notas |
|---|---|---|---|
| `screen-open` | `persian_techniques` | `screen_open` | Instrucción SUGERENCIAS añadida al bloque |
| `technique` | `persian_techniques` | `click_technique` | Lógica condicional por técnica eliminada |
| `planet` | `natal_chart` | `click_planet` | — |
| `transit` | `transits` | `click_transit` | `currentDate` = `transit_date` si viene |
| `domain` | `hf_map` | `domain_select` | `activeDomain` propagado |
| `solar-return` | `hf_map` | `sr_domain_select` | `activeDomain` = `active_domain ?? domain` |
| `city` | `hf_map` | `city_select` | `activeCity` poblado con `{name, lat, lon, hf_score}` |
| `chat` | `chat` | `chat` | Bloque en system prompt; filtro `!m.hidden` en history |

**Historial unificado** ✅
- Todos los callers reactivos envían `messages` (array local OracleChat, incluye reactivos).
- `/api/chat` filtra `hidden: true` antes de enviar a Anthropic (mensajes sintéticos son ruido en chat libre).
- Reactivos NO filtran `hidden` — el historial completo llega como contexto a routes reactivas.

**Bug fixes aplicados en esta sesión:**
- `chat/route.ts`: `currentDate` usaba `meta?.date` (fecha nacimiento) → corregido a `new Date().toISOString()`
- `OracleChat.tsx handleSubmit`: ahora envía `timeline` a `/api/chat`

**Verificación manual** ✅
- "¿Cuál es mi ascendente?" → Lilly responde **Acuario 26.9°** (no Capricornio)
- "¿En qué período estoy?" → Lilly menciona Firdaria Júpiter → **30 jul 2026**, Profección Casa 12 → **5 jul 2026**, convergencia de ambos cierres

**Archivos modificados en sesión 2026-03-22:**
- `next_app/lib/store.ts` — campo `timeline` + `setTimeline`
- `next_app/components/OracleChat.tsx` — fetch biography + `timeline` en todos los callers
- `next_app/app/api/lilly/screen-open/route.ts` — migrada
- `next_app/app/api/lilly/technique/route.ts` — migrada
- `next_app/app/api/lilly/planet/route.ts` — migrada
- `next_app/app/api/lilly/transit/route.ts` — migrada
- `next_app/app/api/lilly/domain/route.ts` — migrada
- `next_app/app/api/lilly/solar-return/route.ts` — migrada
- `next_app/app/api/lilly/city/route.ts` — migrada
- `next_app/app/api/chat/route.ts` — migrada + bug fix currentDate

---

### Context Builder — sesión 2026-03-20

**Base context completo en todas las routes** (`buildBaseContext()` en `lib/lilly-prompt.ts`)
- `buildBaseContext(abuData)` exportada — produce bloque natal estructurado: sect · todos los planetas (signo/grado/casa/dignidad/score/retrógrado) · ASC/MC con señores y sus dignidades · profección anual (casa/signo/señor derivados de la cúspide) · firdaria con fechas completas
- Inyectada en las 7 routes Lilly vía `natalData: abuData` en el payload (agregado en `OracleChat.tsx`)
- `max_tokens` subido a 1024 mínimo en todas las routes (`planet`: 512→1024, `technique`: 512→1024, `city`: 768→1024)

**Fix field names en `/api/chat/route.ts`**
- `profection?.lord` → derivado correctamente desde la cúspide de la casa activa (el campo no existe en el response del backend)
- `profection?.house_number` → `profection?.house` (field name correcto)

**Historial unificado Sistema A/B** (`OracleChat.tsx`)
- Mensajes reactivos (Sistema A) ahora incluyen un `user` sintético con `hidden: true` antes del `assistant`: `{ role: 'user', content: '[click_planet]', hidden: true }`
- `screen_open` también recibe su sintético: `{ role: 'user', content: '[carta_cargada]', hidden: true }`
- El `while` de `/api/chat/route.ts` ya no descarta el contexto reactivo previo — el array completo llega al LLM
- Render filtra `hidden: true` — el usuario no ve los sintéticos

**Fechas del período mayor de Firdaria** (`lib/lilly-prompt.ts`)
- `_computeFirdariaMajorDates(abuData)` — deriva `major_start` / `major_end` desde la fecha de inicio del subperíodo (backend) restando el offset acumulado de los sub-períodos anteriores
- No requiere fecha de nacimiento: usa los mismos valores que calculó el backend → sin error acumulado
- Bloque FIRDARIA ACTIVO ahora incluye: `Mayor: Sun (Peregrine) · inicio: 5 abr 2018 · cierre: 5 abr 2028` + `Menor: Jupiter (Exaltation) · inicio: 22 dic 2024 · cierre: 30 jul 2026`
- Badge `(período histórico aproximado)` cuando `historical_fallback: true`

**`/api/chat` max_tokens**: 1500 → 2500

**Archivos modificados:**
- `next_app/lib/lilly-prompt.ts` — `buildBaseContext()` + `_computeFirdariaMajorDates()` + `_formatDateEs()`
- `next_app/components/OracleChat.tsx` — `natalData` en fetches + user sintéticos hidden (reactivos + screen_open)
- `next_app/app/api/chat/route.ts` — fix profection lord + max_tokens 2500
- `next_app/app/api/lilly/planet/route.ts` — buildBaseContext + max_tokens 1024
- `next_app/app/api/lilly/technique/route.ts` — buildBaseContext + max_tokens 1024
- `next_app/app/api/lilly/domain/route.ts` — buildBaseContext
- `next_app/app/api/lilly/solar-return/route.ts` — buildBaseContext
- `next_app/app/api/lilly/transit/route.ts` — buildBaseContext
- `next_app/app/api/lilly/city/route.ts` — buildBaseContext + max_tokens 1024
- `next_app/app/api/lilly/screen-open/route.ts` — buildBaseContext + natalData

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

### Avance confirmado (2026-03-18) — Flujo de pago crypto completo (sesión actual)

**Decisión de arquitectura:** pago en **500 USDC** (Arbitrum One), no ETH. Alchemy reporta ERC-20 con `asset: "USDC"` y `value: 500`.

**Flujo end-to-end:**
```
Landing → Step 1 (email) → Step 2 (MetaMask connect) → Step 3 (USDC transfer)
  → POST /api/collect-email → Firestore pending_payments { email, wallet_address, status: "pending" }
  → usdc.transfer(SAFE_WALLET, 500_000_000) firmado en MetaMask
  → tx.wait(1) → Step 4: countdown 3s → redirect app.abu-oracle.com

Alchemy webhook (asíncrono):
  → query pending_payments by wallet_address → email real → status: "matched"
  → Firebase Auth user creado → Resend email de bienvenida
```

**Archivos nuevos/modificados:**
- `next_app/app/api/collect-email/route.ts` — NUEVO. POST `{ email, wallet_address }` → Firestore `pending_payments`. CORS: `https://abu-oracle.com`. OPTIONS preflight incluido.
- `next_app/app/api/webhook/crypto-payment/route.ts` — MODIFICADO:
  - Filtro: `asset === "ETH"` → `asset === "USDC"`, `GENESIS_PRICE_ETH` → `GENESIS_PRICE_USDC`
  - `provisionGenesisUser`: busca email real en `pending_payments` por `wallet_address` antes de crear usuario Firebase. Fallback a `wallet@abu-oracle.com` si no encuentra.
- `abu-oracle-landing/index.html` — MODIFICADO:
  - Sección `#wallet` reemplazada con flujo 4 pasos (email → MetaMask → confirm → confirmado)
  - ethers.js 5.7.2 via CDN. USDC ERC-20 transfer con `balanceOf` check previo.
  - Errores inline (sin `alert()`). Countdown 3s → redirect `app.abu-oracle.com`.
  - Botón "Contact to pay" eliminado (Paddle pendiente).
  - 100 Genesis slots (era 20).

**Cloud Run env vars (abu-oracle-app, revision 00007-tn2):**
- `GENESIS_PRICE_USDC=500` agregado
- `GENESIS_PRICE_ETH` eliminado

**Firestore — nueva colección `pending_payments`:**
```
{
  email: string,
  wallet_address: string | null,
  created_at: ISO string,
  status: "pending" | "matched"
}
```
Index requerido: single-field en `wallet_address` (Firestore lo crea automáticamente).

**Constantes de pago (hardcodeadas en landing):**
- USDC contract Arbitrum: `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`
- Safe wallet destino: `0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82`
- Monto: `500 * 1000000` (6 decimales)
- chainId Arbitrum One: `42161` (`0xa4b1`)

### Avance confirmado (2026-03-20) — Rediseño landing + Corpus publicado

**Landing page `abu-oracle-landingpage` — commit `3e9f030`:**
- `index.html` rediseñado completamente: hero nuevo ("Where in the world does your life work better?"), sección How it Works, stats empíricos (5,359 cartas / 527 eventos / r=0.615), sección Corpus con 3 documentos + hashes SHA-256, Pricing $500 USDC.
- El flujo de pago MetaMask/USDC fue removido del `index.html` (ese código estaba desactualizado). La página ahora dirige a `app.abu-oracle.com` directamente.
- Nueva carpeta `corpus/` con 5 páginas HTML, diseño dark tipográfico coherente:
  - `corpus/axiom-es.html` — Axiomática de los Cielos v0.4 (ES) — contenido completo del docx
  - `corpus/axiom-en.html` — Axiomatics of Heavens v0.4 (EN) — contenido completo del docx
  - `corpus/canon-es.html` — Cuerpo Canónico de Divulgación v1.0 (ES) — contenido completo del docx
  - `corpus/canon-en.html` — Canonical Communication Reference (EN) — contenido completo del docx
  - `corpus/on-the-geometry-of-heaven.html` — placeholder con hash + authorship
- Fuentes docx en `ai-oracle/docs/concepts/`: `AbuOracle_axiom_{es,en}.docx`, `AbuOracle_canon_{es,en}.docx`
- URLs activas: `abu-oracle.com/corpus/axiom-es`, `abu-oracle.com/corpus/axiom-en`, `abu-oracle.com/corpus/canon-es`, `abu-oracle.com/corpus/canon-en`, `abu-oracle.com/corpus/on-the-geometry-of-heaven`
- `vercel.json` ya tenía `cleanUrls: true` — sin cambios

**Notas de estado actual de la landing:**
- El flujo de pago (MetaMask + USDC) ya NO está en `index.html`. Toda la conversión pasa por `app.abu-oracle.com` (botón "Generate Your Map").
- El flujo de pago crypto sigue funcionando en `app.abu-oracle.com/api/collect-email` + webhook Alchemy.

### Siguiente bloque operativo

1. Probar E2E con 500 USDC real → verificar Firestore + email Resend (webhook Alchemy activo)
2. **Webhook Paddle** → `next_app/app/api/webhook/payment/route.ts` (cuando aprueben cuenta)
3. LANZAMIENTO

---

## Ideas y tareas futuras

### PENDIENTE — Axiomática y Canon (post Context Builder)

Una vez que el Context Builder canónico esté funcionando, dedicar una sesión a formalizar los siguientes conceptos:

**AXIOMA 9 — Convergencia Temporal** (para `AXIOMATICS_OF_HEAVENS`)
> "El tiempo no es un punto sino un campo. El nativo no existe en un momento astrológico — existe en la intersección de múltiples técnicas temporales simultáneas. La lectura válida es aquella que ubica al nativo en ese continuo, no la que fotografía un instante. La validez interpretativa aumenta cuando profección, firdaria y tránsito lento convergen sobre el mismo período."

**PRINCIPIOS OPERATIVOS** (para Canon)
- **Navegación biográfica**: el pasado es verificable y por eso es la base de la confianza del nativo en el sistema. Lilly puede navegar hacia atrás con la misma precisión que hacia adelante.
- **Ventana de acción**: el período donde convergen las técnicas favorables tiene fecha de inicio y fecha de cierre. Lilly debe comunicar ambas con precisión, sin generar ansiedad por el cierre.
- **Convergencia como señal**: cuando profección + firdaria + tránsito lento señalan el mismo período, Lilly lo nombra explícitamente como convergencia — no como coincidencia.

Estos conceptos deben integrarse en:
- `AXIOMATICS_OF_HEAVENS`: nuevo Axioma 9
- Canon (ES + EN): sección nueva "Navegación Temporal"
