#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sanity check para domain_ranking.py con datos del desarrollador del sistema.
Ejecutar desde Docker: docker exec abu_engine python scripts/sanity_check_domain.py
O desde repo: PYTHONPATH=abu_engine python scripts/sanity_check_domain.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "abu_engine"))

from datetime import datetime, timezone
from core.domain_ranking import score_city_for_domain, rank_cities_for_domain, DOMAINS

# Atilio: 5 julio 1978, 21:15 hora local Argentina → 00:15 UTC del 6/7/1978
# Stellium: Sol + Mercurio + Jupiter en Cancer, casa 5
BIRTH = datetime(1978, 7, 6, 0, 15, tzinfo=timezone.utc)

CITIES = [
    {"name": "Buenos Aires",     "lat": -34.6037, "lon": -58.3816, "country": "AR"},
    {"name": "Barcelona",        "lat":  41.3851,  "lon":   2.1734, "country": "ES"},
    {"name": "Lisboa",           "lat":  38.7223,  "lon":  -9.1393, "country": "PT"},
    {"name": "Ciudad de Mexico", "lat":  19.4326, "lon": -99.1332, "country": "MX"},
    {"name": "Nueva York",       "lat":  40.7128, "lon": -74.0060, "country": "US"},
    {"name": "Londres",          "lat":  51.5074, "lon":  -0.1278, "country": "GB"},
    {"name": "Berlin",           "lat":  52.5200, "lon":  13.4050, "country": "DE"},
    {"name": "Tokio",            "lat":  35.6762, "lon": 139.6503, "country": "JP"},
]

def run():
    print("=== Sanity check: domain_ranking.py ===")
    print("Carta: Atilio, 6 jul 1978 00:15 UTC, Balcarce AR")
    print("SR year: 2026\n")

    for domain in ("creativity", "career", "love"):
        result = rank_cities_for_domain(
            birth_dt=BIRTH,
            cities=CITIES,
            domain=domain,
            year=2026,
            mode="solar_return",
            top_n=3,
        )
        label = result["domain_label"]
        print(f"--- {domain.upper()} ({label}) ---")
        for r in result["top_recommendations"]:
            bd = {}
            # get breakdown from rankings list
            for full in result["rankings"]:
                if full["city"].startswith(r["city"].split(",")[0]):
                    bd = full.get("breakdown", {})
                    break
            ruler = bd.get("house_ruler", {}).get("ruler", "?")
            print(f"  #{r['rank']} {r['city']:<25} {r['total_score']:5.1f}/{r['max_possible']} ({r['grade']})  "
                  f"lord={ruler}  ASC={r['asc_sign']}")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")
        print()

    # Verify all 7 domains run without error
    errors = []
    for dk in DOMAINS:
        res = score_city_for_domain(BIRTH, -34.6037, -58.3816, dk, year=2026)
        if res.get("error"):
            errors.append(f"{dk}: {res['error']}")
    if errors:
        print("ERRORS:", errors)
    else:
        print(f"OK — todos los {len(DOMAINS)} dominios sin error.")

    # Invalid domain
    res_bad = score_city_for_domain(BIRTH, -34.6037, -58.3816, "astral_travel")
    assert res_bad.get("error"), "Dominio invalido no retorno error"
    print("OK — dominio invalido manejado correctamente.")

if __name__ == "__main__":
    run()
