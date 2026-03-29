"""HF v6 — Angularidad × Dignidad × Amplificador de intersección Firdaria∩Dominio.

Diseño:
    HF_v6 = HF_aspects(v3, subset_k) + β * HF_angles_v6 + γ * HF_houses(v3, subset_k)

    HF_angles_v6 = Σ_{p ∈ subset_k} angularity(p, φ, λ) × dignity_score(p) × w(p, t, k)

    w(p, t, k) = 2.0  si p ∈ (firdaria_planets ∩ significadores_k)
                 1.0  en caso contrario

Diferencias respecto a HF_v5:
    - HF_aspects: sin modificación — misma geometría gaussiana de HF_v3.
      (HF_v5 mezclaba dignidad dentro del kernel de aspecto; aquí se separan.)
    - HF_angles: angularidad × dignidad × amplificador de intersección.
      La dignidad modula la angularidad, no los aspectos.
    - w(p,t,k) amplifica SOLO planetas que simultáneamente son lord del período
      firdaria activo Y significadores del dominio consultado (intersección, no unión).
      Si la intersección es vacía → w=1.0 para todos (sin amplificación).
    - HF_houses: sin modificación.

Nota sobre dignity_score=0 (peregrine):
    angularity(p) × 0 × w = 0 → el planeta no contribuye al término angular.
    Correcto doctrinalmente: un peregrine angular no activa el dominio.

Nota sobre dignity_score<0 (detrimento / caída):
    Contribución negativa → valle de adversidad en (φ, λ).
    Un Saturno en detrimento angular genera obstáculos locales para ese dominio.
"""

from __future__ import annotations

import math
import itertools
from datetime import datetime
from typing import Dict, List, Optional, Set

from core.extended_calc import calculate_dignity
from core.fardars import get_current_fardar, is_diurnal_chart
from harmony.angularity import planet_angular_strengths, derive_angles_from_asc_mc
from harmony.houses import house_significators
from harmony.field_v3 import compute_hf_aspects, compute_hf_houses
from harmony.resonance import GROUP_WEIGHTS


# ---------------------------------------------------------------------------
# Constants (inherit from v3)
# ---------------------------------------------------------------------------

_BETA_ANG: float = 0.6
_GAMMA_HOUSES: float = 0.3

_LOWER_TO_TITLE: Dict[str, str] = {
    "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
    "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
    "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto",
    "asc": "ASC", "mc": "MC",
}

_FIRDARIA_W_INTERSECT: float = 2.0


# ---------------------------------------------------------------------------
# Private helpers (same extraction logic as hf_v5, kept local)
# ---------------------------------------------------------------------------

def _extract_planet_lons(natal_data: dict) -> Dict[str, float]:
    result: Dict[str, float] = {}
    raw = natal_data.get("planets")
    if isinstance(raw, list):
        for p in raw:
            name = p.get("name", "")
            lon = p.get("longitude") if p.get("longitude") is not None else p.get("lon")
            if name and lon is not None:
                try:
                    result[name] = float(lon)
                except (TypeError, ValueError):
                    pass
    else:
        for key, val in natal_data.items():
            if key in _LOWER_TO_TITLE.values():
                try:
                    result[key] = float(val)
                except (TypeError, ValueError):
                    pass
    return result


def _extract_birth_dt(natal_data: dict) -> Optional[datetime]:
    for key in ("birth_date", "birthDate", "birth_datetime", "birthDatetime"):
        val = natal_data.get(key)
        if val:
            try:
                return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
    return None


def _extract_asc(natal_data: dict) -> float:
    for key in ("ascendant", "asc", "asc_lon", "ascLon", "ASC"):
        v = natal_data.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    for p in natal_data.get("planets", []):
        if p.get("name", "").upper() in ("ASC", "ASCENDANT"):
            try:
                return float(p.get("longitude", 0.0))
            except (TypeError, ValueError):
                pass
    return 0.0


def _extract_cusps(natal_data: dict) -> Optional[List[float]]:
    """Extract list of 12 cusp longitudes from natal_data['houses']."""
    houses = natal_data.get("houses")
    if not isinstance(houses, list) or len(houses) < 12:
        return None
    try:
        return [float(h["longitude"]) for h in sorted(houses, key=lambda h: h["num"])]
    except (KeyError, TypeError, ValueError):
        return None


def _firdaria_planet_set(fardar: dict) -> Set[str]:
    planets: Set[str] = set()
    for key in ("major", "sub"):
        val = fardar.get(key)
        if val and val not in ("N/A", ""):
            planets.add(str(val))
    return planets


# ---------------------------------------------------------------------------
# HF_angles_v6
# ---------------------------------------------------------------------------

