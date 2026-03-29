"""Runner: compara Cohen's d de HF_v5 vs HF_v3 sobre los 527 eventos.

HF_v5 (natal + dignidad + firdaria):
  compute_hf_v5(natal_data, query_date=event_dt, house_domain, lat=birth_lat, lon=birth_lon)

HF_v3 domain (existente, de domain_correlation_results.json):
  ya calculado en correlate_by_domain.py — se lee directamente.

Uso:
  .venv/Scripts/python.exe scripts/run_hf_v5_comparison.py
"""
from __future__ import annotations

import json
import logging
import sys
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))

from core.chart import _compute_planet_positions
from core.houses_swiss import calculate_houses, HOUSE_SYSTEM_PLACIDUS
from harmony.hf_v5 import compute_hf_v5

# ── Paths ─────────────────────────────────────────────────────────────────────
EVENTS_DIR  = REPO_ROOT / "data" / "biographical_events_v2"
V3_RESULTS  = REPO_ROOT / "analysis" / "domain_correlation_results.json"

VALENCE_MAP = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}

# Subject birth coords — same dict as correlate_by_domain.py
SUBJECT_BIRTH_COORDS: Dict[str, dict] = {
    "GS_001": {"lat": 47.60, "lon": 9.35,    "birth_date": "1875-07-26T19:29:00"},
    "GS_002": {"lat": 45.25, "lon": 14.45,   "birth_date": "1856-07-10T00:00:00"},
    "GS_003": {"lat": 51.51, "lon": -0.13,   "birth_date": "1912-06-23T00:00:00"},
    "308660": {"lat": 48.40, "lon": 9.98,    "birth_date": "1879-03-14T11:30:00"},
    "12145":  {"lat": -34.60, "lon": -58.38, "birth_date": "1899-08-24T00:00:00"},
    "35255":  {"lat": 19.35, "lon": -99.15,  "birth_date": "1907-07-06T00:00:00"},
    "76835":  {"lat": 36.72, "lon": -4.42,   "birth_date": "1881-10-25T23:15:00"},
    "317785": {"lat": 51.85, "lon": 4.47,    "birth_date": "1853-03-30T11:00:00"},
    "337730": {"lat": 49.20, "lon": 18.75,   "birth_date": "1856-05-06T18:30:00"},
    "61360":  {"lat": 21.62, "lon": 69.67,   "birth_date": "1869-10-02T07:12:00"},
    "232650": {"lat": 51.47, "lon": 0.00,    "birth_date": "1947-01-08T09:00:00"},
    "16510":  {"lat": 34.05, "lon": -118.24, "birth_date": "1926-06-01T09:30:00"},
    "232580": {"lat": 34.26, "lon": -88.70,  "birth_date": "1935-01-08T04:35:00"},
    "239610": {"lat": 38.25, "lon": -85.76,  "birth_date": "1942-01-17T18:35:00"},
    "99835":  {"lat": 47.61, "lon": -122.33, "birth_date": "1942-11-27T10:15:00"},
    "240895": {"lat": 29.90, "lon": -93.93,  "birth_date": "1943-01-19T09:45:00"},
    "106715": {"lat": 28.08, "lon": -80.61,  "birth_date": "1943-12-08T11:55:00"},
    "288130": {"lat": 40.56, "lon": -85.66,  "birth_date": "1931-02-08T09:00:00"},
    "349770": {"lat": 38.89, "lon": -90.18,  "birth_date": "1926-05-26T05:00:00"},
    "2280":   {"lat": 40.57, "lon": -84.19,  "birth_date": "1930-08-05T00:31:00"},
    "99810":  {"lat": 37.77, "lon": -122.42, "birth_date": "1940-11-27T07:12:00"},
    "113610": {"lat": 48.85, "lon": 2.35,    "birth_date": "1915-12-19T05:00:00"},
    "336770": {"lat": 50.83, "lon": 4.37,    "birth_date": "1929-05-04T03:00:00"},
    "14525":  {"lat": 59.33, "lon": 18.07,   "birth_date": "1915-08-29T03:30:00"},
    "9945":   {"lat": 47.27, "lon": -0.08,   "birth_date": "1883-08-19T16:00:00"},
    "70110":  {"lat": 53.34, "lon": -6.27,   "birth_date": "1854-10-16T03:00:00"},
}


