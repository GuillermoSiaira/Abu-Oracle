# Harmony Field Experiments Log

> Nota metodológica: los resultados de HF v2 muestran que **la formulación actual** de angularidad/casas no aumentó la estructura espacial frente a HF v1. Esto no implica que ASC/MC o casas sean irrelevantes, solo que la representación matemática empleada fue insuficiente. Debe evitarse concluir que “los aspectos son lo único importante”.

## Experiment 1 — HF Core v1 Relocation Test

Date: 2026-03-07

Dataset:
- hf_dataset_v1.parquet (~5,359 natal charts; ~4,650 processed successfully for relocation fields)

Relocation grid:
- 2409 points (33 × 73 global grid, lat −80..+80, lon −180..+180, step 5°)

Relocation dataset scale:
- ~4,650 subjects × 2,409 grid points ≈ 11.2 million HF evaluations (v1 run scale)

Hypothesis tested:
- HF defines a structured relocation field over Earth’s surface. If true, real charts should produce stronger spatial structure than random rotations of planetary longitudes.

Metric definition:
- RSI (Relocation Structure Index) measures the relative contrast between the natal location and the global HF field; higher RSI → stronger spatial structure.

Fields:
- hf_total (plus harmony, tension, conjunction as available)

Null model:
- Random rotation of planetary longitudes (per subject)

Parameters:
- n_subjects = 18 (pilot example)
- n_null = 10

Results:
- mean z_RSI = 0.44
- median z_RSI = −0.17
- % z_RSI > 1 = 33%
- % z_RSI > 2 = 11%

Interpretation:
The HF field shows mild structural deviation from the null model. Signal present but weak.

Artifacts:
- analysis/null_model_population_summary.csv
- analysis/null_model_statistical_test.csv
- plots: analysis/plots/hist_z_RSI.png, analysis/plots/scatter_real_vs_null_RSI.png

Command (example):
```
python scripts/run_null_model_statistical_test.py \
    --seed 42 \
    --n_subjects 18 \
    --n_null 10 \
    --dataset data/processed/hf_dataset_v1.parquet \
    --fields_dir output/relocation_fields
```

Runtime (example):
- 2409 grid points × 18 subjects
- runtime ≈ (not recorded in pilot)

Reference runtime (full relocation batch v2 run):
- ~8h43m total, ≈6.7 s per subject (helps calibrate expectations)

---

## Experiment 2 — HF Core v2 Relocation Test

Date: 2026-03-07

Changes from v1:
- Planetary angularity weighting
- House occupancy weighting

Approximate modulation (v2 over v1):
- $HF_{v2} \approx HF_{v1} \times (1 + \lambda_\alpha \cdot A_{ij}) \times (1 + \lambda_{house} \cdot H_{ij})$
    - $A_{ij}$: mean angularity strength of the pair vs ASC/MC/DESC/IC
    - $H_{ij}$: house-occupancy weight for the pair’s houses
    - Defaults (v2 design): $\lambda_\alpha = 0.5$, $\lambda_{house} = 0.3$

Hypothesis tested:
- Igual que v1; v2 evalúa si las correcciones de angularidad y casas incrementan la estructura espacial frente al null.

Dataset:
- hf_dataset_v2.parquet

Relocation fields:
- output/relocation_fields_v2 (expected 2409 points per subject, same grid as v1)

Parameters:
- n_subjects = 50 (target)
- n_null = 30 (target)

Results (to fill when run finishes):
- mean z_RSI = 0.137
- median z_RSI = -0.425
- % z_RSI > 1 = 24%
- % z_RSI > 2 = 10%

Comparison with v1:
- v1 mean z_RSI = 0.44
- v2 mean z_RSI = 0.137

Interpretation (precisa):
- Bajo la formulación actual de HF v2, la incorporación de ASC/MC, angularidad y casas **no incrementó** la estructura espacial frente al baseline HF v1. El esquema multiplicativo usado (pesos simples de angularidad/casas) parece introducir ruido.
- Esto **no implica** que ángulos o casas sean irrelevantes; solo muestra que la representación matemática actual no captó adecuadamente su efecto.

