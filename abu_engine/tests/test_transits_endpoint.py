import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from abu_engine.main import app

client = TestClient(app)


def _get_natal_planets(date_iso: str, lat: float, lon: float):
    resp = client.get(
        "/api/astro/chart",
        params={"date": date_iso, "lat": lat, "lon": lon},
    )
    assert resp.status_code == 200
    data = resp.json()
    return [
        {"name": p["name"], "longitude": p["lon"]}
        for p in data["planets"]
    ]


def test_get_transits_returns_conjunction_same_date():
    date_iso = "2026-01-01T00:00:00Z"
    lat = 0.0
    lon = 0.0
    natal_planets = _get_natal_planets(date_iso, lat, lon)

    resp = client.get(
        "/api/astro/transits",
        params={
            "natalPlanets": json.dumps(natal_planets),
            "date": date_iso,
            "lat": lat,
            "lon": lon,
            "includeMajorOnly": False,
            "includeMinor": False,
        },
    )
    assert resp.status_code == 200
    transits = resp.json()

    assert any(
        t["natal_planet"] == "Sun"
        and t["transit_planet"] == "Sun"
        and t["aspect"] == "conjunction"
        and abs(t["orb"]) < 0.1
        for t in transits
    ), "Expected Sun conjunction with orb ~0 when natal = transit date"


def test_post_transits_with_natal_works():
    birth_iso = "1990-01-01T12:00:00Z"
    transit_iso = "2026-01-01T00:00:00Z"
    lat = -34.6
    lon = -58.4

    payload = {
        "birthDate": birth_iso,
        "birthLat": lat,
        "birthLon": lon,
        "transitDate": transit_iso,
        "transitLat": lat,
        "transitLon": lon,
        "includeMajorOnly": False,
        "includeMinor": False,
    }

    resp = client.post("/api/astro/transits/with-natal", json=payload)
    assert resp.status_code == 200
    transits = resp.json()
    assert isinstance(transits, list)
    assert len(transits) > 0

    # Should contain at least one transit involving Sun or Moon (outer filter off)
    assert any(t["natal_planet"] in {"Sun", "Moon"} for t in transits)
