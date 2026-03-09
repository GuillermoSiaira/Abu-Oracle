# Harmony Field Relocation Validation

## Goal
Ensure numerical correctness, reproducibility, and backend parity for relocation experiments.

## Validation Subset
- Use a fixed subset: e.g., 2 subjects × 20 grid points (covering latitude bounds ±80° and longitude wrap-around ±180°).
- Include one out-of-ephemeris subject to exercise the `ephemeris_range` error path.

## Checks
1. **CPU vs accelerated parity (if applicable):** Compare HF outputs with tolerance < 1e-9 absolute difference.
2. **Repeatability:** Re-run the subset twice in a clean environment; expect byte-identical Parquet rows and summaries.
3. **Schema conformance:** All required columns present with expected dtypes; fail fast on mismatch.
4. **Angle sanity:** No NaNs in ASC/MC; house computation must succeed or set valid_flag = False with `house_fail`.
5. **HF finiteness:** Reject rows with non-finite HF metrics; tag as `nan_output`.
6. **Boundary coverage:** Explicitly include points near ±80° latitude and ±180° longitude.

## Logging
- Emit a validation log (e.g., `logs/hf_reloc_validation.txt`) capturing subjects, grid points, backend, tolerances, and pass/fail outcomes.
- Record environment: Python version, OS, Abu Engine commit, HF Core commit, ephemeris version, house system.

## Acceptance
- Validation must pass before scaling from pilot to full dataset.
- Parity differences or non-determinism block promotion until resolved.