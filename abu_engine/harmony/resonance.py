"""Resonance kernel utilities for Harmony Field (HF Core v1)."""

from typing import Dict
import math

ASPECTS: Dict[str, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

# Standard deviation (sigma) per aspect in degrees
SIGMAS: Dict[str, float] = {
    "conjunction": 4.0,
    "sextile": 4.0,
    "square": 4.0,
    "trine": 4.0,
    "opposition": 4.0,
}

# Relative weights per aspect (can be tuned externally)
ASPECT_WEIGHTS: Dict[str, float] = {
    "conjunction": 1.0,
    "sextile": 1.0,
    "square": 1.0,
    "trine": 1.0,
    "opposition": 1.0,
}

# Group-level weights for HF v4 weighted formula (optimized via grid search)
# HF_weighted = w_harmony * (sextile+trine) + w_tension * (square+opposition) + w_conjunction * conjunction
# Optimization v2 (527 bio events, 26 subjects): corr_nn=+0.156, Cohen's d=+0.447
# Sign pattern confirmed: harmony and tension both SUBTRACT; conjunction ADDS.
# Conjunctions dominate: w_c=2.5 is the strongest weight.
GROUP_WEIGHTS: Dict[str, float] = {
    "w_harmony": -1.0,
    "w_tension": -1.0,
    "w_conjunction": 2.5,
}


def angular_distance_deg(a_deg: float, b_deg: float) -> float:
    """Smallest angular distance on the circle in degrees (0–180]."""
    return abs((a_deg - b_deg + 180) % 360 - 180)


def gaussian_resonance(delta_deg: float, aspect_deg: float, sigma: float) -> float:
    """Gaussian resonance centered at a target aspect.

    Args:
        delta_deg: Angular separation between two points (degrees).
        aspect_deg: Target aspect angle (degrees).
        sigma: Standard deviation of the Gaussian (degrees).

    Returns:
        Resonance value in (0, 1].

    Raises:
        ValueError: If sigma is not positive.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    diff = delta_deg - aspect_deg
    return math.exp(-(diff * diff) / (2 * sigma * sigma))
