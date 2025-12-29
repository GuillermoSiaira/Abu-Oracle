"""
Revolución Solar (Solar Return) con Reubicación
Calcula el instante exacto del retorno solar y permite reubicación geográfica.
"""

try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:
    SWE_AVAILABLE = False

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


def find_solar_return_time(
    birth_date: datetime,
    birth_sun_longitude: float,
    year: int,
    precision_hours: float = 0.01
) -> datetime:
    """
    Encuentra el momento exacto del retorno solar para un año dado.
    
    Args:
        birth_date: Fecha de nacimiento
        birth_sun_longitude: Longitud del Sol natal
        year: Año de la revolución solar
        precision_hours: Precisión en horas (default: 0.01 = ~36 segundos)
    
    Returns:
        datetime: Momento exacto del retorno solar (UTC)
    """
    if not SWE_AVAILABLE:
        raise ImportError("pyswisseph no está instalado")
    
    # Estimar fecha cercana al cumpleaños
    estimated_date = datetime(year, birth_date.month, birth_date.day, 
                              birth_date.hour, birth_date.minute)
    
    # Búsqueda binaria para encontrar el momento exacto
    min_date = estimated_date - timedelta(days=2)
    max_date = estimated_date + timedelta(days=2)
    
    target_longitude = birth_sun_longitude % 360
    
    while (max_date - min_date).total_seconds() / 3600 > precision_hours:
        mid_date = min_date + (max_date - min_date) / 2
        
        # Calcular longitud del Sol en mid_date
        jd = swe.julday(mid_date.year, mid_date.month, mid_date.day,
                        mid_date.hour + mid_date.minute / 60.0)
        sun_pos, _ = swe.calc_ut(jd, swe.SUN)
        sun_long = sun_pos[0]
        
        # Diferencia angular
        diff = abs((sun_long - target_longitude + 180) % 360 - 180)
        
        # Determinar si estamos antes o después
        if diff < 0.01:  # Suficientemente cerca
            return mid_date
        
        # Ajustar rango de búsqueda
        # Si el Sol aún no alcanzó la posición natal, buscar más adelante
        if (sun_long - target_longitude + 360) % 360 > 180:
            min_date = mid_date
        else:
            max_date = mid_date
    
    return min_date + (max_date - min_date) / 2


def calculate_solar_return(
    birth_sun_longitude: float,
    year: int,
    lat: float,
    lon: float,
    birth_date: datetime = None
) -> Dict:
    """
    Calcula una Revolución Solar completa con casas para ubicación específica.
    
    Args:
        birth_sun_longitude: Longitud del Sol natal
        year: Año de la RS
        lat: Latitud de la ubicación de la RS
        lon: Longitud de la ubicación de la RS
        birth_date: Fecha de nacimiento (para encontrar el momento exacto)
    
    Returns:
        dict: {
            "solar_return_datetime": str (ISO),
            "location": {"lat": float, "lon": float},
            "sun": {"longitude": float, "sign": str, "degree": float},
            "asc": {"longitude": float, "sign": str, "degree": float},
            "mc": {"longitude": float, "sign": str, "degree": float},
            "houses": [...],
            "planets": [...],
            "aspects": [...]
        }
    """
    if not SWE_AVAILABLE:
        raise ImportError("pyswisseph no está instalado")
    
    # Encontrar momento exacto del retorno solar
    if birth_date is None:
        # Estimar fecha (15 de junio del año solicitado como fallback)
        sr_datetime = datetime(year, 6, 15, 12, 0, 0)
    else:
        sr_datetime = find_solar_return_time(birth_date, birth_sun_longitude, year)
    
    # Calcular posiciones planetarias para ese momento
    jd = swe.julday(sr_datetime.year, sr_datetime.month, sr_datetime.day,
                    sr_datetime.hour + sr_datetime.minute / 60.0)
    
    # Calcular casas para la ubicación de la RS
    from .houses_swiss import (
        calculate_houses, 
        format_houses_output, 
        longitude_to_sign_degree,
        HOUSE_SYSTEM_PLACIDUS
    )
    
    houses_data = calculate_houses(sr_datetime, lat, lon, HOUSE_SYSTEM_PLACIDUS)
    houses_formatted = format_houses_output(houses_data)
    
    # Calcular planetas
    planets = []
    planet_ids = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
    }
    
    for planet_name, planet_id in planet_ids.items():
        pos, _ = swe.calc_ut(jd, planet_id)
        longitude = pos[0]
        sign, degree = longitude_to_sign_degree(longitude)
        
        planets.append({
            "name": planet_name,
            "longitude": longitude,
            "sign": sign,
            "degree": round(degree, 2)
        })
    
    # Calcular aspectos básicos
    from .aspects import aspect_between
    
    aspects = []
    for i, p1 in enumerate(planets):
        for p2 in planets[i + 1:]:
            aspect_type, orb = aspect_between(p1["longitude"], p2["longitude"])
            if aspect_type:
                aspects.append({
                    "planet1": p1["name"],
                    "planet2": p2["name"],
                    "aspect": aspect_type,
                    "orb": orb
                })
    
    return {
        "solar_return_datetime": sr_datetime.isoformat(),
        "location": {"lat": lat, "lon": lon},
        "sun": {
            "longitude": birth_sun_longitude,
            "sign": longitude_to_sign_degree(birth_sun_longitude)[0],
            "degree": round(longitude_to_sign_degree(birth_sun_longitude)[1], 2)
        },
        "asc": houses_formatted["asc"],
        "mc": houses_formatted["mc"],
        "houses": houses_formatted["houses"],
        "planets": planets,
        "aspects": aspects
    }


def compare_natal_to_solar_return(natal_chart: Dict, solar_return: Dict) -> Dict:
    """
    Compara la carta natal con la revolución solar para resaltar cambios importantes.
    
    Returns:
        dict: {
            "asc_change": {"natal": str, "solar": str, "diff_degrees": float},
            "mc_change": {...},
            "angular_planets": [...]  # Planetas que caen en ángulos en RS
        }
    """
    # TODO: implementar comparación detallada
    return {
        "note": "Comparison feature to be implemented"
    }
