"""
Cálculo de Lotes (Partes) - Astrología Persa/Helenística
Parte de Fortuna, Espíritu, y otros lotes secundarios.
"""

from typing import Dict, List


def is_diurnal(sun_longitude: float, asc_longitude: float) -> bool:
    """
    Determina si la carta es diurna o nocturna.
    Diurna: Sol sobre el horizonte (entre ASC y DESC pasando por MC).
    
    Args:
        sun_longitude: Longitud del Sol
        asc_longitude: Longitud del Ascendente
    
    Returns:
        bool: True si es diurna, False si es nocturna
    """
    # Calcular la posición relativa del Sol respecto al ASC
    # Si el Sol está en casas 7-12 (bajo el horizonte) es nocturna
    sun_from_asc = (sun_longitude - asc_longitude) % 360
    
    # Diurna: Sol en casas 1-6 (0° a 180° desde ASC)
    return sun_from_asc < 180


def calculate_lot_of_fortune(
    sun_long: float,
    moon_long: float,
    asc_long: float,
    diurnal: bool = None
) -> float:
    """
    Calcula la Parte de Fortuna (Pars Fortunae).
    
    Fórmula diurna: ASC + Luna - Sol
    Fórmula nocturna: ASC + Sol - Luna
    
    Args:
        sun_long: Longitud del Sol (0-360)
        moon_long: Longitud de la Luna (0-360)
        asc_long: Longitud del Ascendente (0-360)
        diurnal: Si es carta diurna. Si None, se calcula automáticamente.
    
    Returns:
        float: Longitud de la Parte de Fortuna
    """
    if diurnal is None:
        diurnal = is_diurnal(sun_long, asc_long)
    
    if diurnal:
        # Diurna: ASC + Luna - Sol
        fortune = (asc_long + moon_long - sun_long) % 360
    else:
        # Nocturna: ASC + Sol - Luna
        fortune = (asc_long + sun_long - moon_long) % 360
    
    return fortune


def calculate_lot_of_spirit(
    sun_long: float,
    moon_long: float,
    asc_long: float,
    diurnal: bool = None
) -> float:
    """
    Calcula la Parte de Espíritu (Pars Spiritus).
    
    Fórmula diurna: ASC + Sol - Luna
    Fórmula nocturna: ASC + Luna - Sol
    (Inversa a Fortuna)
    
    Returns:
        float: Longitud de la Parte de Espíritu
    """
    if diurnal is None:
        diurnal = is_diurnal(sun_long, asc_long)
    
    if diurnal:
        # Diurna: ASC + Sol - Luna
        spirit = (asc_long + sun_long - moon_long) % 360
    else:
        # Nocturna: ASC + Luna - Sol
        spirit = (asc_long + moon_long - sun_long) % 360
    
    return spirit


def calculate_lot_of_eros(
    venus_long: float,
    spirit_long: float,
    asc_long: float
) -> float:
    """
    Calcula la Parte de Eros.
    Fórmula: ASC + Venus - Espíritu
    """
    return (asc_long + venus_long - spirit_long) % 360


def calculate_lot_of_necessity(
    fortune_long: float,
    mercury_long: float,
    asc_long: float
) -> float:
    """
    Calcula la Parte de Necesidad (Némesis).
    Fórmula: ASC + Fortuna - Mercury
    """
    return (asc_long + fortune_long - mercury_long) % 360


def longitude_to_sign_degree(longitude: float) -> tuple:
    """Convierte longitud a (signo, grado)."""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    longitude = longitude % 360
    sign_index = int(longitude / 30)
    degree = longitude % 30
    return signs[sign_index], degree


def calculate_all_lots(
    planets: Dict[str, float],
    asc_long: float,
    cusps: List[float] = None
) -> List[Dict]:
    """
    Calcula todos los lotes principales.
    
    Args:
        planets: Dict {planet_name: longitude}
        asc_long: Longitud del Ascendente
        cusps: Lista de cúspides (opcional, para asignar casa)
    
    Returns:
        List[Dict]: [
            {
                "name": "Fortuna",
                "longitude": float,
                "sign": str,
                "degree": float,
                "house": int (si cusps disponibles)
            },
            ...
        ]
    """
    sun_long = planets.get("Sun", 0)
    moon_long = planets.get("Moon", 0)
    venus_long = planets.get("Venus", 0)
    mercury_long = planets.get("Mercury", 0)
    
    diurnal = is_diurnal(sun_long, asc_long)
    
    # Fortuna
    fortune_long = calculate_lot_of_fortune(sun_long, moon_long, asc_long, diurnal)
    
    # Espíritu
    spirit_long = calculate_lot_of_spirit(sun_long, moon_long, asc_long, diurnal)
    
    # Eros
    eros_long = calculate_lot_of_eros(venus_long, spirit_long, asc_long)
    
    # Necesidad
    necessity_long = calculate_lot_of_necessity(fortune_long, mercury_long, asc_long)
    
    lots = [
        {"name": "Fortuna", "longitude": fortune_long},
        {"name": "Spirit", "longitude": spirit_long},
        {"name": "Eros", "longitude": eros_long},
        {"name": "Necessity", "longitude": necessity_long},
    ]
    
    # Agregar signo, grado y casa
    from .houses_swiss import get_planet_house
    
    result = []
    for lot in lots:
        sign, degree = longitude_to_sign_degree(lot["longitude"])
        lot_data = {
            "name": lot["name"],
            "longitude": lot["longitude"],
            "sign": sign,
            "degree": round(degree, 1)
        }
        
        if cusps:
            lot_data["house"] = get_planet_house(lot["longitude"], cusps)
        
        result.append(lot_data)
    
    return result
