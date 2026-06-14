# -*- coding: utf-8 -*-
"""
Extended astrological calculations: dignities, Arabic parts, detailed positions

BUG-01 FIX (2026-03-23):
  Two parallel dignity systems implemented as separate layers per doctrinal decision:
  · Traditional (Hellenistic/Persian, 7 classical planets) — default, used by Lilly
  · Modern (20th-century outer-planet rulerships) — kept for dual display

Decisions applied:
  D1 — Two systems as separate layers, no synthesis.
  D2 — Uranus/Neptune/Pluto: no exaltation/fall in any system.
       Always peregrine (score 0) in traditional.
  D3 — Three dignity fields: dignity (= traditional, backward compat),
       dignity_traditional, dignity_modern.
  D4 — Scoring: domicile +5 / exaltation +4 / peregrine 0 / detriment −4 / fall −5.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Zodiac sign boundaries (0-based index)
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Transpersonal planets: no dignity in traditional system (D2)
_TRANSPERSONAL = {"Uranus", "Neptune", "Pluto"}

# ─── Traditional tables — Hellenistic/Persian, 7 classical planets ────────────

RULERSHIPS_TRADITIONAL = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",        # Traditional: Mars (not Pluto)
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",     # Traditional: Saturn (not Uranus)
    "Pisces": "Jupiter",      # Traditional: Jupiter (not Neptune)
}

# Detriments: planet ruling the opposite sign (derived from RULERSHIPS_TRADITIONAL)
DETRIMENTS_TRADITIONAL = {
    "Aries": "Venus",         # Venus rules Libra (opposite)
    "Taurus": "Mars",         # Mars rules Scorpio (opposite) — was Pluto in modern
    "Gemini": "Jupiter",      # Jupiter rules Sagittarius (opposite)
    "Cancer": "Saturn",       # Saturn rules Capricorn (opposite)
    "Leo": "Saturn",          # Saturn rules Aquarius (opposite) — was Uranus in modern
    "Virgo": "Jupiter",       # Jupiter rules Pisces (opposite) — was Neptune in modern
    "Libra": "Mars",          # Mars rules Aries (opposite)
    "Scorpio": "Venus",       # Venus rules Taurus (opposite)
    "Sagittarius": "Mercury", # Mercury rules Gemini (opposite)
    "Capricorn": "Moon",      # Moon rules Cancer (opposite)
    "Aquarius": "Sun",        # Sun rules Leo (opposite)
    "Pisces": "Mercury",      # Mercury rules Virgo (opposite)
}

# Exaltations: 7 classical planets only (D2)
# Uranus/Neptune/Pluto: no entry — peregrine by default
EXALTATIONS_TRADITIONAL = {
    "Sun":     ("Aries",      19),
    "Moon":    ("Taurus",      3),
    "Mercury": ("Virgo",      15),
    "Venus":   ("Pisces",     27),
    "Mars":    ("Capricorn",  28),
    "Jupiter": ("Cancer",     15),
    "Saturn":  ("Libra",      21),
}

# Falls: opposite sign and degree of exaltation (7 classical planets only, D2)
FALLS_TRADITIONAL = {
    "Sun":     ("Libra",      19),
    "Moon":    ("Scorpio",     3),
    "Mercury": ("Pisces",     15),
    "Venus":   ("Virgo",      27),
    "Mars":    ("Cancer",     28),
    "Jupiter": ("Capricorn",  15),
    "Saturn":  ("Aries",      21),
}

# ─── Modern tables — 20th-century outer-planet rulerships ────────────────────

RULERSHIPS_MODERN = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Pluto",       # Modern: Pluto
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Uranus",     # Modern: Uranus
    "Pisces": "Neptune",      # Modern: Neptune
}

# Exaltations: 10 planets including transpersonals (modern additions)
EXALTATIONS_MODERN = {
    "Sun":     ("Aries",      19),
    "Moon":    ("Taurus",      3),
    "Mercury": ("Virgo",      15),
    "Venus":   ("Pisces",     27),
    "Mars":    ("Capricorn",  28),
    "Jupiter": ("Cancer",     15),
    "Saturn":  ("Libra",      21),
    "Uranus":  ("Scorpio",     0),  # Modern
    "Neptune": ("Cancer",      0),  # Modern
    "Pluto":   ("Leo",         0),  # Modern
}

# Falls: opposite sign/degree of EXALTATIONS_MODERN
FALLS_MODERN = {
    "Sun":     ("Libra",      19),
    "Moon":    ("Scorpio",     3),
    "Mercury": ("Pisces",     15),
    "Venus":   ("Virgo",      27),
    "Mars":    ("Cancer",     28),
    "Jupiter": ("Capricorn",  15),
    "Saturn":  ("Aries",      21),
    "Uranus":  ("Taurus",      0),  # Modern
    "Neptune": ("Capricorn",   0),  # Modern
    "Pluto":   ("Aquarius",    0),  # Modern
}

# Detriments: derived from RULERSHIPS_MODERN
DETRIMENTS_MODERN = {
    "Aries": "Venus",
    "Taurus": "Pluto",        # Pluto rules Scorpio (opposite)
    "Gemini": "Jupiter",
    "Cancer": "Saturn",
    "Leo": "Uranus",          # Uranus rules Aquarius (opposite)
    "Virgo": "Neptune",       # Neptune rules Pisces (opposite)
    "Libra": "Mars",
    "Scorpio": "Venus",
    "Sagittarius": "Mercury",
    "Capricorn": "Moon",
    "Aquarius": "Sun",
    "Pisces": "Mercury",
}

# ─── Backward-compat aliases (external code that imports RULERSHIPS etc.) ─────
RULERSHIPS  = RULERSHIPS_MODERN
EXALTATIONS = EXALTATIONS_MODERN
FALLS       = FALLS_MODERN
DETRIMENTS  = DETRIMENTS_MODERN


# ─── Utility functions ────────────────────────────────────────────────────────

def normalize_lon(lon: float) -> float:
    """Normalize longitude to 0-360 range"""
    return lon % 360.0


def get_sign_index(lon: float) -> int:
    """Get 0-based sign index from ecliptic longitude"""
    return int(normalize_lon(lon) // 30)


def get_sign_name(lon: float) -> str:
    """Get sign name from ecliptic longitude"""
    return SIGNS[get_sign_index(lon)]


def get_degree_in_sign(lon: float) -> float:
    """Get degree within sign (0-30)"""
    return normalize_lon(lon) % 30


def format_position(lon: float) -> str:
    """Format position as traditional notation: 15°32' Aries"""
    sign = get_sign_name(lon)
    deg_in_sign = get_degree_in_sign(lon)
    degrees = int(deg_in_sign)
    minutes = int((deg_in_sign - degrees) * 60)
    return f"{degrees}°{minutes:02d}' {sign}"