def _compute_hf_angles_v6(
    active_title: List[str],
    planet_lons: Dict[str, float],
    lat: float,
    lon: float,
    birth_dt: datetime,
    interseccion: Set[str],
    system: str,
) -> float:
    """Compute HF_angles_v6 = Σ angularity(p) × dignity_score(p) × w(p).

    Uses houses at (lat, lon) with birth_dt to get the local ASC/MC angles.
    Non-fatal: returns 0.0 on any exception.
    """
    try:
        from core.houses_swiss import calculate_houses as _calc_houses, HOUSE_SYSTEM_PLACIDUS
        houses_result = _calc_houses(birth_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
        asc_at_loc = float(houses_result["asc"])
        mc_at_loc  = float(houses_result["mc"])
        angles_at_loc = derive_angles_from_asc_mc(asc_at_loc, mc_at_loc)
        active_pos = {p: planet_lons[p] for p in active_title if p in planet_lons}
        per_planet, _ = planet_angular_strengths(active_pos, angles_at_loc)
    except Exception:
        return 0.0

    score = 0.0
    for p_title in active_title:
        if p_title not in per_planet:
            continue
        ang = per_planet[p_title].get("mean_strength", 0.0)
        dig = calculate_dignity(p_title, planet_lons.get(p_title, 0.0), system)["dignity_score"]
        if dig == 0:
            continue  # peregrine — no contribution
        w = _FIRDARIA_W_INTERSECT if p_title in interseccion else 1.0
        score += ang * dig * w

    return float(score)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def compute_hf_v6(
    natal_data: dict,
    query_date: datetime,
    house_domain: int,
    lat: float,
    lon: float,
    system: str = "traditional",
) -> float:
    """Compute HF v6 score for a given domain and geographic coordinate.

    HF_v6 = HF_aspects(v3, subset) + β * HF_angles_v6 + γ * HF_houses(v3, subset)

    Args:
        natal_data:   Abu Engine natal JSON (planets list + houses list).
        query_date:   Date for firdaria lookup (UTC-aware recommended).
        house_domain: House number (1–12) to filter planet_subset.
        lat:          Latitude of the location to evaluate (degrees).
        lon:          Longitude of the location to evaluate (degrees).
        system:       Dignity system: 'traditional' (default) or 'modern'.

    Returns:
        float — HF v6 score. Positive = dignified angular significators.
        0.0 if subset < 2 planets or data is insufficient.
    """
    # ── 1. Planet subset for this domain ──────────────────────────────────────
    subset_lower = house_significators(natal_data, house=house_domain)
    active_title = [_LOWER_TO_TITLE[p] for p in subset_lower if p in _LOWER_TO_TITLE]

    # ── 2. Planet longitudes (natal) ───────────────────────────────────────────
    planet_lons = _extract_planet_lons(natal_data)
    active = [p for p in active_title if p in planet_lons]

    if len(active) < 2:
        return 0.0

    # ── 3. Firdaria active planets ─────────────────────────────────────────────
    firdaria_planets: Set[str] = set()
    birth_dt = _extract_birth_dt(natal_data)

    if birth_dt is not None:
        try:
            asc_lon = _extract_asc(natal_data)
            sun_lon = planet_lons.get("Sun", 0.0)
            diurnal = is_diurnal_chart(sun_lon, asc_lon)
            current_fardar = get_current_fardar(birth_dt, diurnal, query_date)
            firdaria_planets = _firdaria_planet_set(current_fardar)
        except Exception:
            pass  # non-fatal — firdaria_planets stays empty

    # ── 4. Intersección firdaria ∩ significadores_k ────────────────────────────
    # Title-case set of subset (for direct comparison with firdaria_planets)
    subset_title: Set[str] = set(active)
    interseccion: Set[str] = firdaria_planets & subset_title

    # ── 5. HF_aspects (pure geometry, v3, filtered by subset) ─────────────────
    angles_deg: Dict[str, float] = dict(planet_lons)
    pair_total = compute_hf_aspects(
        angles_deg,
        group_weights=GROUP_WEIGHTS,
        planet_subset=subset_lower,
    )

    # ── 6. HF_angles_v6 (angularity × dignity × w_intersect) ──────────────────
    ang_score = 0.0
    if birth_dt is not None:
        ang_score = _compute_hf_angles_v6(
            active, planet_lons, lat, lon, birth_dt, interseccion, system
        )

    # ── 7. HF_houses (v3, filtered by subset) ─────────────────────────────────
    cusps = _extract_cusps(natal_data)
    house_score = compute_hf_houses(
        angles_deg,
        cusps=cusps,
        planet_subset=subset_lower,
    )

    # ── 8. Final score ─────────────────────────────────────────────────────────
    return pair_total + _BETA_ANG * ang_score + _GAMMA_HOUSES * house_score
