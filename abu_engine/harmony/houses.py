"""House occupancy utilities for HF Core v2.

Lightweight helpers to derive house-based features from cusp data and
planetary positions. Delegates house computation to `abu_engine.core.houses_swiss`.
"""

from __future__ import annotations

from typing import Dict, List, Mapping, Tuple
import math

from core.houses_swiss import get_planet_house, longitude_to_sign_degree

from .schema_v2 import PLANET_ORDER, DEFAULT_PLANET_WEIGHTS, HOUSE_COUNT_COLS, HOUSE_WEIGHTED_COLS


# Sign → planetary ruler(s) — modern rulerships (co-rulers included for outer planets)
_SIGN_RULERS: Dict[str, List[str]] = {
    "Aries":       ["Mars"],
    "Taurus":      ["Venus"],
    "Gemini":      ["Mercury"],
    "Cancer":      ["Moon"],
    "Leo":         ["Sun"],
    "Virgo":       ["Mercury"],
    "Libra":       ["Venus"],
    "Scorpio":     ["Mars", "Pluto"],
    "Sagittarius": ["Jupiter"],
    "Capricorn":   ["Saturn"],
    "Aquarius":    ["Saturn", "Uranus"],
    "Pisces":      ["Jupiter", "Neptune"],
}

# Canonical lowercase keys matching CLAUDE.md contract
_CANONICAL_LOWER: List[str] = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
    "asc", "mc",
]

# Title-case → lowercase normalisation (covers PLANET_ORDER + angles)
_TO_LOWER: Dict[str, str] = {p: p.lower() for p in PLANET_ORDER}
_TO_LOWER.update({"ASC": "asc", "MC": "mc"})


def assign_planet_houses(
    planet_positions: Mapping[str, float],
    cusps: List[float],
) -> Dict[str, int]:
    """Return planet → house (1-12) mapping using Swiss house helper.

    Args:
        planet_positions: Mapping of planet name to longitude degrees.
        cusps: List of 12 cusp longitudes (degrees).
    """
    houses: Dict[str, int] = {}
    for planet in PLANET_ORDER:
        if planet not in planet_positions:
            continue
        houses[planet] = int(get_planet_house(float(planet_positions[planet]), cusps))
    return houses


def _empty_house_arrays() -> Tuple[List[float], List[float]]:
    return [0.0] * 12, [0.0] * 12


def house_occupancy_features(
    planet_positions: Mapping[str, float],
    cusps: List[float],
    planet_weights: Mapping[str, float] = DEFAULT_PLANET_WEIGHTS,
) -> Dict[str, float]:
    """Compute house counts and weighted counts.

    Returns flat dict with keys house_count_1..12, house_weighted_1..12,
    plus aggregate distribution stats (entropy, total_weight).
    """
    counts, weighted = _empty_house_arrays()
    assignments = assign_planet_houses(planet_positions, cusps)

    for planet, house in assignments.items():
        idx = max(1, min(12, house)) - 1
        counts[idx] += 1.0
        weight = float(planet_weights.get(planet, 1.0))
        weighted[idx] += weight

    total_w = sum(weighted) if weighted else 0.0
    dist = [w / total_w for w in weighted] if total_w > 0 else [0.0] * 12
    entropy = -sum(p * math.log(p) for p in dist if p > 0)

    features: Dict[str, float] = {col: counts[i] for i, col in enumerate(HOUSE_COUNT_COLS)}
    features.update({col: weighted[i] for i, col in enumerate(HOUSE_WEIGHTED_COLS)})
    features["house_weight_total"] = total_w
    features["house_entropy"] = entropy
    return features


def house_weight_for_planet(house_idx: int, weighted_counts: List[float]) -> float:
    """Normalized weight for a house index (1-12). Returns 0 if no weight."""
    if not weighted_counts:
        return 0.0
    total = sum(weighted_counts)
    if total <= 0:
        return 0.0
    idx = max(1, min(12, house_idx)) - 1
    return float(weighted_counts[idx] / total)


def house_significators(natal_data: dict, house: int) -> List[str]:
    """Return planets that rule and/or occupy a given house number (1-12).

    Accepts the JSON natal format returned by Abu Engine (chart-detailed response):
      - ``natal_data["houses"]``: list of ``{"num": int, "longitude": float, ...}``
      - ``natal_data["planets"]``: list of ``{"name": str, "longitude": float, ...}``

    Alternatively accepts a flat angles_deg mapping
    (``{"Sun": float, ..., "ASC": float, "MC": float}``) with an optional
    ``"cusps"`` key containing the 12 cusp longitudes.

    Returns:
        Deduplicated list of planet names in lowercase canonical order
        (``'sun'``, ``'moon'``, …, ``'pluto'``).  ``'asc'`` and ``'mc'``
        are never returned as occupants (they are angles, not bodies).
    """
    if not (1 <= house <= 12):
        return []

    # ── 1. Extract cusp longitudes ────────────────────────────────────
    cusps: List[float] = []
    raw_houses = natal_data.get("houses")
    if isinstance(raw_houses, list) and raw_houses:
        if isinstance(raw_houses[0], dict):
            sorted_h = sorted(raw_houses, key=lambda h: h.get("num", 0))
            cusps = [float(h["longitude"]) for h in sorted_h if "longitude" in h]
        else:
            # plain list of floats
            cusps = [float(c) for c in raw_houses]
    elif "cusps" in natal_data:
        cusps = [float(c) for c in natal_data["cusps"]]

    if len(cusps) < 12:
        return []

    # ── 2. Sign on cusp → ruler(s) ────────────────────────────────────
    cusp_lon = cusps[house - 1]
    sign, _ = longitude_to_sign_degree(cusp_lon)
    rulers: List[str] = _SIGN_RULERS.get(sign, [])

    # ── 3. Planets occupying the house ────────────────────────────────
    planet_positions: Dict[str, float] = {}
    raw_planets = natal_data.get("planets")
    if isinstance(raw_planets, list):
        for p in raw_planets:
            name = p.get("name", "")
            lon = p.get("longitude")
            if name and lon is not None and name in _TO_LOWER:
                planet_positions[name] = float(lon)
    else:
        # Flat mapping: {"Sun": float, ...}
        for key, val in natal_data.items():
            if key in _TO_LOWER and key not in ("ASC", "MC"):
                try:
                    planet_positions[key] = float(val)
                except (TypeError, ValueError):
                    pass

    occupants: List[str] = [
        p for p in PLANET_ORDER
        if p in planet_positions
        and get_planet_house(planet_positions[p], cusps) == house
    ]

    # ── 4. Merge rulers + occupants, deduplicated, canonical order ────
    merged: set = {_TO_LOWER[p] for p in rulers + occupants if p in _TO_LOWER}

    # ── 5. Fallback: if subset < 3, add ASC ruler + Sun/Moon + personal planets ──
    if len(merged) < 3:
        # ASC ruler (sign ruler of H1)
        asc_sign, _ = longitude_to_sign_degree(cusps[0])
        for p in _SIGN_RULERS.get(asc_sign, []):
            if p in _TO_LOWER:
                merged.add(_TO_LOWER[p])
        # Add in priority order until ≥ 3
        for fallback in ("sun", "moon", "mercury", "venus", "mars"):
            if len(merged) >= 3:
                break
            merged.add(fallback)

    return [p for p in _CANONICAL_LOWER if p in merged]
