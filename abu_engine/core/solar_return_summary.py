"""
Solar Return Summary Module

Generates a compact, narrative-friendly summary of a Solar Return chart
for integration into the derived analysis block. Extracts key symbolic elements:
ascendant sign/degree, chart ruler, house emphasis, main aspect, and a templated summary.

Author: Abu Engine
Version: 1.0
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from core.chart import solar_return_chart, normalize_lon
from core.extended_calc import get_sign_name


# Traditional rulership table (classical 7-planet system)
TRADITIONAL_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter"
}


def get_chart_ruler(asc_sign: str) -> str:
    """
    Returns the traditional ruler of a given Ascendant sign.
    
    Args:
        asc_sign: Zodiac sign name (e.g., "Sagittarius")
    
    Returns:
        Ruling planet name
    """
    return TRADITIONAL_RULERS.get(asc_sign, "Unknown")


def format_degree_position(longitude: float) -> str:
    """
    Formats a longitude as "Sign Degree°" (e.g., "Sagittarius 12°").
    
    Args:
        longitude: Ecliptic longitude (0-360)
    
    Returns:
        Formatted position string
    """
    sign = get_sign_name(longitude)
    degree_in_sign = longitude % 30
    return f"{sign} {int(degree_in_sign)}°"


def compute_house_emphasis(planets: List[Dict[str, Any]]) -> List[int]:
    """
    Identifies the two houses with the most planetary occupancy.
    
    Args:
        planets: List of planet dictionaries with 'house' key
    
    Returns:
        List of up to 2 house numbers (1-12) sorted by count, then by house number
    """
    house_counts = {}
    for planet in planets:
        house = planet.get("house")
        if house is not None and 1 <= house <= 12:
            house_counts[house] = house_counts.get(house, 0) + 1
    
    if not house_counts:
        return []
    
    # Sort by count (descending), then by house number (ascending)
    sorted_houses = sorted(house_counts.items(), key=lambda x: (-x[1], x[0]))
    return [h for h, _ in sorted_houses[:2]]


def select_main_aspect(aspects: List[Dict[str, Any]], planets_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Selects the most significant aspect involving the Sun.
    Priority: applying benefic aspects (trine/sextile/conjunction to Jupiter/Venus),
    then strongest aspect by orb.
    
    Args:
        aspects: List of aspect dictionaries with keys: a, b, type, orb
        planets_dict: Dictionary mapping planet names to their data
    
    Returns:
        String description of main aspect (e.g., "Sun trine Jupiter") or None
    """
    if not aspects:
        return None
    
    # Filter aspects involving Sun
    # Normalize keys (support both p1/p2 and a/b naming)
    norm_aspects: List[Dict[str, Any]] = []
    for asp in aspects:
        if "a" in asp and "b" in asp:
            norm_aspects.append({"p1": asp.get("a"), "p2": asp.get("b"), "type": asp.get("type"), "orb": asp.get("orb")})
        else:
            norm_aspects.append({"p1": asp.get("p1"), "p2": asp.get("p2"), "type": asp.get("type"), "orb": asp.get("orb")})

    sun_aspects = [asp for asp in norm_aspects if asp.get("p1") == "Sun" or asp.get("p2") == "Sun"]
    if not sun_aspects:
        # Fallback: pick any strongest aspect
        strongest = min(norm_aspects, key=lambda a: a.get("orb", 999))
        return strongest
    
    # Prioritize benefic aspects (trine, sextile, conjunction to Jupiter/Venus)
    benefic_planets = {"Jupiter", "Venus"}
    benefic_types = {"trine", "sextile", "conjunction"}
    
    for asp in sun_aspects:
        other_planet = asp["p2"] if asp["p1"] == "Sun" else asp["p1"]
        if other_planet in benefic_planets and asp["type"] in benefic_types:
            return asp
    
    # Fallback: strongest Sun aspect by orb
    strongest_sun = min(sun_aspects, key=lambda a: a.get("orb", 999))
    return strongest_sun


def generate_summary(ruler: str, main_aspect: Optional[Dict[str, Any]], house_emphasis: List[int], lang: str = "es") -> str:
    """
    Generates a templated summary sentence for the Solar Return.
    
    Args:
        ruler: Chart ruler planet name
        main_aspect: Main aspect description (e.g., "Sun trine Jupiter")
        house_emphasis: List of emphasized house numbers
        lang: Language code ("es", "en", "pt", "fr")
    
    Returns:
        Summary sentence
    """
    templates = {
        "es": {
            "base": "Un año bajo la guía de {ruler}.",
            "aspect": "El aspecto {aspect} marca el tono del período.",
            "houses": "Énfasis en las casas {houses}, activando temas de {themes}."
        },
        "en": {
            "base": "A year under the guidance of {ruler}.",
            "aspect": "The {aspect} aspect sets the tone for the period.",
            "houses": "Emphasis on houses {houses}, activating themes of {themes}."
        }
    }
    
    # Fallback to Spanish if language not supported
    tmpl = templates.get(lang, templates["es"])
    
    parts = [tmpl["base"].format(ruler=ruler)]
    
    if main_aspect:
        aspect_str = f"{main_aspect['p1']} {main_aspect['type']} {main_aspect['p2']}"
        parts.append(tmpl["aspect"].format(aspect=aspect_str))
    
    # Simple house theme mapping (subset for brevity)
    house_themes = {
        1: "identidad", 2: "recursos", 3: "comunicación", 4: "hogar",
        5: "creatividad", 6: "servicio", 7: "relaciones", 8: "transformación",
        9: "expansión", 10: "carrera", 11: "comunidad", 12: "trascendencia"
    }
    if house_emphasis:
        themes = ", ".join([house_themes.get(h, "desarrollo") for h in house_emphasis])
        houses_str = ", ".join(map(str, house_emphasis))
        parts.append(tmpl["houses"].format(houses=houses_str, themes=themes))
    
    return " ".join(parts)


