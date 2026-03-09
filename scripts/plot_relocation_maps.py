"""Visualize relocation harmony field results as global heatmaps.

Run:
    python scripts/plot_relocation_maps.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import matplotlib

# Use a non-interactive backend for headless environments
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import griddata


REQUIRED_COLUMNS = [
    "relocation_latitude",
    "relocation_longitude",
    "delta_hf_total",
    "delta_hf_harmony",
    "delta_hf_tension",
    "delta_hf_conjunction",
]

INPUT_DIR = Path("output/relocation_fields")
OUTPUT_DIR = Path("output/relocation_maps")


def load_subject_data(parquet_path: Path) -> pd.DataFrame:
    """Load a subject parquet ensuring required columns are present."""
    df = pd.read_parquet(parquet_path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {parquet_path.name}: {missing}")
    return df[REQUIRED_COLUMNS]


def _maybe_interpolate(df: pd.DataFrame, lats: np.ndarray, lons: np.ndarray, base_grid: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Optionally smooth using griddata; fall back to base grid on failure."""
    try:
        # Increase resolution modestly for a smoother look
        lat_fine = np.linspace(lats.min(), lats.max(), len(lats) * 2 - 1)
        lon_fine = np.linspace(lons.min(), lons.max(), len(lons) * 2 - 1)
        lon_fine_grid, lat_fine_grid = np.meshgrid(lon_fine, lat_fine)

        points = np.column_stack([df["relocation_longitude"], df["relocation_latitude"]])
        values = df["delta_hf_total"].to_numpy()

        interp = griddata(points, values, (lon_fine_grid, lat_fine_grid), method="cubic")
        if np.all(np.isfinite(interp)):
            return interp, lat_fine_grid, lon_fine_grid
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  Smoothing skipped ({exc})")

    # Fallback to the original grid
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    return base_grid, lat_grid, lon_grid


def create_heatmap(df: pd.DataFrame, subject_id: str, smoothing: bool = True):
    """Create a matplotlib figure for the subject heatmap."""
    lats = np.sort(df["relocation_latitude"].unique())
    lons = np.sort(df["relocation_longitude"].unique())
    pivot = (
        df.pivot(index="relocation_latitude", columns="relocation_longitude", values="delta_hf_total")
        .sort_index()
        .sort_index(axis=1)
    )
    base_grid = pivot.to_numpy()

    if smoothing:
        data_to_plot, lat_grid, lon_grid = _maybe_interpolate(df, lats, lons, base_grid)
    else:
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        data_to_plot = base_grid

    vmax = float(np.nanmax(np.abs(df["delta_hf_total"].to_numpy())))
    vmin = -vmax if vmax > 0 else 0.0

    fig, ax = plt.subplots(figsize=(11, 5.5))
    im = ax.imshow(
        data_to_plot,
        origin="lower",
        cmap="coolwarm",
        extent=[lon_grid.min(), lon_grid.max(), lat_grid.min(), lat_grid.max()],
        vmin=vmin,
        vmax=vmax,
        aspect="auto",
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("ΔHF_total")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Relocation Harmony Field – Subject {subject_id}")

    return fig


def save_map(fig, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def process_all_subjects(input_dir: Path = INPUT_DIR, output_dir: Path = OUTPUT_DIR, smoothing: bool = True) -> None:
    parquet_files = sorted(input_dir.glob("subject_*.parquet"))
    total = len(parquet_files)
    if total == 0:
        raise SystemExit(f"No parquet files found in {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, parquet_path in enumerate(parquet_files, start=1):
        subject_id = parquet_path.stem.split("_")[-1]
        print(f"Processing subject {idx}/{total}: {subject_id}")

        df = load_subject_data(parquet_path)
        fig = create_heatmap(df, subject_id, smoothing=smoothing)

        out_file = output_dir / f"subject_{subject_id}_delta_hf_total.png"
        save_map(fig, out_file)
        print(f"Saved map {out_file.name}")

    print(f"Total maps generated: {total}")


def main():
    process_all_subjects()


if __name__ == "__main__":
    main()
