from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional


def normalize_to_utc(iso_datetime: str, default_timezone: Optional[str] = "UTC") -> datetime:
    """
    Normaliza un string ISO8601 a datetime timezone-aware en UTC.

    - Acepta sufijo 'Z', offsets (+02:00, -05:00) o datetime naive.
    - Si es naive y default_timezone es None ? ValueError.
    - Usa solo stdlib (datetime, zoneinfo).
    - No retorna skyfield.Time.
    """
    if iso_datetime is None:
        raise ValueError("iso_datetime is required (got None)")
    if not isinstance(iso_datetime, str) or not iso_datetime.strip():
        raise ValueError("iso_datetime must be a non-empty ISO8601 string")

    raw = iso_datetime.strip()
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw

    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO8601 datetime: {iso_datetime}") from exc

    if dt.tzinfo is None:
        if not default_timezone:
            raise ValueError("Naive datetime requires a default_timezone")
        try:
            tz = ZoneInfo(default_timezone)
        except Exception as exc:
            raise ValueError(f"Unknown timezone: {default_timezone}") from exc
        dt = dt.replace(tzinfo=tz)

    return dt.astimezone(timezone.utc)
