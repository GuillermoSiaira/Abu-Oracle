# -*- coding: utf-8 -*-
"""
domain_ranking.py — Solar Return & Natal Chart Domain Scoring

Scores any city/coordinate for a specific life domain (career, love, health, etc.)
using the Solar Return chart or a natal chart for a given birth moment.

Compatible with the existing Abu Engine infrastructure:
- Uses solar_return_chart() from core.chart
- Uses calculate_houses() / get_planet_house() from core.houses_swiss
- Uses get_planet_dignity() from core.dignities
- Uses get_ruler() from core.dignities

Two entry points:
1. score_city_for_domain()     — single city, returns detailed breakdown
2. rank_cities_for_domain()    — list of cities, returns sorted ranking

Two use cases:
A. Solar Return (cumpleaños): where to be on your birthday to activate a domain
B. Natal (nacimiento): which city gives the best natal chart for a given domain/date

Author: AI Oracle
Version: 1.0
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# — Internal imports (same pattern as solar_return_ranking.py) ——————————————
from core.chart import solar_return_chart
from core.dignities import get_planet_dignity, get_ruler
from core.houses_swiss import (
    calculate_houses,
    longitude_to_sign_degree,
    get_planet_house,
    HOUSE_SYSTEM_PLACIDUS,
)


# ——————————————————————————————————————————————————————————————————————————
# Domain definitions
# ——————————————————————————————————————————————————————————————————————————

DOMAINS: Dict[str, Dict] = {
    "career": {
        "label": "Carrera",
        "house": 10,
        "supporting_houses": [6, 2],
        "key_planets": ["Sun", "Saturn", "Mars"],
        "benefic_in_house": ["Jupiter", "Venus", "Sun"],
        "malefic_in_house": ["Saturn", "Mars"],
    },
    "love": {
        "label": "Amor / Pareja",
        "house": 7,
        "supporting_houses": [5, 11],
        "key_planets": ["Venus", "Moon"],
        "benefic_in_house": ["Venus", "Jupiter"],
        "malefic_in_house": ["Saturn", "Mars"],
    },
    "health": {
        "label": "Salud / Vitalidad",
        "house": 1,
        "supporting_houses": [6, 8],
        "key_planets": ["Sun", "Moon", "Mars"],
        "benefic_in_house": ["Jupiter", "Venus", "Sun"],
        "malefic_in_house": ["Saturn"],
    },
    "family": {
        "label": "Hogar / Familia",
        "house": 4,
        "supporting_houses": [3, 10],
        "key_planets": ["Moon", "Saturn"],
        "benefic_in_house": ["Moon", "Venus", "Jupiter"],
        "malefic_in_house": ["Mars", "Saturn"],
    },
    "resources": {
        "label": "Recursos / Finanzas",
        "house": 2,
        "supporting_houses": [8, 11],
        "key_planets": ["Jupiter", "Venus"],
        "benefic_in_house": ["Jupiter", "Venus"],
        "malefic_in_house": ["Saturn", "Mars"],
    },
    "creativity": {
        "label": "Creatividad / Expresion",
        "house": 5,
        "supporting_houses": [1, 9],
        "key_planets": ["Sun", "Venus", "Jupiter"],
        "benefic_in_house": ["Venus", "Jupiter", "Sun"],
        "malefic_in_house": ["Saturn"],
    },
    "expansion": {
        "label": "Expansion / Espiritualidad",
        "house": 9,
        "supporting_houses": [3, 12],
        "key_planets": ["Jupiter", "Sun"],
        "benefic_in_house": ["Jupiter", "Sun"],
        "malefic_in_house": ["Saturn", "Mars"],
    },
}

ANGULAR_HOUSES = {1, 4, 7, 10}
SUCCEDENT_HOUSES = {2, 5, 8, 11}
CADENT_HOUSES = {3, 6, 9, 12}

MAX_RULER_SCORE      = 40
MAX_ANGULARITY_SCORE = 30
MAX_HOUSE_SCORE      = 20
MAX_SUPPORT_SCORE    = 10


# ——————————————————————————————————————————————————————————————————————————
# Helpers
# ——————————————————————————————————————————————————————————————————————————

def _angular_strength(house: int) -> float:
    """Fuerza posicional: angular=1.0, sucedente=0.5, cadente=0.0."""
    if house in ANGULAR_HOUSES:
        return 1.0
    if house in SUCCEDENT_HOUSES:
        return 0.5
    return 0.0


def _dignity_multiplier(planet_name: str, sign: str, lon: float) -> float:
    """
    Devuelve un multiplicador segun dignidad esencial del planeta en ese signo.
    domicilio = 1.5 | exaltacion = 1.3 | perjuicio = 0.5 | caida = 0.3 | neutro = 1.0
    """
    try:
        degree = lon % 30
        info = get_planet_dignity(planet_name, sign, degree)
        kind = info.get("kind", "peregrine")
        return {
            "domicile":   1.5,
            "exaltation": 1.3,
            "triplicity": 1.1,
            "term":       1.05,
            "detriment":  0.5,
            "fall":       0.3,
        }.get(kind, 1.0)
    except Exception:
        return 1.0


def _build_planet_index(planets: List[Dict]) -> Dict[str, Dict]:
    """Indexa planetas por nombre para acceso rapido."""
    return {p["name"]: p for p in planets}


def _enrich_with_houses(
    planets: List[Dict],
    sr_dt: datetime,
    lat: float,
    lon: float,
) -> Tuple[List[Dict], str, str]:
    """
    Aniade 'house' a cada planeta y retorna (enriched_planets, asc_sign, mc_sign).
    Si falla el calculo de casas, devuelve planetas sin enriquecer y signos por defecto.
    """
    try:
        houses_raw = calculate_houses(sr_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
        cusps = houses_raw.get("cusps", [])
        if len(cusps) != 12:
            return planets, "Aries", "Capricorn"

        asc_sign, _ = longitude_to_sign_degree(houses_raw["asc"])
        mc_sign, _  = longitude_to_sign_degree(houses_raw["mc"])

        enriched = []
        for p in planets:
            p2 = dict(p)
            p2["house"] = get_planet_house(p["lon"], cusps) if p.get("lon") is not None else None
            enriched.append(p2)
        return enriched, asc_sign, mc_sign

    except Exception:
        return planets, "Aries", "Capricorn"


# ——————————————————————————————————————————————————————————————————————————
# Scoring components
# ——————————————————————————————————————————————————————————————————————————

def _score_house_ruler(
    domain_cfg: Dict,
    asc_sign: str,
    mc_sign: str,
    house_cusps_signs: Dict[int, str],
    planet_index: Dict[str, Dict],
) -> Tuple[float, Dict]:
    """
    Componente 1 — Senor de la casa del dominio. Max 40 pts.
    """
    domain_house = domain_cfg["house"]
    details = {}

    cusp_sign = house_cusps_signs.get(domain_house)
    if not cusp_sign:
        return 0.0, {"note": "no cusp sign available", "total": 0.0}

    ruler_name = get_ruler(cusp_sign)
    ruler = planet_index.get(ruler_name)
    if not ruler:
        return 0.0, {"ruler": ruler_name, "note": "ruler not found in chart", "total": 0.0}

    ruler_house = ruler.get("house")
    if not ruler_house:
        return 0.0, {"ruler": ruler_name, "note": "ruler house not assigned", "total": 0.0}

    ang = _angular_strength(ruler_house)
    base_score = ang * 28.0

    ruler_sign = ruler.get("sign", "")
    ruler_lon   = ruler.get("lon", 0.0)
    dig_mult    = _dignity_multiplier(ruler_name, ruler_sign, ruler_lon)
    final_score = min(base_score * dig_mult, MAX_RULER_SCORE)

    details = {
        "ruler":         ruler_name,
        "ruler_house":   ruler_house,
        "ruler_sign":    ruler_sign,
        "angularity":    ang,
        "dignity_mult":  round(dig_mult, 2),
        "total":         round(final_score, 2),
    }
    return final_score, details


def _score_key_planets_angularity(
    domain_cfg: Dict,
    planet_index: Dict[str, Dict],
) -> Tuple[float, Dict]:
    """
    Componente 2 — Planetas clave del dominio en angulos. Max 30 pts.
    """
    key_planets  = domain_cfg["key_planets"]
    malefics_h   = set(domain_cfg["malefic_in_house"])

    score    = 0.0
    details  = {"planets": []}
    n        = len(key_planets)
    per_planet_max = MAX_ANGULARITY_SCORE / max(n, 1)

    for name in key_planets:
        p = planet_index.get(name)
        if not p:
            continue

        house = p.get("house")
        if not house:
            continue

        ang       = _angular_strength(house)
        sign      = p.get("sign", "")
        lon       = p.get("lon", 0.0)
        dig_mult  = _dignity_multiplier(name, sign, lon)

        if name in malefics_h and dig_mult < 1.0:
            ang = ang * 0.3

        planet_score = min(ang * per_planet_max * dig_mult, per_planet_max)
        score += planet_score

        details["planets"].append({
            "planet":      name,
            "house":       house,
            "angularity":  ang,
            "dignity_mult": round(dig_mult, 2),
            "score":       round(planet_score, 2),
        })

    final_score = min(score, MAX_ANGULARITY_SCORE)
    details["total"] = round(final_score, 2)
    return final_score, details


def _score_planets_in_domain_house(
    domain_cfg: Dict,
    planet_index: Dict[str, Dict],
) -> Tuple[float, Dict]:
    """
    Componente 3 — Planetas en la casa del dominio. Max 20 pts.
    """
    domain_house = domain_cfg["house"]
    benefics_h   = set(domain_cfg["benefic_in_house"])
    malefics_h   = set(domain_cfg["malefic_in_house"])

    score   = 0.0
    details = {"planets_in_house": []}

    for name, p in planet_index.items():
        if p.get("house") != domain_house:
            continue

        sign     = p.get("sign", "")
        lon      = p.get("lon", 0.0)
        dig_mult = _dignity_multiplier(name, sign, lon)

        if name in benefics_h:
            planet_score = 7.0 * dig_mult
        elif name in malefics_h:
            planet_score = 3.0 * dig_mult if dig_mult >= 1.0 else -4.0
        else:
            planet_score = 3.0 * dig_mult

        score += planet_score
        details["planets_in_house"].append({
            "planet":      name,
            "dignity_mult": round(dig_mult, 2),
            "score":       round(planet_score, 2),
        })

    final_score = max(min(score, MAX_HOUSE_SCORE), -10.0)
    details["total"] = round(final_score, 2)
    return final_score, details


def _score_supporting_houses(
    domain_cfg: Dict,
    planet_index: Dict[str, Dict],
) -> Tuple[float, Dict]:
    """
    Componente 4 — Planetas beneficos en casas de apoyo. Max 10 pts.
    """
    supporting = set(domain_cfg["supporting_houses"])
    benefics_h = set(domain_cfg["benefic_in_house"])

    score   = 0.0
    details = {"planets_in_support": []}

    for name in benefics_h:
        p = planet_index.get(name)
        if not p:
            continue
        if p.get("house") in supporting:
            sign     = p.get("sign", "")
            lon      = p.get("lon", 0.0)
            dig_mult = _dignity_multiplier(name, sign, lon)
            planet_score = 3.5 * dig_mult
            score += planet_score
            details["planets_in_support"].append({
                "planet": name,
                "house":  p["house"],
                "score":  round(planet_score, 2),
            })

    final_score = min(score, MAX_SUPPORT_SCORE)
    details["total"] = round(final_score, 2)
    return final_score, details


# ——————————————————————————————————————————————————————————————————————————
# Chart builder (Solar Return o Natal puro)
# ——————————————————————————————————————————————————————————————————————————

def _build_chart(
    birth_dt: datetime,
    lat: float,
    lon: float,
    year: Optional[int],
    mode: str,
) -> Tuple[Optional[Dict], datetime, str]:
    """
    Construye la carta segun el modo:
    - "solar_return": calcula el SR para `year` en (lat, lon)
    - "natal":        usa la carta natal en (lat, lon) (misma fecha birth_dt)

    Retorna (chart_raw, sr_dt, error_msg).
    """
    if mode == "solar_return":
        try:
            result = solar_return_chart(birth_dt, lat, lon, year)
            sr_dt_str = result.get("solar_return_datetime", "")
            sr_dt = datetime.fromisoformat(sr_dt_str.replace("Z", "+00:00")) if sr_dt_str else birth_dt
            return result, sr_dt, ""
        except Exception as e:
            return None, birth_dt, str(e)
    else:
        try:
            from core.chart import chart_json
            chart_raw = chart_json(lat, lon, birth_dt)
            planets = [
                {
                    "name": p.name,
                    "lon":  p.lon,
                    "sign": longitude_to_sign_degree(p.lon)[0],
                }
                for p in chart_raw.planets
            ]
            return {"planets": planets, "aspects": []}, birth_dt, ""
        except Exception as e:
            return None, birth_dt, str(e)


# ——————————————————————————————————————————————————————————————————————————
# Public API
# ——————————————————————————————————————————————————————————————————————————

def score_city_for_domain(
    birth_dt: datetime,
    lat: float,
    lon: float,
    domain: str,
    year: Optional[int] = None,
    mode: str = "solar_return",
    city_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calcula el score de una ciudad para un dominio de vida especifico.

    Args:
        birth_dt:  Fecha/hora de nacimiento (UTC).
        lat:       Latitud de la ciudad a evaluar.
        lon:       Longitud de la ciudad a evaluar.
        domain:    Dominio de vida: 'career', 'love', 'health', 'family',
                   'resources', 'creativity', 'expansion'.
        year:      Anio del Solar Return (None = anio actual). Solo para mode='solar_return'.
        mode:      'solar_return' — usa la RS para ese anio en esa ciudad.
                   'natal'       — usa la carta natal en esa ciudad/fecha.
        city_name: Nombre descriptivo (opcional, solo para el output).

    Returns:
        {
          "city":          str,
          "coordinates":   {"lat": float, "lon": float},
          "domain":        str,
          "domain_label":  str,
          "total_score":   float,
          "max_possible":  100,
          "grade":         str,
          "breakdown": {...},
          "chart_meta": {...},
          "error": str | None,
        }
    """
    domain_cfg = DOMAINS.get(domain)
    if not domain_cfg:
        return {
            "error": "Unknown domain '%s'. Valid: %s" % (domain, list(DOMAINS.keys())),
            "total_score": 0.0,
        }

    label = domain_cfg["label"]
    name_out = city_name or "%.2f,%.2f" % (lat, lon)

    chart_raw, chart_dt, err = _build_chart(birth_dt, lat, lon, year, mode)
    if chart_raw is None:
        return {
            "city":         name_out,
            "coordinates":  {"lat": lat, "lon": lon},
            "domain":       domain,
            "domain_label": label,
            "total_score":  0.0,
            "error":        err,
        }

    planets_raw = chart_raw.get("planets", [])

    planets, asc_sign, mc_sign = _enrich_with_houses(planets_raw, chart_dt, lat, lon)
    planet_index = _build_planet_index(planets)

    house_cusps_signs: Dict[int, str] = {}
    try:
        houses_raw = calculate_houses(chart_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
        cusps = houses_raw.get("cusps", [])
        for i, cusp_lon in enumerate(cusps, start=1):
            sign, _ = longitude_to_sign_degree(cusp_lon)
            house_cusps_signs[i] = sign
    except Exception:
        pass

    ruler_score,   ruler_details   = _score_house_ruler(
        domain_cfg, asc_sign, mc_sign, house_cusps_signs, planet_index
    )
    ang_score,     ang_details     = _score_key_planets_angularity(domain_cfg, planet_index)
    house_score,   house_details   = _score_planets_in_domain_house(domain_cfg, planet_index)
    support_score, support_details = _score_supporting_houses(domain_cfg, planet_index)

    total = ruler_score + ang_score + house_score + support_score
    max_possible = MAX_RULER_SCORE + MAX_ANGULARITY_SCORE + MAX_HOUSE_SCORE + MAX_SUPPORT_SCORE

    pct = total / max_possible
    grade = "A" if pct >= 0.75 else "B" if pct >= 0.55 else "C" if pct >= 0.35 else "D"

    return {
        "city":         name_out,
        "coordinates":  {"lat": lat, "lon": lon},
        "domain":       domain,
        "domain_label": label,
        "total_score":  round(total, 2),
        "max_possible": max_possible,
        "grade":        grade,
        "breakdown": {
            "house_ruler":    ruler_details,
            "key_angularity": ang_details,
            "domain_house":   house_details,
            "support_houses": support_details,
        },
        "chart_meta": {
            "asc_sign": asc_sign,
            "mc_sign":  mc_sign,
            "datetime": chart_dt.isoformat(),
            "mode":     mode,
        },
        "error": None,
    }


def rank_cities_for_domain(
    birth_dt: datetime,
    cities: List[Dict[str, Any]],
    domain: str,
    year: Optional[int] = None,
    mode: str = "solar_return",
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Rankea una lista de ciudades para un dominio de vida.

    Args:
        birth_dt: Fecha/hora de nacimiento (UTC).
        cities:   Lista de dicts con al menos {"name": str, "lat": float, "lon": float}.
        domain:   Dominio de vida ('career', 'love', 'health', etc.).
        year:     Anio del SR (None = anio actual).
        mode:     'solar_return' | 'natal'.
        top_n:    Numero de ciudades top a destacar.
    """
    if not DOMAINS.get(domain):
        return {"error": "Unknown domain '%s'. Valid: %s" % (domain, list(DOMAINS.keys()))}

    results  = []
    errors   = []

    for city in cities:
        name    = city.get("name") or city.get("city") or "Unknown"
        country = city.get("country", "")
        lat     = city.get("lat") or city.get("latitude")
        lon     = city.get("lon") or city.get("longitude")

        if lat is None or lon is None:
            errors.append("%s: missing coordinates" % name)
            continue

        result = score_city_for_domain(
            birth_dt=birth_dt,
            lat=float(lat),
            lon=float(lon),
            domain=domain,
            year=year,
            mode=mode,
            city_name=("%s, %s" % (name, country)).strip(", "),
        )

        if result.get("error"):
            errors.append("%s: %s" % (name, result["error"]))
        else:
            result["country"] = country
            results.append(result)

    results.sort(key=lambda r: r["total_score"], reverse=True)

    top = []
    for i, r in enumerate(results[:top_n], start=1):
        breakdown = r.get("breakdown", {})

        components = {
            "Senor de casa activo":          breakdown.get("house_ruler", {}).get("total", 0),
            "Planetas clave angulares":       breakdown.get("key_angularity", {}).get("total", 0),
            "Planetas en casa del dominio":   breakdown.get("domain_house", {}).get("total", 0),
            "Casas de apoyo activas":         breakdown.get("support_houses", {}).get("total", 0),
        }
        best_component = max(components, key=components.get)

        top.append({
            "rank":         i,
            "city":         r["city"],
            "country":      r.get("country", ""),
            "coordinates":  r["coordinates"],
            "total_score":  r["total_score"],
            "max_possible": r["max_possible"],
            "grade":        r["grade"],
            "asc_sign":     r.get("chart_meta", {}).get("asc_sign", ""),
            "mc_sign":      r.get("chart_meta", {}).get("mc_sign", ""),
            "key_insight":  best_component,
        })

    return {
        "domain":               domain,
        "domain_label":         DOMAINS[domain]["label"],
        "mode":                 mode,
        "year":                 year,
        "cities_analyzed":      len(results) + len(errors),
        "top_n":                top_n,
        "rankings":             results,
        "top_recommendations":  top,
        "errors":               errors,
    }
