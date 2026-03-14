"""Regenerate demo pack at a finer grid resolution (2.5° default).

Recomputes HF relocation fields + deduped city rankings + GeoJSON
for the 10 demo subjects. Overwrites output/demo/{slug}/.

Usage:
    python scripts/regenerate_demo_hires.py [--step 2.5]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, date, time as dt_time, timezone, timedelta
from math import radians, sin, cos, asin, sqrt
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))

from abu_engine.core.chart import chart_json
from abu_engine.core.houses_swiss import HOUSE_SYSTEM_PLACIDUS, calculate_houses
from abu_engine.harmony.field_v3 import compute_hf_v3

# ── Subjects ──────────────────────────────────────────────────────────
DEMO_SUBJECTS = [
    {"id": 308660, "slug": "einstein",   "display": "Albert Einstein",   "rating": "AA"},
    {"id": 12145,  "slug": "borges",     "display": "Jorge Luis Borges", "rating": "AA"},
    {"id": 35255,  "slug": "frida",      "display": "Frida Kahlo",       "rating": "AA"},
    {"id": 76835,  "slug": "picasso",    "display": "Pablo Picasso",     "rating": "AA"},
    {"id": 317785, "slug": "vangogh",    "display": "Vincent Van Gogh",  "rating": "AA"},
    {"id": 337730, "slug": "freud",      "display": "Sigmund Freud",     "rating": "AA"},
    {"id": 366580, "slug": "jung",       "display": "Carl Gustav Jung",  "rating": "A"},
    {"id": 61360,  "slug": "gandhi",     "display": "Mohandas Gandhi",   "rating": "A"},
    {"id": 357700, "slug": "tesla",      "display": "Nikola Tesla",      "rating": "B"},
    {"id": 232650, "slug": "bowie",      "display": "David Bowie",       "rating": "A"},
]

DATASET_PATH = REPO_ROOT / "data" / "processed" / "hf_dataset_v2.parquet"
CITIES_PATH  = REPO_ROOT / "data" / "external" / "worldcities.csv"
DEMO_DIR     = REPO_ROOT / "output" / "demo"
PUBLIC_DIR   = REPO_ROOT / "next_app" / "public" / "demo"

TOP_N = 20


def _scalar(v: Any) -> Any:
    if pd.isna(v):
        return None
    try:
        return v.item()
    except Exception:
        return v


# ── Grid generation ───────────────────────────────────────────────────
def make_grid(step: float) -> List[Tuple[float, float]]:
    lats = np.arange(-80, 80 + step / 2, step)
    lons = np.arange(-180, 180 + step / 2, step)
    return [(float(lat), float(lon)) for lat in lats for lon in lons]


# ── HF computation ───────────────────────────────────────────────────
def compute_field(birth_dt: datetime, natal_lat: float, natal_lon: float,
                  grid: List[Tuple[float, float]]) -> Tuple[Dict[str, float], List[dict]]:
    """Compute natal HF + full relocation grid. Returns (natal_metrics, rows)."""
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=timezone.utc)

    chart = chart_json(natal_lat, natal_lon, birth_dt)
    planet_pos = {p.name: float(p.lon) for p in chart.planets}

    # Natal HF
    natal_houses = calculate_houses(birth_dt, natal_lat, natal_lon, HOUSE_SYSTEM_PLACIDUS)
    natal_angles = dict(planet_pos)
    natal_angles["ASC"] = float(natal_houses["asc"])
    natal_angles["MC"] = float(natal_houses["mc"])
    natal_cusps = list(natal_houses["cusps"])
    natal_hf = compute_hf_v3(natal_angles, cusps=natal_cusps)
    natal_total = float(natal_hf["hf_total_v3"])

    rows = []
    for i, (rlat, rlon) in enumerate(grid):
        try:
            h = calculate_houses(birth_dt, rlat, rlon, HOUSE_SYSTEM_PLACIDUS)
            cusps = list(h["cusps"])
            angles = dict(planet_pos)
            angles["ASC"] = float(h["asc"])
            angles["MC"] = float(h["mc"])
            hf = compute_hf_v3(angles, cusps=cusps)
            total = float(hf["hf_total_v3"])
            rows.append({
                "lat": rlat, "lon": rlon,
                "hf_total": round(total, 4),
                "delta_hf": round(total - natal_total, 4),
                "hf_aspects": round(float(hf["hf_aspects"]), 4),
                "hf_angles": round(float(hf["hf_angles"]), 4),
                "hf_houses": round(float(hf["hf_houses"]), 4),
                "asc_lon": round(float(h["asc"]), 4),
                "mc_lon": round(float(h["mc"]), 4),
            })
        except Exception:
            rows.append({
                "lat": rlat, "lon": rlon,
                "hf_total": natal_total, "delta_hf": 0.0,
                "hf_aspects": 0, "hf_angles": 0, "hf_houses": 0,
                "asc_lon": 0, "mc_lon": 0,
            })

        if (i + 1) % 2000 == 0 or (i + 1) == len(grid):
            print(f"      grid {i+1}/{len(grid)}")

    natal_metrics = {
        "hf_total_v3": natal_total,
        "hf_aspects": float(natal_hf["hf_aspects"]),
        "hf_angles": float(natal_hf["hf_angles"]),
        "hf_houses": float(natal_hf["hf_houses"]),
    }
    return natal_metrics, rows


# ── GeoJSON builder ──────────────────────────────────────────────────
def build_geojson(rows: List[dict], subject_id, name, natal_lat, natal_lon) -> dict:
    features = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
        "properties": {k: r[k] for k in ("hf_total", "delta_hf", "hf_aspects", "hf_angles", "hf_houses")},
    } for r in rows]

    return {
        "type": "FeatureCollection",
        "properties": {
            "subject_id": subject_id,
            "name": name,
            "natal_latitude": natal_lat,
            "natal_longitude": natal_lon,
        },
        "features": features,
    }


# ── Deduped ranking ─────────────────────────────────────────────────
def load_cities():
    df = pd.read_csv(CITIES_PATH)
    return df["lat"].values, df["lon"].values, df["city"].tolist(), df["country"].tolist()


def make_ranking(rows: List[dict], subject_id, c_lat, c_lon, c_names, c_countries) -> List[dict]:
    sorted_rows = sorted(rows, key=lambda r: r["hf_total"], reverse=True)
    candidates = sorted_rows[:TOP_N * 5]

    seen: dict[str, dict] = {}
    for r in candidates:
        dlat = np.radians(c_lat - r["lat"])
        dlon = np.radians(c_lon - r["lon"])
        a = np.sin(dlat/2)**2 + np.cos(np.radians(r["lat"])) * np.cos(np.radians(c_lat)) * np.sin(dlon/2)**2
        dist = 6371.0 * 2 * np.arcsin(np.sqrt(a))
        idx = int(np.argmin(dist))
        city_key = f"{c_names[idx]}|{c_countries[idx]}"

        if city_key in seen and seen[city_key]["hf_total_v3"] >= r["hf_total"]:
            continue

        seen[city_key] = {
            "subject_id": str(subject_id),
            "relocation_latitude": r["lat"],
            "relocation_longitude": r["lon"],
            "hf_total_v3": r["hf_total"],
            "hf_aspects": r["hf_aspects"],
            "hf_angles": r["hf_angles"],
            "hf_houses": r["hf_houses"],
            "asc_lon": r["asc_lon"],
            "mc_lon": r["mc_lon"],
            "city": c_names[idx],
            "country": c_countries[idx],
            "city_lat": float(c_lat[idx]),
            "city_lon": float(c_lon[idx]),
            "distance_km": round(float(dist[idx]), 2),
        }

    return sorted(seen.values(), key=lambda x: x["hf_total_v3"], reverse=True)[:TOP_N]


# ── Main ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Regenerate demo pack at higher resolution")
    parser.add_argument("--step", type=float, default=2.5, help="Grid step in degrees (default: 2.5)")
    args = parser.parse_args()
    step = args.step

    print(f"Loading dataset from {DATASET_PATH}...")
    ds = pd.read_parquet(DATASET_PATH)
    if "subject_id" not in ds.columns and "id" in ds.columns:
        ds["subject_id"] = ds["id"]

    # Build birth_datetime from separate columns if needed
    if "birth_datetime" not in ds.columns:
        demo_ids = {s["id"] for s in DEMO_SUBJECTS}
        ds_demo = ds[ds["subject_id"].isin(demo_ids)].copy()
        print(f"  Building birth_datetime for {len(ds_demo)} demo subjects...")
        tz_re = re.compile(r"^[+-]?\d{1,2}:\d{2}:\d{2}$")
        dts = []
        for _, r in ds_demo.iterrows():
            d = datetime.strptime(str(r["birth_date"]), "%Y-%m-%d").date()
            t = datetime.strptime(str(r["birth_time"]), "%H:%M:%S").time()
            tz_str = str(r["timezone"]).strip()
            if tz_re.match(tz_str):
                sign = -1 if tz_str.startswith("-") else 1
                hh, mm, ss = map(int, tz_str.lstrip("+-").split(":"))
                tz = timezone(timedelta(seconds=sign * (hh*3600 + mm*60 + ss)))
            else:
                tz = timezone.utc
            dts.append(datetime.combine(d, t, tzinfo=tz).astimezone(timezone.utc))
        ds_demo["birth_datetime"] = dts
        ds = ds_demo

    grid = make_grid(step)
    print(f"Grid: step={step}°, {len(grid)} points")

    print(f"Loading cities from {CITIES_PATH}...")
    c_lat, c_lon, c_names, c_countries = load_cities()
    print(f"  {len(c_lat)} cities loaded")

    index_entries = []
    t0 = time.time()

    for i, subj in enumerate(DEMO_SUBJECTS):
        sid = subj["id"]
        slug = subj["slug"]
        row = ds[ds["subject_id"] == sid]
        if row.empty:
            print(f"  SKIP {slug}: not found in dataset (id={sid})")
            continue

        row = row.iloc[0]
        birth_dt = pd.Timestamp(row["birth_datetime"]).to_pydatetime()
        natal_lat = float(row["latitude"])
        natal_lon = float(row["longitude"])

        print(f"\n[{i+1}/{len(DEMO_SUBJECTS)}] {subj['display']} ({slug})")
        print(f"    birth={birth_dt.isoformat()} lat={natal_lat:.2f} lon={natal_lon:.2f}")

        # Compute field
        natal_metrics, field_rows = compute_field(birth_dt, natal_lat, natal_lon, grid)
        natal_hf = natal_metrics["hf_total_v3"]

        # Build GeoJSON
        geojson = build_geojson(field_rows, sid, subj["display"], natal_lat, natal_lon)

        # Build ranking (deduped)
        ranking = make_ranking(field_rows, sid, c_lat, c_lon, c_names, c_countries)

        # Write to output/demo/{slug}/
        out_dir = DEMO_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)

        (out_dir / "geojson.json").write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
        (out_dir / "ranking.json").write_text(json.dumps(ranking, indent=2, ensure_ascii=False), encoding="utf-8")

        # Preserve existing narrative if present
        narr_path = out_dir / "narrative.json"
        has_narrative = narr_path.exists()

        hf_values = [r["hf_total"] for r in field_rows]
        max_hf = max(hf_values)
        min_hf = min(hf_values)

        entry = {
            "id": sid,
            "slug": slug,
            "display_name": subj["display"],
            "rodden_rating": subj["rating"],
            "birth_datetime": birth_dt.isoformat(),
            "natal_lat": natal_lat,
            "natal_lon": natal_lon,
            "natal_hf": round(natal_hf, 4),
            "max_hf": round(max_hf, 4),
            "min_hf": round(min_hf, 4),
            "grid_points": len(field_rows),
            "grid_step_deg": step,
            "has_geojson": True,
            "has_ranking": len(ranking) > 0,
            "has_narrative": has_narrative,
        }
        index_entries.append(entry)

        geojson_kb = len(json.dumps(geojson)) / 1024
        print(f"    OK — HF [{min_hf:.2f}, {max_hf:.2f}], natal={natal_hf:.2f}, "
              f"grid={len(field_rows)}, ranking={len(ranking)} cities, geojson={geojson_kb:.0f}KB")

    # Write index.json
    index = {
        "version": "2.0",
        "generated": pd.Timestamp.now().isoformat(),
        "description": f"Demo pack: {len(index_entries)} subjects at {step}° grid resolution",
        "grid_step_deg": step,
        "subjects": index_entries,
    }
    (DEMO_DIR / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s — {len(index_entries)} subjects regenerated at {step}°")
    print(f"Grid: {len(grid)} points per subject")

    # Sync to public/demo/
    if PUBLIC_DIR.exists():
        import shutil
        for subj in DEMO_SUBJECTS:
            src = DEMO_DIR / subj["slug"]
            dst = PUBLIC_DIR / subj["slug"]
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
        # Copy index
        shutil.copy2(DEMO_DIR / "index.json", PUBLIC_DIR / "index.json")
        print(f"Synced to {PUBLIC_DIR}")


if __name__ == "__main__":
    main()
