"""Tarea 2.3 — Correlación HF segmentada por house_domain.

Para cada dominio de casa (10, 7, 4, ...):
1. Filtra eventos de biographical_events_v2 con house_domain == k
2. Computa transit_hf_domain usando el planet_subset de los significadores
   de esa casa en la carta natal del sujeto
3. Compara corr(HF_domain, valence_k) vs corr(HF_global, valence_k)

Hypothesis: corr(HF_h10, eventos_h10) > corr(HF_global, eventos_h10)

Uso:
    .venv/Scripts/python.exe scripts/correlate_by_domain.py
    # guarda analysis/domain_correlation_report.md
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# ── Path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))

from core.chart import _compute_planet_positions
from core.houses_swiss import calculate_houses, HOUSE_SYSTEM_PLACIDUS
from harmony.field_v3 import compute_hf_v3
from harmony.houses import house_significators

# ── Paths ─────────────────────────────────────────────────────────────────────
EVENTS_V2_DIR = REPO_ROOT / "data" / "biographical_events_v2"
BIRTHDATA_PATH = REPO_ROOT / "data" / "raw" / "raw_birthdata.jsonl"
OUTPUT_DIR = REPO_ROOT / "analysis"

VALENCE_MAP = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}

# Birth coords mirror from event_hf_correlator.py
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


def _parse_dt(date_str: str) -> Optional[datetime]:
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


def _build_natal_data(natal_positions: dict, natal_cusps: list) -> dict:
    """Build minimal natal_data dict for house_significators."""
    return {
        "planets": [{"name": k, "longitude": v} for k, v in natal_positions.items()
                    if k not in ("ASC", "MC")],
        "houses": [{"num": i + 1, "longitude": c} for i, c in enumerate(natal_cusps)],
    }


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _cohens_d(values: np.ndarray, labels: np.ndarray) -> float:
    """Cohen's d between positive (label=1) and negative (label=-1) groups."""
    pos = values[labels > 0]
    neg = values[labels < 0]
    if len(pos) < 2 or len(neg) < 2:
        return float("nan")
    pooled_std = np.sqrt((np.var(pos, ddof=1) + np.var(neg, ddof=1)) / 2)
    if pooled_std < 1e-9:
        return float("nan")
    return float((np.mean(pos) - np.mean(neg)) / pooled_std)


