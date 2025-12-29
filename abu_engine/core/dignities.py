"""
Dignidades y Debilidades Esenciales (Astrología Persa/Clásica)
Domicilio, Exaltación, Exilio, Caída por signo y grado.
"""

# Domicilio (Rulership)
RULERSHIPS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",  # Tradicional
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",  # Tradicional
    "Pisces": "Jupiter",  # Tradicional
}

# Exaltaciones (Exaltation) - con grado exacto
EXALTATIONS = {
    "Sun": {"sign": "Aries", "degree": 19},
    "Moon": {"sign": "Taurus", "degree": 3},
    "Mercury": {"sign": "Virgo", "degree": 15},
    "Venus": {"sign": "Pisces", "degree": 27},
    "Mars": {"sign": "Capricorn", "degree": 28},
    "Jupiter": {"sign": "Cancer", "degree": 15},
    "Saturn": {"sign": "Libra", "degree": 21},
}

# Exilio (Detriment) - signo opuesto al domicilio
DETRIMENTS = {
    "Aries": "Venus",
    "Taurus": "Mars",
    "Gemini": "Jupiter",
    "Cancer": "Saturn",
    "Leo": "Saturn",
    "Virgo": "Jupiter",
    "Libra": "Mars",
    "Scorpio": "Venus",
    "Sagittarius": "Mercury",
    "Capricorn": "Moon",
    "Aquarius": "Sun",
    "Pisces": "Mercury",
}

# Caída (Fall) - signo opuesto a la exaltación
FALLS = {
    "Sun": {"sign": "Libra", "degree": 19},
    "Moon": {"sign": "Scorpio", "degree": 3},
    "Mercury": {"sign": "Pisces", "degree": 15},
    "Venus": {"sign": "Virgo", "degree": 27},
    "Mars": {"sign": "Cancer", "degree": 28},
    "Jupiter": {"sign": "Capricorn", "degree": 15},
    "Saturn": {"sign": "Aries", "degree": 21},
}

# Puntajes por dignidad
DIGNITY_SCORES = {
    "domicile": 5,
    "exaltation": 4,
    "triplicity": 3,
    "term": 2,
    "face": 1,
    "detriment": -5,
    "fall": -4,
    "peregrine": 0,
}


def get_planet_dignity(planet_name: str, sign: str, degree: float) -> dict:
    """
    Calcula la dignidad esencial de un planeta.
    
    Args:
        planet_name: Nombre del planeta (Sun, Moon, Mercury, etc.)
        sign: Signo zodiacal (Aries, Taurus, etc.)
        degree: Grado dentro del signo (0-30)
    
    Returns:
        dict: {
            "kind": str (domicile, exaltation, detriment, fall, peregrine),
            "score": int
        }
    """
    # Domicilio
    if RULERSHIPS.get(sign) == planet_name:
        return {"kind": "domicile", "score": DIGNITY_SCORES["domicile"]}
    
    # Exaltación
    if planet_name in EXALTATIONS:
        exalt = EXALTATIONS[planet_name]
        if exalt["sign"] == sign:
            # Orbe de 5° para exaltación exacta
            if abs(degree - exalt["degree"]) <= 5:
                return {"kind": "exaltation", "score": DIGNITY_SCORES["exaltation"]}
    
    # Exilio
    if DETRIMENTS.get(sign) == planet_name:
        return {"kind": "detriment", "score": DIGNITY_SCORES["detriment"]}
    
    # Caída
    if planet_name in FALLS:
        fall = FALLS[planet_name]
        if fall["sign"] == sign:
            # Orbe de 5° para caída exacta
            if abs(degree - fall["degree"]) <= 5:
                return {"kind": "fall", "score": DIGNITY_SCORES["fall"]}
    
    # Peregrino (sin dignidad)
    return {"kind": "peregrine", "score": DIGNITY_SCORES["peregrine"]}


def get_ruler(sign: str) -> str:
    """
    Obtiene el regente (ruler) de un signo zodiacal.
    
    Args:
        sign: Nombre del signo (Aries, Taurus, etc.)
    
    Returns:
        str: Nombre del planeta regente
    """
    return RULERSHIPS.get(sign, "Unknown")


def get_all_dignities(planets: list) -> dict:
    """
    Calcula dignidades para todos los planetas de una carta.
    
    Args:
        planets: Lista de dicts con {name, sign, degree}
    
    Returns:
        dict: {planet_name: dignity_info}
    """
    result = {}
    for planet in planets:
        name = planet.get("name")
        sign = planet.get("sign")
        degree = planet.get("degree", 0)
        
        if name and sign:
            result[name] = get_planet_dignity(name, sign, degree)
    
    return result
