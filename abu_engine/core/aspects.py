# -*- coding: utf-8 -*-
ASPECTS = {"conjunction": 0, "sextile": 60, "square": 90, "trine": 120, "opposition": 180}

# Aspectos menores
MINOR_ASPECTS = {
    "semisextile": 30,
    "semisquare": 45,
    "sesquisquare": 135,
    "quincunx": 150,
}

def aspect_between(a_lon, b_lon, orb=6):
    """
    Devuelve el tipo de aspecto y la diferencia angular (orb) si existe.
    """
    diff = abs((a_lon - b_lon + 180) % 360 - 180)
    for name, angle in ASPECTS.items():
        if abs(diff - angle) <= orb:
            return name, round(diff - angle, 2)
    return None, None


def calculate_aspect_type(lon_a: float, lon_b: float, include_minor: bool = False) -> dict:
    """
    Calcula el tipo de aspecto y orbe entre dos longitudes.
    
    Args:
        lon_a: Longitud del primer punto
        lon_b: Longitud del segundo punto
        include_minor: Incluir aspectos menores
    
    Returns:
        dict: {"aspect": str, "orb": float, "angle": float}
    """
    # Diferencia angular normalizada
    diff = abs((lon_a - lon_b + 180) % 360 - 180)
    
    # Buscar en aspectos mayores
    aspects_to_check = ASPECTS.copy()
    if include_minor:
        aspects_to_check.update(MINOR_ASPECTS)
    
    closest_aspect = None
    closest_orb = 999
    
    for aspect_name, aspect_angle in aspects_to_check.items():
        orb = abs(diff - aspect_angle)
        if orb < closest_orb:
            closest_orb = orb
            closest_aspect = aspect_name
    
    # Devolver solo si el orbe es razonable (< 10°)
    if closest_orb < 10:
        return {
            "aspect": closest_aspect,
            "orb": round(closest_orb, 2),
            "angle": round(diff, 2)
        }
    
    return {"aspect": None, "orb": None, "angle": round(diff, 2)}


def is_applying(lon_natal: float, lon_transit: float, speed_transit: float) -> bool:
    """
    Determina si un aspecto es aplicativo o separativo.
    
    Args:
        lon_natal: Longitud del planeta natal
        lon_transit: Longitud del planeta en tránsito
        speed_transit: Velocidad del planeta en tránsito (°/día)
    
    Returns:
        bool: True si es aplicativo, False si es separativo
    """
    # Si la velocidad es 0 o no disponible, asumir aplicativo
    if speed_transit == 0:
        return True
    
    # Calcular diferencia angular
    diff = (lon_transit - lon_natal + 180) % 360 - 180
    
    # Si la velocidad es positiva (directo) y diff es negativa, está aplicando
    # Si la velocidad es negativa (retrógrado) y diff es positiva, está aplicando
    if speed_transit > 0:
        return diff < 0
    else:
        return diff > 0


