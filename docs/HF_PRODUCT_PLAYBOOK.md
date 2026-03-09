# HF Product Playbook (v3)

Guía breve y accionable para correr, validar y entregar el Atlas Harmony Field v3. Lista para ingesta en IA/Obsidian.

## Estado actual
- **Modelo**: HF v3 (aditivo) — aspectos + β·ángulos + γ·casas (β=0.6, γ=0.3, σ_angle=10°).
- **Scripts nuevos**:
  - `scripts/generate_relocation_field_v3.py` → genera Parquet con `hf_total_v3`, componentes y `grid_lat_index/grid_lon_index`.
  - `scripts/generate_hf_map.py` → heatmaps PNG (normalización `hf_total_v3_norm`, métricas delta, coastlines/borders si hay Cartopy, fallback GeoPandas; overlay top-5 ciudades dedupe + marcador natal opcional).
  - `scripts/generate_city_ranking.py` → top-N rankings, nearest city (requiere CSV de ciudades).
  - `scripts/export_hf_geojson.py` → exporta Parquet HF v3 a GeoJSON (`delta_hf` + `hf_total`) y copia opcional a `next_app/public/geojson` + ranking a `next_app/public/rankings`.
  - Frontend: `next_app/components/HFRelocationMap.tsx` + ruta `app/relocation-map/page.tsx` (MapLibre heatmap + círculos + marcadores top-5 + natal).
- **Salidas esperadas**:
  - `output/relocation_fields_v3/subject_<id>.parquet`
  - `output/maps/subject_<id>_<metric>.png`
  - `output/rankings/subject_<id>_ranking.json`
  - `output/geojson/subject_<id>_hf.geojson` (opcionalmente duplicado a `next_app/public/geojson`)

## Cómo correr (end-to-end mínimo)
1) Campos HF v3
```
python scripts/generate_relocation_field_v3.py
```
  - Usa `data/processed/hf_dataset_v2.parquet`.
  - Espera ~2409 filas/sujeto (grid 5°), sin NaN en `hf_total_v3`.

2) Mapas (ejemplo)
```
python scripts/generate_hf_map.py --input output/relocation_fields_v3/subject_001.parquet --metric hf_total_v3
```
  - Métricas soportadas: `hf_total_v3`, `hf_total_v3_norm`, `hf_aspects`, `hf_angles`, `hf_houses`, `delta_hf_*`.
  - Output: `output/maps/subject_001_<metric>.png`.
  - Defaults de demo: `--metric delta_hf_total_v3 --alpha 0.9` (escala delta simétrica por percentil 98 si no fijas `vmin/vmax`).

3) Rankings (ejemplo)
```
python scripts/generate_city_ranking.py --input output/relocation_fields_v3/subject_001.parquet --cities data/external/worldcities.csv --metric hf_total_v3 --top-n 20
```
  - Output: `output/rankings/subject_001_ranking.json`.
  - Se recomienda usar el mismo ranking para overlay en mapas (`--ranking`).

4) GeoJSON para mapa interactivo (opcional, recomendado)
```
python scripts/export_hf_geojson.py \
  --input output/relocation_fields_v3/subject_001.parquet \
  --public-dir next_app/public/geojson \
  --ranking output/rankings/subject_001_ranking.json
```
  - Output local: `output/geojson/subject_001_hf.geojson`.
  - Copias para frontend: `next_app/public/geojson/subject_001_hf.geojson` y `next_app/public/rankings/subject_001_ranking.json`.
  - Incluye propiedades en cada punto: `delta_hf` y `hf_total`.

