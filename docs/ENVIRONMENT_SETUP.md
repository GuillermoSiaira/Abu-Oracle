# Environment Setup for Harmony Field Relocation Experiments

This guide explains how to provision a Python environment to run `scripts/generate_relocation_field.py` on Windows PowerShell.

## Quick setup (recommended)

```powershell
cd d:\projects\ai-oracle
scripts\setup_environment.ps1
```

What it does:
- Creates `.venv/` in the repo root if missing.
- Activates it.
- Upgrades `pip`.
- Installs dependencies from `requirements.txt`.
- Verifies imports (`pandas, numpy, pyarrow, swisseph, matplotlib, tqdm`).

After setup, activate when needed:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the relocation pilot:

```powershell
python scripts/generate_relocation_field.py
```

Outputs are written to `output/relocation_fields/` per subject.

## Manual setup (if you prefer explicit steps)

```powershell
cd d:\projects\ai-oracle
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "import pandas, numpy, pyarrow, swisseph; print('Environment OK')"
```

Then run:

```powershell
python scripts/generate_relocation_field.py
```

## Notes
- The relocation script expects `data/processed/hf_dataset_v1.parquet` with the required columns (`subject_id, name, birth_datetime, latitude, longitude`).
- The grid is deterministic (33×73 points at 5° resolution) and CPU-only; no JAX required.
- If you change Python versions, recreate the virtual environment.