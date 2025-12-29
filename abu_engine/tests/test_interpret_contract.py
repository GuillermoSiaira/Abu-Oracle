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

import main  # noqa: E402

client = TestClient(main.app)


def test_interpret_contract_shape():
    """Verifica que /api/astro/interpret devuelva el contrato esperado de Lilly."""
    payload = {
        "birthDate": "1990-01-01T12:00:00Z",
        "lat": -34.6037,
        "lon": -58.3816,
        "language": "es"
    }

    r = client.post("/api/astro/interpret", json=payload)
    
    # Lilly puede estar caída (502) o responder (200)
    assert r.status_code in (200, 502), f"Expected 200 or 502, got {r.status_code}"
    
    if r.status_code == 200:
        data = r.json()
        
        # Validar llaves del contrato de Lilly
        assert "headline" in data, "Missing 'headline' in response"
        assert "narrative" in data, "Missing 'narrative' in response"
        assert "actions" in data, "Missing 'actions' in response"
        assert "astro_metadata" in data, "Missing 'astro_metadata' in response"
        
        # Validar tipos básicos
        assert isinstance(data["headline"], str)
        assert isinstance(data["narrative"], str)
        assert isinstance(data["actions"], list)
        assert isinstance(data["astro_metadata"], dict)


def test_interpret_missing_params():
    """Verifica que /api/astro/interpret retorne 422 si faltan parámetros (Pydantic validation)."""
    # Sin birthDate (Pydantic falla validación)
    r = client.post("/api/astro/interpret", json={"lat": -34.6, "lon": -58.4})
    assert r.status_code == 422
    
    # Sin lat
    r = client.post("/api/astro/interpret", json={"birthDate": "1990-01-01T12:00:00Z", "lon": -58.4})
    assert r.status_code == 422


def test_interpret_invalid_date():
    """Verifica que /api/astro/interpret retorne 422 si el formato de fecha es inválido."""
    r = client.post("/api/astro/interpret", json={
        "birthDate": "invalid-date",
        "lat": -34.6,
        "lon": -58.4
    })
    assert r.status_code == 422
