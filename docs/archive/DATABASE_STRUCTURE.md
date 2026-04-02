# AI Oracle — Estructura de la Base de Datos

> Documento generado: 2026-03-09  
> Versión canónica de output: **v3 (modelo aditivo)**

---

## Visión general

El sistema AI Oracle opera con datos astrológicos en tres capas:

```
Scraper (carta-natal.es)
  → data/raw/                    Registros natales crudos
    → data/processed/            Embeddings HF (Harmony Field)
      → output/relocation_fields/  Evaluaciones de relocalización por sujeto
        → output/rankings/         Rankings de mejores ciudades
        → output/maps/             Mapas de calor geográficos
        → output/geojson/          Campos HF para visualización interactiva
```

---

## 1. `data/` — Datos de entrada y referencia

### `data/raw/`

| Archivo | Descripción |
|---------|-------------|
| `raw_birthdata.jsonl` | 5,359 registros natales scrapeados de carta-natal.es, enriquecidos con reverse geocoding y Rodden rating inferido. Un JSON por línea. |
| `raw_birthdata_original.jsonl` | Respaldo del JSONL original (sin enriquecer). |
| `ids.csv` | Lista de IDs scrapeados. |

**Campos por registro:**

| Campo | Tipo | Completitud | Notas |
|-------|------|-------------|-------|
| `id` | int | 100% | ID único del perfil en carta-natal.es |
| `name` | str | 100% | Nombre de la persona |
| `birth_date` | str | 99.8% | Fecha ISO (11 nulls) |
| `birth_time` | str | 99.8% | Hora de nacimiento |
| `time_precision` | str | 100% | `"exact"` o `"approximate"` |
| `timezone` | str | 99.8% | Zona horaria del lugar de nacimiento |
| `latitude` | float | 99.8% | Latitud del lugar de nacimiento |
| `longitude` | float | 99.8% | Longitud del lugar de nacimiento |
| `city` | str | **99.8%** | Reverse geocoding offline (GeoNames 144K+ ciudades via `reverse_geocoder`). |
| `country` | str | **99.8%** | Nombre del país en español. |
| `country_code` | str | **99.8%** | ISO 3166-1 alpha-2. |
| `rodden_rating` | str | **99.8%** | Inferido de `source` + `time_precision` (AA/A/B/C/DD/XX). |
| `source` | str | 99.8% | Fuente del dato de nacimiento |
| `url` | str | 100% | URL del perfil en carta-natal.es |

**Origen:** Scraper en `astro_dataset/cartanatal/`. Cache HTML en `astro_dataset/data/cache/profiles/`.

---

### `data/processed/`

Estos archivos contienen los **embeddings natales** (resumen 36D de cada carta natal). Son independientes de la geografía — representan al sujeto, no a un lugar. Sirven como **input** para generar los campos de relocalización en `output/`.

> **Nota sobre versionado:** Las versiones aquí (v1, v2) se refieren a variantes del embedding natal. Son distintas de las versiones de `output/relocation_fields/` (v1, v2, v3) que se refieren a variantes del modelo de evaluación geográfica. El embedding v2 es el input que alimenta el modelo de relocalización v3.

| Archivo | Filas | Descripción |
|---------|-------|-------------|
| `hf_dataset_v2.parquet` | 4,650 | **CANÓNICO.** Embeddings HF 36D con pesos de casa. Es el input para `output/relocation_fields/` (v3). |
| `hf_dataset_v1.parquet` | 4,650 | Histórico. Embeddings HF 36D puro (sin casas). |
| `hf_dataset_v1_summary.json` | — | Estadísticas descriptivas de v1. |
| `hf_dataset_v2_summary.json` | — | Estadísticas descriptivas de v2. |

**Embedding HF (36 dimensiones):**

| Componente | Dims | Fórmula |
|------------|------|---------|
| Vector Circular | 24D | $(cos θ_i, sin θ_i)$ para 12 puntos (Sol → MC) |
| Armónicos | 8D | $H_k = \|Σ w_i e^{ikθ_i}\|$ para $k ∈ \{1,2,3,4,5,6,8,12\}$ |
| Métricas HF | 4D | `hf_total`, `hf_harmony`, `hf_tension`, `hf_conjunction` |

**Estadísticas clave (v1):**

| Métrica | Media | Std | Min | Max |
|---------|-------|-----|-----|-----|
| hf_total | 14.61 | 2.62 | 8.23 | 29.59 |
| hf_harmony | 7.20 | 2.04 | 1.76 | 19.87 |
| hf_tension | 5.23 | 1.82 | 0.32 | 16.35 |
| hf_conjunction | 2.17 | 1.25 | 0.001 | 13.90 |

