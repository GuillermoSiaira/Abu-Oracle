import pytest
from datetime import timezone, datetime

from abu_engine.utils.time import normalize_to_utc


@pytest.mark.parametrize(
    "value,default_tz,expected",
    [
        ("1990-01-01T12:00:00Z", "UTC", "1990-01-01T12:00:00+00:00"),
        ("1990-01-01T12:00:00+03:00", "UTC", "1990-01-01T09:00:00+00:00"),
        ("1990-01-01T12:00:00-05:00", "UTC", "1990-01-01T17:00:00+00:00"),
        ("1990-01-01T12:00:00", "UTC", "1990-01-01T12:00:00+00:00"),
        ("1990-01-01T12:00:00", "America/Argentina/Buenos_Aires", "1990-01-01T15:00:00+00:00"),
        ("1650-06-01T08:30:00Z", "UTC", "1650-06-01T08:30:00+00:00"),
    ],
)
def test_normalize_valid_cases(value, default_tz, expected):
    dt = normalize_to_utc(value, default_tz)
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None
    assert dt.tzinfo == timezone.utc
    assert dt.isoformat() == expected


@pytest.mark.parametrize(
    "value,default_tz",
    [
        ("not-a-date", "UTC"),
        ("1990-13-40T99:99:99", "UTC"),
        ("", "UTC"),
        (None, "UTC"),  # type: ignore[arg-type]
    ],
)
def test_normalize_invalid_cases(value, default_tz):
    with pytest.raises(ValueError):
        normalize_to_utc(value, default_tz)


def test_naive_without_default_timezone():
    with pytest.raises(ValueError):
        normalize_to_utc("1990-01-01T12:00:00", default_timezone=None)
