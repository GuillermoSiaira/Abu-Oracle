# Harmony Field Relocation Pipeline

## Responsibility Split
- **Abu Engine:** Astronomical calculations (planetary longitudes, sidereal time, ASC, MC, houses) for each grid point.
- **HF Core v1:** Pure/stateless computation of circular vectors, harmonic features, resonance, and HF metrics from supplied angles and longitudes.

## Data Flow
```
subject record (birth datetime UTC, natal lat/lon)
→ Abu Engine (natal) → HF Core (natal HF)
→ Grid loop over (φ, λ):
     Abu Engine (ASC/MC/houses at φ, λ)
     HF Core v1 (HF metrics)
     ΔHF vs natal
→ Persist rows (Parquet) → Summaries → Visualizations
```

## Implementation Guidelines
- **Determinism:** Fix grid ordering (lat-major), stable column order, and consistent degree↔radian handling.
- **Batching:** Batch by latitude band or by subject to amortize Abu Engine calls; cache Abu outputs keyed by (t₀, φ, λ, house_system, ephemeris).
- **Error handling:** Mark invalid rows with valid_flag = False and error_type; skip catastrophic failures early (ephemeris range).
- **Finiteness:** Reject non-finite HF outputs; log angles for debugging.
- **Compression & layout:** Prefer one Parquet per subject; use Snappy/ZSTD.

## Suggested Code Layout
- `scripts/generate_relocation_field.py` — CLI to run the pipeline for one or many subjects.
- `experiments/run_relocation_pilot.py` — Pilot harness (10 subjects), produces plots and summaries.
- `src/relocation/grid.py` — Grid construction and ordering utilities.
- `src/relocation/pipeline.py` — Orchestration: Abu calls, HF Core invocation, delta computation, persistence.
- `src/relocation/summary.py` — Summary statistics and validation helpers.
- `src/relocation/viz.py` — Heatmap generation for HF_total and ΔHF_total.

## Performance Notes
- At 5° resolution the grid has 2,409 points per subject; scale linearly with finer grids.
- JAX acceleration may target only the HF computation stage; validate CPU/JAX parity on a fixed subset.
- Parallelize across subjects or latitude bands; maintain reproducible ordering when writing outputs.

## Metadata Emission
Include in outputs and logs: experiment_version, grid_step_deg, house_system, ephemeris_version, hf_core_version, commit_hash, backend, processed_at.