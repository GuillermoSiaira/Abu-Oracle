# HF Relocation Pilot — Results

## Experiment Overview

This experiment evaluates how the Harmony Field (HF) changes when the geographic location of a natal chart is modified.

The objective is to measure:

\( \Delta HF = HF(\text{relocation}) - HF(\text{natal}) \)

across a global geographic grid.

## Dataset

Source dataset: `hf_dataset_v1.parquet`

Charts used in pilot: **10 subjects**

Each subject evaluated over: **33 × 73 grid (latitude × longitude)**

Total relocation points per subject: **2409**

Latitude range: **-80° to +80°**

Longitude range: **-180° to +180°**

Grid step: **5°**

House system: **Placidus**

HF Core version: **HF Core v1**

Experiment version: **HF_RELOC_v1**

## Pipeline

Data flow:

Birth data → Abu Engine → Chart vector → HF Core → Relocation grid → ΔHF computation → relocation_fields parquet outputs

Script used: `scripts/generate_relocation_field.py`

Output files: `output/relocation_fields/subject_<id>.parquet`

## Output Schema

Each row represents one relocation point.

Columns include:

- subject_id
- name
- birth_datetime
- natal_latitude
- natal_longitude
- relocation_latitude
- relocation_longitude
- asc_lon
- mc_lon
- hf_total
- hf_harmony
- hf_tension
- hf_conjunction
- delta_hf_total
- delta_hf_harmony
- delta_hf_tension
- delta_hf_conjunction
- valid_flag
- error_type
- experiment_version
- grid_step_deg
- house_system
- processed_at

## Validation Results

- Rows per subject: **2409**
- Validation status: **100% valid rows**
- No house computation errors.

## Statistical Findings

Example chart: **Jack Kramer** (subject_420)

Relocation Sensitivity Index (RSI):

RSI = mean(|ΔHF_total|)

Result: **RSI ≈ 1.91**

HF delta statistics (subject_420):

- mean ≈ **-1.87**
- std ≈ **1.06**
- max ≈ **+1.61**
- min ≈ **-4.78**

Interpretation:

The natal location tends to correspond to a local HF maximum, as most relocations reduce HF_total.

## Field Properties

The experiment confirms that the Harmony Field can be modeled as a scalar field over Earth:

\( HF : S^2 \to \mathbb{R} \)

Where:

- \( S^2 \) is the Earth's surface.
- HF varies continuously across geographic coordinates.

Preliminary visualizations show structured spatial patterns rather than random noise.

## Next Research Steps

1. Compute RSI distribution across the entire dataset.
2. Evaluate spatial smoothness of the HF field.
3. Introduce house-aware features in HF Core v2.
4. Implement JAX acceleration for large relocation grids.
5. Generate geographic HF maps for visualization.

## Conclusion

This pilot demonstrates that the Harmony Field produces measurable geographic variation and can be used to construct relocation maps for natal charts.

This establishes the foundation for geographic optimization within the Abu Oracle system.