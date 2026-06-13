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


# --- V7 Extensions (Sect and Dignity N1/N2) ---

SECT_MULTIPLIERS = {
    "luminaria_secta": 1.15,
    "benefico_secta": 1.15,
    "benefico_contrario": 1.00,
    "malefico_secta": 0.85,
    "malefico_contrario": 1.15,
    "neutro": 1.00
}

DIGNITY_MULTIPLIERS = {
    "domicilio": 1.30,
    "exaltacion": 1.20,
    "triplicidad": 1.10,
    "termino": 1.05,
    "faz": 1.00,
    "peregrino": 0.90,
    "detrimento": 0.75,
    "caida": 0.70
}

def get_sect_role(planet: str, sect: str) -> str:
    """Determine the sect role of a planet given the chart's sect ('diurnal' or 'nocturnal')."""
    planet = planet.lower()
    sect = sect.lower()
    
    if planet in ("mercury", "uranus", "neptune", "pluto"):
        return "neutro"
        
    is_diurnal = sect == "diurnal"
    
    if planet == "sun":
        return "luminaria_secta" if is_diurnal else "neutro"
    if planet == "moon":
        return "luminaria_secta" if not is_diurnal else "neutro"
        
    if planet == "jupiter":
        return "benefico_secta" if is_diurnal else "benefico_contrario"
    if planet == "venus":
        return "benefico_secta" if not is_diurnal else "benefico_contrario"
        
    if planet == "saturn":
        return "malefico_secta" if is_diurnal else "malefico_contrario"
    if planet == "mars":
        return "malefico_secta" if not is_diurnal else "malefico_contrario"
        
    return "neutro"

def compute_planet_weights_v7(
    sect: str = "diurnal", 
    dignities: Dict[str, str] = None, 
    enable_n1_sect: bool = False,
    enable_n2_dignity: bool = False
) -> Dict[str, float]:
    from .schema_v2 import PLANET_ORDER
    weights = {p: 1.0 for p in PLANET_ORDER}
    
    if not enable_n1_sect and not enable_n2_dignity:
        return weights
        
    dignities = dignities or {}
    
    for p in PLANET_ORDER:
        w = 1.0
        if enable_n1_sect:
            role = get_sect_role(p, sect)
            w *= SECT_MULTIPLIERS.get(role, 1.0)
            
        if enable_n2_dignity:
            dig = dignities.get(p.lower(), "peregrino")
            dig_norm = dig.lower()
            if dig_norm in ("domicile", "domicilio"): val = DIGNITY_MULTIPLIERS["domicilio"]
            elif dig_norm in ("exaltation", "exaltacion"): val = DIGNITY_MULTIPLIERS["exaltacion"]
            elif dig_norm in ("triplicity", "triplicidad"): val = DIGNITY_MULTIPLIERS["triplicidad"]
            elif dig_norm in ("term", "termino"): val = DIGNITY_MULTIPLIERS["termino"]
            elif dig_norm in ("face", "faz", "decan"): val = DIGNITY_MULTIPLIERS["faz"]
            elif dig_norm in ("detriment", "detrimento"): val = DIGNITY_MULTIPLIERS["detrimento"]
            elif dig_norm in ("fall", "caida"): val = DIGNITY_MULTIPLIERS["caida"]
            else: val = DIGNITY_MULTIPLIERS["peregrino"]
            
            w *= val
            
        weights[p] = w
        
    return weights

