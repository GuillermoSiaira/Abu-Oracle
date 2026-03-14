# HF v3 – Grids de reubicación y exports GeoJSON

## Qué hicimos
- Confirmamos que los grids HFv3 por sujeto están en `output/relocation_fields_v3/` (1 parquet por sujeto).
- Exportamos GeoJSON para los sujetos famosos solicitados usando `scripts/export_hf_geojson.py`, copiando también a `next_app/public/geojson/`.
- No se copiaron rankings porque no existen archivos `output/rankings/subject_*_ranking.json` para estos IDs.

## Archivos generados
- GeoJSON locales: `output/geojson/subject_<id>_hf.geojson`
- Copias para frontend: `next_app/public/geojson/subject_<id>_hf.geojson`
- Sujetos exportados:
  - 308660 — Albert Einstein
  - 337730 — Sigmund Freud
  - 371165 — Marie Curie
  - 357700 — Nikola Tesla
  - 61360 — Mohandas Gandhi
  - 238010 — Martin Luther King Jr.
  - 35255 — Frida Kahlo
  - 370945 — Frida Kahlo (rectificada)

## Estructura de los Parquet HFv3 (ejemplo `output/relocation_fields_v3/subject_308660.parquet`)
- Filas ≈ 2.4k (rejilla global)
- Columnas principales:
  - Identidad y natal: `subject_id`, `name`, `birth_datetime`, `natal_latitude`, `natal_longitude`
  - Rejilla: `relocation_latitude`, `relocation_longitude`, `grid_lat_index`, `grid_lon_index`, `grid_step_deg`
  - Métricas HF v3: `hf_total_v3`, `delta_hf_total_v3`, `hf_aspects`, `hf_angles`, `hf_houses`, `delta_hf_aspects`, `delta_hf_angles`, `delta_hf_houses`
  - Otros: `asc_lon`, `mc_lon`, `valid_flag`, `error_type`, `experiment_version`, `house_system`, `processed_at`

## Script de exportación
- Ruta: `scripts/export_hf_geojson.py`
- Requisitos en el Parquet: `relocation_latitude`, `relocation_longitude`, `delta_hf_total_v3`, `hf_total_v3`
- Uso típico:
  - `python scripts/export_hf_geojson.py --input output/relocation_fields_v3/subject_<id>.parquet --output-dir output/geojson --public-dir next_app/public/geojson`
  - Opcional: `--ranking output/rankings/subject_<id>_ranking.json` (si existe)

## Pendientes / notas
- No hay rankings para estos sujetos en `output/rankings/`; si se generan, se pueden reexportar pasando `--ranking` para copiarlos a `next_app/public/rankings/`.
- Si se agregan más sujetos, basta con colocar el Parquet en `output/relocation_fields_v3/` y ejecutar el script con su ID.
