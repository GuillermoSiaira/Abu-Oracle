"""
Condiciones Solares (Óptica)
Combustión, Bajo Rayos, Cazimi
"""

def get_solar_condition(planet_longitude: float, sun_longitude: float, planet_name: str) -> dict:
    """
    Determina la condición solar de un planeta.
    
    Condiciones:
    - Cazimi: < 0.28° (17 minutos de arco)
    - Combustión: < 8°
    - Bajo rayos: < 17°
    
    Args:
        planet_longitude: Longitud del planeta
        sun_longitude: Longitud del Sol
        planet_name: Nombre del planeta (para excluir luminarias)
    
    Returns:
        dict: {
            "state": str ("cazimi", "combust", "under_beams", "free"),
            "distance_deg": float
        }
    """
    # No aplica a Sol y Luna
    if planet_name in ["Sun", "Moon"]:
        return {"state": "n/a", "distance_deg": 0}
    
    # Calcular distancia angular
    diff = abs((planet_longitude - sun_longitude + 180) % 360 - 180)
    
    # Cazimi (corazón del Sol)
    if diff < 0.28:  # ~17 minutos de arco
        return {"state": "cazimi", "distance_deg": round(diff, 2)}
    
    # Combustión
    if diff < 8:
        return {"state": "combust", "distance_deg": round(diff, 2)}
    
    # Bajo rayos
    if diff < 17:
        return {"state": "under_beams", "distance_deg": round(diff, 2)}
    
    # Libre del Sol
    return {"state": "free", "distance_deg": round(diff, 2)}


def get_all_solar_conditions(planets: list, sun_longitude: float) -> dict:
    """
    Calcula condiciones solares para todos los planetas.
    
    Args:
        planets: Lista de planetas [{name, longitude, ...}]
        sun_longitude: Longitud del Sol
    
    Returns:
        dict: {planet_name: solar_condition}
    """
    result = {}
    for planet in planets:
        name = planet.get("name")
        longitude = planet.get("longitude", 0)
        
        if name:
            result[name] = get_solar_condition(longitude, sun_longitude, name)
    
    return result
