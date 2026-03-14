# -*- coding: utf-8 -*-
"""
Test de humo para domain_ranking.py.
Ejecutar directamente con: python tests/test_domain_ranking.py
(desde abu_engine/ con PYTHONPATH=. o desde repo con PYTHONPATH=abu_engine)
"""
from datetime import datetime, timezone
from core.domain_ranking import score_city_for_domain, rank_cities_for_domain, DOMAINS

# Frida Kahlo: 6 Jul 1907, 08:30 local Mexico City (UTC-6) => 14:30 UTC
FRIDA_BIRTH = datetime(1907, 7, 6, 14, 30, tzinfo=timezone.utc)

TEST_CITIES = [
    {"name": "Ciudad de Mexico", "lat": 19.4326,  "lon": -99.1332, "country": "MX"},
    {"name": "Nueva York",       "lat": 40.7128,  "lon": -74.0060, "country": "US"},
    {"name": "Paris",            "lat": 48.8566,  "lon":   2.3522, "country": "FR"},
    {"name": "Buenos Aires",     "lat": -34.6037, "lon": -58.3816, "country": "AR"},
]


def test_single_city():
    result = score_city_for_domain(
        birth_dt=FRIDA_BIRTH,
        lat=19.4326,
        lon=-99.1332,
        domain="creativity",
        year=1939,
        mode="solar_return",
        city_name="Ciudad de Mexico",
    )
    assert result["error"] is None, "Error: %s" % result["error"]
    assert 0 <= result["total_score"] <= 110, "Score fuera de rango: %s" % result["total_score"]
    assert result["grade"] in ["A", "B", "C", "D"]
    assert "breakdown" in result
    print("OK Single city: %s => %.1f (%s)" % (result["city"], result["total_score"], result["grade"]))
    print("   ASC: %s, MC: %s" % (result["chart_meta"]["asc_sign"], result["chart_meta"]["mc_sign"]))
    bd = result["breakdown"]
    print("   ruler=%.1f  angularity=%.1f  house=%.1f  support=%.1f" % (
        bd["house_ruler"]["total"],
        bd["key_angularity"]["total"],
        bd["domain_house"]["total"],
        bd["support_houses"]["total"],
    ))


def test_ranking():
    result = rank_cities_for_domain(
        birth_dt=FRIDA_BIRTH,
        cities=TEST_CITIES,
        domain="love",
        year=1929,
        top_n=3,
    )
    assert "top_recommendations" in result
    assert len(result["top_recommendations"]) <= 3
    assert result["domain"] == "love"
    print("\nOK Ranking 'love' para Frida Kahlo (1929):")
    for r in result["top_recommendations"]:
        print("   #%d %s: %.1f (%s) — %s" % (
            r["rank"], r["city"], r["total_score"], r["grade"], r["key_insight"]
        ))
    if result["errors"]:
        print("   Errors:", result["errors"])


def test_all_domains():
    for domain_key in DOMAINS.keys():
        result = score_city_for_domain(
            birth_dt=FRIDA_BIRTH,
            lat=19.4326,
            lon=-99.1332,
            domain=domain_key,
            year=1939,
            mode="solar_return",
        )
        assert result["error"] is None, "Fallo domain '%s': %s" % (domain_key, result["error"])
    print("\nOK Todos los dominios funcionan sin error (%d dominios)" % len(DOMAINS))


def test_unknown_domain():
    result = score_city_for_domain(
        birth_dt=FRIDA_BIRTH,
        lat=19.4326,
        lon=-99.1332,
        domain="astral_travel",
        year=1939,
    )
    assert result.get("error") is not None
    print("\nOK Dominio invalido retorna error controlado: %s" % result["error"])


def test_natal_mode():
    result = score_city_for_domain(
        birth_dt=FRIDA_BIRTH,
        lat=19.4326,
        lon=-99.1332,
        domain="creativity",
        mode="natal",
        city_name="Ciudad de Mexico (natal)",
    )
    assert result["error"] is None, "Error natal mode: %s" % result["error"]
    assert result["chart_meta"]["mode"] == "natal"
    print("\nOK Natal mode: %s => %.1f (%s)" % (
        result["city"], result["total_score"], result["grade"]
    ))


if __name__ == "__main__":
    print("=== Test de humo: domain_ranking.py ===\n")
    test_single_city()
    test_ranking()
    test_all_domains()
    test_unknown_domain()
    test_natal_mode()
    print("\n=== Todos los tests pasaron ===")