**¿Por qué 4,650 de 5,359?** 695 registros fallaron al procesar (la mayoría por fechas fuera del rango de la efeméride DE440s: 1849-12-26 a 2150-01-22). Los fallos están documentados en `failures/`.

---

### `data/processed/failures/`

| Archivo | Descripción |
|---------|-------------|
| `hf_dataset_v1_failures.jsonl` | 695 registros que fallaron en v1 (razón incluida). |
| `hf_dataset_v2_failures.jsonl` | Fallos de v2 (0 adicionales — misma base). |

---

### `data/gold_standard/`

Registros manualmente curados con datos biográficos verificables para validación experimental.

| Archivo | Sujeto | Rodden | Eventos |
|---------|--------|--------|---------|
| `GS_001_JUNG.json` | Carl Gustav Jung | AA | Crisis con Freud, infarto 1944, muerte 1961 |
| `GS_002_TESLA.json` | Nikola Tesla | AA | — |
| `GS_003_TURING.json` | Alan Turing | AA | — |

**Schema (v1.2):** `meta` (ID, nombre, Rodden rating, fuente), `birth_data` (fecha ISO, location con lat/lon/elevation, timezone), `biographical_events[]` (fecha, tipo, descripción, axiom target, confianza).

**Estado:** Solo 3 registros. **Objetivo: expandir a 10-20** con sujetos que tengan Rodden AA/A y eventos biográficos datados.

---

### `data/audit/`

Resultados de la auditoría de calidad del dataset crudo. Originalmente en `audit_output/`.

| Archivo | Contenido |
|---------|-----------|
| `dataset_audit_report.md` | Reporte narrativo completo de calidad |
| `dataset_overview.json` | Campos, tipos, conteo total (5,359) |
| `field_completeness.csv` | Completitud por campo (city/country/rodden = 0%) |
| `reliability_distribution.json` | high: 2,318 / medium: 2,137 / low: 687 / unknown: 217 |
| `categorical_distributions.json` | Distribuciones de valores categóricos |
| `temporal_distribution.json` | Distribución temporal de nacimientos |
| `dataset_anomalies.csv` | Registros con problemas detectados |
| `duplicate_records.csv` | Registros duplicados |
| `geo_anomalies.csv` | 11 anomalías geográficas |

---

### `data/external/`

| Archivo | Filas | Descripción |
|---------|-------|-------------|
| `worldcities.csv` | 144,563 | Base completa de ciudades GeoNames (pop. > 1,000). Usada para rankings y reverse geocoding de grilla. |
| `cities_sample.csv` | 50 | Muestra reducida (histórica). |

---

## 2. `output/` — Resultados computados

> **Versión canónica: v3 (modelo aditivo)**  
> Ver `output/MANIFEST.json` para detalle completo.

### `output/relocation_fields/` (CANÓNICA — v3)

**4,650 archivos parquet**, uno por sujeto. Cada uno tiene 2,409 filas (grilla global de 5° × 5°, lat ∈ [-70, 70], lon ∈ [-180, 175]).

**Columnas por archivo:**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `lat` | float | Latitud del punto de la grilla |
| `lon` | float | Longitud del punto de la grilla |
| `hf_total_v3` | float | HF total = aspectos + ángulos + casas |
| `hf_aspects` | float | Contribución de aspectos planetarios |
| `hf_angles` | float | Contribución de angularidad (ASC/MC) |
| `hf_houses` | float | Puntuación de ocupación de casas |
| `asc_lon` | float | Longitud eclíptica del ASC recomputado |
| `mc_lon` | float | Longitud eclíptica del MC recomputado |

**Modelo HF v3:**

$$HF_{total}(\phi, \lambda) = HF_{aspects} + HF_{angles}(\phi, \lambda) + HF_{houses}(\phi, \lambda)$$

Donde $HF_{aspects}$ es fijo por carta natal, y $HF_{angles}$ + $HF_{houses}$ varían geográficamente (ASC/MC dependen del horizonte local).

---

### `output/rankings/`

**4,650 archivos JSON** — Top 20 ciudades por sujeto, ordenadas por `hf_total_v3`.

**Campos por entrada:**

```json
{
  "subject_id": 1000,
  "relocation_latitude": 70.0,
  "relocation_longitude": 90.0,
  "hf_total_v3": 25.77,
  "hf_aspects": 20.55,
  "hf_angles": 3.70,
  "hf_houses": 10.0,
  "asc_lon": 150.42,
  "mc_lon": 31.24,
  "city": "Moscow",
  "country": "Russia",
  "city_lat": 55.76,
  "city_lon": 37.62,
  "distance_km": 2956.14
}
```

