"""HF Core v3: additive, minimal model for relocation.

Design goals:
- Keep HF v1 aspects untouched and reusable.
- Add angularity (ASC/MC) and house occupancy as additive terms, not multiplicative.
- Provide a small, auditable API ready for product use and future acceleration.
"""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Sequence
import itertools
import math

from .field import aggregate_field
from .resonance import ASPECTS, SIGMAS, ASPECT_WEIGHTS, GROUP_WEIGHTS, angular_distance_deg, gaussian_resonance, compute_planet_weights_v7, check_mutual_reception_v7
from .schema_v2 import PLANET_ORDER, DEFAULT_PLANET_WEIGHTS
from .houses import assign_planet_houses
from .antiscia import compute_antiscia_score


# Normalise lowercase planet names (from house_significators) → Title-case used in angles_deg
_LOWER_TO_TITLE: Dict[str, str] = {
    "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
    "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn", "uranus": "Uranus",
    "neptune": "Neptune", "pluto": "Pluto", "asc": "ASC", "mc": "MC",
}


def _to_title_subset(planet_subset: List[str]) -> List[str]:
    """Convert a lowercase planet_subset to the Title-case keys used in angles_deg."""
    return [_LOWER_TO_TITLE[p] for p in planet_subset if p in _LOWER_TO_TITLE]


# Defaults for HF v3 weights
DEFAULT_BETA: float = 0.6
DEFAULT_GAMMA: float = 0.3
DEFAULT_SIGMA_ANGLE: float = 10.0

# Simple, fixed house weights (can be tuned downstream)
DEFAULT_HOUSE_WEIGHTS: Dict[int, float] = {
    1: 1.2,
    2: 1.0,
    3: 1.0,
    4: 1.1,
    5: 1.05,
    6: 0.9,
    7: 1.1,
    8: 0.95,
    9: 1.05,
    10: 1.2,
    11: 1.0,
    12: 0.85,
}


def gaussian_strength(delta_deg: float, sigma_deg: float) -> float:
    if sigma_deg <= 0:
        raise ValueError("sigma_deg must be positive")
    return math.exp(-((delta_deg ** 2) / (2.0 * sigma_deg * sigma_deg)))


def compute_hf_aspects(
    angles_deg: Mapping[str, float],
    aspects: Mapping[str, float] = ASPECTS,
    sigmas: Mapping[str, float] = SIGMAS,
    aspect_weights: Mapping[str, float] = ASPECT_WEIGHTS,
    group_weights: Mapping[str, float] = GROUP_WEIGHTS,
    planet_subset: List[str] | None = None,
    planet_weights: Mapping[str, float] = DEFAULT_PLANET_WEIGHTS,
    enable_n3a_reception: bool = False,
) -> float:
    """Return HF_aspects using HF v4 weighted aggregation.

    Uses HF_weighted = w_harmony*harmony + w_tension*tension + w_conjunction*conjunction.

    Args:
        angles_deg: Mapping of point name to longitude degrees (expects HF v1 points).
        group_weights: Group-level weights {w_harmony, w_tension, w_conjunction}.
        planet_subset: Optional list of lowercase planet names (from house_significators).
            If None → all 12 points. If provided → only pairs within the subset.
        planet_weights: Optional per-planet weights (e.g. from HF v7 N1/N2).
        enable_n3a_reception: Toggle v7 Reception N3a attenuator.
    """
    is_custom_weights = any(w != 1.0 for w in planet_weights.values())

    if planet_subset is None and not is_custom_weights and not enable_n3a_reception:
        agg = aggregate_field(angles_deg, aspects=aspects, sigmas=sigmas,
                              aspect_weights=aspect_weights, group_weights=group_weights)
        return float(agg.get("HF_weighted", 0.0))

    # Filtered mode or custom weights: compute pairwise manually
    if planet_subset is not None:
        active = [p for p in _to_title_subset(planet_subset) if p in angles_deg]
    else:
        # ALL points (incl. ASC/MC) — must match aggregate_field exactly so that
        # at unit weights this path == v6_base.
        active = [p for p in angles_deg]

    if len(active) < 2:
        return 0.0

    totals: Dict[str, float] = {asp: 0.0 for asp in aspects}
    for a, b in itertools.combinations(active, 2):
        delta = angular_distance_deg(angles_deg[a], angles_deg[b])
        w_a = planet_weights.get(a, 1.0)
        w_b = planet_weights.get(b, 1.0)
        pair_weight = (w_a + w_b) / 2.0
        
        for asp_name, asp_angle in aspects.items():
            sigma = sigmas[asp_name]
            weight = aspect_weights.get(asp_name, 1.0)
            
            # N3a - Mutual Reception Attenuator
            if enable_n3a_reception and asp_name in ("square", "opposition"):
                if a in PLANET_ORDER and b in PLANET_ORDER:
                    if check_mutual_reception_v7(a, angles_deg[a], b, angles_deg[b]):
                        weight *= 0.5
            
            totals[asp_name] += weight * gaussian_resonance(delta, asp_angle, sigma) * pair_weight

    hf_harmony = totals.get("sextile", 0.0) + totals.get("trine", 0.0)
    hf_tension = totals.get("square", 0.0) + totals.get("opposition", 0.0)
    hf_conjunction = totals.get("conjunction", 0.0)
    w_h = group_weights.get("w_harmony", 1.5)
    w_t = group_weights.get("w_tension", -0.8)
    w_c = group_weights.get("w_conjunction", 1.0)
    return float(w_h * hf_harmony + w_t * hf_tension + w_c * hf_conjunction)