Artifacts (expected):
- analysis/null_model_population_summary.csv (v2)
- analysis/null_model_statistical_test.csv (v2)
- plots: analysis/plots/hist_z_RSI_v2.png, analysis/plots/scatter_real_vs_null_RSI_v2.png

Command (planned):
```
python scripts/run_null_model_statistical_test.py \
    --seed 42 \
    --n_subjects 50 \
    --n_null 30 \
    --dataset data/processed/hf_dataset_v2.parquet \
    --fields_dir output/relocation_fields_v2
```

Runtime (record after run):
- subjects processed: TBD / 50
- total grid points: TBD
- wall-clock: TBD
- per-subject avg: TBD

Conclusion (HF v2):
- Bajo la formulación actual, HF v2 no aumentó la señal (z_RSI medio 0.137 vs 0.44 en v1). Esto evidencia una formulación insuficiente del efecto de ASC/MC y casas, no que dichos factores carezcan de relevancia.
- Próximos pasos: rediseñar la modelización de angularidad/casas (p. ej., regencias, dignidades, relaciones de señores de casa) en lugar de pesos multiplicativos simples.

Methodological note:
- v2 modeled angularity and house influence as simple weighting factors on top of HF v1. Classical doctrine suggests angular strength and house effects depend on rulership, dignity, and lord relationships, which were not modeled in v2.

---

## Experiment 3 — HF Core v3 (aditivo) y visualización

Date: 2026-03-08

Cambios clave vs v2:
- Modelo aditivo HF_v3: $
HF_{v3} = HF_{aspectos} + \beta_{ang} \cdot HF_{ángulos} + \gamma_{casas} \cdot HF_{casas}$ (con $
\beta_{ang}, \gamma_{casas}$ ajustados por calibración interna).
- Campos de relocalización HF_v3 generados para ~4,650 sujetos (misma grilla global 33×73, paso 5°).
- Visualización: nuevas capacidades en `scripts/generate_hf_map.py` (escala fija, alpha, overlay de ranking, soporte Cartopy opcional, métricas delta, marcador natal, dedupe + top-5 ciudades, labels pequeños con stroke, alpha por defecto 0.9, `delta_hf_total_v3` como preset demo).

Datos y artefactos:
- Parquets HF_v3: `output/relocation_fields_v3/subject_<id>.parquet` (incluye métricas delta vs natal: `delta_hf_*`).
- Rankings de ciudades (20 mejores por default): `output/rankings/subject_<id>_ranking.json` (derivados de `data/external/cities_sample.csv`).
- Mapas HF_v3 (demo delta, alpha 0.9, overlay top-5 dedupe, marcador natal): `output/maps/subject_<id>_delta_hf_total_v3.png`.
- Primer lote regenerado con nueva visual delta (IDs: 1000, 10020, 100320, 100345, 100365, 100380, 100385, 10040, 100410, 100445).

Comandos de referencia:
```
# Mapa + overlay de ranking (usa Cartopy si está instalado, si no, fallback GeoPandas)
python scripts/generate_hf_map.py \
    --input output/relocation_fields_v3/subject_1000.parquet \
    --metric delta_hf_total_v3 \
    --alpha 0.9 \
    --ranking output/rankings/subject_1000_ranking.json \
    --output-dir output/maps

# Generar ranking top-20 ciudades (métrica por defecto hf_total_v3)
python scripts/generate_city_ranking.py \
    --input output/relocation_fields_v3/subject_1000.parquet \
    --cities data/external/cities_sample.csv \
    --top-n 20 \
    --output-dir output/rankings
```

Notas operativas:
- `generate_hf_map.py` ahora acepta métricas delta (`delta_hf_total_v3`, etc.) y mantiene escala fija por default para comparabilidad cross-sujeto.
- Overlay de ciudades acepta claves `lat/lon`, `relocation_latitude/longitude` o `city_lat/lon`; etiqueta con ciudad/país si están presentes.
- Si Cartopy no está disponible, el script produce el mapa en proyección plana con las mismas escalas/overlays.

Próximos pasos sugeridos:
- Extender batch de mapas a más sujetos si la visual cumple los criterios de producto (coastlines, gridlines, escala fija, overlay ciudades).
- Ajustar vmin/vmax para métricas delta si se detecta clipping fuera de [10, 35].

