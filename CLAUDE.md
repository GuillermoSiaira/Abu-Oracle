# CLAUDE.md — AI Oracle / Abu Engine
> Leer este archivo antes de cualquier tarea. Contiene el estado actual del proyecto, arquitectura, convenciones y el plan de desarrollo activo.

---

## Proyecto

**AI Oracle** — motor astrológico computacional con campo escalar geográfico (Harmony Field) e interpretación por agentes LLM (Lilly Swarm). Stack: Python (backend / engine), TypeScript / Next.js (frontend), Docker, GCP.

Raíz del repo: `D:\projects\ai-oracle`

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
| GeoJSON para frontend | `output/geojson/` + `next_app/public/geojson/` | ✅ 9 sujetos |
| Rankings top-20 ciudades | `output/rankings/` | ✅ 4,650 sujetos |
| Demo pack (10 sujetos curados) | `output/demo/` | ✅ completo |
| Frontend Next.js + MapLibre | `next_app/` | ✅ funcional |
| Mapa de relocalización | `next_app/components/HFRelocationMap.tsx` | ✅ funcional |
| Eventos biográficos | `data/biographical_events/` | ✅ 527 eventos |
| Correlator HF↔eventos | `scripts/hf_correlator/` | ✅ ejecutado |

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
- `abu_engine/harmony/houses.py` — asignación planeta→casa, ocupación, entropía
- `abu_engine/harmony/angularity.py` — fuerza gaussiana a ángulos

### Resultado de optimización de pesos (grid search, 527 eventos, 9,261 combinaciones)

| Métrica | Pesos óptimos | Valor |
|---|---|---|
| Mejor corr_all | w_h=-0.75, w_t=-1.0, w_c=2.5 | corr=0.155, Cohen's d=0.441 |
| Mejor composite | w_h=-2.0, w_t=-2.0, w_c=3.0 | corr=0.148, separation=2.678 |

**Hallazgo clave**: los pesos óptimos son negativos para harmony y tension — la hipótesis original (harmony→positivo, tension→negativo) no se confirma globalmente. La razón probable: HF global mezcla eventos de distintas casas. Ver plan de desarrollo abajo.

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
Filas: 2,409 (grilla 5°×5°, lat∈[-70,70], lon∈[-180,175])

### GeoJSON multi-propiedad (generado) ✅
Cada Feature tiene: `hf_global, hf_h1, hf_h4, hf_h7, hf_h10, delta_global, delta_h1, delta_h4, delta_h7, delta_h10`
Archivos: `next_app/public/geojson/{slug}_domains.geojson` (10 sujetos demo, 2409 pts, ~710 KB c/u)

---

## Plan de desarrollo activo — HF por dominio de casa

El objetivo es mostrar un campo escalar diferente por casa (dominio de vida) en el mapa de relocalización. El usuario selecciona "Casa 10 · Carrera" y el heatmap muestra el HF calculado solo con los planetas significadores de esa casa.

### Fase 1 — Motor: planet_filter en field_v3.py ✅ `[COMPLETA]`

**Tarea 1.1** ✅ — `abu_engine/harmony/houses.py`
Agregar función:
```python
def house_significators(natal_data: dict, house: int) -> list[str]:
    """
    Dado el JSON natal de Abu Engine y un número de casa (1-12),
    devuelve la lista de planetas que rigen (señor del signo en cúspide)
    y ocupan esa casa.
    Formato planeta: 'sun', 'moon', 'mercury', 'venus', 'mars',
                     'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'asc', 'mc'
    """
```

**Tarea 1.2** ✅ — `abu_engine/harmony/field_v3.py`
Modificar `compute_hf_aspects()` y `compute_relocation_field()` para aceptar:
```python
planet_subset: list[str] | None = None
# Si None → comportamiento actual (todos los planetas)
# Si lista → solo usar esos planetas en resonancias y angularidad
```

**Tarea 1.3** ✅ — Test visual
Para Frida Kahlo (ID 35255): generar mapa matplotlib de HF_global, HF_h7, HF_h10.
Los tres deben ser visualmente distintos. Si son iguales, revisar el filtro.

---

### Fase 2 — Data: etiquetar eventos por house_domain ✅ `[COMPLETA]`

**Tarea 2.1** ✅ — Crear `config/event_house_map.json`:
```json
{
  "professional_achievement": 10,
  "career_change": 10,
  "relationship": 7,
  "marriage": 7,
  "divorce": 7,
  "family": 4,
  "health": 1,
  "illness": 6,
  "travel": 9,
  "finances": 2,
  "death": 8,
  "creative": 5,
  "psychological_crisis": 1,
  "spiritual": 12
}
```