def compute_hf_angles(
    angles_deg: Mapping[str, float],
    sigma_angle: float = DEFAULT_SIGMA_ANGLE,
    planet_weights: Mapping[str, float] = DEFAULT_PLANET_WEIGHTS,
    planet_subset: List[str] | None = None,
    enable_n3d_angle_aspects: bool = False,
) -> float:
    """Compute angular contribution using proximity to ASC and MC (additive score).

    Args:
        angles_deg: Mapping with planet longitudes and ASC/MC (degrees).
        sigma_angle: Gaussian sigma in degrees for angular proximity.
        planet_weights: Optional per-planet weights (default 1.0 each).
        planet_subset: Optional lowercase planet names to include. ASC/MC are always
            used as angular targets regardless of this filter.
        enable_n3d_angle_aspects: Toggle for N3d operator (aspects to local ASC/MC).
    """
    asc = angles_deg.get("ASC")
    mc = angles_deg.get("MC")
    if asc is None or mc is None:
        return 0.0

    # Determine which bodies to score (subset or full PLANET_ORDER; never ASC/MC as sources)
    if planet_subset is not None:
        active_titles = [p for p in _to_title_subset(planet_subset)
                         if p in PLANET_ORDER and p in angles_deg]
    else:
        active_titles = [p for p in PLANET_ORDER if p in angles_deg]

    total = 0.0
    for planet in active_titles:
        p_lon = float(angles_deg[planet])
        w = float(planet_weights.get(planet, 1.0))

        delta_asc = angular_distance_deg(p_lon, float(asc))
        delta_mc = angular_distance_deg(p_lon, float(mc))

        s_asc = gaussian_strength(delta_asc, sigma_angle)
        s_mc = gaussian_strength(delta_mc, sigma_angle)

        total += w * (s_asc + s_mc)

    if enable_n3d_angle_aspects:
        from .angularity import compute_n3d_angle_aspects
        # Extract subset of positions for active planets
        pos = {p: angles_deg[p] for p in active_titles}
        total += compute_n3d_angle_aspects(pos, angles_deg, planet_weights)

    return float(total)


def compute_hf_houses(
    angles_deg: Mapping[str, float],
    cusps: Optional[Sequence[float]] = None,
    house_weights: Mapping[int, float] = DEFAULT_HOUSE_WEIGHTS,
    planet_weights: Mapping[str, float] = DEFAULT_PLANET_WEIGHTS,
    planet_subset: List[str] | None = None,
) -> float:
    """Compute a simple house occupancy score (additive).

    Args:
        angles_deg: Mapping with planet longitudes.
        cusps: Optional list of 12 cusp longitudes (deg). Required for non-zero output.
        house_weights: Weight per house number (1-12).
        planet_weights: Optional per-planet weights.
        planet_subset: Optional lowercase planet names to include.
    """
    if not cusps or len(cusps) < 12:
        return 0.0

    if planet_subset is not None:
        active = [p for p in _to_title_subset(planet_subset) if p in PLANET_ORDER]
    else:
        active = list(PLANET_ORDER)

    planet_positions = {p: float(angles_deg[p]) for p in active if p in angles_deg}
    assignments = assign_planet_houses(planet_positions, list(cusps))

    score = 0.0
    for planet, house_idx in assignments.items():
        w_p = float(planet_weights.get(planet, 1.0))
        w_h = float(house_weights.get(int(house_idx), 1.0))
        score += w_p * w_h

    return float(score)


