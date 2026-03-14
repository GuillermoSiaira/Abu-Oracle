"""
Generate demo pack: GeoJSON + ranking + metadata for 10 curated subjects.

Usage:
    python scripts/generate_demo_pack.py

Output:
    output/demo/
        index.json              — manifest with all demo subjects
        {slug}/
            geojson.json        — HF field for map rendering
            ranking.json        — top 20 cities
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

# ── Demo subjects ──────────────────────────────────────────────────────
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

ROOT = Path(__file__).resolve().parent.parent
RELOC_DIR = ROOT / "output" / "relocation_fields"
RANK_DIR = ROOT / "output" / "rankings"
DEMO_DIR = ROOT / "output" / "demo"


def _scalar(value: Any) -> Any:
    if pd.isna(value):
        return None
    try:
        return value.item()
    except Exception:
        return value


def build_geojson(df: pd.DataFrame) -> dict:
    """Build GeoJSON FeatureCollection from a relocation parquet DataFrame."""
    subject_id = _scalar(df.iloc[0].get("subject_id", "unknown"))
    name = _scalar(df.iloc[0].get("name", ""))
    natal_lat = _scalar(df.iloc[0].get("natal_latitude"))
    natal_lon = _scalar(df.iloc[0].get("natal_longitude"))

    features = []
    for _, row in df.iterrows():
        lat = float(row["relocation_latitude"])
        lon = float(row["relocation_longitude"])
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "hf_total": round(float(row["hf_total_v3"]), 4),
                "delta_hf": round(float(row.get("delta_hf_total_v3", float("nan"))), 4),
                "hf_aspects": round(float(row.get("hf_aspects", 0)), 4),
                "hf_angles": round(float(row.get("hf_angles", 0)), 4),
                "hf_houses": round(float(row.get("hf_houses", 0)), 4),
            },
        })

    return {
        "type": "FeatureCollection",
        "properties": {
            "subject_id": subject_id,
            "name": name,
            "natal_latitude": float(natal_lat) if natal_lat is not None else None,
            "natal_longitude": float(natal_lon) if natal_lon is not None else None,
        },
        "features": features,
    }


def process_subject(subj: dict) -> dict | None:
    """Generate GeoJSON + copy ranking for one subject. Returns index entry."""
    sid = subj["id"]
    slug = subj["slug"]
    out_dir = DEMO_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Parquet → GeoJSON ──
    pq_path = RELOC_DIR / f"subject_{sid}.parquet"
    if not pq_path.exists():
        print(f"  SKIP {slug}: no parquet at {pq_path}")
        return None

    df = pd.read_parquet(pq_path)
    fc = build_geojson(df)
    geojson_path = out_dir / "geojson.json"
    geojson_path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")

    # ── Ranking ──
    rk_path = RANK_DIR / f"subject_{sid}_ranking.json"
    ranking_path = out_dir / "ranking.json"
    if rk_path.exists():
        shutil.copy2(rk_path, ranking_path)
    else:
        print(f"  WARN {slug}: no ranking at {rk_path}")

    # ── Extract metadata from parquet ──
    row0 = df.iloc[0]
    birth_datetime = _scalar(row0.get("birth_datetime", ""))
    natal_lat = _scalar(row0.get("natal_latitude"))
    natal_lon = _scalar(row0.get("natal_longitude"))

    # natal HF (the row where relocation == natal coords, or row with delta~0)
    natal_hf = float(df.loc[df["delta_hf_total_v3"].abs().idxmin(), "hf_total_v3"])
    max_hf = float(df["hf_total_v3"].max())
    min_hf = float(df["hf_total_v3"].min())

    entry = {
        "id": sid,
        "slug": slug,
        "display_name": subj["display"],
        "rodden_rating": subj["rating"],
        "birth_datetime": birth_datetime,
        "natal_lat": float(natal_lat) if natal_lat is not None else None,
        "natal_lon": float(natal_lon) if natal_lon is not None else None,
        "natal_hf": round(natal_hf, 4),
        "max_hf": round(max_hf, 4),
        "min_hf": round(min_hf, 4),
        "grid_points": len(df),
        "has_geojson": True,
        "has_ranking": rk_path.exists(),
        "has_narrative": False,  # will be set when Lilly generates narratives
    }
    return entry


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    index_entries = []

    print(f"Generating demo pack for {len(DEMO_SUBJECTS)} subjects...")
    for subj in DEMO_SUBJECTS:
        print(f"  Processing {subj['slug']} (id={subj['id']})...")
        entry = process_subject(subj)
        if entry:
            index_entries.append(entry)
            print(f"    OK — HF range [{entry['min_hf']:.2f}, {entry['max_hf']:.2f}], natal={entry['natal_hf']:.2f}")

    # ── Write index ──
    index = {
        "version": "1.0",
        "generated": pd.Timestamp.now().isoformat(),
        "description": "Demo pack: 10 curated subjects with GeoJSON + rankings for HF relocation visualization",
        "subjects": index_entries,
    }
    index_path = DEMO_DIR / "index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone! {len(index_entries)} subjects in {DEMO_DIR}")
    print(f"Index: {index_path}")


if __name__ == "__main__":
    main()
