"""HF Core v2: house- and angular-aware field aggregation.

Built as an extension over HF Core v1 (see `field.py`).
"""

from __future__ import annotations

from typing import Dict, Mapping, List

from .field import compute_pairwise_resonances
from .resonance import ASPECTS, SIGMAS, ASPECT_WEIGHTS
from .schema_v2 import (
    PLANET_ORDER,
    DEFAULT_PLANET_WEIGHTS,
    DEFAULT_ANGULAR_SIGMA_DEG,
    DEFAULT_CUSP_SIGMA_DEG,
    DEFAULT_LAMBDA_HOUSE,
    DEFAULT_LAMBDA_ANGLE,
)
from .houses import house_occupancy_features, house_weight_for_planet, assign_planet_houses
from .angularity import derive_angles_from_asc_mc, planet_angular_strengths


def _default_planet_positions(angles_deg: Mapping[str, float]) -> Dict[str, float]:
    return {p: float(angles_deg[p]) for p in PLANET_ORDER if p in angles_deg}


def aggregate_field_v2(
    angles_deg: Mapping[str, float],
    cusps: List[float],
    planet_weights: Mapping[str, float] = DEFAULT_PLANET_WEIGHTS,
    aspects: Mapping[str, float] = ASPECTS,
    sigmas: Mapping[str, float] = SIGMAS,
    aspect_weights: Mapping[str, float] = ASPECT_WEIGHTS,
    sigma_angular_deg: float = DEFAULT_ANGULAR_SIGMA_DEG,
    lambda_house: float = DEFAULT_LAMBDA_HOUSE,
    lambda_angle: float = DEFAULT_LAMBDA_ANGLE,
) -> Dict[str, object]:
    """Aggregate HF v2 metrics.

    Args:
        angles_deg: Mapping with Sun..Pluto + ASC/MC (deg).
        cusps: List of 12 cusp longitudes (deg).
        planet_weights: Weights for house occupancy.
        sigma_angular_deg: Sigma for angular strength kernel.
        lambda_house: Multiplier weight for house-aware term.
        lambda_angle: Multiplier weight for angularity term.
    """

    planet_positions = _default_planet_positions(angles_deg)

    # House features
    house_feats = house_occupancy_features(planet_positions, cusps, planet_weights)
    weighted_counts = [house_feats[f"house_weighted_{i}"] for i in range(1, 13)]
    assignments = assign_planet_houses(planet_positions, cusps)

    # Angularity features
    asc = float(angles_deg.get("ASC", 0.0))
    mc = float(angles_deg.get("MC", 0.0))
    angles_full = derive_angles_from_asc_mc(asc, mc)
    per_planet_ang, ang_agg = planet_angular_strengths(planet_positions, angles_full, sigma_deg=sigma_angular_deg)

    # Base pair resonances (v1)
    pairs = compute_pairwise_resonances(angles_deg, aspects, sigmas, aspect_weights)

    totals_v1: Dict[str, float] = {aspect: 0.0 for aspect in aspects}
    totals_v2: Dict[str, float] = {aspect: 0.0 for aspect in aspects}

    for entry in pairs:
        (a, b) = entry["pair"]
        for aspect_name, base_val in entry["resonance"].items():
            totals_v1[aspect_name] += base_val

            # House weight component
            h_a = house_weight_for_planet(assignments.get(a, 0), weighted_counts) if a in assignments else 0.0
            h_b = house_weight_for_planet(assignments.get(b, 0), weighted_counts) if b in assignments else 0.0
            house_multiplier = 1.0 + lambda_house * ((h_a + h_b) / 2.0)

            # Angularity component (mean strength per planet)
            a_ang = per_planet_ang.get(a, {}).get("mean_strength", 0.0)
            b_ang = per_planet_ang.get(b, {}).get("mean_strength", 0.0)
            ang_multiplier = 1.0 + lambda_angle * ((a_ang + b_ang) / 2.0)

            weighted_val = base_val * house_multiplier * ang_multiplier
            totals_v2[aspect_name] += weighted_val

    hf_harmony_v2 = totals_v2.get("sextile", 0.0) + totals_v2.get("trine", 0.0)
    hf_tension_v2 = totals_v2.get("square", 0.0) + totals_v2.get("opposition", 0.0)
    hf_conjunction_v2 = totals_v2.get("conjunction", 0.0)
    hf_total_v2 = sum(totals_v2.values())

    # Base metrics from v1 (for comparison)
    hf_harmony_v1 = totals_v1.get("sextile", 0.0) + totals_v1.get("trine", 0.0)
    hf_tension_v1 = totals_v1.get("square", 0.0) + totals_v1.get("opposition", 0.0)
    hf_conjunction_v1 = totals_v1.get("conjunction", 0.0)
    hf_total_v1 = sum(totals_v1.values())

    return {
        "pairs": pairs,
        "totals_v1": totals_v1,
        "totals_v2": totals_v2,
        "HF_total_v1": hf_total_v1,
        "HF_harmony_v1": hf_harmony_v1,
        "HF_tension_v1": hf_tension_v1,
        "HF_conjunction_v1": hf_conjunction_v1,
        "HF_total_v2": hf_total_v2,
        "HF_harmony_v2": hf_harmony_v2,
        "HF_tension_v2": hf_tension_v2,
        "HF_conjunction_v2": hf_conjunction_v2,
        "HF_angularity": ang_agg.get("angularity_sum", 0.0),
        "HF_house_balance": house_feats.get("house_entropy", 0.0),
        "house_features": house_feats,
        "angular_features": {"per_planet": per_planet_ang, "aggregate": ang_agg},
        "config": {
            "sigma_angular_deg": sigma_angular_deg,
            "lambda_house": lambda_house,
            "lambda_angle": lambda_angle,
            "planet_weights": dict(planet_weights),
            "cusp_sigma_deg": DEFAULT_CUSP_SIGMA_DEG,
        },
    }
