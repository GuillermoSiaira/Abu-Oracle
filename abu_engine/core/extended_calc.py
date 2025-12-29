# -*- coding: utf-8 -*-
"""
Extended astrological calculations: dignities, Arabic parts, detailed positions
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Zodiac sign boundaries (0-based index)
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Rulerships (domicile)
RULERSHIPS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Pluto",  # Modern: Pluto, Traditional: Mars
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Uranus",  # Modern: Uranus, Traditional: Saturn
    "Pisces": "Neptune"  # Modern: Neptune, Traditional: Jupiter
}

# Exaltations
EXALTATIONS = {
    "Sun": ("Aries", 19),
    "Moon": ("Taurus", 3),
    "Mercury": ("Virgo", 15),
    "Venus": ("Pisces", 27),
    "Mars": ("Capricorn", 28),
    "Jupiter": ("Cancer", 15),
    "Saturn": ("Libra", 21),
    "Uranus": ("Scorpio", 0),  # Modern
    "Neptune": ("Cancer", 0),  # Modern
    "Pluto": ("Leo", 0)  # Modern
}

# Falls (opposite of exaltation)
FALLS = {
    "Sun": ("Libra", 19),
    "Moon": ("Scorpio", 3),
    "Mercury": ("Pisces", 15),
    "Venus": ("Virgo", 27),
    "Mars": ("Cancer", 28),
    "Jupiter": ("Capricorn", 15),
    "Saturn": ("Aries", 21),
    "Uranus": ("Taurus", 0),
    "Neptune": ("Capricorn", 0),
    "Pluto": ("Aquarius", 0)
}

# Detriments (opposite of rulership)
DETRIMENTS = {
    "Aries": "Venus",
    "Taurus": "Pluto",
    "Gemini": "Jupiter",
    "Cancer": "Saturn",
    "Leo": "Uranus",
    "Virgo": "Neptune",
    "Libra": "Mars",
    "Scorpio": "Venus",
    "Sagittarius": "Mercury",
    "Capricorn": "Moon",
    "Aquarius": "Sun",
    "Pisces": "Mercury"
}


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
    """
    Format position as traditional notation: 15°32' Aries
    """
    sign = get_sign_name(lon)
    deg_in_sign = get_degree_in_sign(lon)
    degrees = int(deg_in_sign)
    minutes = int((deg_in_sign - degrees) * 60)
    return f"{degrees}°{minutes:02d}' {sign}"


def calculate_dignity(planet_name: str, lon: float) -> Dict[str, any]:
    """
    Calculate essential dignity for a planet.
    
    Returns:
        Dict with dignity status: domicile, exaltation, detriment, fall, peregrine
    """
    sign = get_sign_name(lon)
    deg_in_sign = get_degree_in_sign(lon)
    
    dignity = {
        "domicile": False,
        "exaltation": False,
        "detriment": False,
        "fall": False,
        "peregrine": False,
        "score": 0  # Traditional scoring: +5 domicile, +4 exalt, -5 detri, -4 fall
    }
    
    # Check domicile (rulership)
    if RULERSHIPS.get(sign) == planet_name:
        dignity["domicile"] = True
        dignity["score"] += 5
    
    # Check exaltation
    if planet_name in EXALTATIONS:
        exalt_sign, exalt_degree = EXALTATIONS[planet_name]
        if sign == exalt_sign:
            # Within 5° of exact exaltation degree
            if abs(deg_in_sign - exalt_degree) <= 5 or abs(deg_in_sign - exalt_degree) >= 25:
                dignity["exaltation"] = True
                dignity["score"] += 4
    
    # Check detriment
    if DETRIMENTS.get(sign) == planet_name:
        dignity["detriment"] = True
        dignity["score"] -= 5
    
    # Check fall
    if planet_name in FALLS:
        fall_sign, fall_degree = FALLS[planet_name]
        if sign == fall_sign:
            if abs(deg_in_sign - fall_degree) <= 5 or abs(deg_in_sign - fall_degree) >= 25:
                dignity["fall"] = True
                dignity["score"] -= 4
    
    # Peregrine: no major dignity
    if dignity["score"] == 0:
        dignity["peregrine"] = True
    
    return dignity


def calculate_part_of_fortune(sun_lon: float, moon_lon: float, asc_lon: float, is_day_chart: bool = True) -> float:
    """
    Calculate Part of Fortune (Pars Fortunae).
    
    Day chart: Asc + Moon - Sun
    Night chart: Asc + Sun - Moon
    
    Args:
        sun_lon: Sun ecliptic longitude
        moon_lon: Moon ecliptic longitude
        asc_lon: Ascendant longitude
        is_day_chart: True if Sun above horizon
    
    Returns:
        Ecliptic longitude of Part of Fortune
    """
    if is_day_chart:
        pof = asc_lon + moon_lon - sun_lon
    else:
        pof = asc_lon + sun_lon - moon_lon
    
    return normalize_lon(pof)


def get_lunar_nodes(date: datetime) -> Tuple[float, float]:
    """
    Calculate True Lunar Node positions (North and South).
    
    This is a simplified approximation. For production, use swiss ephemeris.
    
    Args:
        date: datetime to calculate for
    
    Returns:
        Tuple of (north_node_lon, south_node_lon)
    """
    # Simplified calculation based on mean node
    # Mean node regresses ~19.3° per year
    # Node was at 0° Aries on 1900-01-01 (approximate)
    
    from datetime import datetime as dt, timezone
    
    reference_date = dt(1900, 1, 1, tzinfo=timezone.utc)
    
    # Ensure date is timezone-aware
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    days_diff = (date - reference_date).days
    years_diff = days_diff / 365.25
    
    # Mean node longitude (regresses)
    mean_node = -19.3356 * years_diff
    north_node = normalize_lon(mean_node)
    south_node = normalize_lon(north_node + 180)
    
    return north_node, south_node


def calculate_detailed_positions(planets: Dict[str, float], houses: Optional[List[float]] = None) -> List[Dict]:
    """
    Generate detailed position table with degrees, minutes, sign, house, dignity.
    
    Args:
        planets: Dict of planet_name -> ecliptic_longitude
        houses: Optional list of house cusp longitudes (12 cusps)
    
    Returns:
        List of dicts with detailed planet info
    """
    detailed = []
    
    for name, lon in planets.items():
        pos_info = {
            "name": name,
            "longitude": round(lon, 4),
            "sign": get_sign_name(lon),
            "degree_in_sign": round(get_degree_in_sign(lon), 2),
            "formatted": format_position(lon),
            "dignity": calculate_dignity(name, lon)
        }
        
        # Assign house if cusps provided
        if houses:
            house_num = find_house(lon, houses)
            pos_info["house"] = house_num
        
        detailed.append(pos_info)
    
    return detailed


def find_house(lon: float, cusps: List[float]) -> int:
    """
    Find which house a planet is in based on cusp longitudes.
    
    Args:
        lon: Planet ecliptic longitude
        cusps: List of 12 house cusp longitudes (starting with ASC/1st house)
    
    Returns:
        House number (1-12)
    """
    if len(cusps) != 12:
        return 0  # Unable to determine
    
    lon_norm = normalize_lon(lon)
    
    for i in range(12):
        cusp_start = normalize_lon(cusps[i])
        cusp_end = normalize_lon(cusps[(i + 1) % 12])
        
        # Handle wrap-around at 0°
        if cusp_start < cusp_end:
            if cusp_start <= lon_norm < cusp_end:
                return i + 1
        else:  # Wraps around 360°/0°
            if lon_norm >= cusp_start or lon_norm < cusp_end:
                return i + 1
    
    return 1  # Default to 1st house if calculation fails
