# Harmony Field Theoretical Framework (HF Core v1)

## Purpose
This document summarizes the mathematical constructs of Harmony Field (HF) Core v1. It provides a concise reference for the angular representation, harmonic features, resonance kernel, and HF metrics that underpin all downstream experiments, including relocation sensitivity.

## Model Elements
- **Angular points (12):** Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Ascendant (ASC), Midheaven (MC).
- **Circular vector (24D):** For each point with longitude θᵢ (radians), encode (cos θᵢ, sin θᵢ) to preserve rotational symmetry and enable harmonic aggregation.
- **Harmonic signature (8D):** For harmonics k ∈ {1, 2, 3, 4, 5, 6, 8, 12}, compute H_k = |Σ wᵢ · e^{i·k·θᵢ}| using point weights wᵢ from HF Core v1.
- **Resonance kernel:** Gaussian resonance over major aspects (0°, 60°, 90°, 120°, 180°) with configurable σ and aspect weights; applied to pairwise angular separations.
- **HF metrics (4D):**
  - `hf_total`: aggregate resonance across aspect classes.
  - `hf_harmony`: resonance from sextile (60°) and trine (120°).
  - `hf_tension`: resonance from square (90°) and opposition (180°).
  - `hf_conjunction`: resonance near 0°.
- **Total embedding:** 36 dimensions = 24 (circular) + 8 (harmonic) + 4 (HF metrics).

## Relocation Field Definition
For a birth instant t₀ and natal site (φ₀, λ₀):
- **HF(φ, λ):** HF metrics computed at latitude φ and longitude λ with planetary longitudes fixed at t₀, while ASC/MC/houses are recomputed for (φ, λ).
- **ΔHF(φ, λ):** Component-wise delta: HF(φ, λ) − HF(φ₀, λ₀).

Planetary positions are invariant under relocation; only location-dependent angles vary. Abu Engine supplies ASC/MC/houses; HF Core computes the embedding and metrics.

## Architectural Boundary
- **Abu Engine:** Astronomy (planetary longitudes, sidereal time, ASC, MC, houses).
- **HF Core:** Mathematical transforms (circular vector, harmonic features, resonance, HF metrics). HF Core functions are pure/stateless and may be batched or cached.

## Notes for Future Extensions
- HF v2 is expected to incorporate house cusps/occupancy to make the embedding explicitly house-aware.
- JAX acceleration may target the HF computation stage only; astronomical calculations stay in Abu Engine.