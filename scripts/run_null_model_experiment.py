"""Compare real relocation HF fields with a null (rotated planets) model.

Usage:
    python scripts/run_null_model_experiment.py

Outputs:
    analysis/null_model_comparison.csv
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

# Prefer non-interactive backend if matplotlib is imported elsewhere

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

DATASET_PATH = REPO_ROOT / "data" / "processed" / "hf_dataset_v1.parquet"
REAL_FIELDS_DIR = REPO_ROOT / "output" / "relocation_fields"
OUTPUT_FILE = REPO_ROOT / "analysis" / "null_model_comparison.csv"

N_SUBJECTS = 20
GRID_STEP_DEG = 5.0
GRID_LAT_START, GRID_LAT_END = -80.0, 80.0
GRID_LON_START, GRID_LON_END = -180.0, 180.0

REQUIRED_COLS = ["subject_id", "birth_datetime", "latitude", "longitude"]


def generate_grid(step: float = GRID_STEP_DEG) -> List[Tuple[float, float]]:
    def frange(start: float, end: float, step_val: float) -> Iterable[float]:
        n = int(round((end - start) / step_val))
        for i in range(n + 1):
            yield round(start + i * step_val, 6)

    lats = list(frange(GRID_LAT_START, GRID_LAT_END, step))
    lons = list(frange(GRID_LON_START, GRID_LON_END, step))
    return [(lat, lon) for lat in lats for lon in lons]


def compute_hf_metrics(angles_deg: Dict[str, float]) -> Dict[str, float]:
    hf = aggregate_field(angles_deg)
    return {"hf_total": float(hf["HF_total"])}


def rotate_planets(planet_positions: Dict[str, float], angle_deg: float) -> Dict[str, float]:
    return {name: (lon + angle_deg) % 360.0 for name, lon in planet_positions.items()}


def build_grid_arrays(points: List[Tuple[float, float]], values: List[float]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    lats = sorted(set(lat for lat, _ in points))
    lons = sorted(set(lon for _, lon in points))
    lat_idx = {lat: i for i, lat in enumerate(lats)}
    lon_idx = {lon: j for j, lon in enumerate(lons)}
    grid = np.full((len(lats), len(lons)), np.nan, dtype=float)
    for (lat, lon), val in zip(points, values):
        grid[lat_idx[lat], lon_idx[lon]] = val
    return np.array(lats), np.array(lons), grid


def compute_metrics_from_series(points: List[Tuple[float, float]], hf_values: List[float], delta_values: List[float]) -> Dict[str, float]:
    lats, lons, grid = build_grid_arrays(points, hf_values)
    delta = np.array(delta_values)

    # RSI and range on delta_hf_total
    rsi = float(np.nanmean(np.abs(delta)))
    dynamic_range = float(np.nanmax(delta) - np.nanmin(delta))
    variance = float(np.nanvar(delta))

    # Smoothness on hf_total grid (mean abs diff of 4-neighbors)
    diffs_lat = np.abs(np.diff(grid, axis=0))
    diffs_lon = np.abs(np.diff(grid, axis=1))
    smoothness = float(np.nanmean(np.concatenate([diffs_lat.ravel(), diffs_lon.ravel()])))

    # Anisotropy: variance along longitude / variance along latitude (hf_total grid)
    var_lon = np.nanmean(np.var(grid, axis=1))
    var_lat = np.nanmean(np.var(grid, axis=0))
    anisotropy = float(var_lon / var_lat) if var_lat not in (0, np.nan) else np.nan

    return {
        "rsi": rsi,
        "dynamic_range": dynamic_range,
        "smoothness": smoothness,
        "anisotropy": anisotropy,
        "variance": variance,
    }


def compute_real_metrics(parquet_path: Path) -> Dict[str, float]:
    df = pd.read_parquet(parquet_path)
    points = list(zip(df["relocation_latitude"], df["relocation_longitude"]))
    hf_values = df["hf_total"].to_list()
    delta_values = df["delta_hf_total"].to_list()
    metrics = compute_metrics_from_series(points, hf_values, delta_values)
    return {
        "rsi_real": metrics["rsi"],
        "dynamic_range_real": metrics["dynamic_range"],
        "smoothness_real": metrics["smoothness"],
        "anisotropy_real": metrics["anisotropy"],
        "variance_real": metrics["variance"],
    }


def compute_null_metrics(subject: pd.Series, grid_points: List[Tuple[float, float]]) -> Dict[str, float]:
    birth_dt = pd.to_datetime(subject["birth_datetime"], utc=True)
    lat = float(subject["latitude"])
    lon = float(subject["longitude"])

    chart = chart_json(lat, lon, birth_dt)
    planet_positions = {p.name: float(p.lon) for p in chart.planets}

    rng = np.random.default_rng()
    angle = float(rng.uniform(0.0, 360.0))
    rotated = rotate_planets(planet_positions, angle)

    # Natal (null)
    houses_natal = calculate_houses(birth_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
    angles_natal = dict(rotated)
    angles_natal["ASC"] = float(houses_natal["asc"])
    angles_natal["MC"] = float(houses_natal["mc"])
    natal_metrics = compute_hf_metrics(angles_natal)
    natal_hf = natal_metrics["hf_total"]

    hf_values: List[float] = []
    delta_values: List[float] = []

    for rel_lat, rel_lon in grid_points:
        houses = calculate_houses(birth_dt, rel_lat, rel_lon, HOUSE_SYSTEM_PLACIDUS)
        angles = dict(rotated)
        angles["ASC"] = float(houses["asc"])
        angles["MC"] = float(houses["mc"])
        metrics = compute_hf_metrics(angles)
        hf_val = metrics["hf_total"]
        hf_values.append(hf_val)
        delta_values.append(hf_val - natal_hf)

    metrics = compute_metrics_from_series(grid_points, hf_values, delta_values)
    return {
        "rsi_null": metrics["rsi"],
        "dynamic_range_null": metrics["dynamic_range"],
        "smoothness_null": metrics["smoothness"],
        "anisotropy_null": metrics["anisotropy"],
        "variance_null": metrics["variance"],
    }


def select_subjects(df: pd.DataFrame, n: int) -> pd.DataFrame:
    if "trust_score" in df.columns:
        return df.sort_values("trust_score", ascending=False).head(n)
    return df.head(n)


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_parquet(DATASET_PATH)

    # Normalize subject_id / name
    if "subject_id" not in df.columns:
        if "id" in df.columns:
            df["subject_id"] = df["id"]
        else:
            raise KeyError("Dataset missing subject_id/id column")
    if "name" not in df.columns:
        df["name"] = ""

    # birth_datetime normalization
    if "birth_datetime" in df.columns:
        df["birth_datetime"] = pd.to_datetime(df["birth_datetime"], utc=True, errors="coerce")
    elif "birth_date" in df.columns and "birth_time" in df.columns:
        birth_dt_str = df["birth_date"].astype(str).str.strip() + "T" + df["birth_time"].astype(str).str.strip()
        df["birth_datetime"] = pd.to_datetime(birth_dt_str, utc=True, errors="coerce")
    else:
        raise KeyError("Dataset missing birth_datetime or birth_date/birth_time columns")

    if df["birth_datetime"].isna().any():
        raise ValueError("Some birth_datetime values could not be parsed to datetime")

    # Ensure numeric lat/lon
    for col in ("latitude", "longitude"):
        if col not in df.columns:
            raise KeyError(f"Dataset missing required column: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[["latitude", "longitude"]].isna().any().any():
        raise ValueError("Some latitude/longitude values are NaN after conversion")

    subset = select_subjects(df, N_SUBJECTS).copy()
    grid = generate_grid(GRID_STEP_DEG)

    results = []
    for idx, subj in enumerate(subset.itertuples(index=False), start=1):
        s = subj._asdict()
        sid = s["subject_id"]
        name = s.get("name", "")
        real_path = REAL_FIELDS_DIR / f"subject_{sid}.parquet"
        if not real_path.exists():
            print(f"[{idx}/{len(subset)}] {name} (id={sid}) -> skip (real field missing)")
            continue
        print(f"[{idx}/{len(subset)}] {name} (id={sid})")

        real_metrics = compute_real_metrics(real_path)
        null_metrics = compute_null_metrics(pd.Series(s), grid)

        row = {"subject_id": sid, **real_metrics, **null_metrics}
        results.append(row)

    if not results:
        print("No results produced.")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
    print(f"Saved null model comparison to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