def summarize_solar_return(
    birth_dt: datetime,
    lat: float,
    lon: float,
    year: Optional[int] = None,
    lang: str = "es"
) -> Dict[str, Any]:
    """
    Generates a compact Solar Return summary for the derived analysis block.
    
    Calls solar_return_chart() to compute the precise Solar Return moment,
    then extracts:
    - Ascendant sign and degree
    - Chart ruler (traditional rulership)
    - House emphasis (top 2 houses by planetary occupancy)
    - Main aspect (prioritizes Sun aspects with benefics)
    - Templated summary sentence
    
    Args:
        birth_dt: Natal birth datetime
        lat: Latitude for Solar Return location
        lon: Longitude for Solar Return location
        year: Target year (defaults to current year)
        lang: Language for summary text ("es", "en", "pt", "fr")
    
    Returns:
        Dictionary with keys:
        - location: {"lat": float, "lon": float}
        - datetime: ISO string of Solar Return moment
        - ascendant: Formatted position (e.g., "Sagittarius 12°")
        - ruler: Chart ruler planet name
        - house_emphasis: List of 1-2 house numbers
        - main_aspect: Description of main aspect (e.g., "Sun trine Jupiter")
        - score_summary: Aspect score summary (from solar_return_chart)
        - summary: Narrative summary sentence
    
    Raises:
        Exception: If solar_return_chart() fails
    """
    # Get full Solar Return chart
    sr_chart = solar_return_chart(birth_dt, lat, lon, year)
    
    # Extract ascendant from planets (if included) or reconstruct from houses
    # Note: solar_return_chart returns planets without houses integrated yet
    # We need to compute houses separately for ascendant
    from core.houses_swiss import calculate_houses, HOUSE_SYSTEM_PLACIDUS
    from datetime import datetime as dt
    
    sr_datetime_str = sr_chart["solar_return_datetime"]
    sr_dt = dt.fromisoformat(sr_datetime_str.replace("Z", "+00:00"))
    
    # Calculate houses for Solar Return moment
    houses_data = calculate_houses(sr_dt, lat, lon, HOUSE_SYSTEM_PLACIDUS)
    asc_lon = houses_data["asc"]
    asc_formatted = format_degree_position(asc_lon)
    asc_sign = get_sign_name(asc_lon)
    
    # Determine chart ruler
    ruler = get_chart_ruler(asc_sign)
    
    # Compute house emphasis
    # Note: sr_chart["planets"] may not have house assignments yet
    # For now, we'll use a simplified approach or skip house emphasis if unavailable
    planets = sr_chart.get("planets", [])
    house_emphasis = compute_house_emphasis(planets) if planets else []
    
    # Select main aspect
    aspects = sr_chart.get("aspects", [])
    planets_dict = {p["name"]: p for p in planets}
    main_aspect = select_main_aspect(aspects, planets_dict)
    
    # Generate summary
    summary_text = generate_summary(ruler, main_aspect, house_emphasis, lang)
    
    return {
        "location": f"{lat:.2f}, {lon:.2f}",
        "datetime": sr_chart["solar_return_datetime"],
    "ascendant": {"sign": asc_sign, "position": asc_formatted},
        "ruler": ruler,
        "house_emphasis": house_emphasis,
    "main_aspect": main_aspect,
        "score_summary": sr_chart.get("score_summary", {}),
        "summary": summary_text
    }


def is_near_birthday(birth_dt: datetime, current_dt: Optional[datetime] = None, window_days: int = 30) -> bool:
    """
    Checks if current date is within a specified window of the birthday (ignoring year).
    
    Args:
        birth_dt: Natal birth datetime
        current_dt: Current datetime (defaults to now UTC)
        window_days: Window in days around birthday (default 30)
    
    Returns:
        True if within window, False otherwise
    """
    from datetime import datetime as dt, timezone
    
    if current_dt is None:
        current_dt = dt.now(tz=timezone.utc)
    
    # Extract month/day only
    birth_month_day = (birth_dt.month, birth_dt.day)
    current_month_day = (current_dt.month, current_dt.day)
    
    # Simple heuristic: compare day-of-year distance
    from datetime import date
    birth_doy = date(2000, birth_dt.month, birth_dt.day).timetuple().tm_yday
    current_doy = date(2000, current_dt.month, current_dt.day).timetuple().tm_yday
    
    # Account for year wrap (e.g., Dec 31 to Jan 1)
    distance = abs(current_doy - birth_doy)
    if distance > 365 / 2:
        distance = 365 - distance
    
    return distance <= window_days
