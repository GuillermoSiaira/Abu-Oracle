"""Antiscia utilities for HF Core v7."""

from typing import Mapping, List
import itertools
from .resonance import angular_distance_deg

def compute_antiscia_score(
    angles_deg: Mapping[str, float],
    active_planets: List[str],
    planet_weights: Mapping[str, float]
) -> float:
    """Compute N3b antiscia contribution.
    
    Antiscio: (180 - λ) mod 360
    Contra-antiscio: (360 - λ) mod 360
    """
    total_score = 0.0
    
    # We only consider planet <-> planet
    from .schema_v2 import PLANET_ORDER
    planets_only = [p for p in active_planets if p in PLANET_ORDER]
    
    for a, b in itertools.combinations(planets_only, 2):
        lon_a = angles_deg[a]
        lon_b = angles_deg[b]
        
        w_a = planet_weights.get(a, 1.0)
        w_b = planet_weights.get(b, 1.0)
        pair_weight = (w_a + w_b) / 2.0
        
        antiscio_b = (180.0 - lon_b) % 360.0
        contra_b = (360.0 - lon_b) % 360.0
        
        # Check aspect A to Antiscio of B
        delta_antiscio = angular_distance_deg(lon_a, antiscio_b)
        if delta_antiscio <= 2.0:
            total_score += 1.0 * pair_weight
            
        # Check aspect A to Contra-Antiscio of B
        delta_contra = angular_distance_deg(lon_a, contra_b)
        if delta_contra <= 2.0:
            total_score += -0.8 * pair_weight
            
    return float(total_score)
