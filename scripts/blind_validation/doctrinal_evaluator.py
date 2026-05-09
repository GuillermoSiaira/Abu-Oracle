#!/usr/bin/env python3
"""
doctrinal_evaluator.py - Evalua precision doctrinal de respuestas de Lilly.

Extrae afirmaciones verificables de Capa 3 y las contrasta contra un JSON de
Abu Engine previamente generado. No requiere Abu Engine corriendo.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional


ESSENTIAL_DIGNITIES = {
    "Sol": {
        "domicilio": ["Leo"],
        "exaltacion": ["Aries"],
        "detrimento": ["Acuario"],
        "caida": ["Libra"],
    },
    "Luna": {
        "domicilio": ["Cancer"],
        "exaltacion": ["Tauro"],
        "detrimento": ["Capricornio"],
        "caida": ["Escorpio"],
    },
    "Mercurio": {
        "domicilio": ["Geminis", "Virgo"],
        "exaltacion": ["Virgo"],
        "detrimento": ["Sagitario", "Piscis"],
        "caida": ["Piscis"],
    },
    "Venus": {
        "domicilio": ["Tauro", "Libra"],
        "exaltacion": ["Piscis"],
        "detrimento": ["Aries", "Escorpio"],
        "caida": ["Virgo"],
    },
    "Marte": {
        "domicilio": ["Aries", "Escorpio"],
        "exaltacion": ["Capricornio"],
        "detrimento": ["Tauro", "Libra"],
        "caida": ["Cancer"],
    },
    "Júpiter": {
        "domicilio": ["Sagitario", "Piscis"],
        "exaltacion": ["Cáncer"],
        "detrimento": ["Géminis", "Virgo"],
        "caida": ["Capricornio"],
    },
    "Saturno": {
        "domicilio": ["Capricornio", "Acuario"],
        "exaltacion": ["Libra"],
        "detrimento": ["Cancer", "Leo"],
        "caida": ["Aries"],
    },
}

PLANET_ALIASES = {
    "sun": "Sol",
    "sol": "Sol",
    "moon": "Luna",
    "luna": "Luna",
    "mercury": "Mercurio",
    "mercurio": "Mercurio",
    "venus": "Venus",
    "mars": "Marte",
    "marte": "Marte",
    "jupiter": "Júpiter",
    "saturn": "Saturno",
    "saturno": "Saturno",
    "uranus": "Urano",
    "urano": "Urano",
    "neptune": "Neptuno",
    "neptuno": "Neptuno",
    "pluto": "Plutón",
    "pluton": "Plutón",
}

DISPLAY_NAMES = {
    "Sol": "Sol",
    "Luna": "Luna",
    "Mercurio": "Mercurio",
    "Venus": "Venus",
    "Marte": "Marte",
    "Júpiter": "Júpiter",
    "Saturno": "Saturno",
    "Urano": "Urano",
    "Neptuno": "Neptuno",
    "Plutón": "Plutón",
}

_PLANET_TERMS = sorted(
    {
        "Sol",
        "Luna",
        "Mercurio",
        "Venus",
        "Marte",
        "Jupiter",
        "Júpiter",
        "Saturno",
        "Urano",
        "Neptuno",
        "Pluton",
        "Plutón",
        "Sun",
        "Moon",
        "Mercury",
        "Mars",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
    },
    key=len,
    reverse=True,
)
_PLANET_PATTERN = "|".join(re.escape(name) for name in _PLANET_TERMS)


def extract_doctrinal_claims(response_text: str) -> list[dict]:
    """
    Extrae afirmaciones doctrinales verificables del texto de Lilly.

    Returns list[dict] con campos como type, planet, house, dignity y raw.
    """
    claims: list[dict] = []
    text = response_text

    for m in re.finditer(
        rf"\b({_PLANET_PATTERN})\b\s+(?:es\s+)?(?:el\s+)?se[nñ]or\s+del\s+a[nñ]o",
        text,
        re.IGNORECASE,
    ):
        claims.append(
            {"type": "señor_del_año", "planet": _normalize_planet(m.group(1)), "raw": m.group(0)}
        )

    for m in re.finditer(
        rf"\b({_PLANET_PATTERN})\b\s+rige\s+(?:este\s+)?a[nñ]o",
        text,
        re.IGNORECASE,
    ):
        claims.append(
            {"type": "señor_del_año", "planet": _normalize_planet(m.group(1)), "raw": m.group(0)}
        )

    for m in re.finditer(
        rf"(?:periodo|per[ií]odo|firdaria|fardaria)\s+(?:mayor\s+)?(?:de\s+)?\b({_PLANET_PATTERN})\b",
        text,
        re.IGNORECASE,
    ):
        claims.append(
            {"type": "firdaria_mayor", "planet": _normalize_planet(m.group(1)), "raw": m.group(0)}
        )

    for m in re.finditer(
        rf"\b({_PLANET_PATTERN})\b\s+(?:se\s+encuentra\s+)?(?:est[aá]\s+)?(?:en\s+)?"
        r"(detrimento|ca[ií]da|domicilio|exaltaci[oó]n)",
        text,
        re.IGNORECASE,
    ):
        claims.append(
            {
                "type": "dignidad",
                "planet": _normalize_planet(m.group(1)),
                "dignity": _normalize_key(m.group(2)),
                "raw": m.group(0),
            }
        )

    for m in re.finditer(
        r"(?:Parte\s+de\s+)?Fortuna\s+(?:est[aá]\s+)?en\s+Casa\s+(\d+)",
        text,
        re.IGNORECASE,
    ):
        claims.append({"type": "fortuna_house", "house": int(m.group(1)), "raw": m.group(0)})

    for m in re.finditer(
        rf"\b({_PLANET_PATTERN})\b\s+(?:ocupa|est[aá]\s+en)\s+(?:la\s+)?Casa\s+(\d+)",
        text,
        re.IGNORECASE,
    ):
        claims.append(
            {
                "type": "ocupa_casa",
                "planet": _normalize_planet(m.group(1)),
                "house": int(m.group(2)),
                "raw": m.group(0),
            }
        )

    return _dedupe_claims(claims)


def verify_claims(claims: list[dict], abu_json: dict) -> list[dict]:
    """
    Verifica afirmaciones contra datos de Abu Engine.

    Cada resultado agrega:
      - verified: bool | None
      - ground_truth: str
    """
    derived = abu_json.get("derived", {})
    planets = _planet_index(abu_json.get("chart", {}).get("planets", []))
    active_prof = _active_item(derived.get("profections", []))
    active_fird = _active_item(derived.get("firdaria", []))
    fortuna = derived.get("lots", {}).get("fortuna")

    results: list[dict] = []
    for claim in claims:
        c = dict(claim)
        c["verified"] = None
        c["ground_truth"] = "N/A"

        if claim["type"] == "señor_del_año" and active_prof:
            truth = _normalize_planet(str(active_prof.get("lord", "")))
            c["ground_truth"] = _display(truth)
            c["verified"] = claim["planet"] == truth

        elif claim["type"] == "firdaria_mayor" and active_fird:
            truth = _normalize_planet(str(active_fird.get("major_planet", "")))
            c["ground_truth"] = _display(truth)
            c["verified"] = claim["planet"] == truth

        elif claim["type"] == "dignidad":
            planet = claim["planet"]
            dignity = claim["dignity"]
            planet_row = planets.get(planet)
            if planet in ESSENTIAL_DIGNITIES and planet_row:
                sign = str(planet_row.get("sign", "")).strip()
                sign_key = _normalize_key(sign)
                dignity_key = _dignity_key(dignity)
                valid_signs = ESSENTIAL_DIGNITIES[planet].get(dignity_key, [])
                valid_keys = {_normalize_key(valid_sign) for valid_sign in valid_signs}
                c["ground_truth"] = f"{_display(planet)} in {sign}; {dignity_key}: {', '.join(valid_signs)}"
                c["verified"] = sign_key in valid_keys

        elif claim["type"] == "fortuna_house" and fortuna:
            truth = _coerce_int(fortuna.get("house"))
            c["ground_truth"] = str(truth) if truth is not None else "?"
            c["verified"] = claim["house"] == truth if truth is not None else None

        elif claim["type"] == "ocupa_casa":
            planet_row = planets.get(claim["planet"])
            if planet_row:
                truth = _coerce_int(planet_row.get("house"))
                c["ground_truth"] = str(truth) if truth is not None else "?"
                c["verified"] = claim["house"] == truth if truth is not None else None

        results.append(c)

    return results


def compute_precision(verified_claims: list[dict]) -> Optional[float]:
    """Retorna correctas / verificables, o None si no hay verificables."""
    verifiable = [c for c in verified_claims if c.get("verified") is not None]
    if not verifiable:
        return None
    correct = sum(1 for c in verifiable if c.get("verified") is True)
    return correct / len(verifiable)


def evaluate_response(response_text: str, abu_json: dict) -> dict:
    """Pipeline completo: texto -> claims -> verificacion -> precision."""
    claims = extract_doctrinal_claims(response_text)
    verified = verify_claims(claims, abu_json)
    precision = compute_precision(verified)
    verifiable = [c for c in verified if c.get("verified") is not None]
    correct = [c for c in verifiable if c.get("verified") is True]

    return {
        "total_claims": len(claims),
        "verifiable_claims": len(verifiable),
        "correct_claims": len(correct),
        "precision": precision,
        "details": verified,
    }


def _active_item(items: object) -> Optional[dict]:
    if isinstance(items, dict):
        items = list(items.values())
    if not isinstance(items, list):
        return None
    return next((item for item in items if isinstance(item, dict) and item.get("is_active")), None)


def _planet_index(planets: object) -> dict[str, dict]:
    if isinstance(planets, dict):
        iterable = planets.values()
    elif isinstance(planets, list):
        iterable = planets
    else:
        return {}

    indexed: dict[str, dict] = {}
    for planet in iterable:
        if not isinstance(planet, dict):
            continue
        name = planet.get("name") or planet.get("planet")
        if name:
            indexed[_normalize_planet(str(name))] = planet
    return indexed


def _normalize_planet(planet_str: str) -> str:
    key = _normalize_key(planet_str)
    return PLANET_ALIASES.get(key.lower(), planet_str.strip().title())


def _display(planet: str) -> str:
    return DISPLAY_NAMES.get(planet, planet)


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return ascii_text.strip().lower()


def _dignity_key(dignity: str) -> str:
    key = _normalize_key(dignity)
    if key == "exaltacion":
        return "exaltacion"
    if key == "caida":
        return "caida"
    return key


def _coerce_int(value: object) -> Optional[int]:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        m = re.search(r"\d+", value)
        return int(m.group(0)) if m else None
    return None


def _dedupe_claims(claims: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    unique: list[dict] = []
    for claim in claims:
        key = (
            claim.get("type"),
            claim.get("planet"),
            claim.get("dignity"),
            claim.get("house"),
            claim.get("raw"),
        )
        if key not in seen:
            seen.add(key)
            unique.append(claim)
    return unique


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("Usage: python doctrinal_evaluator.py <lilly_response.txt> <abu_json.json>")
        return 1

    response_text = Path(argv[1]).read_text(encoding="utf-8")
    abu_json = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    result = evaluate_response(response_text, abu_json)

    print(f"Total claims extracted:  {result['total_claims']}")
    print(f"Verifiable:              {result['verifiable_claims']}")
    print(f"Correct:                 {result['correct_claims']}")
    if result["precision"] is not None:
        print(f"Doctrinal precision:     {result['precision']:.1%}")
    else:
        print("Doctrinal precision:     N/A (no verifiable claims found)")

    print("\nDetails:")
    for claim in result["details"]:
        status = "OK" if claim["verified"] is True else ("NO" if claim["verified"] is False else "??")
        print(f"  [{status}] {claim['type']}: {claim.get('planet', '')} - GT: {claim['ground_truth']}")
        print(f"       Raw: \"{claim['raw']}\"")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