**Tarea 2.2** ✅ — Script `scripts/enrich_events.py`:
Lee `data/biographical_events/*.json`, añade campo `house_domain: int`, guarda en `data/biographical_events_v2/`.

**Tarea 2.3** ✅ — Script `scripts/correlate_by_domain.py` (extender correlator):
Segmentar correlación por `house_domain`. Hypothesis: corr(HF_h10, eventos_h10) > corr(HF_global, eventos_h10).

---

### Fase 3 — Pipeline: grillas por dominio (demo pack) ✅ `[COMPLETA]`

**Tarea 3.1** ✅ — Script `scripts/generate_hf_domain_grids.py`:
Para cada sujeto demo × {global, h1, h4, h7, h10}:
```
output/relocation_fields_domain/{slug}_domains.parquet
```

**Tarea 3.2** ✅ — Script `scripts/export_hf_domain_geojson.py`:
Leer parquet multi-dominio → producir `geojson_domains.json` por sujeto con todas las propiedades por dominio en cada Feature.

**Tarea 3.3** ✅ — Copiado a `next_app/public/geojson/` y validado.
- Archivos: `next_app/public/geojson/{slug}_domains.geojson` (10 sujetos)
- **Actualizado 2026-03-14**: Resolución 2.5°×2.5° (9425 pts, ~4.2 MB cada uno)
- **Dominios ampliados**: `global, h1, h2, h4, h5, h6, h7, h9, h10` (9 dominios, antes 5)
- Propiedades por Feature: `hf_{domain}` y `delta_{domain}` para cada dominio

---

### Fase 4 — Frontend: selector de dominio en el mapa ✅ `[COMPLETA]`

**Tarea 4.1** ✅ — `next_app/components/HFRelocationMap.tsx`:
- Prop `domain?: Domain` agregada; `deltaKey`/`hfKey` se resuelven dinámicamente
- Heatmap, círculos y tooltip leen `hf_{domain}` / `delta_{domain}` del GeoJSON
- `displayCities` useMemo: en modo dominio ordena features del GeoJSON; en modo global usa ranking
- `useEffect` deps actualizadas: `[filteredGeojson, displayCities, domain, deltaKey, hfKey, ...]`
- Top-3 header muestra "Top 3 · Relaciones" etc. según dominio activo

**Tarea 4.2** ✅ — Nuevo componente `next_app/components/DomainSelector.tsx`:
Pills: Global / Identidad / Recursos / Hogar / Creatividad / Trabajo / Relaciones / Expansión / Carrera.
**Actualizado 2026-03-14**: 9 dominios (antes 5). Activo en ámbar, inactivo en slate.

**Tarea 4.3** ✅ — Integración en `next_app/app/relocation/RelocationClient.tsx`:
- Único consumer de `HFRelocationMap` (ruta `relocation-map/` eliminada del repo)
- `domain` state + `DomainSelector` renderizado sobre el mapa
- `geojsonUrl` apunta a `/geojson/{slug}_domains.geojson`
- **Rebuild Docker completado** — en producción desde 2026-03-13

---

### Fase 5 — Domain Ranking por Solar Return ✅ `[COMPLETA 2026-03-13]`

Motor de scoring por dominio de vida usando Solar Return o carta natal en cualquier ciudad.
Doctrina de Abu Mashar: señor de casa + planetas angulares + ocupantes + casas de apoyo.
Score 0–100, grade A/B/C/D. Implementa Axioma 7 (Domain Specificity) de AXIOMATICS v0.4.

**Archivos creados:**
- `abu_engine/core/domain_ranking.py` — `score_city_for_domain()` + `rank_cities_for_domain()`
- `abu_engine/tests/test_domain_ranking.py` — 5 smoke tests
- `next_app/components/LifeDomainSelector.tsx` — 7 dominios: career/love/health/family/resources/creativity/expansion

**Endpoints nuevos en `main.py`:**
- `GET /api/astro/domain-score?birthDate&lat&lon&domain&year&mode` — ciudad puntual
- `POST /api/astro/domain-ranking?birthDate&domain&year` + body `[{name,lat,lon}]` — lista → ranking

**Integración frontend:**
- `next_app/components/relocation-tab.tsx` — `LifeDomainSelector` + sección "Top 5 por dominio"
- Flujo: user selecciona dominio → POST con top-20 ciudades del HF ranking → muestra grade + key_insight

**Dominios y casas:**

| Key | Casa | Planetas clave |
|---|---|---|
| career | 10 | Sol, Saturno, Marte |
| love | 7 | Venus, Luna |
| health | 1 | Sol, Luna, Marte |
| family | 4 | Luna, Saturno |
| resources | 2 | Júpiter, Venus |
| creativity | 5 | Sol, Venus, Júpiter |
| expansion | 9 | Júpiter, Sol |