def process_all_subjects() -> List[dict]:
    """Load v2 events, compute transit HF (global + domain) for every event."""
    all_rows: List[dict] = []

    for events_file in sorted(EVENTS_V2_DIR.glob("*.json")):
        fname = events_file.stem
        # Skip non-subject files
        if fname in ("correlation_results", "cross_validation_results", "optimization_results"):
            continue
        if fname.startswith("GS_"):
            subject_id = fname[:6]
        else:
            subject_id = fname.split("_", 1)[0]

        birth_info = SUBJECT_BIRTH_COORDS.get(subject_id)
        if not birth_info:
            logging.warning("No birth coords for %s, skipping", fname)
            continue

        birth_dt = _parse_dt(birth_info["birth_date"])
        if not birth_dt:
            continue

        lat, lon = birth_info["lat"], birth_info["lon"]

        # ── Natal chart (fixed per subject) ─────────────────────────────────
        natal_pos = _compute_planet_positions(birth_dt)
        natal_houses = calculate_houses(birth_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
        natal_angles: dict = dict(natal_pos)
        natal_angles["ASC"] = float(natal_houses["asc"])
        natal_angles["MC"] = float(natal_houses["mc"])
        natal_cusps = list(natal_houses["cusps"])

        natal_data_for_sig = _build_natal_data(natal_angles, natal_cusps)

        # ── Precompute significators per unique house in this subject's events ──
        data = json.loads(events_file.read_text(encoding="utf-8"))
        events = data.get("biographical_events", [])
        unique_houses = {e.get("house_domain", 0) for e in events if e.get("house_domain")}
        sigs_cache: Dict[int, List[str]] = {
            h: house_significators(natal_data_for_sig, h) for h in unique_houses
        }

        # ── Natal HF (global baseline) ───────────────────────────────────────
        natal_hf_global = compute_hf_v3(natal_angles, cusps=natal_cusps)["hf_total_v3"]

        subject_name = data.get("meta", {}).get("name", subject_id)
        logging.info("  %s: %d events, houses %s", fname, len(events), sorted(unique_houses))

        for evt in events:
            date_str = evt.get("date", "")
            if not date_str or date_str.startswith("0000"):
                continue
            event_dt = _parse_dt(date_str)
            if not event_dt or event_dt.year < 1550:
                continue

            house_domain = evt.get("house_domain", 0)
            valence_str = evt.get("valence", "neutral")
            valence_num = VALENCE_MAP.get(valence_str, 0.0)

            try:
                transit_pos = _compute_planet_positions(event_dt)
                transit_houses = calculate_houses(event_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
                transit_angles: dict = dict(transit_pos)
                transit_angles["ASC"] = float(transit_houses["asc"])
                transit_angles["MC"] = float(transit_houses["mc"])
                transit_cusps = list(transit_houses["cusps"])

                # Global transit HF
                transit_hf_global = compute_hf_v3(transit_angles, cusps=transit_cusps)["hf_total_v3"]

                # Domain transit HF
                sig = sigs_cache.get(house_domain)
                if sig:
                    transit_hf_domain = compute_hf_v3(
                        transit_angles, cusps=transit_cusps, planet_subset=sig
                    )["hf_total_v3"]
                else:
                    transit_hf_domain = float("nan")

            except Exception as exc:
                logging.warning("    Failed %s @ %s: %s", subject_id, date_str, exc)
                continue

            all_rows.append({
                "subject_id": subject_id,
                "subject_name": subject_name,
                "event_date": date_str,
                "event_type": evt.get("event_type", ""),
                "house_domain": house_domain,
                "valence": valence_str,
                "valence_num": valence_num,
                "natal_hf_global": natal_hf_global,
                "transit_hf_global": transit_hf_global,
                "transit_hf_domain": transit_hf_domain,
                "delta_hf_global": transit_hf_global - natal_hf_global,
                "significators": sigs_cache.get(house_domain, []),
            })

    return all_rows


def compute_domain_table(rows: List[dict]) -> List[dict]:
    """Compute per-house-domain correlation table."""
    from collections import defaultdict
    by_domain: Dict[int, List[dict]] = defaultdict(list)
    for r in rows:
        if r["house_domain"]:
            by_domain[r["house_domain"]].append(r)

    table = []
    for house in sorted(by_domain.keys()):
        domain_rows = by_domain[house]
        valences = np.array([r["valence_num"] for r in domain_rows])
        hf_global = np.array([r["transit_hf_global"] for r in domain_rows])
        hf_domain = np.array([r["transit_hf_domain"] for r in domain_rows])

        # Only include rows where domain HF is valid
        valid = ~np.isnan(hf_domain)
        n_valid = int(valid.sum())

        corr_global = _safe_corr(valences, hf_global)
        corr_domain = _safe_corr(valences[valid], hf_domain[valid]) if n_valid >= 3 else float("nan")
        d_global = _cohens_d(hf_global, valences)
        d_domain = _cohens_d(hf_domain[valid], valences[valid]) if n_valid >= 3 else float("nan")

        table.append({
            "house": house,
            "n_events": len(domain_rows),
            "n_positive": int((valences > 0).sum()),
            "n_negative": int((valences < 0).sum()),
            "corr_global": corr_global,
            "corr_domain": corr_domain,
            "cohens_d_global": d_global,
            "cohens_d_domain": d_domain,
            "improvement_corr": (corr_domain - corr_global)
                if not (np.isnan(corr_global) or np.isnan(corr_domain)) else float("nan"),
        })

    return table


def render_report(table: List[dict], all_rows: List[dict]) -> str:
    """Render markdown report."""
    lines = [
        "# Domain Correlation Report — HF por Casa",
        "",
        f"Total events analysed: {len(all_rows)}",
        "",
        "## Hypothesis",
        "corr(HF_domain, valence_domain) > corr(HF_global, valence_domain)",
        "",
        "## Results by House Domain",
        "",
        "| Casa | N eventos | N+ | N- | corr_global | corr_domain | d_global | d_domain | Δcorr |",
        "|------|-----------|----|----|-------------|-------------|----------|----------|-------|",
    ]

    def _fmt(v) -> str:
        if isinstance(v, float) and np.isnan(v):
            return "n/a"
        if isinstance(v, float):
            return f"{v:+.3f}"
        return str(v)

    for row in table:
        lines.append(
            f"| {row['house']:4d} "
            f"| {row['n_events']:9d} "
            f"| {row['n_positive']:2d} "
            f"| {row['n_negative']:2d} "
            f"| {_fmt(row['corr_global']):11s} "
            f"| {_fmt(row['corr_domain']):11s} "
            f"| {_fmt(row['cohens_d_global']):8s} "
            f"| {_fmt(row['cohens_d_domain']):8s} "
            f"| {_fmt(row['improvement_corr']):5s} |"
        )

    hypothesis_passed = sum(
        1 for r in table
        if not (np.isnan(r["corr_global"]) or np.isnan(r["corr_domain"]))
        and r["corr_domain"] > r["corr_global"]
    )
    total_valid = sum(
        1 for r in table
        if not (np.isnan(r["corr_global"]) or np.isnan(r["corr_domain"]))
    )

    lines += [
        "",
        "## Summary",
        "",
        f"Hypothesis confirmed in {hypothesis_passed}/{total_valid} domains with valid data.",
        "",
        "## Notes",
        "- `corr_domain`: correlation of domain-filtered HF vs valence for same-domain events.",
        "- `corr_global`: correlation of global HF vs valence for same-domain events (baseline).",
        "- `Δcorr`: corr_domain - corr_global (positive = hypothesis confirmed).",
        "- Cohen's d: effect size between positive and negative events.",
    ]

    return "\n".join(lines)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s",
                        stream=sys.stdout)

    print("Loading v2 events and computing transit HF (global + domain)...")
    rows = process_all_subjects()
    print(f"Processed {len(rows)} events with HF computed.")

    table = compute_domain_table(rows)

    # ── Print table ──────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("DOMAIN CORRELATION RESULTS")
    print(f"{'Casa':>4}  {'N':>5}  {'corr_global':>11}  {'corr_domain':>11}  "
          f"{'d_global':>8}  {'d_domain':>8}  {'Dcorr':>6}")
    print("-" * 80)
    for row in table:
        def _f(v):
            return f"{v:+.3f}" if not (isinstance(v, float) and np.isnan(v)) else "  n/a"
        print(f"  H{row['house']:02d}  {row['n_events']:5d}  "
              f"{_f(row['corr_global']):>11s}  {_f(row['corr_domain']):>11s}  "
              f"{_f(row['cohens_d_global']):>8s}  {_f(row['cohens_d_domain']):>8s}  "
              f"{_f(row['improvement_corr']):>6s}")
    print("=" * 80)

    # ── Save report ──────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "domain_correlation_report.md"
    report_path.write_text(render_report(table, rows), encoding="utf-8")
    print(f"\nMarkdown report saved -> {report_path}")

    json_path = OUTPUT_DIR / "domain_correlation_results.json"
    json_path.write_text(
        json.dumps({"table": table, "n_events": len(rows)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"JSON data saved       -> {json_path}")


if __name__ == "__main__":
    main()
