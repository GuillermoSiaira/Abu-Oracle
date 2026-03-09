"""Bridge script: raw natal dataset → HF Core v1 features (36D) with Abu Engine.

Usage:
    python scripts/generate_hf_dataset.py \
      --input data/raw/raw_birthdata.jsonl \
      --output data/processed/hf_dataset_v1.parquet \
      --failures data/processed/hf_dataset_v1_failures.jsonl \
      --summary data/processed/hf_dataset_v1_summary.json
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, date, time, timezone, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
from tqdm import tqdm

# Abu Engine + HF Core imports
from abu_engine.harmony import (
    POINT_ORDER,
    build_circle_vector,
    compute_harmonics,
    aggregate_field,
)
from abu_engine.core.chart import chart_json
from abu_engine.core.houses_swiss import calculate_houses, HOUSE_SYSTEM_PLACIDUS


LOGGER = logging.getLogger("generate_hf_dataset")

PIPELINE_VERSION = "hf_dataset_v1"
HF_CORE_VERSION = "HF Core v1"

TZ_PATTERN = re.compile(r"^[+-]?\d{1,2}:\d{2}:\d{2}$")


@dataclass
class Paths:
    input_path: Path
    output_path: Path
    failures_path: Path
    summary_path: Path

    def ensure_dirs(self) -> None:
        for p in [self.output_path, self.failures_path, self.summary_path]:
            p.parent.mkdir(parents=True, exist_ok=True)


# -------------------- Parsing helpers --------------------


def parse_date(value: str) -> Optional[date]:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def parse_time(value: str) -> Optional[time]:
    try:
        return datetime.strptime(value, "%H:%M:%S").time()
    except Exception:
        return None


def parse_timezone_offset(tz_str: str) -> Optional[timezone]:
    if tz_str is None:
        return None
    tz_clean = str(tz_str).strip()
    if not TZ_PATTERN.match(tz_clean):
        return None
    sign = -1 if tz_clean.startswith("-") else 1
    hh, mm, ss = map(int, tz_clean.lstrip("+-").split(":"))
    if mm >= 60 or ss >= 60:
        return None
    total_seconds = sign * (hh * 3600 + mm * 60 + ss)
    # Practical bounds
    if not (-14 * 3600 <= total_seconds <= 14 * 3600):
        return None
    return timezone(timedelta(seconds=total_seconds))


def trust_score_from_source(source: Optional[str]) -> float:
    if source is None or (isinstance(source, float) and math.isnan(source)):
        return 0.5
    text = str(source).lower()
    if "certificado" in text or "registro nacimiento" in text:
        return 1.0
    if any(term in text for term in ["memorias", "bio", "noticias", "cartas natales"]):
        return 0.7
    if any(term in text for term in ["sin confirmar", "contradictoria"]):
        return 0.3
    return 0.5


def angles_from_chart(lat: float, lon: float, dt_utc: datetime) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Compute planetary angles and houses (ASC/MC) using Abu Engine primitives."""
    chart = chart_json(lat, lon, dt_utc)
    planet_positions = {p.name: float(p.lon) % 360.0 for p in chart.planets}

    houses_data = calculate_houses(dt_utc, lat, lon, HOUSE_SYSTEM_PLACIDUS)
    asc = float(houses_data["asc"]) % 360.0
    mc = float(houses_data["mc"]) % 360.0

    angles: Dict[str, float] = {
        **planet_positions,
        "ASC": asc,
        "MC": mc,
    }
    return angles, planet_positions


def validate_row(row: pd.Series) -> Optional[str]:
    if str(row.get("time_precision", "")).strip().lower() != "exact":
        return "time_precision_not_exact"
    if pd.isna(row.get("birth_date")):
        return "missing_birth_date"
    if pd.isna(row.get("birth_time")):
        return "missing_birth_time"
    if pd.isna(row.get("latitude")) or pd.isna(row.get("longitude")):
        return "missing_coordinates"
    tz = parse_timezone_offset(row.get("timezone"))
    if tz is None:
        return "invalid_timezone"
    if parse_date(str(row.get("birth_date"))) is None:
        return "invalid_birth_date"
    if parse_time(str(row.get("birth_time"))) is None:
        return "invalid_birth_time"
    return None