# ─── Dignity calculation ──────────────────────────────────────────────────────

def calculate_dignity(planet_name: str, lon: float, system: str = 'traditional') -> Dict[str, any]:
    """
    Calculate essential dignity for a planet.

    Args:
        planet_name: Planet name (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn,
                     Uranus, Neptune, Pluto)
        lon: Ecliptic longitude (0-360)
        system: 'traditional' (default) — Hellenistic/Persian 7-planet doctrine.
                'modern' — 20th-century outer-planet rulerships.

    Returns:
        Dict with new canonical fields plus backward-compat boolean fields:
          dignity        (str)  — canonical: 'domicile'|'exaltation'|'detriment'|'fall'|'peregrine'
          dignity_score  (int)  — D4 scoring: domicile+5/exaltation+4/peregrine 0/detriment-4/fall-5
          domicile       (bool) — backward compat
          exaltation     (bool) — backward compat
          detriment      (bool) — backward compat
          fall           (bool) — backward compat
          peregrine      (bool) — backward compat
          score          (int)  — backward compat alias for dignity_score
    """
    # D2: transpersonal planets always peregrine in traditional
    if system == 'traditional' and planet_name in _TRANSPERSONAL:
        return {
            "dignity": "peregrine",
            "dignity_score": 0,
            "domicile": False, "exaltation": False,
            "detriment": False, "fall": False,
            "peregrine": True, "score": 0,
        }

    rulerships = RULERSHIPS_TRADITIONAL if system == 'traditional' else RULERSHIPS_MODERN
    detriments = DETRIMENTS_TRADITIONAL if system == 'traditional' else DETRIMENTS_MODERN
    exaltations = EXALTATIONS_TRADITIONAL if system == 'traditional' else EXALTATIONS_MODERN
    falls       = FALLS_TRADITIONAL       if system == 'traditional' else FALLS_MODERN

    sign        = get_sign_name(lon)

    # Domicile
    domicile = (rulerships.get(sign) == planet_name)

    # Exaltation
    exaltation = False
    if planet_name in exaltations:
        exalt_sign, _ = exaltations[planet_name]
        if sign == exalt_sign:
            exaltation = True

    # Detriment
    detriment = (detriments.get(sign) == planet_name)

    # Fall
    fall = False
    if planet_name in falls:
        fall_sign, _ = falls[planet_name]
        if sign == fall_sign:
            fall = True

    # D4 scoring: domicile+5, exaltation+4, peregrine 0, detriment-4, fall-5
    score = 0
    if domicile:
        score += 5
    if exaltation:
        score += 4
    if detriment:
        score -= 4
    if fall:
        score -= 5

    # Canonical dignity string — highest dignity wins
    if domicile:
        dignity_str = "domicile"
    elif exaltation:
        dignity_str = "exaltation"
    elif detriment:
        dignity_str = "detriment"
    elif fall:
        dignity_str = "fall"
    else:
        dignity_str = "peregrine"

    return {
        "dignity":       dignity_str,
        "dignity_score": score,
        "domicile":      domicile,
        "exaltation":    exaltation,
        "detriment":     detriment,
        "fall":          fall,
        "peregrine":     not (domicile or exaltation or detriment or fall),
        "score":         score,   # backward compat alias
    }


