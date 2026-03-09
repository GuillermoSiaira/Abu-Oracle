"""Audit script for raw astrological birth dataset.

Analyzes `raw_birthdata.jsonl` and generates diagnostic artifacts in `audit_output/`:

- dataset_overview.json
- field_completeness.csv
- categorical_distributions.json
- geo_anomalies.csv
- temporal_distribution.json
- reliability_distribution.json
- duplicate_records.csv
- dataset_anomalies.csv
- dataset_audit_report.md

Run:
    python scripts/audit_raw_birthdata.py raw_birthdata.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd


LOGGER = logging.getLogger("audit_raw_birthdata")


# -------------------- Data containers --------------------


@dataclass
class AuditPaths:
    dataset_path: Path
    output_dir: Path

    def ensure_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)


# -------------------- Helpers --------------------


def load_dataset(path: Path) -> pd.DataFrame:
    """Load JSONL dataset into a DataFrame."""
    LOGGER.info("Loading dataset: %s", path)
    df = pd.read_json(path, lines=True)
    LOGGER.info("Loaded %d records with %d fields", len(df), len(df.columns))
    return df


def compute_dataset_overview(df: pd.DataFrame) -> Dict[str, object]:
    """Compute basic overview: total records, schema, field types."""
    overview = {
        "total_records": int(len(df)),
        "fields": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
    return overview


def compute_field_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Compute null counts, null percent, and unique values per field."""
    total = len(df)
    rows = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        unique_values = int(df[col].nunique(dropna=True))
        rows.append(
            {
                "field": col,
                "total": total,
                "null_count": null_count,
                "null_percent": round((null_count / total) * 100, 3) if total else 0.0,
                "unique_values": unique_values,
            }
        )
    return pd.DataFrame(rows)


def compute_categorical_distributions(
    df: pd.DataFrame, fields: Iterable[str]
) -> Dict[str, Dict[str, int]]:
    """Frequency counts for selected categorical fields (including nulls)."""
    distributions: Dict[str, Dict[str, int]] = {}
    for field in fields:
        if field not in df.columns:
            continue
        counts = df[field].fillna("<NULL>").astype(str).value_counts()
        distributions[field] = counts.to_dict()
    return distributions


def angular_in_range(value: Optional[float], min_val: float, max_val: float) -> bool:
    return value is not None and pd.notna(value) and (min_val <= value <= max_val)


