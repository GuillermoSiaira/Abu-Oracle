from typing import Dict, List

ELEMENT_BY_SIGN = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}

RULER_BY_SIGN = {
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
    "Pisces": "Jupiter",
}

PLANET_NATURE = {
    "Saturn":  ["cold", "dry"],
    "Jupiter": ["hot", "moist"],
    "Mars":    ["hot", "dry"],
    "Sun":     ["hot", "dry"],
    "Venus":   ["cold", "moist"],
    "Mercury": ["variable"],
    "Moon":    ["cold", "moist"],
    "North Node": ["expansive"],
    "South Node": ["contractive"],
}

ANGULAR_HOUSES = {1, 4, 7, 10}
SUCCEDENT_HOUSES = {2, 5, 8, 11}
CADENT_HOUSES = {3, 6, 9, 12}

def element_of_sign(sign: str) -> str:
    return ELEMENT_BY_SIGN.get(sign, "unknown")

def ruler_of_sign(sign: str) -> str:
    return RULER_BY_SIGN.get(sign, "Unknown")

def is_angular_house(house: int) -> bool:
    return house in ANGULAR_HOUSES

def is_succedent_house(house: int) -> bool:
    return house in SUCCEDENT_HOUSES

def is_cadent_house(house: int) -> bool:
    return house in CADENT_HOUSES