**Estado:** Completo. 4,650 sujetos con ranking de top 20 ciudades.

---

### `output/maps/`

**21 PNGs** — Mapas de calor HF generados con Cartopy.

- `subject_{id}_hf_total_v3.png` — Mapa absoluto de HF total sobre la superficie terrestre.
- `subject_{id}_delta_hf_total_v3.png` — Mapa de diferencia (HF relocalizado − HF natal).

**Estado:** ~10 sujetos con ambos mapas. Pendiente generar para el resto.

---

### `output/geojson/`

**9 archivos GeoJSON** — Campos HF en formato apto para mapas interactivos (Leaflet, Mapbox, frontend Next.js).

**Estado:** Solo 9 sujetos.

---

### `output/demo/` (NUEVO)

**10 sujetos curados** para demostración y testing del frontend. Cada sujeto tiene su propia carpeta con tres archivos.

| Sujeto | Slug | Rodden | HF natal | HF máx | Ganancia |
|--------|------|--------|----------|--------|----------|
| Albert Einstein | `einstein` | AA | 15.30 | 21.40 | +39.8% |
| Jorge Luis Borges | `borges` | AA | 18.75 | 24.96 | +33.1% |
| Frida Kahlo | `frida` | AA | 18.26 | 24.31 | +33.1% |
| Pablo Picasso | `picasso` | AA | 14.88 | 21.09 | +41.7% |
| Vincent Van Gogh | `vangogh` | AA | 17.54 | 22.62 | +29.0% |
| Sigmund Freud | `freud` | AA | 14.69 | 20.97 | +42.8% |
| Carl Gustav Jung | `jung` | A | 17.52 | 23.31 | +33.0% |
| Mohandas Gandhi | `gandhi` | A | 23.46 | 31.52 | +34.4% |
| Nikola Tesla | `tesla` | B | 19.74 | 24.90 | +26.1% |
| David Bowie | `bowie` | A | 19.84 | 22.35 | +12.6% |

**Estructura por sujeto:**

```
output/demo/{slug}/
    geojson.json      — FeatureCollection (2,409 puntos con hf_total, delta_hf, hf_aspects, hf_angles, hf_houses)
    ranking.json      — Top 20 ciudades con HF scores y coordenadas
    narrative.json    — Narrativa interpretativa (offline; regenerar con Lilly para versión LLM)
```

**Índice:** `output/demo/index.json` con metadata de todos los sujetos.

**Scripts:** `scripts/generate_demo_pack.py`, `scripts/generate_demo_narratives.py`

---

### `output/archive/`

Versiones anteriores. **No usar para análisis nuevos.**

| Carpeta | Contenido | Razón de archivo |
|---------|-----------|------------------|
| `relocation_fields_v1/` | 50 sujetos, modelo HF puro (solo aspectos) | Pilot — reemplazado por v3 |
| `relocation_fields_v2/` | 4,650 sujetos, pesos multiplicativos casas/angularidad | **FALLIDO** — z_RSI cayó a 0.137 |
| `relocation_maps_v1/` | 10 mapas delta del pilot | Suprimido por maps/ (v3) |

---

## 3. Relación de confiabilidad

El campo `rodden_rating` fue inferido de `source` + `time_precision` usando reglas de mapeo (script: `scripts/enrich_birthdata.py`):

| Rating | Criterio | Cantidad | Porcentaje |
|--------|----------|----------|------------|
| **AA** | Certificado/registro de nacimiento | 2,322 | 43.3% |
| **A** | Memorias / recuerdo directo | 714 | 13.3% |
| **B** | Biografía, base de datos, entrevista, escuela astrológica | 1,563 | 29.2% |
| **C** | Sin confirmar, hora aproximada, rectificación | 745 | 13.9% |
| **DD** | Datos contradictorios | 4 | 0.1% |
| **XX** | Sin fuente (null) | 11 | 0.2% |

**Recomendación:** Para análisis y demostración, filtrar a **high + medium** (4,455 sujetos, 83.2%).

---

## 4. Destino de datos futuros

Referencia rápida de dónde deben agregarse datos nuevos:

| Dato nuevo | Destino | Estado |
|------------|---------|--------|
| ~~Reverse geocoding (city/country)~~ | `data/raw/raw_birthdata.jsonl` | **✅ Completado** — 5,348 registros geocodificados |
| ~~Rodden rating inferido~~ | `data/raw/raw_birthdata.jsonl` (campo `rodden_rating`) | **✅ Completado** — AA/A/B/C/DD/XX asignados |
| ~~Rankings masivos~~ | `output/rankings/` | **✅ Completado** — 4,650 JSONs generados |
| ~~Demo pack (curado)~~ | `output/demo/` | **✅ Completado** — 10 sujetos con GeoJSON + ranking + narrativa |
| Gold standard expandido | `data/gold_standard/` (más JSONs GS_004…) | Pendiente |

