# Harmony Field Relocation Protocol

## Scope
Defines the experimental design for measuring within-chart relocation sensitivity of Harmony Field (HF) metrics. Applies to pilot and full-dataset runs using HF Core v1 with Abu Engine providing astronomical quantities.

## Subjects
- **Pilot:** 10 charts spanning diverse epochs, hemispheres, and data quality tiers for validation and visualization.
- **Full run:** All ~4,650 charts in `hf_dataset_v1.parquet` after pilot sign-off.

## Grid Specification
- **Latitude (φ):** −80° to +80° inclusive.
- **Longitude (λ):** −180° to +180° inclusive.
- **Resolution:** Default 5° steps. This yields 33 latitude bands and 73 longitude bands → 33 × 73 = 2,409 grid points per subject. Finer grids are allowed but must be recorded.
- **Ordering:** Deterministic (e.g., latitude-major then longitude) for reproducibility.

## Astronomical Conventions
- **Birth instant:** Fixed per subject in UTC; relocation varies only geographic coordinates.
- **House system:** Placidus by default; any alternative must be recorded.
- **Ephemeris:** DE440s by default; upgrades (e.g., DE441) must be recorded.

## Procedure
1. Compute natal HF at (φ₀, λ₀) for the subject (baseline).
2. For each grid point (φ, λ):
   - Abu Engine: recompute ASC, MC, houses (planetary longitudes fixed at t₀).
   - HF Core v1: compute circular vector, harmonic signature, and HF metrics.
   - Compute ΔHF = HF(φ, λ) − HF(φ₀, λ₀) component-wise.
   - Record outputs, validity, and errors.
3. Persist results (see schema) and compute summary statistics.
4. Produce required visualizations for pilot subjects.

## Summary Statistics (per subject)
Computed over valid grid points:
- Mean, std, min, max for {hf_total, hf_harmony, hf_tension, hf_conjunction}.
- Mean |ΔHF|, max |ΔHF|, 95th percentile |ΔHF| for each component.
- Optional robustness: fractions with |ΔHF_total| < 0.5 and < 1.0.
- Recommended diagnostics: finite-difference smoothness (lat/lon bands), skew/kurtosis of ΔHF_total, counts above 2σ/3σ.

## Visualization Requirements
- HF_total heatmap over (φ, λ) using a perceptually uniform colormap (e.g., viridis).
- ΔHF_total heatmap centered at 0 using a diverging colormap (e.g., coolwarm/bwr).
- Optional: hf_harmony and hf_tension maps; contour overlays for gradients.
- Annotate plots with house system, ephemeris, grid step, experiment_version. Save as deterministic filenames.

## Reproducibility Rules
- Record: experiment_version, grid_step_deg, house_system, ephemeris_version, hf_core_version, commit_hash, backend (cpu/jax).
- Use deterministic grid ordering and stable column order.
- No relocation claims are admissible without executing this protocol and emitting the above metadata.