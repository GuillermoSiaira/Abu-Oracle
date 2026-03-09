"""Statistical comparison of real relocation HF fields vs. null (rotated planets) model.

Usage:
    python scripts/run_null_model_statistical_test.py [--seed 42] [--n_subjects 50] [--n_null 30]

Outputs:
    analysis/null_model_statistical_test.csv
    analysis/null_model_population_summary.csv
    analysis/plots/*.png
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Repo paths
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
from abu_engine.harmony.field_v2 import aggregate_field_v2

DATASET_PATH = REPO_ROOT / "data" / "processed" / "hf_dataset_v1.parquet"
REAL_FIELDS_DIR = REPO_ROOT / "output" / "relocation_fields"
ANALYSIS_DIR = REPO_ROOT / "analysis"
OUTPUT_FILE = ANALYSIS_DIR / "null_model_statistical_test.csv"
SUMMARY_FILE = ANALYSIS_DIR / "null_model_population_summary.csv"
PLOTS_DIR = ANALYSIS_DIR / "plots"

GRID_STEP_DEG = 5.0
GRID_LAT_START, GRID_LAT_END = -80.0, 80.0
GRID_LON_START, GRID_LON_END = -180.0, 180.0

REQUIRED_NUMERIC = ["latitude", "longitude"]


@dataclass
class Metrics:
    rsi: float
    dynamic_range: float
    smoothness: float
    anisotropy: float
    variance: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Null model statistical test for HF relocation fields")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--n_subjects", type=int, default=50, help="Number of top-trust subjects to process")
    parser.add_argument("--n_null", type=int, default=30, help="Number of null rotations per subject")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH, help="Dataset parquet (v1 or v2)")
    parser.add_argument("--fields_dir", type=Path, default=REAL_FIELDS_DIR, help="Directory with relocation field parquets")
    return parser.parse_args()


def generate_grid(step: float = GRID_STEP_DEG) -> List[Tuple[float, float]]:
    def frange(start: float, end: float, step_val: float) -> Iterable[float]:
        n = int(round((end - start) / step_val))
        for i in range(n + 1):
            yield round(start + i * step_val, 6)

    lats = list(frange(GRID_LAT_START, GRID_LAT_END, step))
    lons = list(frange(GRID_LON_START, GRID_LON_END, step))
    return [(lat, lon) for lat in lats for lon in lons]


def compute_hf_total(angles_deg: Dict[str, float], houses_data: Dict, use_v2: bool) -> float:
    if use_v2:
        cusps = list(houses_data.get("cusps", []))
        hf = aggregate_field_v2(angles_deg, cusps)
        return float(hf["HF_total_v2"])
    hf = aggregate_field(angles_deg)
    return float(hf["HF_total"])


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


def compute_metrics_from_series(points: List[Tuple[float, float]], hf_values: List[float], delta_values: List[float]) -> Metrics:
    _, _, grid = build_grid_arrays(points, hf_values)
    delta = np.array(delta_values, dtype=float)

    rsi = float(np.nanmean(np.abs(delta)))
    dynamic_range = float(np.nanmax(delta) - np.nanmin(delta))
    variance = float(np.nanvar(delta))

    diffs_lat = np.abs(np.diff(grid, axis=0))
    diffs_lon = np.abs(np.diff(grid, axis=1))
    smoothness = float(np.nanmean(np.concatenate([diffs_lat.ravel(), diffs_lon.ravel()])))

    var_lon = np.nanmean(np.var(grid, axis=1))
    var_lat = np.nanmean(np.var(grid, axis=0))
    anisotropy = float(var_lon / var_lat) if var_lat not in (0, np.nan) else np.nan

    return Metrics(rsi, dynamic_range, smoothness, anisotropy, variance)


def compute_real_metrics(parquet_path: Path) -> Metrics:
    df = pd.read_parquet(parquet_path)
    points = list(zip(df["relocation_latitude"], df["relocation_longitude"]))
    if "hf_total" in df.columns and "delta_hf_total" in df.columns:
        hf_values = df["hf_total"].to_list()
        delta_values = df["delta_hf_total"].to_list()
    elif "hf_total_v2" in df.columns and "delta_hf_total_v2" in df.columns:
        hf_values = df["hf_total_v2"].to_list()
        delta_values = df["delta_hf_total_v2"].to_list()
    else:
        raise KeyError("Parquet missing hf_total/hf_total_v2 columns")
    return compute_metrics_from_series(points, hf_values, delta_values)


def compute_null_metrics(subject: pd.Series, grid_points: List[Tuple[float, float]], n_null: int, rng: np.random.Generator, use_v2: bool) -> Tuple[Metrics, Metrics]:
    """Returns (mean metrics, std metrics) over n_null rotations."""
    birth_dt = pd.to_datetime(subject["birth_datetime"], utc=True)
    lat = float(subject["latitude"])
    lon = float(subject["longitude"])

    chart = chart_json(lat, lon, birth_dt)
    planet_positions = {p.name: float(p.lon) for p in chart.planets}

    # Precompute houses once per subject for natal and every grid point
    houses_natal = calculate_houses(birth_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
    houses_grid = [calculate_houses(birth_dt, rel_lat, rel_lon, HOUSE_SYSTEM_PLACIDUS) for rel_lat, rel_lon in grid_points]

    metrics_list: List[Metrics] = []

    for _ in range(n_null):
        angle = float(rng.uniform(0.0, 360.0))
        rotated = rotate_planets(planet_positions, angle)

        angles_natal = dict(rotated)
        angles_natal["ASC"] = float(houses_natal["asc"])
        angles_natal["MC"] = float(houses_natal["mc"])
        natal_hf = compute_hf_total(angles_natal, houses_natal, use_v2)

        hf_vals: List[float] = []
        delta_vals: List[float] = []

        for (rel_lat, rel_lon), houses in zip(grid_points, houses_grid):
            angles = dict(rotated)
            angles["ASC"] = float(houses["asc"])
            angles["MC"] = float(houses["mc"])
            hf_val = compute_hf_total(angles, houses, use_v2)
            hf_vals.append(hf_val)
            delta_vals.append(hf_val - natal_hf)

        metrics_list.append(compute_metrics_from_series(grid_points, hf_vals, delta_vals))

    # Aggregate mean and std over null runs
    arr = pd.DataFrame([m.__dict__ for m in metrics_list])
    mean_metrics = Metrics(**{k: float(arr[k].mean()) for k in arr.columns})
    std_metrics = Metrics(**{k: float(arr[k].std(ddof=0)) for k in arr.columns})
    return mean_metrics, std_metrics


def z_score(real: float, mean: float, std: float) -> float:
    if std == 0 or np.isnan(std):
        return np.nan
    return (real - mean) / std


def select_subjects(df: pd.DataFrame, n: int) -> pd.DataFrame:
    if "trust_score" in df.columns:
        return df.sort_values("trust_score", ascending=False).head(n)
    return df.head(n)


def load_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_parquet(DATASET_PATH)

    if "subject_id" not in df.columns:
        if "id" in df.columns:
            df["subject_id"] = df["id"]
        else:
            raise KeyError("Dataset missing subject_id/id column")
    if "name" not in df.columns:
        df["name"] = ""

    if "birth_datetime" in df.columns:
        df["birth_datetime"] = pd.to_datetime(df["birth_datetime"], utc=True, errors="coerce")
    elif "birth_date" in df.columns and "birth_time" in df.columns:
        birth_dt_str = df["birth_date"].astype(str).str.strip() + "T" + df["birth_time"].astype(str).str.strip()
        df["birth_datetime"] = pd.to_datetime(birth_dt_str, utc=True, errors="coerce")
    else:
        raise KeyError("Dataset missing birth_datetime or birth_date/birth_time columns")

    if df["birth_datetime"].isna().any():
        raise ValueError("Some birth_datetime values could not be parsed to datetime")

    for col in REQUIRED_NUMERIC:
        if col not in df.columns:
            raise KeyError(f"Dataset missing required column: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[REQUIRED_NUMERIC].isna().any().any():
        raise ValueError("Some latitude/longitude values are NaN after conversion")

    return df


def plot_overlaid_hist(real_vals: List[float], null_vals: List[float], title: str, filename: Path, xlabel: str):
    real_clean = [v for v in real_vals if pd.notnull(v)]
    null_clean = [v for v in null_vals if pd.notnull(v)]
    if not real_clean or not null_clean:
        print(f"Skip plot {filename.name}: insufficient data")
        return
    plt.figure(figsize=(6, 4))
    plt.hist(null_clean, bins=20, alpha=0.7, label="Null mean", color="steelblue", edgecolor="white")
    plt.hist(real_clean, bins=20, alpha=0.7, label="Real", color="orange", edgecolor="white")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Count")
    plt.legend()
    plt.tight_layout()
    filename.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(filename, dpi=150)
    plt.close()


def plot_hist(values: List[float], title: str, filename: Path, xlabel: str):
    clean = [v for v in values if pd.notnull(v)]
    if not clean:
        print(f"Skip plot {filename.name}: insufficient data")
        return
    plt.figure(figsize=(6, 4))
    plt.hist(clean, bins=20, alpha=0.8, color="mediumpurple", edgecolor="white")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Count")
    plt.tight_layout()
    filename.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(filename, dpi=150)
    plt.close()


def plot_scatter(x: List[float], y: List[float], title: str, filename: Path, xlabel: str, ylabel: str):
    clean = [(a, b) for a, b in zip(x, y) if pd.notnull(a) and pd.notnull(b)]
    if not clean:
        print(f"Skip plot {filename.name}: insufficient data")
        return
    xs, ys = zip(*clean)
    plt.figure(figsize=(6, 4))
    plt.scatter(xs, ys, alpha=0.8, color="teal")
    lims = [min(min(xs), min(ys)), max(max(xs), max(ys))]
    plt.plot(lims, lims, "r--", linewidth=1)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    filename.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(filename, dpi=150)
    plt.close()


def main():
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    global DATASET_PATH, REAL_FIELDS_DIR
    DATASET_PATH = Path(args.dataset)
    REAL_FIELDS_DIR = Path(args.fields_dir)

    df = load_dataset()
    subset = select_subjects(df, args.n_subjects).copy()
    grid_points = generate_grid(GRID_STEP_DEG)

    results = []
    use_v2: bool | None = None

    for idx, subj in enumerate(subset.itertuples(index=False), start=1):
        s = subj._asdict()
        sid = s["subject_id"]
        name = s.get("name", "")
        real_path = REAL_FIELDS_DIR / f"subject_{sid}.parquet"
        if not real_path.exists():
            print(f"[{idx}/{len(subset)}] {name} (id={sid}) -> skip (real field missing)")
            continue
        print(f"[{idx}/{len(subset)}] {name} (id={sid})")

        if use_v2 is None:
            sample_df = pd.read_parquet(real_path, columns=None)
            use_v2 = "hf_total_v2" in sample_df.columns
        real_metrics = compute_real_metrics(real_path)
        null_mean, null_std = compute_null_metrics(pd.Series(s), grid_points, args.n_null, rng, use_v2)

        row = {
            "subject_id": sid,
            "RSI_real": real_metrics.rsi,
            "RSI_null_mean": null_mean.rsi,
            "RSI_null_std": null_std.rsi,
            "z_RSI": z_score(real_metrics.rsi, null_mean.rsi, null_std.rsi),
            "range_real": real_metrics.dynamic_range,
            "range_null_mean": null_mean.dynamic_range,
            "range_null_std": null_std.dynamic_range,
            "z_range": z_score(real_metrics.dynamic_range, null_mean.dynamic_range, null_std.dynamic_range),
            "smooth_real": real_metrics.smoothness,
            "smooth_null_mean": null_mean.smoothness,
            "smooth_null_std": null_std.smoothness,
            "z_smooth": z_score(real_metrics.smoothness, null_mean.smoothness, null_std.smoothness),
            "anisotropy_real": real_metrics.anisotropy,
            "anisotropy_null_mean": null_mean.anisotropy,
            "anisotropy_null_std": null_std.anisotropy,
            "z_anisotropy": z_score(real_metrics.anisotropy, null_mean.anisotropy, null_std.anisotropy),
            "variance_real": real_metrics.variance,
            "variance_null_mean": null_mean.variance,
            "variance_null_std": null_std.variance,
            "z_variance": z_score(real_metrics.variance, null_mean.variance, null_std.variance),
        }
        results.append(row)

    if not results:
        print("No subjects processed.")
        return

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    df_out = pd.DataFrame(results)
    df_out.to_csv(OUTPUT_FILE, index=False)

    # Population summary of z-scores
    z_cols = ["z_RSI", "z_range", "z_smooth", "z_anisotropy", "z_variance"]
    summary_rows = []
    for col in z_cols:
        series = df_out[col]
        summary_rows.append(
            {
                "metric": col,
                "mean": series.mean(),
                "median": series.median(),
                "std": series.std(),
            }
        )
    pd.DataFrame(summary_rows).to_csv(SUMMARY_FILE, index=False)

    # Plots: overlay real vs null means
    plot_overlaid_hist(df_out["RSI_real"].tolist(), df_out["RSI_null_mean"].tolist(), "RSI: Real vs Null", PLOTS_DIR / "hist_RSI_real_vs_null.png", "RSI")
    plot_overlaid_hist(df_out["range_real"].tolist(), df_out["range_null_mean"].tolist(), "Range: Real vs Null", PLOTS_DIR / "hist_range_real_vs_null.png", "Dynamic range")
    plot_overlaid_hist(df_out["smooth_real"].tolist(), df_out["smooth_null_mean"].tolist(), "Smoothness: Real vs Null", PLOTS_DIR / "hist_smooth_real_vs_null.png", "Smoothness")
    plot_overlaid_hist(df_out["anisotropy_real"].tolist(), df_out["anisotropy_null_mean"].tolist(), "Anisotropy: Real vs Null", PLOTS_DIR / "hist_anisotropy_real_vs_null.png", "Anisotropy")

    # Z-score hists
    plot_hist(df_out["z_RSI"].tolist(), "z-score RSI", PLOTS_DIR / "hist_z_RSI.png", "z_RSI")
    plot_hist(df_out["z_range"].tolist(), "z-score Range", PLOTS_DIR / "hist_z_range.png", "z_range")
    plot_hist(df_out["z_smooth"].tolist(), "z-score Smooth", PLOTS_DIR / "hist_z_smooth.png", "z_smooth")
    plot_hist(df_out["z_anisotropy"].tolist(), "z-score Anisotropy", PLOTS_DIR / "hist_z_anisotropy.png", "z_anisotropy")

    # Scatter real vs null (RSI)
    plot_scatter(df_out["RSI_null_mean"].tolist(), df_out["RSI_real"].tolist(), "RSI Real vs Null Mean", PLOTS_DIR / "scatter_real_vs_null_RSI.png", "RSI_null_mean", "RSI_real")

    # Console summary
    z_rsi = df_out["z_RSI"].dropna()
    pct_gt1 = 100.0 * (z_rsi > 1).mean() if len(z_rsi) else 0.0
    pct_gt2 = 100.0 * (z_rsi > 2).mean() if len(z_rsi) else 0.0
    print(f"Subjects processed: {len(df_out)}")
    print(f"Mean z_RSI: {z_rsi.mean():.3f}")
    print(f"Median z_RSI: {z_rsi.median():.3f}")
    print(f"% charts with z_RSI > 1: {pct_gt1:.1f}%")
    print(f"% charts with z_RSI > 2: {pct_gt2:.1f}%")
    print(f"Saved results to {OUTPUT_FILE} and summary to {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
