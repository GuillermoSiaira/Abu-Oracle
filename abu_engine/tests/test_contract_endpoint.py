# -*- coding: utf-8 -*-
"""
Test para endpoint /analyze/contract que retorna el JSON schema.
"""
import sys
from pathlib import Path

# Add abu_engine to path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / 'abu_engine'))

from fastapi.testclient import TestClient
from abu_engine.main import app

client = TestClient(app)


def test_analyze_contract_endpoint():
    """Verifica que /analyze/contract retorna un schema válido."""
    response = client.get("/analyze/contract")
    assert response.status_code == 200
    
    data = response.json()
    assert "title" in data
    assert data["title"] == "AnalyzeResponse"
    assert "type" in data
    assert data["type"] == "object"
    assert "required" in data
    assert "chart" in data["required"]
    assert "derived" in data["required"]
    assert "properties" in data
    
    # Verificar que chart tiene planets y houses
    chart_props = data["properties"]["chart"]["properties"]
    assert "planets" in chart_props
    assert "houses" in chart_props
    
    # Verificar que derived tiene sect, firdaria, profection, lunar_transit
    derived_props = data["properties"]["derived"]["properties"]
    assert "sect" in derived_props
    assert "firdaria" in derived_props
    assert "profection" in derived_props
    assert "lunar_transit" in derived_props
    
    # Verificar que life_cycles y forecast están opcionales
    assert "life_cycles" in data["properties"]
    assert "forecast" in data["properties"]