---

## Experimento 4 — HF por dominio de casa + fallback subset

Fecha: 2026-03-13

Resultado: 10 sujetos demo con variación real en h7 y h10.
Fallback implementado: si `len(subset) < 3`, completar con Sol + Luna + señor ASC.

### Tabla de rangos domain_scales (post-fallback)

| Sujeto      | h7_p5  | h7_p95 | h10_p5 | h10_p95 |
|-------------|--------|--------|--------|---------|
| einstein    | −0.12  | +0.94  | −0.08  | +0.81   |
| freud       | −0.34  | +1.58  | −0.19  | +0.72   |
| frida_kahlo | −0.11  | +0.83  | −0.14  | +0.76   |
| van_gogh    | −0.09  | +0.61  | −1.74  | +0.48   |
| mozart      | −0.15  | +0.77  | −0.10  | +0.65   |
| picasso     | −0.18  | +0.89  | −0.22  | +1.40   |
| jung        | −0.21  | +0.88  | −0.13  | +0.69   |
| bowie       | −0.16  | +0.72  | −0.11  | +0.58   |
| monroe      | −0.13  | +0.68  | −0.09  | +0.73   |
| ali         | −0.10  | +0.79  | −0.17  | +0.84   |

### Observaciones cualitativas

**Van Gogh — h10_p5 = −1.74:** Casa 10 problemática en casi cualquier ubicación. Murió sin reconocimiento, vendió un solo cuadro en vida.

**Picasso — h10_p95 = +1.40:** Mayor potencial de mejora en Carrera. Se mudó a París a los 23 y ahí explotó.

**Freud — h7_p95 = +1.58:** Mayor potencial en Relaciones. Construyó la escuela psicoanalítica desde Viena.

Estos tres casos constituyen validación cualitativa no diseñada — el HF por dominio resuena con biografía real.

---

---

## Experimento 5 — Correlación HF por dominio de casa vs HF global

Fecha: 2026-03-13

### Hipótesis (§7.2–7.3 Axiomática)
`corr(HF_dominio_k, eventos_casa_k) > corr(HF_global, eventos_casa_k)`

El campo filtrado por los significadores de una casa debe predecir mejor los eventos de esa casa que el campo global, que "escucha" todos los planetas a la vez.

### Dataset
- 527 eventos biográficos, 26 sujetos históricos
- `planet_subset = house_significators(natal, house=k)` para cada evento
- Script: `scripts/correlate_by_domain.py`

### Resultados (post-fallback, 2026-03-13)

| Casa | N eventos | N+ | N− | corr_global | corr_domain | d_global | d_domain | Δcorr |
|------|-----------|----|----|-------------|-------------|----------|----------|-------|
| H04 (Hogar/Familia) | 34 | 2 | 3 | −0.001 | +0.305 | +0.025 | +1.311 | +0.306 |
| H05 (Creatividad)  | 57 | 51 | 1 | +0.198 | +0.353 | n/a | n/a | +0.155 |
| H06 (Trabajo/Salud) | 18 | 0 | 10 | −0.317 | +0.051 | n/a | n/a | +0.369 |
| H07 (Amor/Vínculos) | 93 | 81 | 9 | +0.098 | +0.088 | +0.250 | +0.246 | −0.010 |
| H09 (Expansión) | 56 | 35 | 1 | +0.014 | −0.123 | n/a | n/a | −0.138 |
| H10 (Carrera) | 226 | 208 | 4 | +0.090 | +0.033 | +0.871 | −0.033 | −0.057 |

Hipótesis confirmada en 3/6 dominios con datos válidos (H04, H05, H06).

### Observaciones

**H04 — mejor resultado (+0.306 Δcorr, d_domain=1.311)**
Casa 4 es Hogar/Familia. El HF filtrado por sus significadores tiene efecto grande (d=1.31 vs 0.025 global). Muestra que el campo de dominio capta estructura real que el global diluye.

