import pytest
from lilly_engine.json_maestro import build_json_maestro

def test_build_json_maestro_basic():
    chart_extended = {
        "chart": {
            "planets": [
                {"name": "Sun", "sign": "Cancer", "house": 10, "dignity": "domicile"},
                {"name": "Moon", "sign": "Pisces", "house": 1, "dignity": "exaltation"},
            ],
            "houses": [
                {"number": 1, "sign": "Pisces", "degree": 12.3},
                {"number": 10, "sign": "Cancer", "degree": 15.0},
            ],
            "angles": {"ASC": {"sign": "Pisces", "degree": 12.3, "house": 1}},
        },
        "extended": {
            "profections": {"time_lord": "Jupiter", "profected_sign": "Pisces", "monthly": {"month": 4, "monthly_sign": "Aries"}},
            "fardars": {"current": {"major": "Saturn", "sub": "Venus"}},
            "lunar_mansion": {"name": "Al-Tarf"},
            "lots": [{"name": "Fortuna", "sign": "Pisces", "degree": 18.1, "house": 1}],
            "solar_return": {"location": "Buenos Aires", "sun": {"sign": "Cancer", "house": 10}},
            "transits": [{"label": "Mars trine Sun", "timing": "2025-11-13"}],
        },
    }
    maestro = build_json_maestro(chart_extended, metadata_context={"language": "es", "birthDate": "1978-07-05"})
    assert "metadata" in maestro
    assert "year_overview" in maestro
    assert "elemental_analysis" in maestro
    assert "lord_of_year" in maestro
    assert "angularity_and_dignities" in maestro
    assert "rs_natal_interplay" in maestro
    assert "transits_contextualized" in maestro
    assert "monthly_windows" in maestro
    assert "critical_days" in maestro
    assert maestro["metadata"]["mode"] == "persian_cosmology"
    assert maestro["year_overview"]["ascendant_rs"]["sign"] == "Pisces"
    assert maestro["lord_of_year"]["final_lord"] in ["Jupiter", "Venus", "Saturn"]
