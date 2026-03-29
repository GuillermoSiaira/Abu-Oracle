"""HF v5 — Dignidad esencial + Firdaria + Angularidad sobre subset de dominio.

Diseño:
    HF_v5 = Σ_pares pair_score(i, j) + β_ang * angularity_sum

    pair_score(i, j) = kernel(δθ, σ) × (dignity_i + dignity_j) × w_firdaria

Diferencias con HF v3/v4:
    - Dignidad esencial D4 modula cada par: pares dignificados amplifican,
      pares debilitados penalizan (score puede ser negativo).
    - El período de Firdaria activo amplifica pares con planetas activos (×1.5).
    - Angularidad calculada en la coordenada (lat, lon) destino, no natal.
    - planet_subset por dominio (igual que v3/v4).
    - Sistema tradicional por defecto (7 planetas clásicos, Helenístico/Persa).

Nota sobre par_score con ambos planetas peregrinos:
    d_i = 0, d_j = 0 → pair_score = 0 (par no contribuye).
    Esto es doctrinalmente correcto: un aspecto entre planetas sin dignidad
    no activa el dominio.
"""

from __future__ import annotations

import math
import itertools
from datetime import datetime
from typing import Dict, List, Set

from core.extended_calc import calculate_dignity
from core.fardars import get_current_fardar, is_diurnal_chart
from harmony.angularity import planet_angular_strengths, derive_angles_from_asc_mc
from harmony.houses import house_significators


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Aspects: (target_angle_deg, sigma_deg) — same values as resonance.py
_ASPECTS: List[tuple] = [
    (0.0,   4.0),   # conjunction
    (60.0,  4.0),   # sextile
    (90.0,  4.0),   # square
    (120.0, 4.0),   # trine
    (180.0, 4.0),   # opposition
]

# Angularity weight (inherits from v3 beta)
_BETA_ANG: float = 0.6

# Firdaria amplification factor for active planets
_FIRDARIA_AMP: float = 1.5

# Lowercase → Title-case mapping for planet names
_LOWER_TO_TITLE: Dict[str, str] = {
    "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
    "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
    "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto",
    "asc": "ASC", "mc": "MC",
}


# ---------------------------------------------------------------------------
# Core scoring function
# ---------------------------------------------------------------------------

def pair_score(
    planet_i: str,
    planet_j: str,
    lon_i: float,
    lon_j: float,
    delta_theta: float,
    aspect_sigma: float,
    firdaria_planets: Set[str],
    system: str = 'traditional',
) -> float:
    """Score a single planetary pair for one aspect.

    Args:
        planet_i, planet_j: Title-case planet names (e.g. 'Sun', 'Mars').
        lon_i, lon_j:       Ecliptic longitudes (degrees).
        delta_theta:        Deviation from the target aspect angle (degrees).
                            0 = exact aspect; increases as orb widens.
        aspect_sigma:       Gaussian sigma for this aspect (degrees).
        firdaria_planets:   Set of Title-case planet names active in current
                            firdaria period (major + sub).
        system:             'traditional' or 'modern' dignity system.

    Returns:
        float — can be negative when combined dignity score < 0.
    """
    # 1. Gaussian kernel over angular deviation
    k = math.exp(-(delta_theta ** 2) / (2.0 * aspect_sigma ** 2))

    # 2. Essential dignity D4: domicile+5 / exaltation+4 / 0 / detriment-4 / fall-5
    d_i = calculate_dignity(planet_i, lon_i, system)["dignity_score"]
    d_j = calculate_dignity(planet_j, lon_j, system)["dignity_score"]

    # 3. Firdaria amplifier
    w_t = _FIRDARIA_AMP if (planet_i in firdaria_planets or planet_j in firdaria_planets) else 1.0

    return k * (d_i + d_j) * w_t


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _angular_distance(a_deg: float, b_deg: float) -> float:
    """Smallest angular distance on the circle (0–180°)."""
    return abs((a_deg - b_deg + 180.0) % 360.0 - 180.0)


def _extract_planet_lons(natal_data: dict) -> Dict[str, float]:
    """Extract {Title-case planet name: longitude} from Abu Engine natal JSON.

    Accepts both list-of-dicts format (``natal_data["planets"]``)
    and flat dict format (``{"Sun": float, ...}``).
    """
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
        # Flat mapping: {"Sun": 120.5, "Moon": 45.3, ...}
        for key, val in natal_data.items():
            if key in _LOWER_TO_TITLE.values():
                try:
                    result[key] = float(val)
                except (TypeError, ValueError):
                    pass
    return result


