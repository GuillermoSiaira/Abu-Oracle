"""Event-HF Correlator: compute HF at each biographical event and measure correlation.

For each subject:
1. Load birth data (from subjects.py or raw_birthdata.jsonl)
2. Load biographical events (from data/biographical_events/)
3. For each event with a date, compute transit chart positions at event_date
4. Compute HF_weighted at that moment (using natal chart as base)
5. Compare HF_weighted with event valence (+1 positive, -1 negative, 0 neutral)
6. Output correlation metrics

The key insight: for relocation events, we vary location (ASC/MC).
For temporal events, we vary transits (planet positions change over time).
This correlator focuses on TRANSITS: what's the sky doing when good/bad things happen?
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Add abu_engine to path for imports
ABU_DIR = Path(__file__).resolve().parent.parent / "abu_engine"
sys.path.insert(0, str(ABU_DIR))

from core.chart import _compute_planet_positions
from core.houses_swiss import calculate_houses, HOUSE_SYSTEM_PLACIDUS
from harmony.field_v3 import compute_hf_v3
from harmony.field import aggregate_field

logger = logging.getLogger(__name__)

EVENTS_DIR = Path(__file__).resolve().parent.parent / "data" / "biographical_events"
BIRTHDATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "raw_birthdata.jsonl"

# Birth coordinates for subjects (fallback if not in birthdata)
SUBJECT_BIRTH_COORDS: Dict[str, dict] = {
    "GS_001": {"lat": 47.60, "lon": 9.35, "birth_date": "1875-07-26T19:29:00"},
    "GS_002": {"lat": 45.25, "lon": 14.45, "birth_date": "1856-07-10T00:00:00"},
    "GS_003": {"lat": 51.51, "lon": -0.13, "birth_date": "1912-06-23T00:00:00"},
    "308660": {"lat": 48.40, "lon": 9.98, "birth_date": "1879-03-14T11:30:00"},
    "12145":  {"lat": -34.60, "lon": -58.38, "birth_date": "1899-08-24T00:00:00"},
    "35255":  {"lat": 19.35, "lon": -99.15, "birth_date": "1907-07-06T00:00:00"},
    "76835":  {"lat": 36.72, "lon": -4.42, "birth_date": "1881-10-25T23:15:00"},
    "317785": {"lat": 51.85, "lon": 4.47, "birth_date": "1853-03-30T11:00:00"},
    "337730": {"lat": 49.20, "lon": 18.75, "birth_date": "1856-05-06T18:30:00"},
    "61360":  {"lat": 21.62, "lon": 69.67, "birth_date": "1869-10-02T07:12:00"},
    "232650": {"lat": 51.47, "lon": 0.00, "birth_date": "1947-01-08T09:00:00"},
    # --- Expansion wave (Session 8) ---
    "16510":  {"lat": 34.05, "lon": -118.24, "birth_date": "1926-06-01T09:30:00"},
    "232580": {"lat": 34.26, "lon": -88.70, "birth_date": "1935-01-08T04:35:00"},
    "239610": {"lat": 38.25, "lon": -85.76, "birth_date": "1942-01-17T18:35:00"},
    "99835":  {"lat": 47.61, "lon": -122.33, "birth_date": "1942-11-27T10:15:00"},
    "240895": {"lat": 29.90, "lon": -93.93, "birth_date": "1943-01-19T09:45:00"},
    "106715": {"lat": 28.08, "lon": -80.61, "birth_date": "1943-12-08T11:55:00"},
    "288130": {"lat": 40.56, "lon": -85.66, "birth_date": "1931-02-08T09:00:00"},
    "349770": {"lat": 38.89, "lon": -90.18, "birth_date": "1926-05-26T05:00:00"},
    "2280":   {"lat": 40.57, "lon": -84.19, "birth_date": "1930-08-05T00:31:00"},
    "99810":  {"lat": 37.77, "lon": -122.42, "birth_date": "1940-11-27T07:12:00"},
    "113610": {"lat": 48.85, "lon": 2.35, "birth_date": "1915-12-19T05:00:00"},
    "336770": {"lat": 50.83, "lon": 4.37, "birth_date": "1929-05-04T03:00:00"},
    "14525":  {"lat": 59.33, "lon": 18.07, "birth_date": "1915-08-29T03:30:00"},
    "9945":   {"lat": 47.27, "lon": -0.08, "birth_date": "1883-08-19T16:00:00"},
    "70110":  {"lat": 53.34, "lon": -6.27, "birth_date": "1854-10-16T03:00:00"},
}

VALENCE_MAP = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}


def _parse_dt(date_str: str) -> Optional[datetime]:
    """Parse date string to timezone-aware datetime."""
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def compute_natal_hf(birth_dt: datetime, lat: float, lon: float) -> dict:
    """Compute natal HF for a subject."""
    positions = _compute_planet_positions(birth_dt)
    houses = calculate_houses(birth_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
    angles = dict(positions)
    angles["ASC"] = float(houses["asc"])
    angles["MC"] = float(houses["mc"])
    cusps = list(houses["cusps"])
    hf = compute_hf_v3(angles, cusps=cusps)
    agg = aggregate_field(angles)
    return {
        "hf_total_v3": hf["hf_total_v3"],
        "hf_aspects": hf["hf_aspects"],
        "hf_weighted": agg["HF_weighted"],
        "hf_harmony": agg["HF_harmony"],
        "hf_tension": agg["HF_tension"],
        "hf_conjunction": agg["HF_conjunction"],
        "hf_total_legacy": agg["HF_total"],
    }


def compute_transit_hf(event_dt: datetime, natal_lat: float, natal_lon: float) -> Optional[dict]:
    """Compute HF at a specific transit date (planet positions at event time, houses at natal location)."""
    try:
        positions = _compute_planet_positions(event_dt)
        houses = calculate_houses(event_dt, natal_lat, natal_lon, HOUSE_SYSTEM_PLACIDUS)
        angles = dict(positions)
        angles["ASC"] = float(houses["asc"])
        angles["MC"] = float(houses["mc"])
        cusps = list(houses["cusps"])
        hf = compute_hf_v3(angles, cusps=cusps)
        agg = aggregate_field(angles)
        return {
            "hf_total_v3": hf["hf_total_v3"],
            "hf_aspects": hf["hf_aspects"],
            "hf_weighted": agg["HF_weighted"],
            "hf_harmony": agg["HF_harmony"],
            "hf_tension": agg["HF_tension"],
            "hf_conjunction": agg["HF_conjunction"],
            "hf_total_legacy": agg["HF_total"],
        }
    except Exception as exc:
        logger.warning("Failed to compute transit HF for %s: %s", event_dt, exc)
        return None


def process_subject(subject_id: str, events_file: Path) -> List[dict]:
    """Process one subject: compute HF at each event date."""
    with open(events_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    birth_info = SUBJECT_BIRTH_COORDS.get(subject_id)
    if not birth_info:
        logger.warning("No birth coords for subject %s", subject_id)
        return []

    birth_dt = _parse_dt(birth_info["birth_date"])
    if not birth_dt:
        logger.warning("Invalid birth date for %s", subject_id)
        return []

    natal_lat = birth_info["lat"]
    natal_lon = birth_info["lon"]

    # Compute natal HF
    natal_hf = compute_natal_hf(birth_dt, natal_lat, natal_lon)
    logger.info("  Natal HF: weighted=%.4f total_v3=%.4f",
                natal_hf["hf_weighted"], natal_hf["hf_total_v3"])

    results = []
    events = data.get("biographical_events", [])
    for evt in events:
        date_str = evt.get("date", "")
        if not date_str or date_str.startswith("0000"):
            continue

        event_dt = _parse_dt(date_str)
        if not event_dt:
            continue

        # Skip events before 1550 (ephemeris limit for de440s)
        if event_dt.year < 1550:
            continue

        transit_hf = compute_transit_hf(event_dt, natal_lat, natal_lon)
        if not transit_hf:
            continue

        valence_str = evt.get("valence", "neutral")
        valence_num = VALENCE_MAP.get(valence_str, 0.0)

        results.append({
            "subject_id": subject_id,
            "subject_name": data["meta"]["name"],
            "event_date": date_str,
            "event_type": evt.get("event_type", ""),
            "description": evt.get("description", ""),
            "valence": valence_str,
            "valence_num": valence_num,
            "confidence": evt.get("confidence", ""),
            # Transit HF at event time
            "transit_hf_weighted": transit_hf["hf_weighted"],
            "transit_hf_total_v3": transit_hf["hf_total_v3"],
            "transit_hf_harmony": transit_hf["hf_harmony"],
            "transit_hf_tension": transit_hf["hf_tension"],
            "transit_hf_conjunction": transit_hf["hf_conjunction"],
            # Natal HF (baseline)
            "natal_hf_weighted": natal_hf["hf_weighted"],
            "natal_hf_total_v3": natal_hf["hf_total_v3"],
            # Delta (transit vs natal)
            "delta_hf_weighted": transit_hf["hf_weighted"] - natal_hf["hf_weighted"],
            "delta_hf_total_v3": transit_hf["hf_total_v3"] - natal_hf["hf_total_v3"],
        })

    return results


def run_correlator() -> dict:
    """Run across all subjects and compute correlation metrics."""
    all_results: List[dict] = []

    for events_file in sorted(EVENTS_DIR.glob("*.json")):
        fname = events_file.stem
        if fname == "correlation_results":
            continue
        # Extract subject ID from filename: e.g. "308660_einstein" → "308660", "GS_001_JUNG" → "GS_001"
        if fname.startswith("GS_"):
            subject_id = fname[:6]  # "GS_001"
        else:
            subject_id = fname.split("_", 1)[0]

        logger.info("Processing %s …", fname)
        results = process_subject(subject_id, events_file)
        all_results.extend(results)
        logger.info("  → %d events with HF computed", len(results))

    if not all_results:
        logger.error("No results to correlate")
        return {}

    # Compute correlations
    valences = np.array([r["valence_num"] for r in all_results])
    hf_weighted = np.array([r["transit_hf_weighted"] for r in all_results])
    hf_total_v3 = np.array([r["transit_hf_total_v3"] for r in all_results])
    delta_weighted = np.array([r["delta_hf_weighted"] for r in all_results])
    delta_total_v3 = np.array([r["delta_hf_total_v3"] for r in all_results])

    # Filter non-neutral events for correlation
    non_neutral = valences != 0
    n_non_neutral = int(non_neutral.sum())

    def safe_corr(a, b):
        if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    # Overall stats
    correlations = {
        "n_total_events": len(all_results),
        "n_positive": int((valences > 0).sum()),
        "n_negative": int((valences < 0).sum()),
        "n_neutral": int((valences == 0).sum()),
        "n_non_neutral": n_non_neutral,
        # Correlations (all events)
        "corr_valence_vs_hf_weighted_all": safe_corr(valences, hf_weighted),
        "corr_valence_vs_hf_total_v3_all": safe_corr(valences, hf_total_v3),
        "corr_valence_vs_delta_weighted_all": safe_corr(valences, delta_weighted),
        "corr_valence_vs_delta_total_v3_all": safe_corr(valences, delta_total_v3),
    }

    # Correlations (non-neutral only)
    if n_non_neutral >= 3:
        v_nn = valences[non_neutral]
        correlations["corr_valence_vs_hf_weighted_nn"] = safe_corr(v_nn, hf_weighted[non_neutral])
        correlations["corr_valence_vs_delta_weighted_nn"] = safe_corr(v_nn, delta_weighted[non_neutral])

    # Group means: mean HF for positive vs negative events
    pos_mask = valences > 0
    neg_mask = valences < 0
    if pos_mask.sum() > 0:
        correlations["mean_hf_weighted_positive"] = float(hf_weighted[pos_mask].mean())
        correlations["mean_delta_weighted_positive"] = float(delta_weighted[pos_mask].mean())
    if neg_mask.sum() > 0:
        correlations["mean_hf_weighted_negative"] = float(hf_weighted[neg_mask].mean())
        correlations["mean_delta_weighted_negative"] = float(delta_weighted[neg_mask].mean())

    return {
        "correlations": correlations,
        "events": all_results,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s",
                        stream=sys.stdout)

    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    except ImportError:
        pass

    result = run_correlator()
    corr = result.get("correlations", {})

    print("\n" + "=" * 65)
    print("EVENT-HF CORRELATION RESULTS")
    print("=" * 65)
    print(f"Total events:       {corr.get('n_total_events', 0)}")
    print(f"  Positive:         {corr.get('n_positive', 0)}")
    print(f"  Negative:         {corr.get('n_negative', 0)}")
    print(f"  Neutral:          {corr.get('n_neutral', 0)}")
    print()
    print("CORRELATIONS (valence ↔ HF):")
    print(f"  All events:")
    print(f"    valence vs HF_weighted:      {corr.get('corr_valence_vs_hf_weighted_all', 0):.4f}")
    print(f"    valence vs HF_total_v3:      {corr.get('corr_valence_vs_hf_total_v3_all', 0):.4f}")
    print(f"    valence vs Δ_HF_weighted:    {corr.get('corr_valence_vs_delta_weighted_all', 0):.4f}")
    print(f"    valence vs Δ_HF_total_v3:    {corr.get('corr_valence_vs_delta_total_v3_all', 0):.4f}")
    print(f"  Non-neutral only:")
    print(f"    valence vs HF_weighted:      {corr.get('corr_valence_vs_hf_weighted_nn', 'N/A')}")
    print(f"    valence vs Δ_HF_weighted:    {corr.get('corr_valence_vs_delta_weighted_nn', 'N/A')}")
    print()
    print("GROUP MEANS:")
    if "mean_hf_weighted_positive" in corr:
        print(f"  Positive events → mean HF_w:   {corr['mean_hf_weighted_positive']:.4f}  Δ: {corr.get('mean_delta_weighted_positive', 0):.4f}")
    if "mean_hf_weighted_negative" in corr:
        print(f"  Negative events → mean HF_w:   {corr['mean_hf_weighted_negative']:.4f}  Δ: {corr.get('mean_delta_weighted_negative', 0):.4f}")
    print("=" * 65)

    # Save full results
    out_path = Path(__file__).resolve().parent.parent / "data" / "biographical_events" / "correlation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nFull results saved to: {out_path}")
