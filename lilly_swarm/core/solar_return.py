"""
Solar Return interpretation module for Lilly Engine.
Analyzes solar return charts and suggests favorable relocation options.
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class Element(str, Enum):
    """Astrological elements."""
    FIRE = "fire"
    EARTH = "earth"
    AIR = "air"
    WATER = "water"


class Mode(str, Enum):
    """Astrological modes/qualities."""
    CARDINAL = "cardinal"
    FIXED = "fixed"
    MUTABLE = "mutable"


# Sign characteristics
SIGN_ATTRIBUTES = {
    "Aries": {"element": Element.FIRE, "mode": Mode.CARDINAL},
    "Taurus": {"element": Element.EARTH, "mode": Mode.FIXED},
    "Gemini": {"element": Element.AIR, "mode": Mode.MUTABLE},
    "Cancer": {"element": Element.WATER, "mode": Mode.CARDINAL},
    "Leo": {"element": Element.FIRE, "mode": Mode.FIXED},
    "Virgo": {"element": Element.EARTH, "mode": Mode.MUTABLE},
    "Libra": {"element": Element.AIR, "mode": Mode.CARDINAL},
    "Scorpio": {"element": Element.WATER, "mode": Mode.FIXED},
    "Sagittarius": {"element": Element.FIRE, "mode": Mode.MUTABLE},
    "Capricorn": {"element": Element.EARTH, "mode": Mode.CARDINAL},
    "Aquarius": {"element": Element.AIR, "mode": Mode.FIXED},
    "Pisces": {"element": Element.WATER, "mode": Mode.MUTABLE},
}

# City coordinates with dominant Ascendant tendencies
# Format: (lat, lon, typical_asc_element)
RELOCATION_CITIES = {
    # Fire cities (energetic, entrepreneurial)
    "Dubai": {"lat": 25.2048, "lon": 55.2708, "element": Element.FIRE, "region": "Middle East"},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437, "element": Element.FIRE, "region": "North America"},
    "Barcelona": {"lat": 41.3851, "lon": 2.1734, "element": Element.FIRE, "region": "Europe"},
    "Sydney": {"lat": -33.8688, "lon": 151.2093, "element": Element.FIRE, "region": "Oceania"},
    
    # Earth cities (stable, practical)
    "Zurich": {"lat": 47.3769, "lon": 8.5417, "element": Element.EARTH, "region": "Europe"},
    "Singapore": {"lat": 1.3521, "lon": 103.8198, "element": Element.EARTH, "region": "Asia"},
    "Toronto": {"lat": 43.6532, "lon": -79.3832, "element": Element.EARTH, "region": "North America"},
    "Copenhagen": {"lat": 55.6761, "lon": 12.5683, "element": Element.EARTH, "region": "Europe"},
    
    # Air cities (intellectual, communicative)
    "London": {"lat": 51.5074, "lon": -0.1278, "element": Element.AIR, "region": "Europe"},
    "Amsterdam": {"lat": 52.3676, "lon": 4.9041, "element": Element.AIR, "region": "Europe"},
    "San Francisco": {"lat": 37.7749, "lon": -122.4194, "element": Element.AIR, "region": "North America"},
    "Berlin": {"lat": 52.5200, "lon": 13.4050, "element": Element.AIR, "region": "Europe"},
    
    # Water cities (emotional, creative)
    "Venice": {"lat": 45.4408, "lon": 12.3155, "element": Element.WATER, "region": "Europe"},
    "Rio de Janeiro": {"lat": -22.9068, "lon": -43.1729, "element": Element.WATER, "region": "South America"},
    "Lisbon": {"lat": 38.7223, "lon": -9.1393, "element": Element.WATER, "region": "Europe"},
    "Buenos Aires": {"lat": -34.6037, "lon": -58.3816, "element": Element.WATER, "region": "South America"},
}


def get_sign_element(sign: str) -> Optional[Element]:
    """Get the element for a zodiac sign."""
    attrs = SIGN_ATTRIBUTES.get(sign)
    return attrs["element"] if attrs else None


def get_sign_mode(sign: str) -> Optional[Mode]:
    """Get the mode for a zodiac sign."""
    attrs = SIGN_ATTRIBUTES.get(sign)
    return attrs["mode"] if attrs else None


def calculate_asc_from_coordinates(lat: float, lon: float, sun_sign: str) -> str:
    """
    Simplified heuristic to estimate Ascendant shift based on latitude.
    In reality, this requires full chart calculation.
    
    This is a placeholder - actual implementation would need Skyfield.
    """
    # Simple heuristic: latitude affects house cusps
    # This is highly simplified for demonstration
    signs = list(SIGN_ATTRIBUTES.keys())
    sun_idx = signs.index(sun_sign) if sun_sign in signs else 0
    
    # Approximate shift based on latitude (very rough)
    lat_shift = int(lat / 15) % 12
    new_idx = (sun_idx + lat_shift) % 12
    
    return signs[new_idx]


def find_favorable_locations(
    natal_asc_sign: str,
    current_element: Element,
    desired_element: Optional[Element] = None,
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """
    Find cities where the solar return Ascendant would be in a favorable element.
    
    Args:
        natal_asc_sign: Natal ascendant sign
        current_element: Current solar return ascendant element
        desired_element: Target element (if None, finds complementary)
        max_results: Maximum number of city suggestions
    
    Returns:
        List of city recommendations with reasoning
    """
    # Element compatibility (simplified)
    ELEMENT_COMPATIBILITY = {
        Element.FIRE: [Element.AIR, Element.FIRE],  # Fire feeds on air
        Element.EARTH: [Element.WATER, Element.EARTH],  # Water nourishes earth
        Element.AIR: [Element.FIRE, Element.AIR],  # Air spreads fire
        Element.WATER: [Element.EARTH, Element.WATER],  # Earth contains water
    }
    
    # If no desired element specified, use compatibility
    if desired_element is None:
        favorable_elements = ELEMENT_COMPATIBILITY.get(current_element, [current_element])
    else:
        favorable_elements = [desired_element]
    
    # Find cities with favorable elements
    recommendations = []
    for city, info in RELOCATION_CITIES.items():
        if info["element"] in favorable_elements:
            recommendations.append({
                "city": city,
                "coordinates": {"lat": info["lat"], "lon": info["lon"]},
                "element": info["element"].value,
                "region": info["region"],
                "compatibility": "high" if info["element"] == favorable_elements[0] else "moderate"
            })
    
    # Sort by compatibility and limit results
    recommendations.sort(key=lambda x: (x["compatibility"] == "high"), reverse=True)
    return recommendations[:max_results]


def interpret_solar_return(
    natal_chart: Dict[str, Any],
    solar_chart: Dict[str, Any],
    language: str = "es"
) -> Dict[str, Any]:
    """
    Interprets a Solar Return chart by comparing with natal chart.
    Suggests favorable relocation options based on Ascendant analysis.
    
    Args:
        natal_chart: Natal chart data (must include planets with signs)
        solar_chart: Solar return chart data
        language: Response language (es, en, pt, fr)
    
    Returns:
        Dictionary with best_locations, reasoning, and astro_metadata
    """
    # Extract natal and solar Ascendants (from Sun sign as approximation if ASC not available)
    natal_sun = next((p for p in natal_chart.get("planets", []) if p["name"] == "Sun"), None)
    solar_sun = next((p for p in solar_chart.get("planets", []) if p["name"] == "Sun"), None)
    
    if not natal_sun or not solar_sun:
        return {
            "best_locations": [],
            "reasoning": "Insufficient chart data to analyze",
            "astro_metadata": {
                "source": "heuristic",
                "model": None,
                "language": language
            }
        }
    
    natal_asc_sign = natal_sun["sign"]  # Simplified - would need actual ASC
    solar_asc_sign = solar_sun["sign"]
    
    # Get elements
    natal_element = get_sign_element(natal_asc_sign)
    solar_element = get_sign_element(solar_asc_sign)
    
    # Find favorable locations
    locations = find_favorable_locations(
        natal_asc_sign=natal_asc_sign,
        current_element=solar_element or natal_element,
        max_results=3
    )
    
    # Build reasoning based on language
    reasoning_templates = {
        "es": f"""El Ascendente natal en {natal_asc_sign} ({natal_element.value if natal_element else 'N/A'}) 
        se combina con el Ascendente del Retorno Solar en {solar_asc_sign} ({solar_element.value if solar_element else 'N/A'}).
        
        Las siguientes ubicaciones ofrecen Ascendentes más favorables para este año:
        {', '.join([loc['city'] for loc in locations[:3]])}.
        
        Estas ciudades enfatizan elementos compatibles que apoyan el crecimiento y la evolución personal.""",
        
        "en": f"""The natal Ascendant in {natal_asc_sign} ({natal_element.value if natal_element else 'N/A'})
        combines with the Solar Return Ascendant in {solar_asc_sign} ({solar_element.value if solar_element else 'N/A'}).
        
        The following locations offer more favorable Ascendants for this year:
        {', '.join([loc['city'] for loc in locations[:3]])}.
        
        These cities emphasize compatible elements that support growth and personal evolution.""",
        
        "pt": f"""O Ascendente natal em {natal_asc_sign} ({natal_element.value if natal_element else 'N/A'})
        combina-se com o Ascendente do Retorno Solar em {solar_asc_sign} ({solar_element.value if solar_element else 'N/A'}).
        
        As seguintes localizações oferecem Ascendentes mais favoráveis para este ano:
        {', '.join([loc['city'] for loc in locations[:3]])}.
        
        Estas cidades enfatizam elementos compatíveis que apoiam o crescimento e a evolução pessoal.""",
        
        "fr": f"""L'Ascendant natal en {natal_asc_sign} ({natal_element.value if natal_element else 'N/A'})
        se combine avec l'Ascendant du Retour Solaire en {solar_asc_sign} ({solar_element.value if solar_element else 'N/A'}).
        
        Les emplacements suivants offrent des Ascendants plus favorables pour cette année:
        {', '.join([loc['city'] for loc in locations[:3]])}.
        
        Ces villes mettent l'accent sur des éléments compatibles qui soutiennent la croissance et l'évolution personnelle."""
    }
    
    reasoning = reasoning_templates.get(language, reasoning_templates["es"])
    
    return {
        "best_locations": [loc["city"] for loc in locations],
        "location_details": locations,
        "reasoning": reasoning.strip(),
        "natal_ascendant": {
            "sign": natal_asc_sign,
            "element": natal_element.value if natal_element else None
        },
        "solar_ascendant": {
            "sign": solar_asc_sign,
            "element": solar_element.value if solar_element else None
        },
        "astro_metadata": {
            "source": "heuristic",
            "model": None,
            "language": language,
            "cities_analyzed": len(RELOCATION_CITIES)
        }
    }