def compute_hf_v3(
    angles_deg: Mapping[str, float],
    cusps: Optional[Sequence[float]] = None,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
    sigma_angle: float = DEFAULT_SIGMA_ANGLE,
    aspects: Mapping[str, float] = ASPECTS,
    sigmas: Mapping[str, float] = SIGMAS,
    aspect_weights: Mapping[str, float] = ASPECT_WEIGHTS,
    group_weights: Mapping[str, float] = GROUP_WEIGHTS,
    house_weights: Mapping[int, float] = DEFAULT_HOUSE_WEIGHTS,
    planet_weights: Mapping[str, float] = DEFAULT_PLANET_WEIGHTS,
    planet_subset: List[str] | None = None,
    # V7 Extensions
    sect: str = "diurnal",
    dignities: Optional[Dict[str, str]] = None,
    enable_n1_sect: bool = False,
    enable_n2_dignity: bool = False,
    enable_n3a_reception: bool = False,
    enable_n3b_antiscia: bool = False,
    enable_n3d_angle_aspects: bool = False,
) -> Dict[str, float]:
    """Compute HF v3 additive score (now using v4 weighted aspects).

    HF_total_v3 = HF_aspects(weighted) + beta * HF_angles + gamma * HF_houses

    Args:
        planet_subset: Optional list of lowercase planet names (from house_significators).
            If None → all 12 points (default behaviour).
            If provided → only those planets participate in aspects, angularity, and house scoring.
        sect: "diurnal" or "nocturnal".
        dignities: dictionary mapping planet name to traditional dignity string.
        enable_n1_sect: Toggle v7 Sect N1 weights.
        enable_n2_dignity: Toggle v7 Dignity N2 weights.
        enable_n3a_reception: Toggle v7 Reception N3a attenuator.
        enable_n3b_antiscia: Toggle v7 Antiscia N3b operator.
        enable_n3d_angle_aspects: Toggle v7 Aspects to angles N3d operator.

    Returns a dict with components and hyperparameters.
    """
    
    # Compute combined V7 weights if N1 or N2 is enabled.
    if enable_n1_sect or enable_n2_dignity:
        derived_weights = compute_planet_weights_v7(
            sect=sect, 
            dignities=dignities, 
            enable_n1_sect=enable_n1_sect, 
            enable_n2_dignity=enable_n2_dignity
        )
        active_planet_weights = derived_weights
    else:
        active_planet_weights = planet_weights

    hf_aspects = compute_hf_aspects(angles_deg, aspects=aspects, sigmas=sigmas,
                                    aspect_weights=aspect_weights, group_weights=group_weights,
                                    planet_subset=planet_subset, planet_weights=active_planet_weights,
                                    enable_n3a_reception=enable_n3a_reception)
                                    
    if enable_n3b_antiscia:
        active_list = _to_title_subset(planet_subset) if planet_subset is not None else list(angles_deg.keys())
        antiscia_score = compute_antiscia_score(angles_deg, active_list, active_planet_weights)
        hf_aspects += antiscia_score
    hf_angles = compute_hf_angles(angles_deg, sigma_angle=sigma_angle,
                                  planet_weights=active_planet_weights, planet_subset=planet_subset,
                                  enable_n3d_angle_aspects=enable_n3d_angle_aspects)
    # HF_houses NO recibe los pesos v7: el spec (SPEC-HF-V7-01 §2) acota W(p) a
    # aspectos + angularidad; las casas se mantienen como v6 (preregistro).
    hf_houses = compute_hf_houses(angles_deg, cusps=cusps, house_weights=house_weights,
                                  planet_weights=planet_weights, planet_subset=planet_subset)

    hf_total_v3 = hf_aspects + beta * hf_angles + gamma * hf_houses

    return {
        "hf_total_v3": float(hf_total_v3),
        "hf_aspects": float(hf_aspects),
        "hf_angles": float(hf_angles),
        "hf_houses": float(hf_houses),
        "beta": float(beta),
        "gamma": float(gamma),
        "sigma_angle": float(sigma_angle),
        "group_weights": {"w_harmony": group_weights.get("w_harmony", 1.5),
                          "w_tension": group_weights.get("w_tension", -0.8),
                          "w_conjunction": group_weights.get("w_conjunction", 1.0)},
        "planet_subset": planet_subset,
        "n1_enabled": enable_n1_sect,
        "n2_enabled": enable_n2_dignity,
        "n3a_enabled": enable_n3a_reception,
        "n3b_enabled": enable_n3b_antiscia,
        "n3d_enabled": enable_n3d_angle_aspects,
    }


def example_usage() -> Dict[str, float]:
    """Tiny example demonstrating the API (using mock angles)."""

    mock_angles = {
        "Sun": 10.0,
        "Moon": 40.0,
        "Mercury": 70.0,
        "Venus": 120.0,
        "Mars": 190.0,
        "Jupiter": 220.0,
        "Saturn": 250.0,
        "Uranus": 300.0,
        "Neptune": 310.0,
        "Pluto": 330.0,
        "ASC": 15.0,
        "MC": 285.0,
    }
    mock_cusps = [i * 30.0 for i in range(12)]  # simplistic whole-sign-like cusps

    return compute_hf_v3(mock_angles, cusps=mock_cusps)


# Notes for integration:
# - In relocation pipelines (e.g., generate_relocation_field.py), pass angles_deg that
#   already include ASC/MC and a list of 12 cusps if house scoring is desired.
# - HF_aspects reuses v1 aggregation; no changes needed in upstream data preparation.
# - Beta/gamma/sigma_angle can be tuned via CLI flags when wiring into scripts.