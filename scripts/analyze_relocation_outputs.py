"""Analyze relocation field outputs and emit summary stats.

Usage:
  python scripts/analyze_relocation_outputs.py
"""

from pathlib import Path
import pandas as pd
import numpy as np


def main():
    root = Path("output/relocation_fields")
    files = sorted(root.glob("subject_*.parquet"))
    print(f"Found {len(files)} parquet files")
    if not files:
        raise SystemExit("No files found")

    all_df = pd.concat([pd.read_parquet(fp).assign(__file=fp.name) for fp in files], ignore_index=True)

    expected = [
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

    missing = [c for c in expected if c not in all_df.columns]
    extra = [c for c in all_df.columns if c not in expected + ["__file"]]
    print("Missing columns:", missing)
    print("Extra columns:", extra)

    counts = all_df.groupby("subject_id").size()
    print("Rows per subject:")
    print(counts)

    valid_pct = 100.0 * (all_df["valid_flag"] == True).mean()
    invalid_pct = 100 - valid_pct
    print(f"Valid rows %: {valid_pct:.3f}, Invalid rows %: {invalid_pct:.3f}")
    err_bd = all_df[all_df["valid_flag"] == False]["error_type"].value_counts(dropna=False)
    print("Error breakdown:")
    print(err_bd)

    abs_delta = all_df["delta_hf_total"].abs()
    metrics_all = {
        "mean_abs": abs_delta.mean(),
        "std": all_df["delta_hf_total"].std(),
        "max_abs": abs_delta.max(),
        "p95_abs": abs_delta.quantile(0.95),
    }
    print("Aggregate delta_hf_total metrics:")
    for k, v in metrics_all.items():
        print(f"  {k}: {v}")

    summary_rows = []
    for sid, g in all_df.groupby("subject_id"):
        abs_d = g["delta_hf_total"].abs()
        summary_rows.append(
            {
                "subject_id": sid,
                "rows": len(g),
                "valid_rows": int(g["valid_flag"].sum()),
                "invalid_rows": int((~g["valid_flag"]).sum()),
                "mean_abs_delta_hf_total": abs_d.mean(),
                "max_abs_delta_hf_total": abs_d.max(),
                "std_delta_hf_total": g["delta_hf_total"].std(),
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values("subject_id")
    out_path = root / "relocation_fields_summary.csv"
    summary_df.to_csv(out_path, index=False)
    print(f"Summary saved to {out_path}")

    print("Per-subject delta_hf_total metrics:")
    for r in summary_rows:
        print(
            f"  subject {r['subject_id']}: mean_abs={r['mean_abs_delta_hf_total']:.4f}, "
            f"std={r['std_delta_hf_total']:.4f}, max_abs={r['max_abs_delta_hf_total']:.4f}"
        )

    verdict = "All rows valid" if (all_df["valid_flag"] == True).all() else "Some rows invalid"
    print("Verdict:", verdict)


if __name__ == "__main__":
    main()