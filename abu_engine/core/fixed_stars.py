"""
Estrellas Fijas (Fixed Stars)
Catálogo de estrellas fijas principales con naturaleza y magnitud.
Incluye cálculo de conjunciones y parans básicos.
"""

from typing import Dict, List, Optional


# Catálogo de estrellas fijas principales (longitud para época ~2000)
# Formato: {nombre: {longitude, magnitude, nature, notes}}
FIXED_STARS = {
    "Regulus": {
        "longitude": 149.76,  # ~29° Leo
        "magnitude": 1.4,
        "nature": "Mars-Jupiter",
        "notes": "Corazón del León, realeza, honor, éxito"
    },
    "Aldebaran": {
        "longitude": 69.88,  # ~9° Gemini
        "magnitude": 0.9,
        "nature": "Mars",
        "notes": "Ojo del Toro, honor militar, impulsividad"
    },
    "Antares": {
        "longitude": 249.76,  # ~9° Sagittarius
        "magnitude": 1.0,
        "nature": "Mars-Jupiter",
        "notes": "Corazón del Escorpión, obstinación, violencia"
    },
    "Fomalhaut": {
        "longitude": 333.76,  # ~3° Pisces
        "magnitude": 1.2,
        "nature": "Venus-Mercury",
        "notes": "Boca del Pez, idealismo, arte, magia"
    },
    "Spica": {
        "longitude": 203.76,  # ~23° Libra
        "magnitude": 1.0,
        "nature": "Venus-Mars",
        "notes": "Espiga de trigo, protección, éxito, talento"
    },
    "Algol": {
        "longitude": 56.0,  # ~26° Taurus
        "magnitude": 2.1,
        "nature": "Saturn-Jupiter",
        "notes": "Cabeza de Medusa, peligro, violencia, decapitación"
    },
    "Sirius": {
        "longitude": 104.0,  # ~14° Cancer
        "magnitude": -1.5,
        "nature": "Jupiter-Mars",
        "notes": "Estrella del Perro, honor, riqueza, fidelidad"
    },
    "Vega": {
        "longitude": 285.0,  # ~15° Capricorn
        "magnitude": 0.0,
        "nature": "Venus-Mercury",
        "notes": "Crítica, idealismo, refinamiento"
    },
    "Arcturus": {
        "longitude": 204.0,  # ~24° Libra
        "magnitude": -0.04,
        "nature": "Mars-Jupiter",
        "notes": "Protección, riqueza, honor"
    },
    "Betelgeuse": {
        "longitude": 88.76,  # ~28° Gemini
        "magnitude": 0.5,
        "nature": "Mars-Mercury",
        "notes": "Aventura, éxito rápido, fortuna cambiante"
    },
}


def get_orb_for_magnitude(magnitude: float) -> float:
    """
    Calcula el orbe permitido según la magnitud de la estrella.
    
    Regla tradicional:
    - Mag < 1: orbe 2°
    - Mag 1-2: orbe 1.5°
    - Mag 2-3: orbe 1°
    - Mag > 3: orbe 0.5°
    
    Returns:
        float: Orbe en grados
    """
    if magnitude < 1:
        return 2.0
    elif magnitude < 2:
        return 1.5
    elif magnitude < 3:
        return 1.0
    else:
        return 0.5


def find_fixed_star_conjunctions(
    planet_longitude: float,
    planet_name: str = None
) -> List[Dict]:
    """
    Encuentra estrellas fijas en conjunción con un planeta o punto.
    
    Args:
        planet_longitude: Longitud del planeta (0-360)
        planet_name: Nombre del planeta (opcional, para contexto)
    
    Returns:
        List[Dict]: [
            {
                "star": str,
                "magnitude": float,
                "nature": str,
                "orb": float,
                "notes": str,
                "match": bool
            },
            ...
        ]
    """
    conjunctions = []
    
    for star_name, star_data in FIXED_STARS.items():
        star_long = star_data["longitude"]
        magnitude = star_data["magnitude"]
        
        # Calcular diferencia angular
        diff = abs((planet_longitude - star_long + 180) % 360 - 180)
        
        # Obtener orbe permitido
        max_orb = get_orb_for_magnitude(magnitude)
        
        # Si está dentro del orbe, es una conjunción
        if diff <= max_orb:
            conjunctions.append({
                "star": star_name,
                "magnitude": magnitude,
                "nature": star_data["nature"],
                "orb": round(diff, 2),
                "notes": star_data["notes"],
                "match": True,
                "longitude": star_long
            })
    
    return conjunctions


def get_all_fixed_star_contacts(planets: List[Dict]) -> List[Dict]:
    """
    Encuentra todas las conjunciones de estrellas fijas con planetas de la carta.
    
    Args:
        planets: Lista de planetas [{name, longitude}]
    
    Returns:
        List[Dict]: Lista de contactos estrella-planeta
    """
    all_contacts = []
    
    for planet in planets:
        planet_name = planet.get("name")
        planet_long = planet.get("longitude", 0)
        
        conjunctions = find_fixed_star_conjunctions(planet_long, planet_name)
        
        for conj in conjunctions:
            conj["planet"] = planet_name
            all_contacts.append(conj)
    
    return all_contacts


def format_fixed_stars_output(contacts: List[Dict]) -> List[Dict]:
    """
    Formatea la salida de estrellas fijas según el esquema persian_calculations.md
    
    Returns:
        List[Dict]: [
            {
                "star": "Regulus",
                "mag": 1.4,
                "long": "Leo 29°",
                "planet": "Sun",
                "match": true,
                "orb": 0.8
            },
            ...
        ]
    """
    result = []
    
    for contact in contacts:
        # Convertir longitud a signo y grado
        star_long = contact.get("longitude", 0)
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        sign_index = int(star_long / 30)
        degree = star_long % 30
        sign_str = f"{signs[sign_index]} {int(degree)}°"
        
        result.append({
            "star": contact["star"],
            "mag": contact["magnitude"],
            "long": sign_str,
            "planet": contact.get("planet", ""),
            "match": contact["match"],
            "orb": contact["orb"],
            "nature": contact["nature"],
            "notes": contact["notes"]
        })
    
    return result


def get_star_catalog() -> Dict:
    """
    Devuelve el catálogo completo de estrellas fijas.
    
    Returns:
        Dict: Catálogo de estrellas con información detallada
    """
    return FIXED_STARS.copy()
