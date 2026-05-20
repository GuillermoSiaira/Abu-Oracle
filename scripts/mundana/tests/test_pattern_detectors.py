"""
Tests deterministas para pattern_detectors.

Validación con efemérides conocidas:
- Conjunción Júpiter-Saturno 2020-12-21 (Gran Conjunción del Acuario)
- Eclipse solar total 2024-04-08
- Stellium en Capricornio enero 2020 (5 planetas)
"""

import sys
import math
from pathlib import Path

import pytest
import swisseph as swe

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pattern_detectors import (
    detect_active_patterns, catalog, scan_window_discrete,
    Pattern, _detect_group_a, _detect_group_b, get_positions_with_node,
)


def _ymd_to_jd(y, m, d, h=12.0):
    return swe.julday(y, m, d, h)


# ───────────── Catálogo ─────────────

def test_catalog_size():
    """El catálogo debe declarar ~100+ patrones distintos."""
    cat = catalog()
    assert len(cat) >= 80, f"Catalog has only {len(cat)} patterns, expected ≥80"
    types = [p.type for p in cat]
    assert len(set(types)) == len(types), "Catalog has duplicate type codes"

def test_catalog_groups():
    """Los 4 grupos deben estar presentes."""
    cat = catalog()
    groups = {p.group for p in cat}
    assert groups == {"A", "B", "C", "D"}


# ───────────── Grupo A: conjunción JS 2020-12-21 ─────────────

def test_jupiter_saturn_conjunction_2020():
    """Gran Conjunción 2020-12-21: deben aparecer JS conjunction con orbe <2°."""
    jd = _ymd_to_jd(2020, 12, 21)
    patterns = detect_active_patterns(jd)
    js_conj = [p for p in patterns if p.type == "conjunction_JS"]
    assert len(js_conj) == 1, f"Expected 1 conjunction_JS, got {len(js_conj)}"
    assert js_conj[0].orb < 2.0, f"Orb too large: {js_conj[0].orb}"


# ───────────── Grupo B: stellium Capricornio enero 2020 ─────────────

def test_stellium_capricorn_january_2020():
    """En enero 2020 hubo stellium en Capricornio: Sol, Mercurio, Júpiter, Saturno, Plutón."""
    jd = _ymd_to_jd(2020, 1, 12)
    patterns = detect_active_patterns(jd)
    stelliums = [p for p in patterns if p.type == "stellium_sign"
                 and p.details.get("sign") == "Capricornio"]
    assert len(stelliums) == 1, f"Expected stellium in Capricornio, got {len(stelliums)}"
    assert stelliums[0].details["count"] >= 4


# ───────────── Grupo C: eclipse solar 2024-04-08 ─────────────

def test_eclipse_2024_04_08():
    jd_start = _ymd_to_jd(2024, 4, 1)
    jd_end = _ymd_to_jd(2024, 4, 15)
    patterns = scan_window_discrete(jd_start, jd_end)
    solar_eclipses = [p for p in patterns if p.type.startswith("eclipse_solar")]
    assert len(solar_eclipses) >= 1
    # Validar fecha
    swe_y, swe_m, swe_d, _ = swe.revjul(solar_eclipses[0].jd)
    assert (swe_y, swe_m, swe_d) == (2024, 4, 8)


# ───────────── Grupo D: ciclo JS post-2020 ─────────────

def test_synodic_js_cycle_start_2020():
    """En diciembre 2020 debe estar activa la fase cycle_start de Júpiter-Saturno."""
    jd = _ymd_to_jd(2020, 12, 21)
    patterns = detect_active_patterns(jd)
    js_synodic = [p for p in patterns if p.type.startswith("synodic_cycle_start")
                  and "jupiter" in p.participants and "saturn" in p.participants]
    assert len(js_synodic) == 1


# ───────────── Sanity check ─────────────

def test_no_crashes_on_modern_dates():
    """Detectar patrones sobre varios JDs no debe lanzar excepciones."""
    for y in [1900, 1950, 2000, 2024, 2050]:
        jd = _ymd_to_jd(y, 6, 15)
        patterns = detect_active_patterns(jd)
        assert isinstance(patterns, list)
        for p in patterns:
            assert isinstance(p, Pattern)
            assert p.group in {"A", "B", "C", "D"}


def test_detect_returns_serializable():
    jd = _ymd_to_jd(2024, 6, 1)
    patterns = detect_active_patterns(jd, lookback_days=15, lookforward_days=15)
    for p in patterns:
        d = p.to_jsonable()
        assert "type" in d and "jd" in d and "participants" in d
