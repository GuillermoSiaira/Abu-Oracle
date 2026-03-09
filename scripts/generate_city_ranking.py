"""Generate top-N city rankings from HF_v3 relocation parquet.

Example:
    python scripts/generate_city_ranking.py \
        --input output/relocation_fields_v3/subject_123.parquet \
        --cities data/external/worldcities.csv \
        --metric hf_total_v3 \
        --top-n 20
"""

from __future__ import annotations

import argparse
import json
from math import radians, sin, cos, asin, sqrt
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd

SUPPORTED_METRICS = {"hf_total_v3", "hf_total_v3_norm"}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def load_cities(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Try to normalize column names
    cols = {c.lower(): c for c in df.columns}
    lat_col = cols.get("lat") or cols.get("latitude")
    lon_col = cols.get("lon") or cols.get("lng") or cols.get("longitude")
    if not lat_col or not lon_col:
        raise KeyError("City file must contain lat/longitude columns")
    city_col = cols.get("city") or cols.get("name") or lat_col
    country_col = cols.get("country") or cols.get("admin_name") or cols.get("iso2")
    df = df.rename(columns={city_col: "city", country_col: "country", lat_col: "lat", lon_col: "lon"})
    return df[["city", "country", "lat", "lon"]]


def compute_normalized(df: pd.DataFrame) -> pd.DataFrame:
    if "hf_total_v3_norm" in df.columns:
        return df
    mean = df["hf_total_v3"].mean()
    std = df["hf_total_v3"].std()
    df = df.copy()
    df["hf_total_v3_norm"] = (df["hf_total_v3"] - mean) / std if std and std > 0 else 0.0
    return df


def nearest_city(lat: float, lon: float, cities: pd.DataFrame) -> Dict[str, object]:
    # vectorized distance
    lat_arr = cities["lat"].values
    lon_arr = cities["lon"].values
    dists = np.vectorize(haversine)(lat, lon, lat_arr, lon_arr)
    idx = int(np.argmin(dists))
    row = cities.iloc[idx]
    return {"city": row["city"], "country": row["country"], "city_lat": float(row["lat"]), "city_lon": float(row["lon"]), "distance_km": float(dists[idx])}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HF_v3 top-N city rankings")
    parser.add_argument("--input", required=True, help="Path to subject parquet (HF_v3)")
    parser.add_argument("--cities", required=True, help="CSV with city locations (lat/lon)")
    parser.add_argument("--metric", default="hf_total_v3", help=f"Metric to rank by ({', '.join(SUPPORTED_METRICS)})")
    parser.add_argument("--top-n", type=int, default=20, help="Number of top locations")
    parser.add_argument("--output-dir", default="output/rankings", help="Directory for JSON output")
    args = parser.parse_args()

    if args.metric not in SUPPORTED_METRICS:
        raise ValueError(f"Unsupported metric {args.metric}")

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(in_path)

    city_path = Path(args.cities)
    if not city_path.exists():
        raise FileNotFoundError(city_path)

    df = pd.read_parquet(in_path)
    df = compute_normalized(df)

    cities = load_cities(city_path)

    # Rank
    top = df.sort_values(args.metric, ascending=False).head(args.top_n)

    rankings: List[Dict[str, object]] = []
    for _, row in top.iterrows():
        nearest = nearest_city(float(row["relocation_latitude"]), float(row["relocation_longitude"]), cities)
        entry = {
            "subject_id": row.get("subject_id"),
            "relocation_latitude": float(row["relocation_latitude"]),
            "relocation_longitude": float(row["relocation_longitude"]),
            "hf_total_v3": float(row["hf_total_v3"]),
            "hf_total_v3_norm": float(row.get("hf_total_v3_norm", float("nan"))),
            "hf_aspects": float(row.get("hf_aspects", float("nan"))),
            "hf_angles": float(row.get("hf_angles", float("nan"))),
            "hf_houses": float(row.get("hf_houses", float("nan"))),
            "asc_lon": float(row.get("asc_lon", float("nan"))),
            "mc_lon": float(row.get("mc_lon", float("nan"))),
            **nearest,
        }
        rankings.append(entry)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subject_id = df.iloc[0].get("subject_id", "unknown")
    out_path = out_dir / f"subject_{subject_id}_ranking.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

    print(f"Saved ranking to {out_path}")


if __name__ == "__main__":
    main()
