from datetime import datetime, timezone

from abu_engine.core.houses_swiss import (
    calculate_houses,
    HOUSE_SYSTEM_PLACIDUS,
    HOUSE_SYSTEM_WHOLE_SIGN,
)


def test_high_latitude_falls_back_to_whole_sign():
    dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    lat = 70.0
    lon = 0.0

    data = calculate_houses(dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)

    assert "cusps" in data and len(data["cusps"]) == 12
    assert data.get("house_system_used") == HOUSE_SYSTEM_WHOLE_SIGN.decode("ascii")


def test_placidus_default_when_in_range():
    dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    lat = 40.0
    lon = -3.7

    data = calculate_houses(dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)

    assert data.get("house_system_used") == HOUSE_SYSTEM_PLACIDUS.decode("ascii")
    assert len(data["cusps"]) == 12
