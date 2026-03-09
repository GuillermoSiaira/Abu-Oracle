"""Schemas and defaults for HF Core v2 (house- and angular-aware).

This module centralizes names and default hyperparameters so other modules can
import a single source of truth. Keep it minimal and deterministic.
"""

from __future__ import annotations

from typing import Dict, List

# Planet list (exclude angles) used for house occupancy and angularity features.
PLANET_ORDER: List[str] = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
]

# Angles considered for angularity strength.
ANGLE_KEYS: List[str] = ["ASC", "MC", "DESC", "IC"]

# Default equal weights per user choice.
DEFAULT_PLANET_WEIGHTS: Dict[str, float] = {p: 1.0 for p in PLANET_ORDER}

# Gaussian sigma (degrees) for angular strength to ASC/MC/DESC/IC.
DEFAULT_ANGULAR_SIGMA_DEG: float = 10.0

# Sigma for cusp proximity (if used by downstream weighting).
DEFAULT_CUSP_SIGMA_DEG: float = 10.0

# House/angle multipliers applied to pair resonance (HF v2 core idea).
DEFAULT_LAMBDA_HOUSE: float = 0.3
DEFAULT_LAMBDA_ANGLE: float = 0.5

# Column name helpers
HOUSE_COUNT_COLS: List[str] = [f"house_count_{i}" for i in range(1, 13)]
HOUSE_WEIGHTED_COLS: List[str] = [f"house_weighted_{i}" for i in range(1, 13)]

# Aggregated metrics names for HF v2 outputs
HF_V2_METRICS: List[str] = [
    "hf_total_v2",
    "hf_harmony_v2",
    "hf_tension_v2",
    "hf_conjunction_v2",
    "hf_angularity",
    "hf_house_balance",
]
