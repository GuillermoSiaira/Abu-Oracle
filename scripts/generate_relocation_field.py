"""
Generate Harmony Field relocation grids (pilot set, CPU reference).

Implements the relocation experiment defined in docs/experiments/HF_RELOCATION_PROTOCOL.md
for the pilot sample (first 10 natal charts) using HF Core v1 and Abu Engine
astronomy on CPU. JAX acceleration is intentionally not used here.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

# Ensure local imports work when running as a script
REPO_ROOT = Path(__file__).resolve().parent.parent
ABU_ROOT = REPO_ROOT / "abu_engine"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(ABU_ROOT) not in sys.path:
    sys.path.insert(0, str(ABU_ROOT))

from abu_engine.core.chart import chart_json  # type: ignore
from abu_engine.core.houses_swiss import (  # type: ignore
    HOUSE_SYSTEM_PLACIDUS,
    calculate_houses,
)
from abu_engine.harmony.field import aggregate_field


EXPERIMENT_VERSION = "HF_RELOC_v1"
GRID_STEP_DEG = 5.0
HOUSE_SYSTEM = "Placidus"

DATASET_PATH = REPO_ROOT / "data" / "processed" / "hf_dataset_v1.parquet"
OUTPUT_DIR = REPO_ROOT / "output" / "relocation_fields"

GRID_LAT_START, GRID_LAT_END = -80.0, 80.0
GRID_LON_START, GRID_LON_END = -180.0, 180.0

REQUIRED_COLUMNS = [
    "subject_id",
    "name",
    "birth_datetime",
    "latitude",
    "longitude",
]


def generate_grid(step: float = GRID_STEP_DEG) -> List[Tuple[float, float]]:
    """Generate a deterministic latitude-major grid.

    Returns:
        List of (lat, lon) tuples ordered by latitude then longitude.
    """

    def frange(start: float, end: float, step_val: float) -> Iterable[float]:
        # Inclusive range with rounding to avoid floating drift
        n = int(round((end - start) / step_val))
        for i in range(n + 1):
            yield round(start + i * step_val, 6)

    lats = list(frange(GRID_LAT_START, GRID_LAT_END, step))
    lons = list(frange(GRID_LON_START, GRID_LON_END, step))
    grid = [(lat, lon) for lat in lats for lon in lons]
    return grid


def compute_hf_metrics(angles_deg: Dict[str, float]) -> Dict[str, float]:
    """Compute HF Core v1 metrics (CPU)."""
    hf = aggregate_field(angles_deg)
    return {
        "hf_total": float(hf["HF_total"]),
        "hf_harmony": float(hf["HF_harmony"]),
        "hf_tension": float(hf["HF_tension"]),
        "hf_conjunction": float(hf["HF_conjunction"]),
    }


def compute_natal_hf(subject: pd.Series, planet_positions: Dict[str, float]) -> Dict[str, float]:
    """Compute natal HF metrics and angles for a subject."""
    birth_dt: datetime = subject["birth_datetime"]
    lat = float(subject["latitude"])
    lon = float(subject["longitude"])

    houses = calculate_houses(birth_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
    angles = dict(planet_positions)
    angles["ASC"] = float(houses["asc"])
    angles["MC"] = float(houses["mc"])

    metrics = compute_hf_metrics(angles)
    return {
        "angles": angles,
        "asc": angles["ASC"],
        "mc": angles["MC"],
        **metrics,
    }


def compute_relocation_hf(
    birth_dt: datetime,
    rel_lat: float,
    rel_lon: float,
    planet_positions: Dict[str, float],
) -> Tuple[bool, str, Dict[str, float]]:
    """Compute HF metrics at a relocation point. Returns (valid, error, metrics)."""
    try:
        houses = calculate_houses(birth_dt, rel_lat, rel_lon, HOUSE_SYSTEM_PLACIDUS)
        angles = dict(planet_positions)
        angles["ASC"] = float(houses["asc"])
        angles["MC"] = float(houses["mc"])
        metrics = compute_hf_metrics(angles)
        metrics.update({"asc": angles["ASC"], "mc": angles["MC"]})
        return True, "", metrics
    except Exception:
        return False, "house_fail", {}


def process_subject(subject: pd.Series, grid: List[Tuple[float, float]]) -> pd.DataFrame:
    """Process one subject over the entire relocation grid."""
    # Fixed birth datetime (UTC-aware)
    birth_dt: datetime = subject["birth_datetime"]
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=timezone.utc)

    # Planetary positions (do not depend on relocation coordinates)
    chart = chart_json(float(subject["latitude"]), float(subject["longitude"]), birth_dt)
    planet_positions = {p.name: float(p.lon) for p in chart.planets}

    # Natal baseline
    natal = compute_natal_hf(subject, planet_positions)

    rows = []
    processed_at = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    for idx, (rel_lat, rel_lon) in enumerate(grid, start=1):
        valid, error_type, metrics = compute_relocation_hf(birth_dt, rel_lat, rel_lon, planet_positions)

        row = {
            "subject_id": subject["subject_id"],
            "name": subject.get("name", ""),
            "birth_datetime": birth_dt.isoformat(),
            "natal_latitude": float(subject["latitude"]),
            "natal_longitude": float(subject["longitude"]),
            "relocation_latitude": rel_lat,
            "relocation_longitude": rel_lon,
            "asc_lon": float(metrics.get("asc", float("nan"))),
            "mc_lon": float(metrics.get("mc", float("nan"))),
            "hf_total": float(metrics.get("hf_total", float("nan"))),
            "hf_harmony": float(metrics.get("hf_harmony", float("nan"))),
            "hf_tension": float(metrics.get("hf_tension", float("nan"))),
            "hf_conjunction": float(metrics.get("hf_conjunction", float("nan"))),
            "delta_hf_total": float(metrics.get("hf_total", float("nan"))) - float(natal["hf_total"])
            if valid
            else float("nan"),
            "delta_hf_harmony": float(metrics.get("hf_harmony", float("nan"))) - float(natal["hf_harmony"])
            if valid
            else float("nan"),
            "delta_hf_tension": float(metrics.get("hf_tension", float("nan"))) - float(natal["hf_tension"])
            if valid
            else float("nan"),
            "delta_hf_conjunction": float(metrics.get("hf_conjunction", float("nan"))) - float(natal["hf_conjunction"])
            if valid
            else float("nan"),
            "valid_flag": bool(valid),
            "error_type": error_type,
            "experiment_version": EXPERIMENT_VERSION,
            "grid_step_deg": GRID_STEP_DEG,
            "house_system": HOUSE_SYSTEM,
            "processed_at": processed_at,
        }
        rows.append(row)

        if idx % 200 == 0 or idx == len(grid):
            print(f"Grid point {idx}/{len(grid)}")

    columns = [
        "subject_id",
        "name",
        "birth_datetime",
        "natal_latitude",
        "natal_longitude",
        "relocation_latitude",
        "relocation_longitude",
        "asc_lon",
        "mc_lon",
        "hf_total",
        "hf_harmony",
        "hf_tension",
        "hf_conjunction",
        "delta_hf_total",
        "delta_hf_harmony",
        "delta_hf_tension",
        "delta_hf_conjunction",
        "valid_flag",
        "error_type",
        "experiment_version",
        "grid_step_deg",
        "house_system",
        "processed_at",
    ]

    return pd.DataFrame(rows, columns=columns)


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Input dataset not found: {DATASET_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(DATASET_PATH)

    # Normalize required fields
    if "subject_id" not in df.columns:
        if "id" in df.columns:
            df["subject_id"] = df["id"]
        else:
            raise KeyError("Dataset missing subject_id/id column")
    if "name" not in df.columns:
        df["name"] = ""

    if "birth_datetime" in df.columns:
        df["birth_datetime"] = pd.to_datetime(df["birth_datetime"], utc=True, errors="coerce")
    else:
        if "birth_date" in df.columns and "birth_time" in df.columns:
            birth_dt_str = df["birth_date"].astype(str).str.strip() + "T" + df["birth_time"].astype(str).str.strip()
            df["birth_datetime"] = pd.to_datetime(birth_dt_str, utc=True, errors="coerce")
        else:
            raise KeyError("Dataset missing birth_datetime or birth_date/birth_time columns")

    if df["birth_datetime"].isna().any():
        raise ValueError("Some birth_datetime values could not be parsed to datetime")

    required_numeric = ["latitude", "longitude"]
    for col in required_numeric:
        if col not in df.columns:
            raise KeyError(f"Dataset missing required column: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[required_numeric].isna().any().any():
        raise ValueError("Some latitude/longitude values are NaN after conversion")

    # Pilot: first 10 records
    pilot_df = df.head(10).copy()

    grid = generate_grid(GRID_STEP_DEG)
    print(f"Grid size: {len(grid)} points (lat-major order)")

    total_subjects = len(pilot_df)
    for idx, subject in enumerate(pilot_df.itertuples(index=False), start=1):
        subj_series = subject._asdict()
        print(f"Processing subject {idx}/{total_subjects} (id={subj_series['subject_id']})")
        df_subject = process_subject(pd.Series(subj_series), grid)
        out_path = OUTPUT_DIR / f"subject_{subj_series['subject_id']}.parquet"
        df_subject.to_parquet(out_path, index=False)
        print(f"Saved {len(df_subject)} rows to {out_path}")


if __name__ == "__main__":
    main()