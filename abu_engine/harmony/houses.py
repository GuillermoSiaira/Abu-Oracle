"""House occupancy utilities for HF Core v2.

Lightweight helpers to derive house-based features from cusp data and
planetary positions. Delegates house computation to `abu_engine.core.houses_swiss`.
"""

from __future__ import annotations

from typing import Dict, List, Mapping, Tuple
import math

from abu_engine.core.houses_swiss import get_planet_house

from .schema_v2 import PLANET_ORDER, DEFAULT_PLANET_WEIGHTS, HOUSE_COUNT_COLS, HOUSE_WEIGHTED_COLS


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
