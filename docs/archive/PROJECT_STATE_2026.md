# Abu Oracle / Harmony Field – Project State (March 2026)

## Components
- **Abu Engine:** FastAPI astronomy service; provides planetary longitudes, ASC, MC, houses; uses DE440s ephemeris by default.
- **HF Core v1 (abu_engine/harmony):** 36D embedding with 12-point circular vectors, 8 harmonic features, and 4 HF metrics (hf_total, hf_harmony, hf_tension, hf_conjunction).
- **Lilly Engine:** LLM-based interpretations (not altered here).
- **Next.js App:** UI consuming Abu/Lilly APIs.

## Datasets
- **hf_dataset_v1.parquet (~4,650 charts):** Generated via `scripts/generate_hf_dataset.py`; includes HF metrics and harmonics for natal charts.
- **Audit outputs:** `audit_output/` for raw birthdata quality checks.

## Protocols & Docs (current split)
- Theory: `docs/theory/HF_THEORETICAL_FRAMEWORK.md`
- Experiments: `docs/experiments/HF_RELOCATION_PROTOCOL.md`, `HF_RELOCATION_SCHEMA.md`, `HF_RELOCATION_VALIDATION.md`
- Architecture: `docs/architecture/HF_RELOCATION_PIPELINE.md`

## Pipelines
- **HF dataset bridge:** `scripts/generate_hf_dataset.py` (natal embedding generation).
- **Planned relocation pipeline:** see `docs/architecture/HF_RELOCATION_PIPELINE.md` (to be implemented).

## Findings to Date
- Natal latitude shows low correlation with `hf_tension`; relocation sensitivity still unmeasured (protocol now defined).
- Ephemeris range constraint: ~1849–2150; outside range triggers failures.
- HF metrics correlations observed: `hf_total` moderately correlated with harmony and tension components.

## Open Directions
- **HF v2:** House-aware features (cusps/occupancy) to capture relocation effects mediated by houses.
- **Relocation field execution:** Implement grid evaluation, summaries, and parity tests; generate pilot plots.
- **Acceleration:** Optional JAX for HF computation stage (CPU remains source of truth for validation).
- **Transits:** Extend relocation sensitivity to transit overlays on natal HF.