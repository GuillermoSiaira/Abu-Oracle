"""Benchmark script for IGP Phase 1 (Sprint 1)

Measures performance of:
- compute_sr_instant
- batch_evaluate_cities for synthetic city sets of given sizes

Usage (PowerShell):
  python scripts/bench_igp.py --sizes 1000,5000,10000 --workers 8 --top 20

If a full cities dataset is not available, it will synthesize a list by jittering
existing RELOCATION_CITIES definitions.
"""
from __future__ import annotations
import argparse
import time
import math
import random
import json
from typing import List, Dict, Any
from datetime import datetime

import os
import sys

# Ensure abu_engine is on sys.path to allow `from core ...` imports when run from repo root
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_ABU_ROOT = os.path.join(_REPO_ROOT, "abu_engine")
if _ABU_ROOT not in sys.path:
    sys.path.insert(0, _ABU_ROOT)

from core.igp_optimizer import compute_sr_instant, batch_evaluate_cities  # type: ignore
from core.solar_return_ranking import RELOCATION_CITIES  # type: ignore


def synthesize_cities(target_size: int) -> List[Dict[str, Any]]:
    """Build a synthetic city list of target_size by jittering base relocation cities.
    Deterministic: fixed seed.
    """
    base = [
        {"name": name, "lat": data["lat"], "lon": data["lon"], "country": data.get("region", "Unknown")}
        for name, data in RELOCATION_CITIES.items()
    ]
    if target_size <= len(base):
        return base[:target_size]

    random.seed(42)
    out: List[Dict[str, Any]] = []
    cycles = math.ceil(target_size / len(base))
    idx = 0
    for c in range(cycles):
        for city in base:
            if idx >= target_size:
                break
            # Jitter within ±0.25° lat/lon to simulate nearby distinct points
            lat_j = city["lat"] + random.uniform(-0.25, 0.25)
            lon_j = city["lon"] + random.uniform(-0.25, 0.25)
            out.append({
                "name": f"{city['name']}_{c}_{idx}",
                "lat": lat_j,
                "lon": lon_j,
                "country": city["country"],
            })
            idx += 1
    return out


def format_row(label: str, dur: float, cities: int, top_score: float) -> str:
    return f"{label:15} | {dur:8.2f} ms | cities: {cities:6d} | top_score: {top_score:.3f}"


def run_benchmark(sizes: List[int], workers: int, top: int) -> Dict[str, Any]:
    from datetime import timezone
    birth = datetime(1990, 1, 15, 10, 30, 0, tzinfo=timezone.utc)  # UTC-aware
    results_summary: Dict[str, Any] = {"runs": []}

    # Compute SR instant once per run/year for fairness (could vary by year)
    target_year = 2026
    t0_sr = time.perf_counter()
    sr_dt = compute_sr_instant(birth, 40.7128, -74.0060, target_year)
    t1_sr = time.perf_counter()
    sr_ms = (t1_sr - t0_sr) * 1000

    print(f"SR instant computed: {sr_dt.isoformat()} ({sr_ms:.2f} ms)\n")
    print("Label           | Duration  | cities: count | top_score")
    print("----------------+-----------+---------------+----------")

    for size in sizes:
        cities = synthesize_cities(size)
        t0 = time.perf_counter()
        scored = batch_evaluate_cities(sr_datetime=sr_dt, cities=cities, max_workers=workers)
        t1 = time.perf_counter()
        dur_ms = (t1 - t0) * 1000
        top_score = scored[0]["score"] if scored else 0.0

        # Slice top
        top_list = scored[:top]
        results_summary["runs"].append({
            "size": size,
            "duration_ms": round(dur_ms, 2),
            "workers": workers,
            "top_score": round(top_score, 4),
            "top": top_list,
        })
        print(format_row(f"cities_{size}", dur_ms, size, top_score))

    return results_summary


def main():
    parser = argparse.ArgumentParser(description="Benchmark IGP Phase 1")
    parser.add_argument("--sizes", type=str, default="1000,5000,10000", help="Comma-separated city sizes to benchmark")
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers")
    parser.add_argument("--top", type=int, default=10, help="Top N results to include in JSON summary")
    parser.add_argument("--json", action="store_true", help="Print JSON summary at end")
    args = parser.parse_args()

    try:
        sizes = [int(x.strip()) for x in args.sizes.split(",") if x.strip()]
    except ValueError:
        raise SystemExit("Invalid sizes format; expected comma-separated integers")

    summary = run_benchmark(sizes, args.workers, args.top)

    if args.json:
        print("\nJSON Summary:")
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
