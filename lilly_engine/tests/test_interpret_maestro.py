from fastapi.testclient import TestClient
import types
import os
import lilly_engine.main as main

app = main.app
client = TestClient(app)

class DummyResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}
    def json(self):
        return self._payload

class DummyClient:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def get(self, url, params=None):
        # Default successful minimal extended payload
        return DummyResponse(200, {
            "chart": {"planets": [{"name": "Sun", "sign": "Cancer", "house": 10}]},
            "extended": {
                "profections": {"time_lord": "Jupiter", "profected_sign": "Pisces", "monthly": {"month": 4, "monthly_sign": "Aries"}},
                "fardars": {"current": {"major": "Saturn", "sub": "Venus"}},
                "lunar_mansion": {"name": "Al-Tarf"},
                "lots": []
            }
        })


def test_interpret_returns_maestro(monkeypatch):
    # Patch httpx.Client to our dummy
    import httpx
    monkeypatch.setattr(httpx, 'Client', DummyClient)

    payload = {
        "birthDate": "1978-07-05T21:15:00Z",
        "lat": -37.8467,
        "lon": -58.2553,
        "language": "es",
        "include_transits": False,
        "include_solar_return": False
    }
    resp = client.post("/api/ai/interpret", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "maestro" in data
    assert "metadata" in data["maestro"]
    assert data["maestro"]["metadata"]["mode"] == "persian_cosmology"


def test_interpret_handles_abu_500(monkeypatch):
    # Patch httpx.Client.get to return 500
    import httpx

    class ErrClient(DummyClient):
        def get(self, url, params=None):
            return DummyResponse(500, {})

    monkeypatch.setattr(httpx, 'Client', ErrClient)

    payload = {
        "birthDate": "1978-07-05T21:15:00Z",
        "lat": -37.8467,
        "lon": -58.2553,
    }
    resp = client.post("/api/ai/interpret", json=payload)
    assert resp.status_code == 502
    assert "Abu Engine error" in resp.text


def test_interpret_handles_empty_extended(monkeypatch):
    # Patch httpx.Client.get to return 200 but empty body
    import httpx

    class EmptyClient(DummyClient):
        def get(self, url, params=None):
            return DummyResponse(200, {})

    monkeypatch.setattr(httpx, 'Client', EmptyClient)

    payload = {
        "birthDate": "1978-07-05T21:15:00Z",
        "lat": -37.8467,
        "lon": -58.2553,
    }
    resp = client.post("/api/ai/interpret", json=payload)
    assert resp.status_code == 400
