"""Generar grillas HF por dominio de casa.

Cubre dos fuentes de sujetos:
  1. output/demo/index.json  — sujetos demo pre-calculados (10 celebridades)
  2. data/biographical_events_v2/*.json  — todos los sujetos con eventos biográficos

Por cada sujeto × {global, h1, h2, h4, h5, h6, h7, h9, h10}:
  1. Calcula los significadores de la casa para esa carta natal
  2. Computa HF(lat, lon) para cada punto de la grilla con planet_subset
  3. Guarda el resultado en output/relocation_fields_domain/{slug}_domains.parquet

Columnas del parquet:
  lat, lon,
  hf_global,  delta_global,
  hf_h1,  delta_h1,
  hf_h2,  delta_h2,
  hf_h4,  delta_h4,
  hf_h5,  delta_h5,
  hf_h6,  delta_h6,
  hf_h7,  delta_h7,
  hf_h9,  delta_h9,
  hf_h10, delta_h10

Uso:
    # Dry-run: muestra qué se generaría sin calcular nada
    .venv/Scripts/python.exe scripts/generate_hf_domain_grids.py --dry-run

    # Un sujeto concreto por slug
    .venv/Scripts/python.exe scripts/generate_hf_domain_grids.py --subject morrison

    # Todos los que faltan (skip si parquet ya existe)
    .venv/Scripts/python.exe scripts/generate_hf_domain_grids.py

    # Grid más fino (como los GeoJSON del demo: 2.5°)
    .venv/Scripts/python.exe scripts/generate_hf_domain_grids.py --step 2.5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
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

DEMO_INDEX     = REPO_ROOT / "output" / "demo" / "index.json"
BIO_DIR        = REPO_ROOT / "data" / "biographical_events_v2"
RAW_BIRTHDATA  = REPO_ROOT / "data" / "raw" / "raw_birthdata.jsonl"
OUTPUT_DIR     = REPO_ROOT / "output" / "relocation_fields_domain"

# Domains: house number (0 = global/no subset)
DOMAINS: List[int] = [0, 1, 2, 4, 5, 6, 7, 9, 10]
DOMAIN_LABEL: Dict[int, str] = {
    0: "global", 1: "h1", 2: "h2", 4: "h4",
    5: "h5", 6: "h6", 7: "h7", 9: "h9", 10: "h10",
}


# ── Helpers ───────────────────────────────────────────────────────────

def make_grid(step: float) -> List[Tuple[float, float]]:
    lats = np.arange(-80, 80 + step / 2, step)
    lons = np.arange(-180, 180 + step / 2, step)
    return [(float(la), float(lo)) for la in lats for lo in lons]


def _parse_birth_dt_iso(dt_str: str) -> datetime:
    """Parse ISO birth_datetime (from demo index) to UTC-aware datetime."""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_tz_offset(tz_str: str) -> int:
    """Parse timezone string like '-4:00:00' or '+05:30:00' → total minutes offset."""
    m = re.match(r'^([+-])(\d+):(\d+):(\d+)$', tz_str.strip())
    if not m:
        return 0
    sign = 1 if m.group(1) == '+' else -1
    h, mn = int(m.group(2)), int(m.group(3))
    return sign * (h * 60 + mn)


def _birth_dt_from_raw(rec: dict) -> datetime:
    """Build UTC datetime from raw_birthdata record fields."""
    bd = rec["birth_date"]                          # '1943-12-08'
    bt = rec.get("birth_time", "12:00:00")          # '11:55:00'
    tz = rec.get("timezone", "+00:00:00")
    offset_min = _parse_tz_offset(tz)
    dt_local = datetime.fromisoformat(f"{bd}T{bt}")
    dt_utc = dt_local - timedelta(minutes=offset_min)
    return dt_utc.replace(tzinfo=timezone.utc)


def build_natal_data_for_sig(
    planet_pos: Dict[str, float], natal_cusps: List[float]
) -> dict:
    return {
        "planets": [{"name": k, "longitude": v} for k, v in planet_pos.items()],
        "houses": [{"num": i + 1, "longitude": c} for i, c in enumerate(natal_cusps)],
    }


# ── Subject loading ───────────────────────────────────────────────────

def _load_raw_birthdata() -> Dict[str, dict]:
    """Return dict keyed by str(id) from raw_birthdata.jsonl."""
    records: Dict[str, dict] = {}
    with open(RAW_BIRTHDATA, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            records[str(rec.get("id", ""))] = rec
    return records


def _load_bio_subjects(raw_by_id: Dict[str, dict]) -> List[dict]:
    """Load subjects from biographical_events_v2/, resolving birth data from raw_birthdata."""
    skip_prefixes = ("correlation", "cross_val", "optimiz", "GS_")
    subjects = []
    for fpath in sorted(BIO_DIR.glob("*.json")):
        if any(fpath.name.startswith(p) for p in skip_prefixes):
            continue
        try:
            meta = json.loads(fpath.read_text(encoding="utf-8")).get("meta", {})
        except Exception:
            continue

        sid = str(meta.get("id", ""))
        slug = fpath.stem.split("_", 1)[1] if "_" in fpath.stem else fpath.stem
        name = meta.get("name", slug)

        raw = raw_by_id.get(sid)
        if raw is None:
            print(f"  [WARN] {slug} (id={sid}): not found in raw_birthdata — skipping")
            continue

        try:
            birth_dt = _birth_dt_from_raw(raw)
        except Exception as e:
            print(f"  [WARN] {slug}: cannot parse birth datetime — {e}")
            continue

        subjects.append({
            "slug": slug,
            "display_name": name,
            "birth_datetime_obj": birth_dt,
            "natal_lat": float(raw.get("latitude", 0)),
            "natal_lon": float(raw.get("longitude", 0)),
        })

    return subjects


def _load_demo_subjects() -> List[dict]:
    """Load subjects from demo/index.json."""
    index = json.loads(DEMO_INDEX.read_text(encoding="utf-8"))
    subjects = []
    for s in index["subjects"]:
        subjects.append({
            "slug": s["slug"],
            "display_name": s.get("display_name", s["slug"]),
            "birth_datetime_obj": _parse_birth_dt_iso(s["birth_datetime"]),
            "natal_lat": float(s["natal_lat"]),
            "natal_lon": float(s["natal_lon"]),
        })
    return subjects


def load_all_subjects() -> List[dict]:
    """Merge demo + bio subjects, deduplicated by slug (demo takes precedence)."""
    demo = _load_demo_subjects()
    demo_slugs = {s["slug"] for s in demo}

    raw_by_id = _load_raw_birthdata()
    bio = _load_bio_subjects(raw_by_id)

    # Add bio subjects not already in demo
    merged = list(demo)
    for s in bio:
        if s["slug"] not in demo_slugs:
            merged.append(s)

    return merged


# ── Core computation ──────────────────────────────────────────────────

def compute_subject_domains(
    birth_dt: datetime,
    natal_lat: float,
    natal_lon: float,
    grid: List[Tuple[float, float]],
    verbose: bool = True,
) -> pd.DataFrame:
    """Compute relocation grid with all domain HFs. Returns combined DataFrame."""
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=timezone.utc)

    # Natal chart — planetary positions are fixed; only ASC/MC vary by location
    chart = chart_json(natal_lat, natal_lon, birth_dt)
    planet_pos: Dict[str, float] = {p.name: float(p.lon) for p in chart.planets}

    natal_houses = calculate_houses(birth_dt, natal_lat, natal_lon, HOUSE_SYSTEM_PLACIDUS)
    natal_cusps = list(natal_houses["cusps"])
    natal_data_for_sig = build_natal_data_for_sig(planet_pos, natal_cusps)

    # Significators per domain (computed once from natal chart)
    sigs: Dict[int, Optional[List[str]]] = {}
    for h in DOMAINS:
        if h == 0:
            sigs[h] = None   # global: no planet_subset filter
        else:
            s = house_significators(natal_data_for_sig, h)
            sigs[h] = s if s else None
            if verbose:
                print(f"    {DOMAIN_LABEL[h]}: {s}")

    # Natal HF per domain (baseline for delta)
    natal_angles = dict(planet_pos)
    natal_angles["ASC"] = float(natal_houses["asc"])
    natal_angles["MC"]  = float(natal_houses["mc"])

    natal_hfs: Dict[int, float] = {}
    for h in DOMAINS:
        natal_hfs[h] = compute_hf_v3(
            natal_angles, cusps=natal_cusps, planet_subset=sigs[h]
        )["hf_total_v3"]

    # Grid loop
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


# ── Main ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate HF domain grids for biographical subjects."
    )
    parser.add_argument(
        "--step", type=float, default=2.5,
        help="Grid step in degrees (default 2.5 — matches existing demo parquets)"
    )
    parser.add_argument(
        "--subject", type=str, default=None,
        help="Process only this slug (e.g. --subject morrison)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be generated without computing anything"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Recompute even if parquet already exists"
    )
    args = parser.parse_args()

    all_subjects = load_all_subjects()

    # Filter by --subject flag
    if args.subject:
        all_subjects = [s for s in all_subjects if s["slug"] == args.subject]
        if not all_subjects:
            print(f"ERROR: subject '{args.subject}' not found. "
                  f"Available slugs: {[s['slug'] for s in load_all_subjects()]}")
            sys.exit(1)

    # Determine which need generation
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    to_process = []
    to_skip = []
    for subj in all_subjects:
        out_path = OUTPUT_DIR / f"{subj['slug']}_domains.parquet"
        if out_path.exists() and not args.force:
            to_skip.append(subj["slug"])
        else:
            to_process.append(subj)

    grid = make_grid(args.step)

    print(f"Grid: step={args.step}°, {len(grid)} points | "
          f"Domains: {list(DOMAIN_LABEL.values())}")
    print(f"Subjects to process: {len(to_process)}  |  skip (already exist): {len(to_skip)}")
    if to_skip:
        print(f"  Skipping: {to_skip}")

    if args.dry_run:
        print("\n--- DRY RUN (no computation) ---")
        for subj in to_process:
            out_path = OUTPUT_DIR / f"{subj['slug']}_domains.parquet"
            print(f"  WOULD GENERATE: {out_path.name}")
            print(f"    birth_dt = {subj['birth_datetime_obj'].isoformat()}")
            print(f"    natal = ({subj['natal_lat']:.4f}, {subj['natal_lon']:.4f})")
            print(f"    domains = {list(DOMAIN_LABEL.values())}")
        return

    # Process
    for subj in to_process:
        slug = subj["slug"]
        birth_dt = subj["birth_datetime_obj"]
        natal_lat = subj["natal_lat"]
        natal_lon = subj["natal_lon"]

        print(f"\n[{slug}] {subj['display_name']}")
        print(f"  birth_dt={birth_dt.isoformat()}  natal=({natal_lat:.4f}, {natal_lon:.4f})")
        t_start = time.time()

        df = compute_subject_domains(birth_dt, natal_lat, natal_lon, grid, verbose=True)

        out_path = OUTPUT_DIR / f"{slug}_domains.parquet"
        df.to_parquet(out_path, index=False)

        elapsed = time.time() - t_start
        print(f"  Saved {out_path.name} "
              f"({len(df)} rows, {out_path.stat().st_size // 1024}KB, {elapsed:.1f}s)")

    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
