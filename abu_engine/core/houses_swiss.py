"""
Sistema de Casas con pyswisseph
Cálculo de Ascendente, MC y cúspides de casas usando el sistema Placidus.
"""

try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:
    SWE_AVAILABLE = False

from datetime import datetime
from typing import Dict, List, Tuple, Optional


# Constantes de pyswisseph para sistemas de casas
HOUSE_SYSTEM_PLACIDUS = b'P'
HOUSE_SYSTEM_KOCH = b'K'
HOUSE_SYSTEM_EQUAL = b'E'
HOUSE_SYSTEM_WHOLE_SIGN = b'W'


def init_swisseph(ephemeris_path: str = None):
    """Inicializa pyswisseph con la ruta a los archivos de efemérides."""
    if not SWE_AVAILABLE:
        raise ImportError("pyswisseph no está instalado. Instálalo con: pip install pyswisseph")
    
    if ephemeris_path:
        swe.set_ephe_path(ephemeris_path)


def calculate_houses(
    dt: datetime,
    lat: float,
    lon: float,
    house_system: bytes = HOUSE_SYSTEM_PLACIDUS
) -> Dict:
    """
    Calcula las cúspides de las casas y los ángulos (ASC, MC, etc.).
    
    Args:
        dt: Fecha y hora (UTC)
        lat: Latitud en grados decimales
        lon: Longitud en grados decimales
        house_system: Sistema de casas (default: Placidus)
    
    Returns:
        dict: {
            "asc": float (longitud del Ascendente),
            "mc": float (longitud del MC),
            "armc": float (ARMC),
            "vertex": float,
            "equatorial_asc": float,
            "co_asc_koch": float,
            "cusps": [float] * 12 (cúspides casas 1-12)
        }
    """
    if not SWE_AVAILABLE:
        raise ImportError("pyswisseph no está instalado")
    
    # Convertir datetime a Julian Day
    jd = swe.julday(dt.year, dt.month, dt.day, 
                    dt.hour + dt.minute / 60.0 + dt.second / 3600.0)
    
    # Calcular casas
    # swe.houses devuelve (cusps, ascmc)
    # cusps[0] está vacío, cusps[1-12] son las cúspides
    # ascmc[0] = ASC, ascmc[1] = MC, ascmc[2] = ARMC, etc.
    cusps, ascmc = swe.houses(jd, lat, lon, house_system)

    # Normalize cusp list to exactly 12 floats in [0,360)
    cusps_list = list(cusps[1:13]) if len(cusps) >= 13 else list(cusps)
    cusps_list = [float(c) % 360.0 for c in cusps_list if c is not None]
    if len(cusps_list) > 12:
        cusps_list = cusps_list[:12]
    
    return {
        "asc": ascmc[0],  # Ascendente
        "mc": ascmc[1],   # Medio Cielo
        "armc": ascmc[2], # ARMC
        "vertex": ascmc[3],
        "equatorial_asc": ascmc[4],
        "co_asc_koch": ascmc[5],
        "cusps": cusps_list  # Cúspides 1-12
    }


def longitude_to_sign_degree(longitude: float) -> Tuple[str, float]:
    """
    Convierte longitud eclíptica (0-360) a signo y grado.
    
    Returns:
        (sign_name, degree_in_sign)
    """
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    # Normalizar a 0-360
    longitude = longitude % 360
    
    sign_index = int(longitude / 30)
    degree = longitude % 30
    
    return signs[sign_index], degree


def get_planet_house(planet_longitude: float, cusps: List[float]) -> int:
    """
    Determina en qué casa está un planeta según su longitud y las cúspides.
    
    Args:
        planet_longitude: Longitud del planeta (0-360)
        cusps: Lista de 12 cúspides de casas
    
    Returns:
        int: Número de casa (1-12)
    """
    if not cusps:
        return 1
    n = len(cusps)
    if n == 1:
        return 1
    
    planet_longitude = float(planet_longitude) % 360.0
    
    for i in range(n):
        cusp_current = float(cusps[i]) % 360.0
        cusp_next = float(cusps[(i + 1) % n]) % 360.0
        
        # Manejar el caso donde la casa cruza 0° Aries
        if cusp_current > cusp_next:
            if planet_longitude >= cusp_current or planet_longitude < cusp_next:
                return i + 1
        else:
            if cusp_current <= planet_longitude < cusp_next:
                return i + 1
    
    # Fallback (no debería llegar aquí)
    return 1


def format_houses_output(houses_data: Dict) -> Dict:
    """
    Formatea la salida de casas según el esquema persian_calculations.md
    
    Returns:
        dict: {
            "asc": "Gemini 14.2°",
            "mc": "Aquarius 22.5°",
            "houses": [
                {"num": 1, "cusp": "Gemini 14.2°", "longitude": 74.2},
                ...
            ]
        }
    """
    asc_sign, asc_deg = longitude_to_sign_degree(houses_data["asc"])
    mc_sign, mc_deg = longitude_to_sign_degree(houses_data["mc"])
    
    houses_list = []
    for i, cusp_long in enumerate(houses_data["cusps"], 1):
        sign, deg = longitude_to_sign_degree(cusp_long)
        houses_list.append({
            "num": i,
            "cusp": f"{sign} {deg:.1f}°",
            "longitude": cusp_long
        })
    
    return {
        "asc": f"{asc_sign} {asc_deg:.1f}°",
        "mc": f"{mc_sign} {mc_deg:.1f}°",
        "asc_longitude": houses_data["asc"],
        "mc_longitude": houses_data["mc"],
        "houses": houses_list
    }


def assign_planets_to_houses(planets: List[Dict], cusps: List[float]) -> List[Dict]:
    """
    Asigna cada planeta a su casa correspondiente.
    
    Args:
        planets: Lista de planetas con longitud
        cusps: Lista de 12 cúspides
    
    Returns:
        Lista de planetas con campo "house" añadido
    """
    result = []
    for planet in planets:
        planet_copy = planet.copy()
        longitude = planet.get("longitude", 0)
        planet_copy["house"] = get_planet_house(longitude, cusps)
        result.append(planet_copy)
    
    return result
