import json
import os
import sys

# Ensure imports that expect to run with cwd=lilly_engine keep working
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.llm import validate_contract


def test_validate_contract_happy_path():
    output = {
        "abu_line": "Saturno en retorno exacto.",
        "lilly_line": "Tiempo de madurez y estructura interna.",
        "headline": "Estructuras que renacen",
        "narrative": "Una narrativa concreta y específica sobre el proceso evolutivo...",
        "actions": ["Planificar hábitos", "Revisar límites", "Estructurar objetivos"],
        "astro_metadata": {
            "model": "gpt-4o-mini",
            "language": "es",
            "events_interpreted": 1,
            "source": "openai",
        },
    }
    ok, errors = validate_contract(output)
    assert ok, f"Contract should be valid, got errors: {errors}"


def test_validate_contract_missing_keys():
    output = {"headline": "H", "actions": []}
    ok, errors = validate_contract(output)
    assert not ok
    assert any("missing key: narrative" in e for e in errors)
    assert any("missing key: astro_metadata" in e for e in errors)