---

### Fase 7 — Mejoras visuales del mapa HF ✅ `[COMPLETA 2026-03-14]`

Correcciones al componente `next_app/components/HFRelocationMap.tsx`:

**Fix 1 — Heatmap visible (color scale relativa)**
- `colorScale` ahora computa p5/p50/p95 desde los valores reales del GeoJSON activo
- Neutro anclado en la **mediana (p50)** → 50% del mundo frío, 50% cálido
- `heatmap-weight`: mapea `delta` → peso usando p5→0, p50→0.5, p95→1
- Resuelve el mapa negro que se veía antes (escala absoluta fija rota)

**Fix 2 — Labels geográficos visibles sobre heatmap**
- Tile base: `dark_nolabels` (sin labels mezclados)
- Tile labels: `dark_only_labels` añadido DESPUÉS de las capas HF → labels encima del heatmap
- Nota: tinte verde (Matrix) no implementado — `raster-hue-rotate` no afecta texto blanco/acromático; requiere vector tiles para controlar color de labels

**Fix 3 — Navegación del mapa**
- `scrollZoom: true`, `dragPan: true` explícitos en el constructor `Map`
- `touchAction: "none"` en el contenedor del div

**Fix 4 — Ranking de ciudades correcto por dominio**
- `CityInfo` ahora tiene campo `delta: number`
- `pickTopFromGeoJSON` almacena `delta_${domain}` del GeoJSON (escala correcta del dominio)
- Render usa `c.delta` en modo dominio, `c.hf - natalHf` en modo global
- Antes: comparaba `hf_h10` (escala dominio) vs `natalHf` (escala global) → valores incorrectos

**Resolución de grilla actualizada**
- Step: 5°×5° → **2.5°×2.5°** (9425 pts vs 2409)
- Scripts: `generate_hf_domain_grids.py --step 2.5`, `export_hf_domain_geojson.py`
- Tiempo de regeneración: ~15-20s por sujeto

**Dominios ampliados**: H1/H2/H4/H5/H6/H7/H9/H10 + Global (antes solo H1/H4/H7/H10)

---

### Fase 6 — Validación estadística ✅ `[COMPLETA 2026-03-13]`

Correlación HF_dominio vs HF_global por casa, sobre 527 eventos biográficos (26 sujetos).
Script: `scripts/correlate_by_domain.py`. Resultados: `analysis/domain_correlation_report.md`.

| Casa | N | corr_global | corr_domain | Δcorr | Resultado |
|------|---|-------------|-------------|-------|-----------|
| H04 Hogar | 34 | −0.001 | +0.305 | +0.306 | ✅ confirmado |
| H05 Creatividad | 57 | +0.198 | +0.353 | +0.155 | ✅ confirmado |
| H06 Trabajo/Salud | 18 | −0.317 | +0.051 | +0.369 | ✅ confirmado |
| H07 Amor | 93 | +0.098 | +0.088 | −0.010 | ❌ sin mejora |
| H09 Expansión | 56 | +0.014 | −0.123 | −0.138 | ❌ sin mejora |
| H10 Carrera | 226 | +0.090 | +0.033 | −0.057 | ❌ sin mejora (sesgo N+=208/N−=4) |

Hipótesis confirmada en 3/6 dominios. H10 tiene Cohen's d_global=+0.871 (el más alto del corpus) — la separación de grupos es real pero el desbalance de valencias limita la correlación lineal. Ver Experimento 5 en `HF_EXPERIMENT_LOG.md`.

---

## Convenciones del proyecto

- **Sistema de casas**: Placidus
- **Referencial**: Topocéntrico
- **Efemérides**: Swiss Ephemeris DE440s (rango 1849-12-26 a 2150-01-22)
- **Grilla relocalización**: 5°×5°, lat∈[-70,70], lon∈[-180,175], 2,409 puntos
- **Planetas activos**: Sol, Luna, Mercurio, Venus, Marte, Júpiter, Saturno, Urano, Neptuno, Plutón + ASC + MC
- **Aspectos**: conjunción 0°, sextil 60°, cuadratura 90°, trígono 120°, oposición 180°
- **Grupos de aspecto**: harmony = sextil+trígono, tension = cuadratura+oposición, conjunction = conjunción

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

Cuando Claude Code retome una sesión, leer este archivo primero y preguntar por la fase activa. La próxima tarea es siempre la primera sin tilde `✅` en el plan de desarrollo.

Al completar una tarea, marcarla con `✅` en este archivo y hacer commit.
