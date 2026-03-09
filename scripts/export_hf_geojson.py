from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd


def _scalar(value: Any) -> Any:
    """Convert numpy/pandas scalars to native Python types for JSON."""
    if pd.isna(value):
        return None
    try:
        # numpy / pandas scalars implement .item()
        return value.item()
    except Exception:
        return value


def build_feature_collection(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        raise ValueError("Input dataframe is empty")

    subject_id = _scalar(df.iloc[0].get("subject_id", "unknown"))
    name = _scalar(df.iloc[0].get("name", ""))
    natal_lat = _scalar(df.iloc[0].get("natal_latitude"))
    natal_lon = _scalar(df.iloc[0].get("natal_longitude"))

    features = []
    for _, row in df.iterrows():
        lat = float(row["relocation_latitude"])
        lon = float(row["relocation_longitude"])
        delta = float(row.get("delta_hf_total_v3", float("nan")))
        total = float(row.get("hf_total_v3", float("nan")))
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "delta_hf": delta,
                "hf_total": total,
            },
        }
        features.append(feature)

    fc: Dict[str, Any] = {
        "type": "FeatureCollection",
        "properties": {
            "subject_id": subject_id,
            "name": name,
            "natal_latitude": float(natal_lat) if natal_lat is not None else None,
            "natal_longitude": float(natal_lon) if natal_lon is not None else None,
        },
        "features": features,
    }
    return fc


def main() -> None:
    parser = argparse.ArgumentParser(description="Export HF_v3 Parquet to GeoJSON for interactive maps")
    parser.add_argument("--input", required=True, help="Path to subject parquet (HF_v3)")
    parser.add_argument("--output-dir", default="output/geojson", help="Directory to write GeoJSON")
    parser.add_argument("--public-dir", default=None, help="Optional directory to copy GeoJSON for frontend (e.g., next_app/public/geojson)")
    parser.add_argument("--ranking", default=None, help="Optional ranking JSON to copy alongside (top cities)")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(in_path)

    df = pd.read_parquet(in_path)
    required_cols = {"relocation_latitude", "relocation_longitude", "delta_hf_total_v3", "hf_total_v3"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise KeyError(f"Missing required columns in parquet: {missing}")

    fc = build_feature_collection(df)

    subject_id = fc.get("properties", {}).get("subject_id", in_path.stem.replace("subject_", ""))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"subject_{subject_id}_hf.geojson"
    out_path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print(f"Saved GeoJSON to {out_path}")

    # Optional copy to public dir
    if args.public_dir:
        pub_dir = Path(args.public_dir)
        pub_dir.mkdir(parents=True, exist_ok=True)
        pub_path = pub_dir / out_path.name
        pub_path.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Copied GeoJSON to {pub_path}")

        if args.ranking:
            r_path = Path(args.ranking)
            if not r_path.exists():
                raise FileNotFoundError(r_path)
            rankings_dir = pub_dir.parent / "rankings"
            rankings_dir.mkdir(parents=True, exist_ok=True)
            dst_rank = rankings_dir / r_path.name
            dst_rank.write_text(r_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Copied ranking to {dst_rank}")


if __name__ == "__main__":
    main()
