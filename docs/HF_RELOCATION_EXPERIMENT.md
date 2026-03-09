# Harmony Field Relocation Sensitivity Experiment (Protocol)

This document defines a complete, reproducible protocol for measuring how Harmony Field (HF) metrics vary when a natal chart is hypothetically relocated across the globe. It is written as a methodological reference for researchers and engineers working on the Abu Oracle stack and assumes familiarity with the existing HF Core v1 implementation (`abu_engine/harmony/`), Abu Engine astronomy services, and the `hf_dataset_v1.parquet` natal dataset. The target audience is technical; the language is intentionally precise, neutral, and oriented toward computational reproducibility.

# Harmony Field Relocation Documentation Index

The relocation sensitivity content has been split into focused documents for maintainability and reproducibility. Start from the references below:

- **Theory:** `docs/theory/HF_THEORETICAL_FRAMEWORK.md`
- **Experiments:**
  - Protocol: `docs/experiments/HF_RELOCATION_PROTOCOL.md`
  - Schema: `docs/experiments/HF_RELOCATION_SCHEMA.md`
  - Validation: `docs/experiments/HF_RELOCATION_VALIDATION.md`
- **Architecture:** `docs/architecture/HF_RELOCATION_PIPELINE.md`
- **Project state snapshot (Mar 2026):** `docs/PROJECT_STATE_2026.md`

This stub remains for backward compatibility; the canonical content now lives in the files above.
- **House-system comparison:** Run paired experiments across house systems (Placidus vs. Whole Sign) to estimate method-induced variance relative to relocation-induced variance.

## 11. Future Work
- **HF v2 (house-aware):** Extend the HF embedding to include house cusps and occupancy so relocation effects on houses are directly represented.
- **Transit relocation:** Evaluate relocation sensitivity under transits applied to the natal HF embedding, producing time-varying relocation fields.
- **Acceleration:** Apply JAX `vmap`/`jit` to the HF computation stage (not to astronomical calculations) to enable finer grids or larger subject batches.
- **Adaptive grids:** Use gradient-guided refinement where |ΔHF| is high to capture local structure with fewer total points.

## 12. Execution Checklist
- [ ] Select pilot subjects (10) and verify birth data quality.
- [ ] Set grid bounds and resolution (default 5°, −80..80 lat, −180..180 lon) and record in metadata.
- [ ] Fix house system (Placidus) and ephemeris version (DE440s or updated); record both.
- [ ] Compute natal HF baseline per subject.
- [ ] Run relocation grid: Abu Engine for angles → HF Core v1 for metrics → ΔHF vs natal.
- [ ] Persist per-subject Parquet with required schema and deterministic ordering; capture errors in valid_flag/error_type.
- [ ] Compute per-subject summary stats (mean, std, min, max, |ΔHF| mean/max/95p) and optional robustness fractions.
- [ ] Generate HF_total and ΔHF_total heatmaps for pilot subjects; review for anomalies.
- [ ] After pilot validation, process full dataset; produce population-level summaries.
- [ ] Archive experiment metadata (experiment_version, commit_hash, grid_step_deg, house_system, ephemeris_version, hf_core_version, backend) alongside outputs.

## 13. Validation and Parity Testing
To ensure that results are trustworthy across implementations and hardware, perform the following validation steps on a small, fixed subset of subjects and grid points (e.g., 2 subjects × 20 grid points):

- **CPU vs. accelerated parity:** If a JAX-accelerated HF stage is used, compare outputs against the reference CPU implementation. Acceptable tolerance: absolute difference < 1e-9 for HF metrics.
- **Repeatability:** Run the same subset twice in a clean environment and verify byte-identical Parquet outputs for the relocation rows and summary statistics. Any divergence should be investigated before scaling up.
- **Schema conformance:** Validate that all required columns are present with correct dtypes. Missing columns or dtype drift should fail the pipeline.
- **Boundary checks:** Include grid points near the latitude bound (±80°) and longitude wrap-around (±180°) in the validation subset to surface angular edge cases.
- **Error-path coverage:** Intentionally include one subject outside ephemeris range to confirm that `ephemeris_range` is set and that the subject is skipped without crashing the batch.

Document validation results in a short log (e.g., `logs/hf_reloc_validation.txt`) that records subjects, grid points, backend, tolerances, and pass/fail outcomes. This log is part of the reproducibility record.

## 14. Implementation Notes and Recommendations
- **Caching Abu calls:** For performance, cache Abu Engine outputs keyed by (t₀, φ, λ, house_system, ephemeris). Ensure cache invalidation when any of these parameters change.
- **I/O layout:** Writing one Parquet per subject avoids hotspots on a single large file and simplifies partial reruns. Use Snappy or ZSTD compression.
- **Chunked processing:** For the full dataset, process subjects in chunks (e.g., 100 subjects per batch) to bound memory and simplify recovery from failures.
- **Logging:** Emit structured logs (JSONL) with subject_id, grid point, valid_flag, error_type, runtime_ms. This supports later profiling and debugging.
- **Environment capture:** Record Python version, Abu Engine commit, HF Core commit, OS, and CPU/GPU info in the run metadata.
- **Numerical stability:** Use radians internally for trigonometric operations; ensure consistent degree↔radian conversions at module boundaries. Clamp or wrap angles to [0, 2π) as in HF Core v1.

## 15. Interpretation Guardrails
This protocol is purely computational. It does not prescribe interpretive meaning for high or low ΔHF. Any narrative or user-facing interpretation must: (1) cite the experiment version and parameters; (2) specify whether house-aware features were included (HF v2 or later); and (3) avoid extrapolating beyond the validated grid resolution. Analysts should explicitly state that relocation sensitivity captures model-specific variation, not empirical outcomes.