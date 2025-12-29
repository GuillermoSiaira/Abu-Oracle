"""
Tránsitos (Transits)
Compara posiciones actuales/futuras con la carta natal para detectar aspectos.
"""

from datetime import datetime
from typing import List, Dict, Optional
from .aspects import calculate_aspect_type, is_applying


# Orbes por tipo de aspecto (configurables)
DEFAULT_ORBS = {
    "conjunction": 8,
    "opposition": 8,
    "trine": 8,
    "square": 7,
    "sextile": 6,
    "semisextile": 3,
    "quincunx": 3,
    "semisquare": 2,
    "sesquisquare": 2,
}


def calculate_transits(
    natal_planets: List[Dict],
    transit_planets: List[Dict],
    orbs: Dict[str, float] = None,
    include_minor: bool = False
) -> List[Dict]:
    """
    Calcula aspectos entre planetas natales y planetas en tránsito.
    
    Args:
        natal_planets: Lista de planetas natales [{name, longitude}]
        transit_planets: Lista de planetas en tránsito [{name, longitude, speed}]
        orbs: Orbes por tipo de aspecto (default: DEFAULT_ORBS)
        include_minor: Incluir aspectos menores (30, 45, 135, 150)
    
    Returns:
        List[Dict]: [
            {
                "natal_planet": str,
                "transit_planet": str,
                "aspect": str,
                "orb": float,
                "applying": bool,
                "exactness": str ("approaching", "exact", "separating"),
                "natal_longitude": float,
                "transit_longitude": float
            },
            ...
        ]
    """
    if orbs is None:
        orbs = DEFAULT_ORBS
    
    transits = []
    
    for natal in natal_planets:
        natal_name = natal.get("name")
        natal_long = natal.get("longitude", 0)
        
        for transit in transit_planets:
            transit_name = transit.get("name")
            transit_long = transit.get("longitude", 0)
            transit_speed = transit.get("speed", 0)
            
            # Calcular aspecto
            aspect_info = calculate_aspect_type(
                natal_long, 
                transit_long,
                include_minor=include_minor
            )
            
            if aspect_info["aspect"]:
                aspect_type = aspect_info["aspect"]
                orb = aspect_info["orb"]
                
                # Verificar si está dentro del orbe permitido
                max_orb = orbs.get(aspect_type, 3)
                
                if orb <= max_orb:
                    # Determinar si es aplicativo o separativo
                    applying = is_applying(natal_long, transit_long, transit_speed)
                    
                    # Determinar exactitud
                    if orb < 1:
                        exactness = "exact"
                    elif applying:
                        exactness = "approaching"
                    else:
                        exactness = "separating"
                    
                    transits.append({
                        "natal_planet": natal_name,
                        "transit_planet": transit_name,
                        "aspect": aspect_type,
                        "orb": round(orb, 2),
                        "applying": applying,
                        "exactness": exactness,
                        "natal_longitude": natal_long,
                        "transit_longitude": transit_long
                    })
    
    return transits


def filter_major_transits(
    transits: List[Dict],
    major_planets_only: bool = True,
    max_orb: float = 3.0
) -> List[Dict]:
    """
    Filtra tránsitos para mostrar solo los más importantes.
    
    Args:
        transits: Lista completa de tránsitos
        major_planets_only: Filtrar solo planetas exteriores (Júpiter, Saturno, Urano, Neptuno, Plutón)
        max_orb: Orbe máximo para considerar el tránsito
    
    Returns:
        Lista filtrada de tránsitos
    """
    outer_planets = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    
    filtered = []
    for transit in transits:
        # Filtrar por orbe
        if transit["orb"] > max_orb:
            continue
        
        # Filtrar por planeta exterior si se requiere
        if major_planets_only:
            if transit["transit_planet"] not in outer_planets:
                continue
        
        filtered.append(transit)
    
    return filtered


def format_transit_description(transit: Dict) -> str:
    """
    Genera una descripción legible del tránsito.
    
    Returns:
        str: "Saturn square natal Moon (applying, orb 2.3°)"
    """
    applying_str = "applying" if transit["applying"] else "separating"
    
    return (
        f"{transit['transit_planet']} {transit['aspect']} "
        f"natal {transit['natal_planet']} "
        f"({applying_str}, orb {transit['orb']}°)"
    )


def get_transit_timeline(
    natal_planets: List[Dict],
    transit_dates: List[datetime],
    calculate_positions_func,
    orbs: Dict[str, float] = None
) -> Dict:
    """
    Calcula tránsitos para múltiples fechas y genera una línea de tiempo.
    
    Args:
        natal_planets: Planetas natales
        transit_dates: Lista de fechas a calcular
        calculate_positions_func: Función para calcular posiciones planetarias
        orbs: Orbes personalizados
    
    Returns:
        dict: {
            "dates": [datetime],
            "transits": [
                {
                    "date": datetime,
                    "transits": [...]
                },
                ...
            ]
        }
    """
    timeline = []
    
    for date in transit_dates:
        # Calcular posiciones para esta fecha
        transit_planets = calculate_positions_func(date)
        
        # Calcular tránsitos
        transits = calculate_transits(natal_planets, transit_planets, orbs)
        
        timeline.append({
            "date": date.isoformat(),
            "transits": transits
        })
    
    return {
        "dates": [d.isoformat() for d in transit_dates],
        "timeline": timeline
    }
