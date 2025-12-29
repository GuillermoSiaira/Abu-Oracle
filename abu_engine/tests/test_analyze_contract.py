import json
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure we can import abu_engine/main.py as a top-level module so its
# internal imports like `from core import ...` resolve (as in the container).
ABU_DIR = Path(__file__).resolve().parents[1]
if str(ABU_DIR) not in sys.path:
    sys.path.insert(0, str(ABU_DIR))

import main  # noqa: E402  (import after sys.path tweak)

client = TestClient(main.app)


def test_analyze_contract_shape():
    payload = {
        "person": {"name": "Test", "question": ""},
        "birth": {"date": "1990-01-01T12:00:00Z", "lat": -34.6037, "lon": -58.3816},
        "current": {"lat": -34.6037, "lon": -58.3816}
    }

    r = client.post("/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()

    # Top-level keys
    assert set(["person", "chart", "derived", "question"]).issubset(data.keys())

    # Houses contract
    houses = data["chart"]["houses"]
    assert isinstance(houses, dict)
    assert "houses" in houses and isinstance(houses["houses"], list)
    if houses["houses"]:
        h0 = houses["houses"][0]
        assert set(["house", "start", "end"]).issubset(h0.keys())
        assert isinstance(h0["house"], int)
        assert isinstance(h0["start"], (int, float))
        assert isinstance(h0["end"], (int, float))
    # asc/mc numeric or None
    assert "asc" in houses and "mc" in houses
    assert (houses["asc"] is None) or isinstance(houses["asc"], (int, float))
    assert (houses["mc"] is None) or isinstance(houses["mc"], (int, float))

    # Derived keys
    derived = data["derived"]
    assert set(["sect", "firdaria", "profection", "lunar_transit"]).issubset(derived.keys())
    # firdaria current may be None, but the key must exist
    assert "current" in derived["firdaria"]
    # profection.house exists (may be null)
    assert "house" in derived["profection"]
    # lunar_transit
    lt = derived["lunar_transit"]
    assert "moon_position" in lt and "aspects" in lt
    assert isinstance(lt["aspects"], list)
    if lt["aspects"]:
        a0 = lt["aspects"][0]
        assert set(["planet", "type", "orb"]).issubset(a0.keys())
