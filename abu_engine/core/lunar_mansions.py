"""
Mansiones Lunares (Lunar Mansions)
28 mansiones de la Luna (Manzil árabe / Nakshatra védico)
"""

from typing import Dict, List


# 28 Mansiones Lunares (cada una ~12°51' = 360/28)
MANSION_SIZE = 360 / 28  # ~12.857°

LUNAR_MANSIONS = [
    {"index": 1, "name": "Al-Sharatain", "start": 0, "nature": "neutral", "ruler": "Mars"},
    {"index": 2, "name": "Al-Butain", "start": 12.857, "nature": "fortunate", "ruler": "Venus"},
    {"index": 3, "name": "Al-Thurayya", "start": 25.714, "nature": "fortunate", "ruler": "Moon"},
    {"index": 4, "name": "Al-Dabaran", "start": 38.571, "nature": "mixed", "ruler": "Mercury"},
    {"index": 5, "name": "Al-Haqa'ah", "start": 51.428, "nature": "neutral", "ruler": "Moon"},
    {"index": 6, "name": "Al-Han'ah", "start": 64.285, "nature": "mixed", "ruler": "Sun"},
    {"index": 7, "name": "Al-Dhira", "start": 77.142, "nature": "mixed", "ruler": "Jupiter"},
    {"index": 8, "name": "Al-Nathrah", "start": 90, "nature": "unfortunate", "ruler": "Saturn"},
    {"index": 9, "name": "Al-Tarf", "start": 102.857, "nature": "unfortunate", "ruler": "Mercury"},
    {"index": 10, "name": "Al-Jabhah", "start": 115.714, "nature": "neutral", "ruler": "Saturn"},
    {"index": 11, "name": "Al-Zubrah", "start": 128.571, "nature": "fortunate", "ruler": "Jupiter"},
    {"index": 12, "name": "Al-Sarfah", "start": 141.428, "nature": "mixed", "ruler": "Mars"},
    {"index": 13, "name": "Al-Awwa", "start": 154.285, "nature": "fortunate", "ruler": "Venus"},
    {"index": 14, "name": "Al-Simak", "start": 167.142, "nature": "fortunate", "ruler": "Mercury"},
    {"index": 15, "name": "Al-Ghafr", "start": 180, "nature": "fortunate", "ruler": "Moon"},
    {"index": 16, "name": "Al-Zubana", "start": 192.857, "nature": "mixed", "ruler": "Saturn"},
    {"index": 17, "name": "Al-Iklil", "start": 205.714, "nature": "mixed", "ruler": "Jupiter"},
    {"index": 18, "name": "Al-Qalb", "start": 218.571, "nature": "unfortunate", "ruler": "Mars"},
    {"index": 19, "name": "Al-Shaulah", "start": 231.428, "nature": "unfortunate", "ruler": "Moon"},
    {"index": 20, "name": "Al-Na'am", "start": 244.285, "nature": "fortunate", "ruler": "Saturn"},
    {"index": 21, "name": "Al-Baldah", "start": 257.142, "nature": "mixed", "ruler": "Jupiter"},
    {"index": 22, "name": "Sa'd al-Dhabih", "start": 270, "nature": "fortunate", "ruler": "Venus"},
    {"index": 23, "name": "Sa'd Bula", "start": 282.857, "nature": "fortunate", "ruler": "Mercury"},
    {"index": 24, "name": "Sa'd al-Su'ud", "start": 295.714, "nature": "fortunate", "ruler": "Sun"},
    {"index": 25, "name": "Sa'd al-Akhbiyah", "start": 308.571, "nature": "fortunate", "ruler": "Moon"},
    {"index": 26, "name": "Al-Fargh al-Mukdim", "start": 321.428, "nature": "mixed", "ruler": "Saturn"},
    {"index": 27, "name": "Al-Fargh al-Thani", "start": 334.285, "nature": "mixed", "ruler": "Jupiter"},
    {"index": 28, "name": "Al-Batn al-Hut", "start": 347.142, "nature": "fortunate", "ruler": "Mars"},
]


def get_lunar_mansion(moon_longitude: float) -> Dict:
    """
    Determina la mansión lunar basada en la longitud de la Luna.
    
    Args:
        moon_longitude: Longitud eclíptica de la Luna (0-360)
    
    Returns:
        dict: {
            "index": int,
            "name": str,
            "start": float,
            "end": float,
            "nature": str,
            "ruler": str,
            "position_in_mansion": float (grados dentro de la mansión)
        }
    """
    # Normalizar longitud
    moon_longitude = moon_longitude % 360
    
    # Encontrar la mansión
    mansion_index = int(moon_longitude / MANSION_SIZE)
    
    # Evitar índice fuera de rango
    if mansion_index >= 28:
        mansion_index = 27
    
    mansion = LUNAR_MANSIONS[mansion_index]
    
    # Calcular posición dentro de la mansión
    position = moon_longitude - mansion["start"]
    
    return {
        "index": mansion["index"],
        "name": mansion["name"],
        "start": mansion["start"],
        "end": (mansion["start"] + MANSION_SIZE) % 360,
        "nature": mansion["nature"],
        "ruler": mansion["ruler"],
        "position_in_mansion": round(position, 2)
    }


def get_mansion_interpretation(mansion: Dict) -> str:
    """
    Genera una interpretación básica de la mansión lunar.
    
    Returns:
        str: Descripción breve de la mansión
    """
    nature_desc = {
        "fortunate": "favorable para la mayoría de asuntos",
        "unfortunate": "desfavorable, usar con precaución",
        "mixed": "neutral, depende del contexto",
        "neutral": "sin influencia particular"
    }
    
    desc = nature_desc.get(mansion["nature"], "sin información")
    
    return (
        f"Mansión {mansion['index']}: {mansion['name']} "
        f"(regida por {mansion['ruler']}). Naturaleza: {desc}."
    )


def find_electional_mansions(nature: str = "fortunate") -> List[Dict]:
    """
    Encuentra mansiones favorables para elecciones.
    
    Args:
        nature: "fortunate", "mixed", "neutral", "unfortunate"
    
    Returns:
        Lista de mansiones que coinciden con la naturaleza especificada
    """
    return [m for m in LUNAR_MANSIONS if m["nature"] == nature]