def _extract_birth_dt(natal_data: dict) -> datetime | None:
    """Try multiple field names to extract a birth datetime."""
    for key in ("birth_date", "birthDate", "birth_datetime", "birthDatetime"):
        val = natal_data.get(key)
        if val:
            try:
                return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
    return None


def _extract_asc(natal_data: dict) -> float:
    """Extract natal Ascendant longitude from natal_data."""
    for key in ("ascendant", "asc", "asc_lon", "ascLon", "ASC"):
        v = natal_data.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    # Fallback: search planets list for an ASC entry
    for p in natal_data.get("planets", []):
        if p.get("name", "").upper() in ("ASC", "ASCENDANT"):
            try:
                return float(p.get("longitude", 0.0))
            except (TypeError, ValueError):
                pass
    return 0.0


def _firdaria_planet_set(fardar: dict) -> Set[str]:
    """Return Title-case set of {major, sub} active firdaria planets.

    Skips 'N/A' (historical fallback) and None values.
    """
    planets: Set[str] = set()
    for key in ("major", "sub"):
        val = fardar.get(key)
        if val and val not in ("N/A", ""):
            planets.add(str(val))
    return planets


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def compute_hf_v5(
    natal_data: dict,
    query_date: datetime,
    house_domain: int,
    lat: float,
    lon: float,
    system: str = 'traditional',
) -> float:
    """Compute HF v5 score for a given domain and geographic coordinate.

    HF_v5 = Σ_pares pair_score(i, j, asp) + β_ang * angularity_sum

    Args:
        natal_data:   Abu Engine natal JSON (chart-detailed format).
                      Requires: ``planets`` list + ``houses`` list.
        query_date:   Date for firdaria lookup (UTC-aware recommended).
        house_domain: House number (1–12) to filter planet_subset.
        lat:          Latitude of the location to evaluate (degrees).
        lon:          Longitude of the location to evaluate (degrees).
        system:       Dignity system: 'traditional' (default) or 'modern'.

    Returns:
        float — HF v5 score. Positive = dignified planets active at this
        location/period. Negative = debilitated planets dominate.
        0.0 if subset < 2 planets or data is insufficient.
    """
    # ── 1. Planet subset for this domain ──────────────────────────────────────
    subset_lower = house_significators(natal_data, house=house_domain)
    active_title = [_LOWER_TO_TITLE[p] for p in subset_lower if p in _LOWER_TO_TITLE]

    # ── 2. Planet longitudes ───────────────────────────────────────────────────
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
            pass  # non-fatal — firdaria_planets stays empty (w_t = 1.0 for all pairs)

    # ── 4. Pairwise scores over all aspects ────────────────────────────────────
    pair_total = 0.0
    for pi, pj in itertools.combinations(active, 2):
        lon_i = planet_lons[pi]
        lon_j = planet_lons[pj]
        sep = _angular_distance(lon_i, lon_j)
        for asp_angle, asp_sigma in _ASPECTS:
            deviation = abs(sep - asp_angle)
            pair_total += pair_score(
                pi, pj, lon_i, lon_j,
                deviation, asp_sigma,
                firdaria_planets, system,
            )

    # ── 5. Angularity at (lat, lon) ────────────────────────────────────────────
    # Requires birth_dt to recalculate ASC/MC at the target location.
    ang_score = 0.0
    if birth_dt is not None:
        try:
            from core.houses_swiss import calculate_houses as _calc_houses, HOUSE_SYSTEM_PLACIDUS
            _cusps, _angles = _calc_houses(birth_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
            asc_at_loc = float(_angles.get("ASC", _angles.get("asc", 0.0)))
            mc_at_loc  = float(_angles.get("MC",  _angles.get("mc",  0.0)))
            angles_at_loc = derive_angles_from_asc_mc(asc_at_loc, mc_at_loc)
            active_pos = {p: planet_lons[p] for p in active}
            _per_planet, aggregate = planet_angular_strengths(active_pos, angles_at_loc)
            ang_score = aggregate.get("angularity_sum", 0.0)
        except Exception:
            pass  # non-fatal — angularity term = 0.0

    # ── 6. Final score ─────────────────────────────────────────────────────────
    return pair_total + _BETA_ANG * ang_score
