"""Vectorization utilities for Harmony Field (HF Core v1).

Transforms a set of ecliptic longitudes (degrees) for the 12 primary points
into a fixed-order 24-dimensional vector (cos, sin pairs) on the unit circle.
"""

from typing import List, Mapping, Tuple
import math

# Fixed order required by HF Core v1
POINT_ORDER: List[str] = [
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
    "ASC",
    "MC",
]


def angle_to_unit_vector(angle_deg: float) -> Tuple[float, float]:
    """Convert an angle in degrees to its unit circle (cos, sin) pair.

    Args:
        angle_deg: Angle in degrees. Values are normalized to [0, 360).

    Returns:
        Tuple (cos(theta), sin(theta)).
    """
    theta_rad = math.radians(angle_deg % 360)
    return math.cos(theta_rad), math.sin(theta_rad)


def build_circle_vector(angles_deg: Mapping[str, float]) -> List[float]:
    """Build a 24-dimensional vector (cos, sin per point) in fixed order.

    Args:
        angles_deg: Mapping from point name to ecliptic longitude in degrees.
            Must include all points in POINT_ORDER.

    Returns:
        List of length 24: [cos(p1), sin(p1), cos(p2), sin(p2), ...].

    Raises:
        KeyError: If a required point is missing.
    """
    vector: List[float] = []
    for point in POINT_ORDER:
        if point not in angles_deg:
            raise KeyError(f"Missing angle for point '{point}'")
        cos_v, sin_v = angle_to_unit_vector(angles_deg[point])
        vector.extend([cos_v, sin_v])
    return vector