## Checklist de validación inmediata
- [ ] 2409 filas por sujeto; `valid_flag` mostly true; `error_type` vacío/"house_fail" muy raro.
- [ ] Sin NaN en `hf_total_v3`; normalización presente (`hf_total_v3_norm`).
- [ ] Mapas: gradientes suaves, estructura espacial coherente (no ruido salt-and-pepper); coastlines visibles (Cartopy/GeoPandas fallback).
- [ ] Rankings: orden estable; entries incluyen ciudad/país/coords/distancia; overlay en mapa dedup (top-5).
 - [ ] GeoJSON: `delta_hf` y `hf_total` presentes; `properties.natal_latitude/natal_longitude` poblados; tamaño razonable (<10 MB por sujeto con grilla 5°).

## Próximos pasos (una vez validados mapas de 10 sujetos)
1) Revisar máximos y patrones geográficos (¿bandas latitudinales? ¿clustering?).
2) Si se usan métricas delta, mantener escala simétrica (percentil 98) o fijar manualmente para comparabilidad.
3) Empaquetar un índice simple (HTML/markdown) con thumbnails y links a rankings.
4) Post-validación: exponer endpoint/backfill en Abu/Lilly o frontend (fuera de esta ola).
5) Activar mapa interactivo y revisar UX.

## Notas y supuestos
- No recalcular dataset natal; se reutiliza `hf_dataset_v2.parquet` y planetas/casas de Abu.
- Grilla definida por indices (`grid_lat_index/grid_lon_index`); reshape seguro independientemente del orden en disco.
- CSV de ciudades: requiere columnas lat/lon (se normalizan a `city`, `country`, `lat`, `lon`).

## Mapa interactivo (Next.js + MapLibre)
- Ruta: `http://localhost:3000/relocation-map?subject=1000` (default `subject=1000`).
- Assets esperados: `next_app/public/geojson/subject_<id>_hf.geojson` y opcional `next_app/public/rankings/subject_<id>_ranking.json`.
- Componente: `HFRelocationMap` (heatmap `delta_hf`, círculos, popups, marcador natal, top-5 markers si hay ranking).
- Dependencia: `maplibre-gl` (ejecutar `npm install` en `next_app` si no está en lockfile).
- Ajustes rápidos:
  - Cambia sujeto vía query `?subject=<id>`.
  - Si el heatmap se satura, ajustar stops en `HFRelocationMap.tsx` (rangos delta default: ±max|delta_hf| del dataset cargado).
  - Ranking es opcional; sin ranking se renderizan heatmap + círculos + natal.

## Flujo sugerido (producto demo interactivo)
1) Genera Parquet HF v3 y ranking como arriba.
2) Exporta GeoJSON + copia a `next_app/public/geojson` (`scripts/export_hf_geojson.py`).
3) En `next_app/`: `npm install` (solo primera vez) y `npm run dev`.
4) Abre `/relocation-map?subject=<id>` y verifica:
   - Heatmap carga en <5 s; controles de zoom/rotación OK.
   - Marcador natal visible; top-5 cities con popups si hay ranking.
   - Tooltip/labels muestran `delta_hf` y `hf_total` coherentes con PNGs previos.

## Registro rápido (avances implementados)
- HF v3 integrado al pipeline de relocación con componentes y deltas vs. natal.
- Normalización de HF en scripts de mapa/ranking para comparación entre sujetos.
- Artefactos de producto listos: Parquet (campo), PNG (mapa), JSON (ranking).

## Qué NO hacer en esta fase
- No tocar pesos/σ del modelo HF v3.
- No introducir tránsitos/progresiones aún.
- No reabrir dataset ni pipeline base hasta ver mapas reales.

## Preset de demo (maps + overlay)
- Comando sugerido:
```
python scripts/generate_hf_map.py \
  --input output/relocation_fields_v3/subject_1000.parquet \
  --metric delta_hf_total_v3 \
  --alpha 0.9 \
  --ranking output/rankings/subject_1000_ranking.json
```
- Overlay: top-5 ciudades, deduplicadas por nombre, etiquetas pequeñas (7pt) con stroke, marcador natal.
- Si Cartopy está instalado: coastlines + borders + ocean/land fill; si no, fallback a GeoPandas (naturalearth_lowres) para contornos.