def build_local_and_utc(row: pd.Series) -> Tuple[datetime, datetime, timezone]:
    d = parse_date(str(row["birth_date"]))
    t = parse_time(str(row["birth_time"]))
    tz = parse_timezone_offset(row.get("timezone"))
    if d is None or t is None or tz is None:
        raise ValueError("Invalid datetime components")
    local_dt = datetime.combine(d, t, tzinfo=tz)
    return local_dt, local_dt.astimezone(timezone.utc), tz


def harmonic_features(angles_deg: Dict[str, float]) -> Dict[str, float]:
    angle_list = [angles_deg[p] for p in POINT_ORDER]
    harmonics = compute_harmonics(angle_list)
    return {f"hk_{k}": float(v) for k, v in harmonics.items()}


def circle_vector_features(angles_deg: Dict[str, float]) -> Dict[str, float]:
    cv = build_circle_vector(angles_deg)
    return {f"cv_{i:02d}": float(v) for i, v in enumerate(cv, start=1)}


def field_features(angles_deg: Dict[str, float]) -> Dict[str, float]:
    field = aggregate_field(angles_deg)
    return {
        "hf_total": float(field["HF_total"]),
        "hf_harmony": float(field["HF_harmony"]),
        "hf_tension": float(field["HF_tension"]),
        "hf_conjunction": float(field["HF_conjunction"]),
    }


def deterministic_column_order() -> List[str]:
    base_cols = [
        "id",
        "name",
        "birth_date",
        "birth_time",
        "time_precision",
        "timezone",
        "latitude",
        "longitude",
        "source",
        "url",
        "trust_score",
    ]
    lon_cols = [
        "sun_lon",
        "moon_lon",
        "mercury_lon",
        "venus_lon",
        "mars_lon",
        "jupiter_lon",
        "saturn_lon",
        "uranus_lon",
        "neptune_lon",
        "pluto_lon",
        "asc_lon",
        "mc_lon",
    ]
    cv_cols = [f"cv_{i:02d}" for i in range(1, 25)]
    hk_cols = ["hk_1", "hk_2", "hk_3", "hk_4", "hk_5", "hk_6", "hk_8", "hk_12"]
    hf_cols = ["hf_total", "hf_harmony", "hf_tension", "hf_conjunction"]
    meta_cols = ["pipeline_version", "hf_core_version", "processed_at"]
    return base_cols + lon_cols + cv_cols + hk_cols + hf_cols + meta_cols


# -------------------- Main pipeline --------------------


def process_row(row: pd.Series, processed_at_iso: str) -> Tuple[Optional[Dict[str, object]], Optional[Dict[str, object]]]:
    """Process a single row, returning (success_record, failure_record)."""
    reason = validate_row(row)
    if reason:
        return None, {
            "id": row.get("id"),
            "name": row.get("name"),
            "reason": reason,
            "birth_date": row.get("birth_date"),
            "birth_time": row.get("birth_time"),
            "timezone": row.get("timezone"),
        }

    try:
        local_dt, utc_dt, tz = build_local_and_utc(row)
        angles, planet_positions = angles_from_chart(
            float(row["latitude"]), float(row["longitude"]), utc_dt
        )
        # Ensure all required points exist
        missing = [p for p in POINT_ORDER if p not in angles]
        if missing:
            raise ValueError(f"missing_points:{','.join(missing)}")

        angle_list = {p: float(angles[p]) % 360.0 for p in POINT_ORDER}

        record: Dict[str, object] = {
            "id": row.get("id"),
            "name": row.get("name"),
            "birth_date": row.get("birth_date"),
            "birth_time": row.get("birth_time"),
            "time_precision": row.get("time_precision"),
            "timezone": row.get("timezone"),
            "latitude": float(row.get("latitude")),
            "longitude": float(row.get("longitude")),
            "source": row.get("source"),
            "url": row.get("url"),
            "trust_score": trust_score_from_source(row.get("source")),
            # Longitudes
            "sun_lon": angle_list["Sun"],
            "moon_lon": angle_list["Moon"],
            "mercury_lon": angle_list["Mercury"],
            "venus_lon": angle_list["Venus"],
            "mars_lon": angle_list["Mars"],
            "jupiter_lon": angle_list["Jupiter"],
            "saturn_lon": angle_list["Saturn"],
            "uranus_lon": angle_list["Uranus"],
            "neptune_lon": angle_list["Neptune"],
            "pluto_lon": angle_list["Pluto"],
            "asc_lon": angle_list["ASC"],
            "mc_lon": angle_list["MC"],
        }

        record.update(circle_vector_features(angle_list))
        record.update(harmonic_features(angle_list))
        record.update(field_features(angle_list))

        record.update(
            {
                "pipeline_version": PIPELINE_VERSION,
                "hf_core_version": HF_CORE_VERSION,
                "processed_at": processed_at_iso,
            }
        )
        return record, None

    except Exception as e:
        return None, {
            "id": row.get("id"),
            "name": row.get("name"),
            "reason": str(e),
            "birth_date": row.get("birth_date"),
            "birth_time": row.get("birth_time"),
            "timezone": row.get("timezone"),
        }


