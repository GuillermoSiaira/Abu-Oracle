"""Analyze relocation Harmony Field outputs and compute structural metrics.

Usage:
    python scripts/analyze_relocation_fields.py

Outputs:
    analysis/relocation_metrics.csv
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

INPUT_DIR = Path("output/relocation_fields")
OUTPUT_DIR = Path("analysis")
OUTPUT_FILE = OUTPUT_DIR / "relocation_metrics.csv"

REQUIRED_COLS = {
    "relocation_latitude",
    "relocation_longitude",
    "hf_total",
    "delta_hf_total",
    "natal_latitude",
    "natal_longitude",
}


def _compute_natal_value(df: pd.DataFrame) -> float:
    # delta_hf_total = hf_total - natal_hf_total, so natal = hf_total - delta
    natal_values = df["hf_total"] - df["delta_hf_total"]
    return float(natal_values.median())


def _compute_smoothness(grid: np.ndarray) -> float:
    # mean absolute difference between neighboring grid points (4-neighbor)
    diffs_lat = np.abs(np.diff(grid, axis=0))
    diffs_lon = np.abs(np.diff(grid, axis=1))
    all_diffs = np.concatenate([diffs_lat.ravel(), diffs_lon.ravel()])
    return float(np.nanmean(all_diffs))


def _compute_anisotropy(grid: np.ndarray) -> float:
    # variance along longitude / variance along latitude
    var_along_lon = np.var(grid, axis=1).mean()  # variations east-west
    var_along_lat = np.var(grid, axis=0).mean()  # variations north-south
    return float(var_along_lon / var_along_lat) if var_along_lat != 0 else np.nan


def _count_local_maxima(grid: np.ndarray) -> int:
    # Strict local maxima vs 4-neighbors (no wrap)
    padded = np.pad(grid, pad_width=1, mode="constant", constant_values=-np.inf)
    center = padded[1:-1, 1:-1]
    up = padded[:-2, 1:-1]
    down = padded[2:, 1:-1]
    left = padded[1:-1, :-2]
    right = padded[1:-1, 2:]
    maxima_mask = (center > up) & (center > down) & (center > left) & (center > right)
    return int(np.sum(maxima_mask))


def compute_metrics_for_subject(df: pd.DataFrame, subject_id: str) -> Dict[str, float]:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in subject {subject_id}: {sorted(missing)}")

    # Pivot to grid
    pivot = df.pivot(index="relocation_latitude", columns="relocation_longitude", values="hf_total")
    pivot = pivot.sort_index().sort_index(axis=1)
    grid = pivot.to_numpy()

    delta = df["delta_hf_total"]
    rsi = float(delta.abs().mean())
    dynamic_range = float(delta.max() - delta.min())
    smoothness = _compute_smoothness(grid)
    anisotropy = _compute_anisotropy(grid)

    natal_value = _compute_natal_value(df)
    hf_values = df["hf_total"]
    natal_rank = float((hf_values <= natal_value).mean())

    n_local_maxima = _count_local_maxima(grid)

    return {
        "subject": subject_id,
        "rsi": rsi,
        "dynamic_range": dynamic_range,
        "smoothness": smoothness,
        "anisotropy": anisotropy,
        "natal_rank": natal_rank,
        "n_local_maxima": n_local_maxima,
    }


def process_all_subjects(input_dir: Path = INPUT_DIR) -> List[Dict[str, float]]:
    parquet_files = sorted(input_dir.glob("subject_*.parquet"))
    if not parquet_files:
        raise SystemExit(f"No parquet files found in {input_dir}")

    metrics: List[Dict[str, float]] = []
    total = len(parquet_files)
    for idx, fp in enumerate(parquet_files, start=1):
        subject_id = fp.stem.split("_")[-1]
        print(f"Processing {subject_id} ({idx}/{total})")
        df = pd.read_parquet(fp)
        metrics.append(compute_metrics_for_subject(df, subject_id))
    return metrics


def save_metrics(rows: List[Dict[str, float]], output_file: Path = OUTPUT_FILE) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values("subject").to_csv(output_file, index=False)
    print(f"Saved metrics to {output_file}")


def main():
    rows = process_all_subjects()
    save_metrics(rows)


if __name__ == "__main__":
    main()