def _parse_dt(s: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00")) if "T" in s \
             else datetime.strptime(s, "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except Exception:
        return None


def _cohens_d(values: np.ndarray, labels: np.ndarray) -> float:
    pos = values[labels > 0]
    neg = values[labels < 0]
    if len(pos) < 2 or len(neg) < 2:
        return float("nan")
    pooled = np.sqrt((np.var(pos, ddof=1) + np.var(neg, ddof=1)) / 2)
    return float("nan") if pooled < 1e-9 else float((np.mean(pos) - np.mean(neg)) / pooled)


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s",
                        stream=sys.stdout)

    all_rows: List[dict] = []
    errors = 0

    for evf in sorted(EVENTS_DIR.glob("*.json")):
        stem = evf.stem
        if stem in ("correlation_results", "cross_validation_results", "optimization_results"):
            continue
        sid = stem[:6] if stem.startswith("GS_") else stem.split("_", 1)[0]
        bio = SUBJECT_BIRTH_COORDS.get(sid)
        if not bio:
            continue

        birth_dt = _parse_dt(bio["birth_date"])
        if not birth_dt:
            continue

        b_lat, b_lon = bio["lat"], bio["lon"]

        # ── Build natal_data once per subject ─────────────────────────────────
        natal_pos = _compute_planet_positions(birth_dt)
        natal_houses_raw = calculate_houses(birth_dt, b_lat, b_lon, HOUSE_SYSTEM_PLACIDUS)
        natal_cusps = list(natal_houses_raw["cusps"])
        natal_data = {
            "planets": [{"name": k, "longitude": v}
                        for k, v in natal_pos.items() if k not in ("ASC", "MC")],
            "houses":  [{"num": i + 1, "longitude": c}
                        for i, c in enumerate(natal_cusps)],
            "birth_date":  bio["birth_date"],
            "ascendant":   float(natal_houses_raw["asc"]),
        }

        data = json.loads(evf.read_text(encoding="utf-8"))
        events = data.get("biographical_events", [])
        name = data.get("meta", {}).get("name", sid)
        logging.info("  %s (%s) — %d events", sid, name, len(events))

        subject_rows: List[dict] = []

        for evt in events:
            date_str = evt.get("date", "")
            if not date_str or date_str.startswith("0000"):
                continue
            event_dt = _parse_dt(date_str)
            if not event_dt or event_dt.year < 1550:
                continue

            house_domain = evt.get("house_domain", 0)
            if not house_domain:
                continue
            valence_num = VALENCE_MAP.get(evt.get("valence", "neutral"), 0.0)

            try:
                score = compute_hf_v5(
                    natal_data,
                    query_date=event_dt,
                    house_domain=house_domain,
                    lat=b_lat,
                    lon=b_lon,
                    system="traditional",
                )
            except Exception as exc:
                logging.debug("  skip %s @ %s: %s", sid, date_str, exc)
                errors += 1
                continue

            subject_rows.append({
                "house_domain": house_domain,
                "valence_num":  valence_num,
                "hf_v5":        score,
            })

        # Z-score per subject
        if subject_rows:
            vals = np.array([r["hf_v5"] for r in subject_rows])
            std = vals.std()
            mean = vals.mean()
            normed = (vals - mean) / std if std > 1e-9 else vals - mean
            for i, r in enumerate(subject_rows):
                r["hf_v5"] = float(normed[i])
            all_rows.extend(subject_rows)

    logging.info("Total events processed: %d  (errors: %d)", len(all_rows), errors)

    # ── Load v3 domain Cohen's d for comparison ────────────────────────────────
    v3_d: Dict[int, float] = {}
    if V3_RESULTS.exists():
        data_v3 = json.loads(V3_RESULTS.read_text(encoding="utf-8"))
        for row in data_v3.get("table", []):
            h = row.get("house")
            d = row.get("cohens_d_domain")
            if h and d is not None and not (isinstance(d, float) and math.isnan(d)):
                v3_d[h] = d

    # ── Per-domain Cohen's d for HF_v5 ────────────────────────────────────────
    from collections import defaultdict
    by_domain: Dict[int, List] = defaultdict(list)
    for r in all_rows:
        by_domain[r["house_domain"]].append(r)

    # Global (all events together, labelled by valence)
    all_vals   = np.array([r["hf_v5"]       for r in all_rows])
    all_labels = np.array([r["valence_num"]  for r in all_rows])
    d_global_v5 = _cohens_d(all_vals, all_labels)

    # Target houses for the report
    TARGET_HOUSES = [4, 5, 7, 10]

    def _fmt(v):
        return f"{v:+.3f}" if not (isinstance(v, float) and math.isnan(v)) else "  n/a"

    print()
    print("=" * 68)
    print("HF_v5 vs HF_v3 — Cohen's d por dominio")
    print(f"Total eventos: {len(all_rows)}")
    print("=" * 68)
    print(f"{'Casa':>6} | {'N':>5} | {'N+':>4} | {'N-':>4} | {'d_v3':>7} | {'d_v5':>7} | {'delta':>7}")
    print("-" * 68)

    for h in TARGET_HOUSES:
        rows_h = by_domain.get(h, [])
        n = len(rows_h)
        vals   = np.array([r["hf_v5"]      for r in rows_h])
        labels = np.array([r["valence_num"] for r in rows_h])
        n_pos = int((labels > 0).sum())
        n_neg = int((labels < 0).sum())
        d_v5  = _cohens_d(vals, labels)
        d_v3  = v3_d.get(h, float("nan"))
        delta = (d_v5 - d_v3) if not (math.isnan(d_v5) or math.isnan(d_v3)) else float("nan")
        print(f"  H{h:02d}  | {n:5d} | {n_pos:4d} | {n_neg:4d} | {_fmt(d_v3):>7} | {_fmt(d_v5):>7} | {_fmt(delta):>7}")

    # Global row
    d_v3_global = 0.441   # from CLAUDE.md / HF_EXPERIMENT_LOG
    delta_g = (d_global_v5 - d_v3_global) if not math.isnan(d_global_v5) else float("nan")
    print(f"{'global':>6} | {len(all_rows):5d} | {'':>4} | {'':>4} | {_fmt(d_v3_global):>7} | {_fmt(d_global_v5):>7} | {_fmt(delta_g):>7}")
    print("=" * 68)


if __name__ == "__main__":
    run()
