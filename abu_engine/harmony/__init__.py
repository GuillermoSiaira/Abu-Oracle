"""Harmony Field core primitives (HF Core v1).

Provides chart vectorization, harmonic energies, resonance kernels,
and aggregated field metrics for 12 primary points.
"""

from .chart_vector import POINT_ORDER, build_circle_vector, angle_to_unit_vector
from .harmonics import DEFAULT_HARMONICS, compute_harmonic_energy, compute_harmonics
from .resonance import ASPECTS, SIGMAS, ASPECT_WEIGHTS, GROUP_WEIGHTS, angular_distance_deg, gaussian_resonance
from .field import compute_pairwise_resonances, aggregate_field
from .schema_v2 import (
    PLANET_ORDER,
    ANGLE_KEYS,
    DEFAULT_PLANET_WEIGHTS,
    DEFAULT_ANGULAR_SIGMA_DEG,
    DEFAULT_LAMBDA_HOUSE,
    DEFAULT_LAMBDA_ANGLE,
)
from .houses import assign_planet_houses, house_occupancy_features, house_weight_for_planet
from .angularity import derive_angles_from_asc_mc, planet_angular_strengths
from .field_v2 import aggregate_field_v2
from .field_v3 import (
    compute_hf_aspects,
    compute_hf_angles,
    compute_hf_houses,
    compute_hf_v3,
    DEFAULT_BETA,
    DEFAULT_GAMMA,
    DEFAULT_SIGMA_ANGLE,
    DEFAULT_HOUSE_WEIGHTS,
)

__all__ = [
    "POINT_ORDER",
    "build_circle_vector",
    "angle_to_unit_vector",
    "DEFAULT_HARMONICS",
    "compute_harmonic_energy",
    "compute_harmonics",
    "ASPECTS",
    "SIGMAS",
    "ASPECT_WEIGHTS",
    "GROUP_WEIGHTS",
    "angular_distance_deg",
    "gaussian_resonance",
    "compute_pairwise_resonances",
    "aggregate_field",
    "PLANET_ORDER",
    "ANGLE_KEYS",
    "DEFAULT_PLANET_WEIGHTS",
    "DEFAULT_ANGULAR_SIGMA_DEG",
    "DEFAULT_LAMBDA_HOUSE",
    "DEFAULT_LAMBDA_ANGLE",
    "assign_planet_houses",
    "house_occupancy_features",
    "house_weight_for_planet",
    "derive_angles_from_asc_mc",
    "planet_angular_strengths",
    "aggregate_field_v2",
    "compute_hf_aspects",
    "compute_hf_angles",
    "compute_hf_houses",
    "compute_hf_v3",
    "DEFAULT_BETA",
    "DEFAULT_GAMMA",
    "DEFAULT_SIGMA_ANGLE",
    "DEFAULT_HOUSE_WEIGHTS",
]
