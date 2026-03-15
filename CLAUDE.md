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

### Fase 9 — Lilly Event System `[PENDIENTE]`

Implementación del contrato Abu↔Lilly definido en `ARCHITECTURE.md`.

**Tarea 9.1** — Event System FE: emisores `LillyEvent` por pantalla (TypeScript)
**Tarea 9.2** — Context Builder: traducción evento → prompt estructurado (determinista, sin LLM)
**Tarea 9.3** — System prompt de Lilly: personalidad, voz, restricciones, citas de Christian Astrology
**Tarea 9.4** — RAG pipeline: chunking de Christian Astrology, recuperación por trigger
**Tarea 9.5** — Benchmark de modelo: Claude Sonnet 4.6 vs GPT-4o en 5 casos representativos

**Prerequisito**: leer `ARCHITECTURE.md` completo antes de tocar cualquier tarea de esta fase.
El contrato LillyEvent, AbuContext schema y las plantillas del Context Builder están definidos ahí.

---

### Fase 10 — Optimización de tránsitos `[PENDIENTE]`

El endpoint `/api/astro/forecast` frecuentemente supera el timeout de 15s del frontend.
Investigar causa raíz en el backend y optimizar el cálculo, no solo el timeout del FE.

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
| frida | 35255 / 370945 | AA |
| einstein | 308660 | AA |
| freud | 337730 | AA |
| tesla | 357700 | B |
| gandhi | 61360 | A |
| mlk | 238010 | A |
| borges | — | AA |
| picasso | — | AA |
| vangogh | — | AA |
| jung | — | A |

## Frontend

- URL local: `http://localhost:3000/relocation`
- Componente mapa: `next_app/components/HFRelocationMap.tsx`
- Ruta activa: `next_app/app/relocation/RelocationClient.tsx` (única consumer del mapa)
- Ruta eliminada: `next_app/app/relocation-map/` (borrada)
- GeoJSON públicos: `next_app/public/geojson/` — formato legacy `subject_*_hf.geojson` + dominios `*_domains.geojson`
- Rankings públicos: `next_app/public/rankings/`

---

## Cómo trabajar con este repo

Cuando Claude Code retome una sesión, leer este archivo primero y preguntar por la fase activa.
La próxima tarea es siempre la primera sin tilde `✅` en el plan de desarrollo — actualmente **Fase 9 (Lilly Event System)** o **Fase 10 (optimización tránsitos)**.

Para tareas que toquen la integración con Lilly (Fase 9 en adelante), leer `ARCHITECTURE.md` antes de escribir código.

Al completar una tarea, marcarla con `✅` en este archivo y hacer commit.
