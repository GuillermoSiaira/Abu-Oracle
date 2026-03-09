"""Harmonic energy calculations for HF Core v1."""

from typing import Iterable, Mapping, Optional, Sequence
import cmath
import math

DEFAULT_HARMONICS = (1, 2, 3, 4, 5, 6, 8, 12)


def compute_harmonic_energy(
    angles_deg: Sequence[float],
    k: int,
    weights: Optional[Sequence[float]] = None,
) -> float:
    """Compute harmonic energy H_k = |Σ w_i * exp(i * k * θ_i)|.

    Args:
        angles_deg: Sequence of angles in degrees.
        k: Harmonic index.
        weights: Optional sequence of weights (same length as angles_deg).

    Returns:
        Magnitude of the complex harmonic sum.

    Raises:
        ValueError: If weights length does not match angles length.
    """
    n = len(angles_deg)
    if weights is None:
        weights = [1.0] * n
    if len(weights) != n:
        raise ValueError("weights length must match angles length")

    accumulator = 0j
    for theta_deg, weight in zip(angles_deg, weights):
        theta_rad = math.radians(theta_deg % 360)
        accumulator += weight * cmath.exp(1j * k * theta_rad)
    return abs(accumulator)


def compute_harmonics(
    angles_deg: Sequence[float],
    ks: Iterable[int] = DEFAULT_HARMONICS,
    weights: Optional[Sequence[float]] = None,
) -> Mapping[int, float]:
    """Compute multiple harmonic energies for a set of ks."""
    return {k: compute_harmonic_energy(angles_deg, k, weights) for k in ks}
