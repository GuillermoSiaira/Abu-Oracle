"""Generate HF Core v3 relocation grids (additive angles/houses).

Clones the v2 relocation pipeline but swaps in HF v3 additive scoring
and stores explicit grid indices for safe reshaping downstream.
"""

from __future__ import annotations

import sys
import re
from datetime import datetime, date, time, timezone, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
ABU_ROOT = REPO_ROOT / "abu_engine"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(ABU_ROOT) not in sys.path:
    sys.path.insert(0, str(ABU_ROOT))

from abu_engine.core.chart import chart_json  # type: ignore
from abu_engine.core.houses_swiss import (  # type: ignore
    HOUSE_SYSTEM_PLACIDUS,
    calculate_houses,
)
from abu_engine.harmony.field_v3 import compute_hf_v3


EXPERIMENT_VERSION = "HF_RELOC_v3"
GRID_STEP_DEG = 5.0
HOUSE_SYSTEM = "Placidus"

DATASET_PATH = REPO_ROOT / "data" / "processed" / "hf_dataset_v2.parquet"
OUTPUT_DIR = REPO_ROOT / "output" / "relocation_fields_v3"

GRID_LAT_START, GRID_LAT_END = -80.0, 80.0
GRID_LON_START, GRID_LON_END = -180.0, 180.0

REQUIRED_COLUMNS = [
    "subject_id",
    "name",
    "birth_datetime",
    "latitude",
    "longitude",
]

TZ_PATTERN = re.compile(r"^[+-]?\d{1,2}:\d{2}:\d{2}$")


def generate_grid(step: float = GRID_STEP_DEG) -> List[Tuple[int, int, float, float]]:
    def frange(start: float, end: float, step_val: float) -> Iterable[float]:
        n = int(round((end - start) / step_val))
        for i in range(n + 1):
            yield round(start + i * step_val, 6)

    lats = list(frange(GRID_LAT_START, GRID_LAT_END, step))
    lons = list(frange(GRID_LON_START, GRID_LON_END, step))
    grid: List[Tuple[int, int, float, float]] = []
    for lat_idx, lat in enumerate(lats):
        for lon_idx, lon in enumerate(lons):
            grid.append((lat_idx, lon_idx, lat, lon))
    return grid


def parse_date(value: str) -> date:
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def parse_time(value: str) -> time:
    return datetime.strptime(str(value), "%H:%M:%S").time()


def parse_timezone_offset(tz_str: str) -> timezone:
    tz_clean = str(tz_str).strip()
    if not TZ_PATTERN.match(tz_clean):
        raise ValueError(f"Invalid timezone offset: {tz_str}")
    sign = -1 if tz_clean.startswith("-") else 1
    hh, mm, ss = map(int, tz_clean.lstrip("+-").split(":"))
    if mm >= 60 or ss >= 60:
        raise ValueError(f"Invalid timezone offset minutes/seconds: {tz_str}")
    total_seconds = sign * (hh * 3600 + mm * 60 + ss)
    if not (-14 * 3600 <= total_seconds <= 14 * 3600):
        raise ValueError(f"Timezone offset out of bounds: {tz_str}")
    return timezone(timedelta(seconds=total_seconds))