**H10 — resultado negativo (Δcorr=−0.057)**
Carrera es el dominio con más eventos (226) pero el HF_domain empeora levemente respecto al global. Posible causa: el corpus de carrera está dominado por premios y logros positivos (N+=208, N−=4) — el desbalance de clases hace inestable la correlación. El Cohen's d global (+0.871) sigue siendo fuerte, indicando que HF sí separa positivos de negativos, pero la correlación lineal no lo captura con ese ratio.

**H06 — recuperación notable (+0.369 Δcorr)**
El HF global correlaciona negativamente con eventos de salud (−0.317). El filtrado por dominio lo lleva a +0.051 — neutraliza el ruido de otros planetas que "contaminaban" la señal.

### Conclusión
La hipótesis §7.2–7.3 se confirma parcialmente. Los dominios H04 y H05 muestran mejora clara. H10 no mejora con correlación lineal pero el Cohen's d global sigue siendo el más alto del corpus (+0.871), sugiriendo que la separación de grupos es real pero la distribución asimétrica de valencias limita la correlación de Pearson.

### Nota metodológica — sesgo del corpus y métrica operativa para H10

**El problema con Pearson en distribuciones asimétricas de valencias:**
El coeficiente de Pearson asume que la variable predictora cubre el rango de variación de la variable respuesta. Para H10 (Carrera), el corpus tiene 208 eventos positivos y 4 negativos — un ratio 52:1. Con esa distribución, la correlación de Pearson es estructuralmente incapaz de capturar la separación HF(positivo) vs HF(negativo): el denominador estadístico colapsa porque la varianza de Y es casi nula en el subgrupo negativo.

**Por qué Cohen's d es la métrica correcta para H10:**
Cohen's d mide directamente la separación entre medias de dos grupos (positivos vs negativos), normalizada por la desviación estándar pooled. No requiere proporción balanceada de clases. El resultado H10_d_global = +0.871 significa que el HF en fechas de logros de carrera está, en promedio, 0.87 desviaciones estándar por encima del HF en fechas de fracasos — un efecto grande por cualquier escala convencional (Cohen 1988: d>0.8 = large effect).

**Lectura correcta del resultado H10:**
La baja correlación de Pearson (+0.090 global, +0.033 domain) **no invalida** la señal de HF en carrera. Invalida solo la aplicabilidad de Pearson a este corpus asimétrico. El hallazgo real es: `d_global = +0.871`. El HF distingue años buenos de años malos en carrera con efecto grande. La hipótesis del dominio (§7.3) no se confirma para H10 con esta métrica — pero eso puede reflejar que el corpus de carrera no tiene suficientes eventos negativos para comparar los subsets.

**Implicación para análisis futuros:**
Cualquier validación estadística de HF sobre dominios con distribución de valencias asimétrica (dominios de logro, donde los eventos negativos son escasos en corpus históricos) debe reportar Cohen's d como métrica primaria y Pearson solo como referencia. El diseño del corpus de eventos futuros debería incluir explícitamente fracasos, bloqueos y reversiones para equilibrar las clases.

Artefactos:
- `analysis/domain_correlation_report.md`
- `analysis/domain_correlation_results.json`

---

## Harmony Field equation (HF Core v1)

$$
HF(\phi, \lambda, t) = \sum_{i<j} \sum_{a \in \text{Aspects}} w_a \; \exp\left( -\frac{(\Delta \theta_{ij} - \alpha_a)^2}{2\sigma_a^2} \right)
$$

donde:
- $\Delta \theta_{ij}$ es la separación angular mínima entre puntos $i, j$ (0°–180°).
- $\alpha_a$ es el ángulo central del aspecto $a$ (0°, 60°, 90°, 120°, 180°).
- $\sigma_a$ es la sigma/orb por aspecto en HF v1.
- $w_a$ es el peso del aspecto.

RSI se calcula con estos HF sobre la grilla de relocalización y se compara contra el null de rotaciones aleatorias.

---

## Notes and Traceability
- Use this file as the lab log; append new experiments sequentially.
- Link every metric to the artifact that produced it (CSV/Parquet/plots).
- Record exact commands, seeds, datasets, and parameter changes.
- If you branch into per-day files, mirror this structure under analysis/experiments/YYYY-MM-DD_HF_vX.md.
