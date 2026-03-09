# Harmony Field (HF) Core v1 — Dataset Report

## 1. Project Overview
Harmony Field (HF) is a computational representation of natal charts that encodes planetary harmonic relationships into a structured feature space. The pipeline transforms birth data into numerical vectors capturing circular positions, harmonic signatures, and resonance-derived field metrics. This document summarizes the implemented modules, the data generation bridge, resulting dataset, statistical properties, sanity checks, failure analysis, and next research steps.

## 2. Architecture
Birth Data → Abu Engine → Chart Vector → Harmonics → Resonance → Harmony Field metrics → Dataset generation.

## 3. Module Descriptions
- `abu_engine/harmony/chart_vector.py`: Builds the 24D circular vector (cos, sin pairs) for 12 fixed points (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, ASC, MC) in a fixed order.
- `abu_engine/harmony/harmonics.py`: Computes harmonic energies H_k = |Σ w_i e^{ikθ_i}| for k ∈ {1,2,3,4,5,6,8,12}.
- `abu_engine/harmony/resonance.py`: Provides angular distance and Gaussian resonance kernels across major aspects (0, 60, 90, 120, 180) with configurable sigmas and weights.
- `abu_engine/harmony/field.py`: Aggregates pairwise resonances over 66 pairs, producing HF_total, HF_harmony, HF_tension, HF_conjunction, and per-aspect totals.

## 4. Dataset Description
- Bridge script: `scripts/generate_hf_dataset.py`.
- Pipeline: AstroDatabank-style birth records → Abu Engine → planetary longitudes via Swiss Ephemeris → circular vector (cv_*) → harmonic features (hk_*) → Harmony Field metrics.
- Outputs:
  - `data/processed/hf_dataset_v1.parquet` (main dataset)
  - `data/processed/hf_dataset_v1_failures.jsonl` (failed/ skipped rows)
  - `data/processed/hf_dataset_v1_summary.json` (counts and stats)

### Structure
- Rows: 4,650
- Columns: 62
- Key fields:
  - Birth data: name, birth_date, birth_time, latitude, longitude, timezone, source, trust_score
  - Planetary longitudes: sun_lon, moon_lon, mercury_lon, venus_lon, mars_lon, jupiter_lon, saturn_lon, uranus_lon, neptune_lon, pluto_lon, asc_lon, mc_lon
  - Circular vector: cv_01 … cv_24
  - Harmonic features: hk_1, hk_2, hk_3, hk_4, hk_5, hk_6, hk_8, hk_12
  - HF metrics: hf_total, hf_harmony, hf_tension, hf_conjunction
  - Metadata: pipeline_version, hf_core_version, processed_at

## 5. Statistical Properties
Count (all metrics): 4,650

| metric           | mean   | std   | min   | max   |
|------------------|--------|-------|-------|-------|
| hf_total         | 14.61  | 2.62  | 8.23  | 29.59 |
| hf_harmony       | 7.20   | 2.04  | —     | —     |
| hf_tension       | 5.23   | 1.82  | —     | —     |
| hf_conjunction   | 2.17   | 1.25  | —     | —     |

## 6. Empirical Tests
- Correlations:
  - corr(hf_total, hf_harmony) ≈ 0.62
  - corr(hf_total, hf_tension) ≈ 0.51
  - corr(hf_harmony, hf_tension) ≈ -0.16
  - corr(hf_total, hf_conjunction) ≈ 0.33
- Latitude test: corr(latitude, hf_tension) ≈ -0.04 → no meaningful dependence on geographic latitude.
- Distribution: hf_total is approximately normal, peaks around 14–15, exhibits a moderate right tail, and shows no saturation or collapse near zero. Metrics appear numerically stable and well distributed.

## 7. Failure Analysis
- Total failures logged: 709
  - 695: ephemeris segment only covers dates 1849-12-26 through 2150-01-22
  - 11: time_precision_not_exact
  - 3: invalid_birth_time
- Conclusion: Most failures arise from the DE440s ephemeris date-range limitation.

## 8. Current Limitations
- Ephemeris range constraint: 1849-12-26 → 2150-01-22; records outside this range are excluded.
- Relocation effects not yet analyzed.
- HF space topology (e.g., manifolds/clusters) not yet explored.

## 9. Future Research Directions
1. PCA projection of the HF feature space.
2. Clustering of natal charts in HF space.
3. Topological analysis of HF space.
4. Investigation of HF relocation fields.
5. Integration with Abu Oracle reasoning engine.
6. Preparation for machine learning experiments on HF vectors.