def calculate_dignity_dual(planet_name: str, lon: float) -> Dict[str, Dict]:
    """
    Calculate essential dignity under both systems.

    Returns:
        {
          'traditional': { dignity, dignity_score, domicile, exaltation, ... },
          'modern':      { dignity, dignity_score, domicile, exaltation, ... }
        }
    """
    return {
        "traditional": calculate_dignity(planet_name, lon, system='traditional'),
        "modern":      calculate_dignity(planet_name, lon, system='modern'),
    }


# ─── Arabic parts ─────────────────────────────────────────────────────────────

def calculate_part_of_fortune(sun_lon: float, moon_lon: float, asc_lon: float, is_day_chart: bool = True) -> float:
    """
    Calculate Part of Fortune (Pars Fortunae).

    Day chart: Asc + Moon - Sun
    Night chart: Asc + Sun - Moon
    """
    if is_day_chart:
        pof = asc_lon + moon_lon - sun_lon
    else:
        pof = asc_lon + sun_lon - moon_lon
    return normalize_lon(pof)


# ─── Lunar nodes (approximate) ────────────────────────────────────────────────

def get_lunar_nodes(date: datetime) -> Tuple[float, float]:
    """
    Calculate approximate True Lunar Node positions (North and South).
    For production accuracy, use Swiss Ephemeris directly.
    """
    from datetime import datetime as dt, timezone

    reference_date = dt(1900, 1, 1, tzinfo=timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    days_diff  = (date - reference_date).days
    years_diff = days_diff / 365.25

    mean_node  = -19.3356 * years_diff
    north_node = normalize_lon(mean_node)
    south_node = normalize_lon(north_node + 180)
    return north_node, south_node


# ─── Detailed positions ───────────────────────────────────────────────────────

def calculate_detailed_positions(planets: Dict[str, float], houses: Optional[List[float]] = None) -> List[Dict]:
    """
    Generate detailed position table with degrees, minutes, sign, house,
    and dual-system dignity fields.

    Args:
        planets: Dict of planet_name -> ecliptic_longitude
        houses:  Optional list of 12 house cusp longitudes

    Returns:
        List of dicts per planet.  Dignity fields per planet (D3):
          dignity             — traditional dignity string (backward compat)
          dignity_score       — traditional dignity score  (backward compat)
          dignity_traditional — traditional dignity string (explicit)
          dignity_modern      — modern dignity string      (explicit)
    """
    detailed = []

    for name, lon in planets.items():
        dual = calculate_dignity_dual(name, lon)

        pos_info = {
            "name":               name,
            "longitude":          round(lon, 4),
            "sign":               get_sign_name(lon),
            "degree_in_sign":     round(get_degree_in_sign(lon), 2),
            "formatted":          format_position(lon),
            # Full traditional dignity dict — backward compat (callers read .score, .domicile, etc.)
            "dignity":            dual["traditional"],
            # Convenience flat fields (D3)
            "dignity_score":      dual["traditional"]["dignity_score"],
            "dignity_traditional": dual["traditional"]["dignity"],
            "dignity_modern":     dual["modern"]["dignity"],
        }

        if houses:
            pos_info["house"] = find_house(lon, houses)

        detailed.append(pos_info)

    return detailed


# ─── House placement ──────────────────────────────────────────────────────────

def find_house(lon: float, cusps: List[float]) -> int:
    """
    Find which house a planet occupies based on cusp longitudes.

    Args:
        lon:   Planet ecliptic longitude
        cusps: List of 12 house cusp longitudes (starting with ASC / 1st house)

    Returns:
        House number (1-12)
    """
    if len(cusps) != 12:
        return 0

    lon_norm = normalize_lon(lon)

    for i in range(12):
        cusp_start = normalize_lon(cusps[i])
        cusp_end   = normalize_lon(cusps[(i + 1) % 12])

        if cusp_start < cusp_end:
            if cusp_start <= lon_norm < cusp_end:
                return i + 1
        else:  # wrap-around at 0°/360°
            if lon_norm >= cusp_start or lon_norm < cusp_end:
                return i + 1

    return 1  # fallback
