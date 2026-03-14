"""Batch-generate top-N city rankings for ALL subjects.

Reads every parquet in output/relocation_fields/, finds the nearest
real city (from worldcities.csv, 144K+ GeoNames places) for each
top grid point, and writes a JSON ranking to output/rankings/.

Usage:
    python scripts/batch_rankings.py [--top-n 20] [--skip-existing]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from math import radians, sin, cos, asin, sqrt
from pathlib import Path

import numpy as np
import pandas as pd


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * asin(sqrt(a))


def load_cities(path: Path) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Load cities into numpy arrays for fast vectorized lookup."""
    df = pd.read_csv(path)
    return (
        df["lat"].values.astype(np.float64),
        df["lon"].values.astype(np.float64),
        df["city"].tolist(),
        df["country"].tolist(),
    )


def nearest_city(lat: float, lon: float,
                 c_lat: np.ndarray, c_lon: np.ndarray,
                 c_names: list[str], c_countries: list[str]) -> dict:
    """Find nearest city using vectorized haversine."""
    dlat = np.radians(c_lat - lat)
    dlon = np.radians(c_lon - lon)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(c_lat)) * np.sin(dlon / 2) ** 2
    dist_km = 6371.0 * 2 * np.arcsin(np.sqrt(a))
    idx = int(np.argmin(dist_km))
    return {
        "city": c_names[idx],
        "country": c_countries[idx],
        "city_lat": float(c_lat[idx]),
        "city_lon": float(c_lon[idx]),
        "distance_km": round(float(dist_km[idx]), 2),
    }


def process_subject(parquet_path: Path, top_n: int,
                    c_lat: np.ndarray, c_lon: np.ndarray,
                    c_names: list[str], c_countries: list[str],
                    out_dir: Path) -> bool:
    """Process one subject parquet and write ranking JSON. Returns True if OK."""
    df = pd.read_parquet(parquet_path)

    # Detect lat/lon column names
    lat_col = "relocation_latitude" if "relocation_latitude" in df.columns else "lat"
    lon_col = "relocation_longitude" if "relocation_longitude" in df.columns else "lon"

    metric = "hf_total_v3"
    if metric not in df.columns:
        return False

    top = df.sort_values(metric, ascending=False).head(top_n)

    # Extract subject_id from filename
    stem = parquet_path.stem  # e.g. "subject_1234"
    subject_id = stem.replace("subject_", "")

    # Gather more candidates than top_n so dedup still yields enough unique cities
    candidates = df.sort_values(metric, ascending=False).head(top_n * 5)

    seen_cities: dict[str, dict] = {}  # city_key → best entry
    for _, row in candidates.iterrows():
        rlat, rlon = float(row[lat_col]), float(row[lon_col])
        nc = nearest_city(rlat, rlon, c_lat, c_lon, c_names, c_countries)
        city_key = f"{nc['city']}|{nc['country']}"
        hf_val = float(row[metric])

        if city_key in seen_cities and seen_cities[city_key]["hf_total_v3"] >= hf_val:
            continue  # already have a better grid point for this city

        seen_cities[city_key] = {
            "subject_id": subject_id,
            "relocation_latitude": rlat,
            "relocation_longitude": rlon,
            "hf_total_v3": hf_val,
            "hf_aspects": float(row.get("hf_aspects", float("nan"))),
            "hf_angles": float(row.get("hf_angles", float("nan"))),
            "hf_houses": float(row.get("hf_houses", float("nan"))),
            "asc_lon": float(row.get("asc_lon", float("nan"))),
            "mc_lon": float(row.get("mc_lon", float("nan"))),
            **nc,
        }

    rankings = sorted(seen_cities.values(), key=lambda x: x["hf_total_v3"], reverse=True)[:top_n]

    out_path = out_dir / f"subject_{subject_id}_ranking.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch generate city rankings")
    parser.add_argument("--top-n", type=int, default=20, help="Top N locations per subject")
    parser.add_argument("--skip-existing", action="store_true", help="Skip subjects that already have rankings")
    parser.add_argument("--input-dir", default="output/relocation_fields", help="Directory with subject parquets")
    parser.add_argument("--cities", default="data/external/worldcities.csv", help="Cities CSV")
    parser.add_argument("--output-dir", default="output/rankings", help="Output directory for JSONs")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    parquets = sorted(in_dir.glob("*.parquet"))
    print(f"Found {len(parquets)} parquet files in {in_dir}")

    if args.skip_existing:
        existing = {p.stem.replace("_ranking", "") for p in out_dir.glob("*_ranking.json")}
        parquets = [p for p in parquets if p.stem not in existing]
        print(f"After skipping existing: {len(parquets)} to process")

    print(f"Loading cities from {args.cities}...")
    c_lat, c_lon, c_names, c_countries = load_cities(Path(args.cities))
    print(f"  {len(c_lat)} cities loaded")

    ok = 0
    fail = 0
    t0 = time.time()

    for i, pq in enumerate(parquets):
        if process_subject(pq, args.top_n, c_lat, c_lon, c_names, c_countries, out_dir):
            ok += 1
        else:
            fail += 1
            print(f"  SKIP {pq.name}: missing hf_total_v3 column")

        if (i + 1) % 500 == 0 or (i + 1) == len(parquets):
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{i+1}/{len(parquets)}] {ok} OK, {fail} failed | {rate:.1f} files/sec")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s — {ok} rankings generated, {fail} failed")


if __name__ == "__main__":
    main()
