# Harmony Field Relocation Dataset Schema

## Storage Recommendation
- Parquet per subject (or small batches) with deterministic row ordering (latitude-major then longitude) and stable column order.
- Compression: Snappy or ZSTD.
- Include run-level metadata (experiment_version, commit_hash) in file-level metadata when possible.

## Required Columns
- **subject_id** (string/int)
- **name** (string; optional/anonymized)
- **birth_datetime** (ISO UTC string)
- **natal_latitude**, **natal_longitude** (float degrees)
- **relocation_latitude**, **relocation_longitude** (float degrees)
- **asc_lon**, **mc_lon** (float degrees; from Abu Engine)
- **hf_total**, **hf_harmony**, **hf_tension**, **hf_conjunction** (float)
- **delta_hf_total**, **delta_hf_harmony**, **delta_hf_tension**, **delta_hf_conjunction** (float; relative to natal)
- **valid_flag** (bool)
- **error_type** (string; e.g., `ephemeris_range`, `house_fail`, `nan_output`)
- **experiment_version** (string; e.g., `HF_RELOC_v1`)
- **hf_core_version** (string; e.g., `HF Core v1`)
- **house_system** (string; e.g., `Placidus`)
- **ephemeris_version** (string; e.g., `DE440s`)
- **grid_step_deg** (float; e.g., 5.0)
- **processed_at** (ISO UTC string)

## Optional but Encouraged
- **commit_hash** (string)
- **backend** (string; `cpu` or `jax`)
- **batch_id** (string)
- **runtime_ms** (float; per grid row)

## Summary Tables
Per-subject summary (Parquet/CSV) should include:
- subject_id, experiment_version, grid_step_deg, house_system, ephemeris_version
- mean, std, min, max for hf_total/hf_harmony/hf_tension/hf_conjunction
- mean |ΔHF|, max |ΔHF|, 95th percentile |ΔHF| for each component
- optional robustness fractions (|ΔHF_total| < 0.5, < 1.0)

Population summary (optional) aggregates the per-subject statistics to describe cohort-level relocation sensitivity.