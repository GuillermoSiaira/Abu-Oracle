"""Tarea 3.1 — Generar grillas HF por dominio de casa para todos los sujetos demo.

Por cada sujeto × {global, h1, h4, h7, h10}:
  1. Calcula los significadores de la casa para esa carta natal
  2. Computa HF(lat, lon) para cada punto de la grilla con planet_subset
  3. Guarda el resultado en output/relocation_fields_domain/{slug}_domains.parquet

Columnas del parquet:
  lat, lon, hf_global, hf_h1, hf_h4, hf_h7, hf_h10,
  delta_global, delta_h1, delta_h4, delta_h7, delta_h10

Uso:
    .venv/Scripts/python.exe scripts/generate_hf_domain_grids.py [--step 5.0]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))

from core.chart import chart_json
from core.houses_swiss import HOUSE_SYSTEM_PLACIDUS, calculate_houses
from harmony.field_v3 import compute_hf_v3
from harmony.houses import house_significators

DEMO_INDEX  = REPO_ROOT / "output" / "demo" / "index.json"
OUTPUT_DIR  = REPO_ROOT / "output" / "relocation_fields_domain"

# Domains to generate: house number (0 = global)
DOMAINS: List[int] = [0, 1, 2, 4, 5, 6, 7, 9, 10]   # 0 → global (no planet_subset)
DOMAIN_LABEL: Dict[int, str] = {0: "global", 1: "h1", 2: "h2", 4: "h4", 5: "h5", 6: "h6", 7: "h7", 9: "h9", 10: "h10"}


def make_grid(step: float) -> List[Tuple[float, float]]:
    lats = np.arange(-80, 80 + step / 2, step)
    lons = np.arange(-180, 180 + step / 2, step)
    return [(float(la), float(lo)) for la in lats for lo in lons]


def _parse_birth_dt(dt_str: str) -> datetime:
    from datetime import timezone
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def build_natal_data_for_sig(planet_pos: Dict[str, float], natal_cusps: List[float]) -> dict:
    return {
        "planets": [{"name": k, "longitude": v} for k, v in planet_pos.items()],
        "houses": [{"num": i + 1, "longitude": c} for i, c in enumerate(natal_cusps)],
    }


def compute_subject_domains(
    birth_dt: datetime,
    natal_lat: float,
    natal_lon: float,
    grid: List[Tuple[float, float]],
    verbose: bool = True,
) -> pd.DataFrame:
    """Compute relocation grid with all domain HFs. Returns combined DataFrame."""
    from datetime import timezone
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=timezone.utc)

    # ── Natal chart (fixed positions, vary ASC/MC) ────────────────────
    chart = chart_json(natal_lat, natal_lon, birth_dt)
    planet_pos: Dict[str, float] = {p.name: float(p.lon) for p in chart.planets}

    natal_houses = calculate_houses(birth_dt, natal_lat, natal_lon, HOUSE_SYSTEM_PLACIDUS)
    natal_cusps = list(natal_houses["cusps"])
    natal_data_for_sig = build_natal_data_for_sig(planet_pos, natal_cusps)

    # ── Significators per domain (computed once, fixed for subject) ───
    sigs: Dict[int, Optional[List[str]]] = {}
    for h in DOMAINS:
        if h == 0:
            sigs[h] = None   # global: no filter
        else:
            s = house_significators(natal_data_for_sig, h)
            sigs[h] = s if s else None
            if verbose:
                label = DOMAIN_LABEL[h]
                print(f"    {label}: {s}")

    # ── Natal HF per domain (baseline for delta) ─────────────────────
    natal_angles = dict(planet_pos)
    natal_angles["ASC"] = float(natal_houses["asc"])
    natal_angles["MC"] = float(natal_houses["mc"])

    natal_hfs: Dict[int, float] = {}
    for h in DOMAINS:
        natal_hfs[h] = compute_hf_v3(
            natal_angles, cusps=natal_cusps, planet_subset=sigs[h]
        )["hf_total_v3"]

    # ── Grid loop ─────────────────────────────────────────────────────
    rows: List[Dict[str, Any]] = []
    n = len(grid)
    t0 = time.time()

    for i, (rlat, rlon) in enumerate(grid):
        try:
            h_data = calculate_houses(birth_dt, rlat, rlon, HOUSE_SYSTEM_PLACIDUS)
            cusps  = list(h_data["cusps"])
            angles = dict(planet_pos)
            angles["ASC"] = float(h_data["asc"])
            angles["MC"]  = float(h_data["mc"])

            row: Dict[str, Any] = {"lat": rlat, "lon": rlon}
            for domain in DOMAINS:
                label = DOMAIN_LABEL[domain]
                hf_val = compute_hf_v3(
                    angles, cusps=cusps, planet_subset=sigs[domain]
                )["hf_total_v3"]
                row[f"hf_{label}"]    = round(hf_val, 5)
                row[f"delta_{label}"] = round(hf_val - natal_hfs[domain], 5)

        except Exception:
            row = {"lat": rlat, "lon": rlon}
            for domain in DOMAINS:
                label = DOMAIN_LABEL[domain]
                row[f"hf_{label}"]    = float("nan")
                row[f"delta_{label}"] = float("nan")

        rows.append(row)

        if verbose and ((i + 1) % 500 == 0 or (i + 1) == n):
            elapsed = time.time() - t0
            print(f"      {i+1}/{n} pts  {elapsed:.0f}s")

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=float, default=5.0,
                        help="Grid step in degrees (default 5.0)")
    parser.add_argument("--subjects", nargs="*", default=None,
                        help="Slugs to process (default: all demo subjects)")
    args = parser.parse_args()

    index = json.loads(DEMO_INDEX.read_text(encoding="utf-8"))
    subjects = index["subjects"]
    if args.subjects:
        subjects = [s for s in subjects if s["slug"] in args.subjects]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    grid = make_grid(args.step)
    print(f"Grid: step={args.step}°, {len(grid)} points | "
          f"Domains: {list(DOMAIN_LABEL.values())} | Subjects: {len(subjects)}")

    for subj in subjects:
        slug = subj["slug"]
        birth_dt = _parse_birth_dt(subj["birth_datetime"])
        natal_lat = float(subj["natal_lat"])
        natal_lon = float(subj["natal_lon"])

        print(f"\n[{slug}] {subj.get('display_name', slug)}")
        t_start = time.time()

        df = compute_subject_domains(birth_dt, natal_lat, natal_lon, grid, verbose=True)

        out_path = OUTPUT_DIR / f"{slug}_domains.parquet"
        df.to_parquet(out_path, index=False)

        elapsed = time.time() - t_start
        print(f"  Saved {out_path.name} ({len(df)} rows, "
              f"{out_path.stat().st_size // 1024}KB, {elapsed:.1f}s)")

    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