def write_failures(failures_path: Path, failures: List[Dict[str, object]]) -> None:
    with failures_path.open("w", encoding="utf-8") as f:
        for entry in failures:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def compute_summary(
    total_input: int,
    eligible: int,
    successes: pd.DataFrame,
    failures_count: int,
    skipped_count: int,
) -> Dict[str, object]:
    def stats(series: pd.Series) -> Dict[str, float]:
        if series.empty:
            return {"mean": None, "std": None, "min": None, "max": None}
        return {
            "mean": float(series.mean()),
            "std": float(series.std(ddof=0)),
            "min": float(series.min()),
            "max": float(series.max()),
        }

    return {
        "total_input_rows": total_input,
        "total_eligible_rows": eligible,
        "total_successful_rows": int(len(successes)),
        "total_failed_rows": failures_count,
        "total_skipped_rows": skipped_count,
        "hf_total": stats(successes.get("hf_total", pd.Series(dtype=float))),
        "hf_harmony": stats(successes.get("hf_harmony", pd.Series(dtype=float))),
        "hf_tension": stats(successes.get("hf_tension", pd.Series(dtype=float))),
        "hf_conjunction": stats(successes.get("hf_conjunction", pd.Series(dtype=float))),
    }


def parse_args() -> Paths:
    parser = argparse.ArgumentParser(description="Generate HF Core v1 dataset from raw natal data")
    parser.add_argument("--input", type=Path, required=True, help="Path to raw_birthdata.jsonl")
    parser.add_argument("--output", type=Path, required=True, help="Output Parquet path")
    parser.add_argument("--failures", type=Path, required=True, help="Failures JSONL path")
    parser.add_argument("--summary", type=Path, required=True, help="Summary JSON path")
    args = parser.parse_args()
    return Paths(args.input, args.output, args.failures, args.summary)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def main() -> None:
    configure_logging()
    paths = parse_args()
    paths.ensure_dirs()

    LOGGER.info("Loading raw dataset: %s", paths.input_path)
    df = pd.read_json(paths.input_path, lines=True)
    total_input = len(df)
    LOGGER.info("Loaded %d rows", total_input)

    processed_at_iso = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    records: List[Dict[str, object]] = []
    failures: List[Dict[str, object]] = []

    eligible_count = 0
    skipped_count = 0

    for _, row in tqdm(df.iterrows(), total=total_input, desc="Processing"):
        success, failure = process_row(row, processed_at_iso)
        if failure and failure.get("reason", "").startswith("time_precision_not_exact"):
            skipped_count += 1
            failures.append(failure)
            continue

        if failure and failure.get("reason") in {
            "missing_birth_date",
            "missing_birth_time",
            "invalid_birth_date",
            "invalid_birth_time",
            "invalid_timezone",
            "missing_coordinates",
        }:
            skipped_count += 1
            failures.append(failure)
            continue

        eligible_count += 1

        if success:
            records.append(success)
        if failure and not success:
            failures.append(failure)

    successes_df = pd.DataFrame(records)

    # Enforce deterministic column order
    cols = deterministic_column_order()
    successes_df = successes_df.reindex(columns=cols)

    # Persist outputs
    LOGGER.info("Writing dataset to %s", paths.output_path)
    successes_df.to_parquet(paths.output_path, index=False)

    LOGGER.info("Writing failures to %s", paths.failures_path)
    write_failures(paths.failures_path, failures)

    summary = compute_summary(
        total_input=total_input,
        eligible=eligible_count,
        successes=successes_df,
        failures_count=len(failures) - skipped_count,
        skipped_count=skipped_count,
    )
    LOGGER.info("Summary: %s", summary)
    paths.summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