---

## 5. Huecos conocidos y próximos pasos

| Hueco | Impacto | Solución propuesta |
|-------|---------|-------------------|
| ~~`city`, `country`: 100% null~~ | ~~No se puede segmentar geográficamente~~ | **✅ Resuelto** — reverse geocoding offline (GeoNames) |
| ~~`rodden_rating`: 100% null~~ | ~~Filtrado por calidad impreciso~~ | **✅ Resuelto** — inferido de `source` + `time_precision` |
| ~~Rankings: 11 / 4,650~~ | ~~99.8% sin output de ciudades~~ | **✅ Resuelto** — 4,650 rankings generados |
| Mapas: ~10 / 4,650 | Sin visualización para casi todo el dataset | Ejecutar `generate_hf_map.py` en batch |
| Gold standard: 3 sujetos | Insuficiente para validación | Curar 20+ con eventos biográficos datados |
| **HF fórmula: tensión suma** | Alto HF = alta actividad, no armonía | **Decidido:** HF v4 Weighted (ver §6) |
| Señal HF débil (z_RSI ≈ 0.44) | Modelo captura parcialmente el fenómeno | Pesos entrenables + dignidades clásicas |

---

## 6. Evolución de la fórmula HF

### HF v1–v3 (actual): Actividad Total

La fórmula vigente en `abu_engine/harmony/field.py` suma todos los aspectos sin distinción:

$$HF_{total} = HF_{harmony} + HF_{tension} + HF_{conjunction}$$

Donde:
- $HF_{harmony} = \sum sextile + trine$ (aspectos armónicos)
- $HF_{tension} = \sum square + opposition$ (aspectos tensos)
- $HF_{conjunction} = \sum conjunction$

Todos los `ASPECT_WEIGHTS` son 1.0. **Problema**: maximizar $HF_{total}$ busca máxima actividad astrológica, no máxima armonía. Un lugar con muchas cuadraturas puntúa igual que uno con trígonos.

Para relocalización (v3), el modelo agrega componentes geográficas:

$$HF_{v3}(\phi, \lambda) = HF_{aspects} + 0.6 \cdot HF_{angles}(\phi, \lambda) + 0.3 \cdot HF_{houses}(\phi, \lambda)$$

Pero $HF_{aspects}$ hereda el problema de base.

### HF v4 (próximo): Weighted — Pesos Entrenables

**Decisión (2026-03-10):** adoptar fórmula con pesos diferenciados por tipo de aspecto:

$$HF_{weighted} = w_h \cdot HF_{harmony} + w_t \cdot HF_{tension} + w_c \cdot HF_{conjunction}$$

**Pesos iniciales** (prior razonable):
| Componente | Peso | Justificación |
|-----------|------|---------------|
| $w_h$ (harmony) | +1.5 | Sextiles y trígonos favorecen |
| $w_t$ (tension) | −0.8 | Cuadraturas y oposiciones restan |
| $w_c$ (conjunction) | +1.0 | Conjunciones son ambivalentes |

### Estrategia de entrenamiento: Correlación Eventos × HF

Los pesos $(w_h, w_t, w_c)$ se optimizarán con datos empíricos:

1. **Scraping de eventos biográficos** — Extender `astro_dataset/` para extraer eventos con fecha, lugar y valencia (positivo/negativo/neutro) de las biografías de los 4,650+ sujetos.
2. **Cómputo de HF por evento** — Para cada evento, calcular la carta de tránsito en la fecha/lugar del evento y computar $HF_{weighted}$.
3. **Correlación** — Medir correlación entre $HF_{weighted}$ y la valencia del evento.
4. **Optimización** — Encontrar $(w_h, w_t, w_c)$ que maximicen la correlación (grid search, gradient-based, o Bayesian optimization).
5. **Validación cruzada** — Contra gold standard (actualmente 3, objetivo 20+).

**Pipeline conceptual:**

```
bio_events.jsonl  →  HF_at_event(date, lat, lon)  →  correlation(HF, event_quality)  →  optimize(w_h, w_t, w_c)
```

**Archivos involucrados:**
- `abu_engine/harmony/resonance.py` — `ASPECT_WEIGHTS` dict (actualmente todo 1.0)
- `abu_engine/harmony/field.py` — `aggregate_field()` computa HF_total, HF_harmony, HF_tension
- `abu_engine/harmony/field_v3.py` — `compute_hf_aspects()` delega a `aggregate_field()`
- Por crear: scraper de eventos, calculador HF por evento, optimizador de pesos
