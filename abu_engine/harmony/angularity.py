"""Angularity utilities for HF Core v2.

Computes Gaussian angular strength of planets to ASC/MC/DESC/IC and aggregated
metrics usable by HF v2 scoring.
"""

from __future__ import annotations

from typing import Dict, Mapping, Tuple
import math

from .resonance import angular_distance_deg
from .schema_v2 import ANGLE_KEYS, PLANET_ORDER, DEFAULT_ANGULAR_SIGMA_DEG


def derive_angles_from_asc_mc(asc: float, mc: float) -> Dict[str, float]:
    desc = (asc + 180.0) % 360.0
    ic = (mc + 180.0) % 360.0
    return {"ASC": asc % 360.0, "MC": mc % 360.0, "DESC": desc, "IC": ic}


def gaussian_strength(delta_deg: float, sigma: float) -> float:
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    return math.exp(-(delta_deg * delta_deg) / (2 * sigma * sigma))


def planet_angular_strengths(
    planet_positions: Mapping[str, float],
    angles_deg: Mapping[str, float],
    sigma_deg: float = DEFAULT_ANGULAR_SIGMA_DEG,
    planet_weights: Optional[Mapping[str, float]] = None,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
    """Return per-planet angular strengths and aggregated scores.

    Returns:
        per_planet: {planet: {angle: strength, ..., "mean_strength": x, "max_strength": y}}
        aggregate: {"angularity_sum": float, "angularity_mean": float}
    """
    per_planet: Dict[str, Dict[str, float]] = {}
    accum = []
    weights = planet_weights or {}
    
    for planet in PLANET_ORDER:
        if planet not in planet_positions:
            continue
        p_lon = float(planet_positions[planet]) % 360.0
        w = float(weights.get(planet, 1.0))
        
        strengths: Dict[str, float] = {}
        for angle_key in ANGLE_KEYS:
            if angle_key not in angles_deg:
                continue
            delta = angular_distance_deg(p_lon, float(angles_deg[angle_key]))
            strengths[angle_key] = gaussian_strength(delta, sigma_deg) * w
            
        if not strengths:
            continue
            
        mean_s = sum(strengths.values()) / len(strengths)
        max_s = max(strengths.values())
        strengths["mean_strength"] = mean_s
        strengths["max_strength"] = max_s
        per_planet[planet] = strengths
        accum.append(mean_s)

    angularity_sum = float(sum(accum))
    angularity_mean = float(angularity_sum / len(accum)) if accum else 0.0
    aggregate = {"angularity_sum": angularity_sum, "angularity_mean": angularity_mean}
    return per_planet, aggregate


def compute_n3d_angle_aspects(
    planet_positions: Mapping[str, float],
    angles_deg: Mapping[str, float],
    planet_weights: Optional[Mapping[str, float]] = None,
) -> float:
    """Compute N3d contribution: aspects from planets to local ASC and MC."""
    from .resonance import gaussian_resonance

    sigma = 3.0
    aspects = {
        "sextile": 60.0,
        "square": 90.0,
        "trine": 120.0,
        "opposition": 180.0
    }
    # Pesos N3d explícitos: aspecto armónico al ángulo local favorece (+), tenso
    # perjudica (−). NO se reusa GROUP_WEIGHTS (w_harmony=w_tension=-1.0, calibrado
    # para el agregado global donde ambos restan): acá la distinción armónico/tenso
    # al ángulo es el punto del operador, y W(p) modula fuerza, no valencia.
    w_h = 1.0
    w_t = -1.0
    
    score = 0.0
    weights = planet_weights or {}
    
    targets = []
    if "ASC" in angles_deg:
        targets.append(float(angles_deg["ASC"]) % 360.0)
    if "MC" in angles_deg:
        targets.append(float(angles_deg["MC"]) % 360.0)
        
    for planet in PLANET_ORDER:
        if planet not in planet_positions:
            continue
        p_lon = float(planet_positions[planet]) % 360.0
        w = float(weights.get(planet, 1.0))
        
        for target_lon in targets:
            delta = angular_distance_deg(p_lon, target_lon)
            for asp_name, asp_angle in aspects.items():
                asp_w = w_h if asp_name in ("sextile", "trine") else w_t
                res = gaussian_resonance(delta, asp_angle, sigma)
                score += res * asp_w * w
                
    return score
