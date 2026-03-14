"""Tarea 3.2 — Exportar grillas de dominio a GeoJSON multi-propiedad.

Lee output/relocation_fields_domain/{slug}_domains.parquet
y produce un GeoJSON con todas las propiedades de dominio por Feature:
  hf_global, hf_h1, hf_h4, hf_h7, hf_h10,
  delta_global, delta_h1, delta_h4, delta_h7, delta_h10

Output por sujeto:
  output/demo/{slug}/geojson_domains.json
  next_app/public/geojson/{slug}_domains.geojson  (copia pública)

Uso:
    .venv/Scripts/python.exe scripts/export_hf_domain_geojson.py [--subjects frida einstein]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

REPO_ROOT     = Path(__file__).resolve().parent.parent
DOMAINS_DIR   = REPO_ROOT / "output" / "relocation_fields_domain"
DEMO_DIR      = REPO_ROOT / "output" / "demo"
PUBLIC_DIR    = REPO_ROOT / "next_app" / "public" / "geojson"
DEMO_INDEX    = DEMO_DIR / "index.json"

DOMAIN_COLS   = ["global", "h1", "h2", "h4", "h5", "h6", "h7", "h9", "h10"]


def _safe(v: Any) -> Any:
    """Convert to JSON-serializable Python scalar."""
    try:
        if np.isnan(v):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return v.item()
    except AttributeError:
        return v


def _compute_domain_scales(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute p5/p95 for each delta column — used as heatmap color stops."""
    scales: Dict[str, Any] = {}
    for col in DOMAIN_COLS:
        key = f"delta_{col}"
        if key in df.columns:
            vals = df[key].dropna()
            scales[key] = {
                "p5":  round(float(np.percentile(vals, 5)),  4),
                "p95": round(float(np.percentile(vals, 95)), 4),
            }
    return scales


def build_domain_geojson(df: pd.DataFrame, meta: dict) -> dict:
    """Build multi-property FeatureCollection from domains parquet."""
    features: List[dict] = []
    for _, row in df.iterrows():
        props: Dict[str, Any] = {}
        for col in DOMAIN_COLS:
            props[f"hf_{col}"]    = _safe(row.get(f"hf_{col}"))
            props[f"delta_{col}"] = _safe(row.get(f"delta_{col}"))

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["lon"]), float(row["lat"])],
            },
            "properties": props,
        })

    return {
        "type": "FeatureCollection",
        "properties": {
            "subject_id":      meta.get("id"),
            "name":            meta.get("display_name", meta.get("slug")),
            "natal_latitude":  meta.get("natal_lat"),
            "natal_longitude": meta.get("natal_lon"),
            "domains":         DOMAIN_COLS,
        },
        "domain_scales": _compute_domain_scales(df),
        "features": features,
    }


def export_subject(slug: str, meta: dict) -> None:
    parquet_path = DOMAINS_DIR / f"{slug}_domains.parquet"
    if not parquet_path.exists():
        print(f"  SKIP {slug}: {parquet_path.name} not found — run generate_hf_domain_grids.py first")
        return

    df = pd.read_parquet(parquet_path)
    fc = build_domain_geojson(df, meta)

    # ── output/demo/{slug}/geojson_domains.json ──────────────────────
    demo_slug_dir = DEMO_DIR / slug
    demo_slug_dir.mkdir(parents=True, exist_ok=True)
    demo_path = demo_slug_dir / "geojson_domains.json"
    demo_path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")

    # ── next_app/public/geojson/{slug}_domains.geojson ───────────────
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    pub_path = PUBLIC_DIR / f"{slug}_domains.geojson"
    pub_path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")

    kb_demo = demo_path.stat().st_size // 1024
    kb_pub  = pub_path.stat().st_size // 1024
    print(f"  {slug}: {len(df)} pts ->demo={kb_demo}KB  public={kb_pub}KB")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", nargs="*", default=None,
                        help="Slugs to export (default: all subjects with parquet)")
    args = parser.parse_args()

    index = json.loads(DEMO_INDEX.read_text(encoding="utf-8"))
    subjects = index["subjects"]
    if args.subjects:
        subjects = [s for s in subjects if s["slug"] in args.subjects]

    print(f"Exporting {len(subjects)} subjects...")
    for subj in subjects:
        export_subject(subj["slug"], subj)

    print(f"\nDemo output   : {DEMO_DIR}/<slug>/geojson_domains.json")
    print(f"Public output : {PUBLIC_DIR}/<slug>_domains.geojson")


if __name__ == "__main__":
    main()