def detect_geo_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Rows with latitude/longitude missing or out of expected bounds."""
    lat_ok = df["latitude"].apply(lambda v: angular_in_range(v, -90, 90)) if "latitude" in df else pd.Series([], dtype=bool)
    lon_ok = df["longitude"].apply(lambda v: angular_in_range(v, -180, 180)) if "longitude" in df else pd.Series([], dtype=bool)

    mask_invalid = (~lat_ok) | (~lon_ok)
    anomalies = df[mask_invalid].copy()
    return anomalies[[c for c in ["id", "name", "latitude", "longitude", "city", "country"] if c in anomalies.columns]]


def parse_birth_dates(df: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(df.get("birth_date"), errors="coerce")


def compute_temporal_distribution(df: pd.DataFrame) -> Dict[str, object]:
    dates = parse_birth_dates(df)
    valid_dates = dates.dropna()
    years = valid_dates.dt.year
    year_counts = years.value_counts().sort_index().to_dict()
    earliest = valid_dates.min()
    latest = valid_dates.max()
    return {
        "birth_year_distribution": {int(k): int(v) for k, v in year_counts.items()},
        "earliest_birth": earliest.isoformat() if pd.notna(earliest) else None,
        "latest_birth": latest.isoformat() if pd.notna(latest) else None,
    }


def categorize_reliability(source: Optional[str]) -> str:
    if source is None or (isinstance(source, float) and pd.isna(source)):
        return "unknown"
    text = str(source).lower()
    if "certificado" in text:
        return "high"
    if any(term in text for term in ["memorias", "bio", "noticias", "cartas natales"]):
        return "medium"
    if any(term in text for term in ["sin confirmar", "contradictoria", "fecha sin confirmar"]):
        return "low"
    return "unknown"


def compute_reliability_distribution(df: pd.DataFrame) -> Dict[str, int]:
    categories = df.get("source", pd.Series([], dtype=object)).apply(categorize_reliability)
    return dict(Counter(categories))


TZ_PATTERN = re.compile(r"^[+-]?\d{1,2}:\d{2}:\d{2}$")


def is_valid_timezone_offset(tz: Optional[str]) -> bool:
    if tz is None or (isinstance(tz, float) and pd.isna(tz)):
        return False
    tz_str = str(tz).strip()
    if not TZ_PATTERN.match(tz_str):
        return False
    sign = -1 if tz_str.startswith("-") else 1
    parts = tz_str.lstrip("+-").split(":")
    hours, minutes, seconds = map(int, parts)
    if not (0 <= minutes < 60 and 0 <= seconds < 60):
        return False
    # Allow offsets within [-14, +14] hours (practical global range)
    total_hours = sign * (hours + minutes / 60 + seconds / 3600)
    return -14 <= total_hours <= 14


def detect_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    key_fields = ["name", "birth_date", "city"]
    for field in key_fields:
        if field not in df.columns:
            df[field] = None
    grouped = df.groupby(key_fields, dropna=False)
    dup_mask = grouped["id"].transform("size") > 1
    duplicates = df[dup_mask].copy()
    if not duplicates.empty:
        duplicates["duplicate_count"] = grouped["id"].transform("size")[dup_mask]
    return duplicates[[c for c in ["id", "name", "birth_date", "city", "country", "duplicate_count"] if c in duplicates.columns]]


def detect_dataset_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    records: List[Dict[str, object]] = []

    dates = parse_birth_dates(df)
    invalid_dates_mask = dates.isna()

    timezone_series = df.get("timezone", pd.Series([None] * len(df)))
    timezone_valid_mask = timezone_series.apply(is_valid_timezone_offset)

    coord_missing_mask = (~df.get("latitude", pd.Series([None] * len(df))).notna()) | (
        ~df.get("longitude", pd.Series([None] * len(df))).notna()
    )

    birth_time_missing_mask = df.get("birth_time", pd.Series([None] * len(df))).isna()

    for idx, row in df.iterrows():
        issues: List[str] = []
        if invalid_dates_mask.iloc[idx]:
            issues.append("invalid_birth_date")
        if birth_time_missing_mask.iloc[idx]:
            issues.append("missing_birth_time")
        if not timezone_valid_mask.iloc[idx]:
            issues.append("invalid_timezone")
        if coord_missing_mask.iloc[idx]:
            issues.append("missing_coordinates")
        if issues:
            records.append(
                {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "issues": ";".join(issues),
                    "birth_date": row.get("birth_date"),
                    "birth_time": row.get("birth_time"),
                    "timezone": row.get("timezone"),
                    "latitude": row.get("latitude"),
                    "longitude": row.get("longitude"),
                }
            )

    return pd.DataFrame(records)


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md_report(
    path: Path,
    overview: Dict[str, object],
    reliability_dist: Dict[str, int],
    field_completeness: pd.DataFrame,
    geo_anomalies: pd.DataFrame,
    temporal_info: Dict[str, object],
    anomalies: pd.DataFrame,
    duplicates: pd.DataFrame,
) -> None:
    lines: List[str] = []
    lines.append("# Dataset Audit Report")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- Registros totales: **{overview.get('total_records', 0)}**")
    lines.append(f"- Campos detectados: {len(overview.get('fields', []))}")
    lines.append("")

    lines.append("## Fiabilidad (según `source`)")
    for k, v in sorted(reliability_dist.items()):
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## Cobertura temporal")
    lines.append(f"- Primer nacimiento: {temporal_info.get('earliest_birth')}")
    lines.append(f"- Último nacimiento: {temporal_info.get('latest_birth')}")
    lines.append(f"- Años muestreados: {len(temporal_info.get('birth_year_distribution', {}))}")
    lines.append("")

    lines.append("## Cobertura geográfica")
    lines.append(f"- Anomalías geográficas: {len(geo_anomalies)} filas fuera de rango o con coordenadas faltantes")
    lines.append("")

    lines.append("## Completitud de campos (top 10 nulos)")
    fc_sorted = field_completeness.sort_values("null_percent", ascending=False).head(10)
    for _, row in fc_sorted.iterrows():
        lines.append(
            f"- {row['field']}: {row['null_percent']:.2f}% nulos (unique={row['unique_values']})"
        )
    lines.append("")

    lines.append("## Anomalías detectadas")
    lines.append(f"- Registros con anomalías: {len(anomalies)}")
    lines.append(f"- Registros duplicados (name + birth_date + city): {len(duplicates)}")
    lines.append("")

    lines.append("## Recomendaciones antes de HF")
    lines.append("- Filtrar o revisar registros con `invalid_timezone`, `invalid_birth_date` o coordenadas faltantes.")
    lines.append("- Priorizar fiabilidad 'high' y 'medium' para ASC/MC precisos.")
    lines.append("- Resolver duplicados manualmente o consolidar.")
    lines.append("- Confirmar husos horarios poco comunes (offsets fraccionarios).")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# -------------------- Main audit routine --------------------


def run_audit(paths: AuditPaths) -> None:
    paths.ensure_output_dir()
    df = load_dataset(paths.dataset_path)

    overview = compute_dataset_overview(df)
    field_completeness = compute_field_completeness(df)
    categorical = compute_categorical_distributions(
        df, fields=["time_precision", "timezone", "country", "source", "rodden_rating"]
    )
    geo_anomalies = detect_geo_anomalies(df)
    temporal_info = compute_temporal_distribution(df)
    reliability_dist = compute_reliability_distribution(df)
    duplicates = detect_duplicates(df)
    anomalies = detect_dataset_anomalies(df)

    # Write artifacts
    write_json(paths.output_dir / "dataset_overview.json", overview)
    field_completeness.to_csv(paths.output_dir / "field_completeness.csv", index=False)
    write_json(paths.output_dir / "categorical_distributions.json", categorical)
    geo_anomalies.to_csv(paths.output_dir / "geo_anomalies.csv", index=False)
    write_json(paths.output_dir / "temporal_distribution.json", temporal_info)
    write_json(paths.output_dir / "reliability_distribution.json", reliability_dist)
    duplicates.to_csv(paths.output_dir / "duplicate_records.csv", index=False)
    anomalies.to_csv(paths.output_dir / "dataset_anomalies.csv", index=False)
    write_md_report(
        paths.output_dir / "dataset_audit_report.md",
        overview,
        reliability_dist,
        field_completeness,
        geo_anomalies,
        temporal_info,
        anomalies,
        duplicates,
    )

    LOGGER.info("Audit completed. Outputs written to %s", paths.output_dir)


def parse_args() -> AuditPaths:
    parser = argparse.ArgumentParser(description="Audit raw birth dataset for HF pipeline readiness")
    parser.add_argument("dataset", type=Path, help="Path to raw_birthdata.jsonl")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("audit_output"),
        help="Directory to store audit artifacts",
    )
    args = parser.parse_args()
    return AuditPaths(dataset_path=args.dataset, output_dir=args.output_dir)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


if __name__ == "__main__":
    configure_logging()
    audit_paths = parse_args()
    run_audit(audit_paths)
