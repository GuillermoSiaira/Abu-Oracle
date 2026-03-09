"""Analyze population-level metrics for relocation HF fields.

Usage:
    python scripts/analyze_population_metrics.py

Outputs:
    analysis/relocation_metrics_summary.csv
    analysis/plots/hist_*.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INPUT_FILE = Path("analysis/relocation_metrics.csv")
SUMMARY_FILE = Path("analysis/relocation_metrics_summary.csv")
PLOTS_DIR = Path("analysis/plots")

HIST_METRICS = ["rsi", "dynamic_range", "natal_rank", "anisotropy"]


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [col for col in df.columns if col != "subject"]
    rows = []
    for metric in metrics:
        series = df[metric]
        rows.append(
            {
                "metric": metric,
                "mean": series.mean(),
                "std": series.std(),
                "min": series.min(),
                "max": series.max(),
            }
        )
    return pd.DataFrame(rows)


def plot_histograms(df: pd.DataFrame, plots_dir: Path = PLOTS_DIR) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)
    for metric in HIST_METRICS:
        series = df[metric]
        plt.figure(figsize=(6, 4))
        plt.hist(series, bins=20, color="steelblue", alpha=0.8, edgecolor="white")
        plt.title(f"Distribution of {metric}")
        plt.xlabel(metric)
        plt.ylabel("Count")
        plt.tight_layout()
        out_path = plots_dir / f"hist_{metric}.png"
        plt.savefig(out_path, dpi=150)
        plt.close()
        print(f"Saved {out_path}")


def main():
    if not INPUT_FILE.exists():
        raise SystemExit(f"Metrics file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)
    summary = compute_summary(df)

    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_FILE, index=False)
    print(f"Saved summary to {SUMMARY_FILE}")

    plot_histograms(df)


if __name__ == "__main__":
    main()
