"""Harmony Field aggregation utilities (HF Core v1)."""

from typing import Dict, List, Mapping, Tuple
import itertools

from .chart_vector import POINT_ORDER
from .resonance import ASPECTS, SIGMAS, ASPECT_WEIGHTS, angular_distance_deg, gaussian_resonance

PairResonance = Dict[str, float]
PairEntry = Dict[str, object]


def compute_pairwise_resonances(
    angles_deg: Mapping[str, float],
    aspects: Mapping[str, float] = ASPECTS,
    sigmas: Mapping[str, float] = SIGMAS,
    aspect_weights: Mapping[str, float] = ASPECT_WEIGHTS,
) -> List[PairEntry]:
    """Compute Gaussian resonances for all 66 pairs across the 12 points.

    Args:
        angles_deg: Mapping from point name to longitude in degrees.
        aspects: Aspect angles in degrees.
        sigmas: Sigma (spread) per aspect.
        aspect_weights: Weight per aspect.

    Returns:
        List of pair entries: {"pair": (A, B), "delta": float, "resonance": {aspect: value}}.

    Raises:
        KeyError: If an expected point or aspect parameter is missing.
    """
    pairs: List[PairEntry] = []
    for a, b in itertools.combinations(POINT_ORDER, 2):
        if a not in angles_deg or b not in angles_deg:
            raise KeyError(f"Missing angle for pair ({a}, {b})")
        delta = angular_distance_deg(angles_deg[a], angles_deg[b])
        resonance_values: PairResonance = {}
        for aspect_name, aspect_angle in aspects.items():
            if aspect_name not in sigmas:
                raise KeyError(f"Missing sigma for aspect '{aspect_name}'")
            sigma = sigmas[aspect_name]
            weight = aspect_weights.get(aspect_name, 1.0)
            resonance_values[aspect_name] = weight * gaussian_resonance(delta, aspect_angle, sigma)
        pairs.append({"pair": (a, b), "delta": delta, "resonance": resonance_values})
    return pairs


def aggregate_field(
    angles_deg: Mapping[str, float],
    aspects: Mapping[str, float] = ASPECTS,
    sigmas: Mapping[str, float] = SIGMAS,
    aspect_weights: Mapping[str, float] = ASPECT_WEIGHTS,
) -> Dict[str, object]:
    """Aggregate Harmony Field metrics across all pairs.

    Returns a dict with per-aspect totals and grouped scores:
    - HF_total: sum of all aspect contributions
    - HF_harmony: sextile + trine
    - HF_tension: square + opposition
    - HF_conjunction: conjunction only
    """
    pairs = compute_pairwise_resonances(angles_deg, aspects, sigmas, aspect_weights)

    totals: Dict[str, float] = {aspect: 0.0 for aspect in aspects}
    for entry in pairs:
        resonance_values = entry["resonance"]
        for aspect_name, value in resonance_values.items():
            totals[aspect_name] = totals.get(aspect_name, 0.0) + value

    hf_harmony = totals.get("sextile", 0.0) + totals.get("trine", 0.0)
    hf_tension = totals.get("square", 0.0) + totals.get("opposition", 0.0)
    hf_conjunction = totals.get("conjunction", 0.0)
    hf_total = sum(totals.values())

    return {
        "pairs": pairs,
        "totals": totals,
        "HF_total": hf_total,
        "HF_harmony": hf_harmony,
        "HF_tension": hf_tension,
        "HF_conjunction": hf_conjunction,
    }
