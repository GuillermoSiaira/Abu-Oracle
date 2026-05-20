"""
Tests para enrich_events.py.

Foco en lógica determinista:
  - parse_fecha detecta precisión correctamente
  - enrich_event encuentra los patrones esperados en eventos célebres
  - audit_precision suma correctamente
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from enrich_events import parse_fecha, audit_precision, enrich_event, to_jd


def test_parse_fecha_precision():
    assert parse_fecha("2020-12-21")[3] == "day"
    assert parse_fecha("2020-03-01")[3] == "month"
    assert parse_fecha("0404-01-01")[3] == "year"


def test_audit_precision_distribution():
    events = [
        {"fecha": "2020-12-21", "descripcion": "Great Conjunction"},
        {"fecha": "0404-01-01", "descripcion": "Roma"},
        {"fecha": "1969-07-20", "descripcion": "Moon landing"},
        {"fecha": "1500-06-01", "descripcion": "Algo en junio"},
    ]
    rep = audit_precision(events)
    assert rep["total"] == 4
    assert rep["counts"]["day"] == 2
    assert rep["counts"]["month"] == 1
    assert rep["counts"]["year"] == 1


def test_enrich_event_great_conjunction_2020():
    """El evento 2020-12-21 (Gran Conjunción) debe tener conjunction_JS en configs_active."""
    ev = {"fecha": "2020-12-21", "descripcion": "Gran Conjunción Júpiter-Saturno"}
    enriched = enrich_event(ev, window_days=10)
    assert enriched["date_precision"] == "day"
    types = [c["type"] for c in enriched["configs_active"]]
    assert "conjunction_JS" in types


def test_enrich_event_year_precision_preserved():
    ev = {"fecha": "0404-01-01", "descripcion": "Eventos en Roma"}
    enriched = enrich_event(ev, window_days=30)
    assert enriched["date_precision"] == "year"
    assert "configs_active" in enriched