def ensure_birth_datetime(df: pd.DataFrame) -> pd.DataFrame:
    if "birth_datetime" in df.columns:
        return df
    required = ["birth_date", "birth_time", "timezone"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Dataset missing columns to build birth_datetime: {missing}")

    datetimes = []
    for _, row in df.iterrows():
        d = parse_date(row["birth_date"])
        t = parse_time(row["birth_time"])
        tz = parse_timezone_offset(row["timezone"])
        local_dt = datetime.combine(d, t, tzinfo=tz)
        datetimes.append(local_dt.astimezone(timezone.utc))

    df = df.copy()
    df["birth_datetime"] = datetimes
    return df


def compute_hf_metrics_v3(angles_deg: Dict[str, float], cusps: List[float]) -> Dict[str, float]:
    hf = compute_hf_v3(angles_deg, cusps=cusps)
    return {
        "hf_total_v3": float(hf.get("hf_total_v3", float("nan"))),
        "hf_aspects": float(hf.get("hf_aspects", float("nan"))),
        "hf_angles": float(hf.get("hf_angles", float("nan"))),
        "hf_houses": float(hf.get("hf_houses", float("nan"))),
    }


def compute_natal_hf(subject: pd.Series, planet_positions: Dict[str, float]) -> Dict[str, float]:
    birth_dt: datetime = subject["birth_datetime"]
    lat = float(subject["latitude"])
    lon = float(subject["longitude"])

    houses = calculate_houses(birth_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
    cusps = list(houses.get("cusps", []))
    angles = dict(planet_positions)
    angles["ASC"] = float(houses["asc"])
    angles["MC"] = float(houses["mc"])

    metrics = compute_hf_metrics_v3(angles, cusps)
    return {
        "angles": angles,
        "asc": angles["ASC"],
        "mc": angles["MC"],
        "cusps": cusps,
        **metrics,
    }


def compute_relocation_hf(
    birth_dt: datetime,
    rel_lat: float,
    rel_lon: float,
    planet_positions: Dict[str, float],
) -> Tuple[bool, str, Dict[str, float]]:
    try:
        houses = calculate_houses(birth_dt, rel_lat, rel_lon, HOUSE_SYSTEM_PLACIDUS)
        cusps = list(houses.get("cusps", []))
        angles = dict(planet_positions)
        angles["ASC"] = float(houses["asc"])
        angles["MC"] = float(houses["mc"])
        metrics = compute_hf_metrics_v3(angles, cusps)
        metrics.update({"asc": angles["ASC"], "mc": angles["MC"]})
        return True, "", metrics
    except Exception:
        return False, "house_fail", {}


def process_subject(subject: pd.Series, grid: List[Tuple[int, int, float, float]]) -> pd.DataFrame:
    birth_dt: datetime = subject["birth_datetime"]
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=timezone.utc)

    chart = chart_json(float(subject["latitude"]), float(subject["longitude"]), birth_dt)
    planet_positions = {p.name: float(p.lon) for p in chart.planets}

    natal = compute_natal_hf(subject, planet_positions)

    rows = []
    processed_at = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    for idx, (lat_idx, lon_idx, rel_lat, rel_lon) in enumerate(grid, start=1):
        valid, error_type, metrics = compute_relocation_hf(birth_dt, rel_lat, rel_lon, planet_positions)

        row = {
            "subject_id": subject["subject_id"],
            "name": subject.get("name", ""),
            "birth_datetime": birth_dt.isoformat(),
            "natal_latitude": float(subject["latitude"]),
            "natal_longitude": float(subject["longitude"]),
            "relocation_latitude": rel_lat,
            "relocation_longitude": rel_lon,
            "grid_lat_index": lat_idx,
            "grid_lon_index": lon_idx,
            "asc_lon": float(metrics.get("asc", float("nan"))),
            "mc_lon": float(metrics.get("mc", float("nan"))),
            "hf_total_v3": float(metrics.get("hf_total_v3", float("nan"))),
            "hf_aspects": float(metrics.get("hf_aspects", float("nan"))),
            "hf_angles": float(metrics.get("hf_angles", float("nan"))),
            "hf_houses": float(metrics.get("hf_houses", float("nan"))),
            "delta_hf_total_v3": float(metrics.get("hf_total_v3", float("nan"))) - float(natal["hf_total_v3"])
            if valid
            else float("nan"),
            "delta_hf_aspects": float(metrics.get("hf_aspects", float("nan"))) - float(natal["hf_aspects"])
            if valid
            else float("nan"),
            "delta_hf_angles": float(metrics.get("hf_angles", float("nan"))) - float(natal["hf_angles"])
            if valid
            else float("nan"),
            "delta_hf_houses": float(metrics.get("hf_houses", float("nan"))) - float(natal["hf_houses"])
            if valid
            else float("nan"),
            "valid_flag": bool(valid),
            "error_type": error_type,
            "experiment_version": EXPERIMENT_VERSION,
            "grid_step_deg": GRID_STEP_DEG,
            "house_system": HOUSE_SYSTEM,
            "processed_at": processed_at,
        }
        rows.append(row)

        if idx % 200 == 0 or idx == len(grid):
            print(f"Grid point {idx}/{len(grid)}")

    columns = [
        "subject_id",
        "name",
        "birth_datetime",
        "natal_latitude",
        "natal_longitude",
        "relocation_latitude",
        "relocation_longitude",
        "grid_lat_index",
        "grid_lon_index",
        "asc_lon",
        "mc_lon",
        "hf_total_v3",
        "hf_aspects",
        "hf_angles",
        "hf_houses",
        "delta_hf_total_v3",
        "delta_hf_aspects",
        "delta_hf_angles",
        "delta_hf_houses",
        "valid_flag",
        "error_type",
        "experiment_version",
        "grid_step_deg",
        "house_system",
        "processed_at",
    ]

    return pd.DataFrame(rows, columns=columns)


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Input dataset not found: {DATASET_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(DATASET_PATH)
    df = ensure_birth_datetime(df)

    if "subject_id" not in df.columns:
        if "id" in df.columns:
            df["subject_id"] = df["id"]
        else:
            raise KeyError("Dataset missing subject_id/id column")

    if "birth_datetime" not in df.columns:
        raise KeyError("Dataset missing birth_datetime column")

    required_missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if required_missing:
        raise KeyError(f"Dataset missing required columns: {required_missing}")

    grid = generate_grid()

    for idx, subj in enumerate(df.itertuples(index=False), start=1):
        s = subj._asdict()
        sid = s["subject_id"]
        name = s.get("name", "")
        print(f"[{idx}/{len(df)}] {name} (id={sid})")

        df_sub = process_subject(pd.Series(s), grid)
        out_path = OUTPUT_DIR / f"subject_{sid}.parquet"
        df_sub.to_parquet(out_path, index=False)


if __name__ == "__main__":
    main()
