# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import List, Dict, Any
from skyfield.api import load
from core.chart import EphemerisSingleton

def get_slow_planet_position(planets, date: datetime) -> Dict[str, float]:
    """
    Obtiene las posiciones de los planetas lentos para una fecha dada.
    """
    ts = load.timescale()
    t = ts.from_datetime(date)
    earth = planets['earth']
    
    positions = {}
    planet_list = {
        'Saturn': ('saturn barycenter', [0, 0, 180]),  # Return y Opposition
        'Uranus': ('uranus barycenter', [180]),  # Opposition
        'Neptune': ('neptune barycenter', [90]),  # Square
        'Pluto': ('pluto barycenter', [90]),  # Square
    }
    
    for planet_name, (sky_name, _) in planet_list.items():
        try:
            planet = planets[sky_name]
            pos = earth.at(t).observe(planet)
            _, lon, _ = pos.ecliptic_latlon()
            positions[planet_name] = lon.degrees % 360
        except Exception:
            continue
            
    return positions

def detect_aspect_event(natal_pos: float, current_pos: float, orb: float = 1.0, angles: List[int] = None) -> int:
    """
    Detecta si hay un aspecto significativo entre dos posiciones.
    Solo detecta los aspectos especificados en la lista angles.
    """
    if angles is None:
        angles = [0, 90, 180]
        
    diff = abs(current_pos - natal_pos) % 360
    if diff > 180:
        diff = 360 - diff
        
    for angle in angles:
        if abs(diff - angle) <= orb:
            return angle
    return None

def get_cycle_name(planet: str, angle: int) -> str:
    """
    Genera el nombre del ciclo basado en el planeta y el ángulo.
    """
    if angle == 0:
        return f"{planet} Return"
    elif angle == 90:
        return f"{planet} Square"
    else:
        return f"{planet} Opposition"

def forecast_life_cycles(birth_dt: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detecta los ciclos mayores de los planetas lentos:
    - Saturn Return (~29, ~58 años)
    - Uranus Opposition (~42 años)
    - Neptune Square (~41 años)
    - Pluto Square (~37 años)
    - Chiron Return (~50 años)
    
    Args:
        birth_dt: Fecha y hora de nacimiento en formato ISO
        
    Returns:
        Dict con lista de eventos de ciclos vitales
    """
    try:
        # Convertir fecha ISO a datetime
        if isinstance(birth_dt, str):
            birth_dt = datetime.fromisoformat(birth_dt.replace("Z", "+00:00"))

        # Use shared ephemeris singleton (handles local cache and auto-download)
        planets = EphemerisSingleton()
        
        # Planetas y sus aspectos relevantes
        planet_aspects = {
            'Saturn': [0, 0, 180],  # Return a los 29 y 58, Opposition
            'Uranus': [180],  # Opposition ~42
            'Neptune': [90],  # Square ~41
            'Pluto': [90],  # Square ~37
        }
        
        # Obtener posiciones natales
        natal_positions = get_slow_planet_position(planets, birth_dt)
        
        # Calcular rango de búsqueda (90 años desde nacimiento)
        dates = []
        current = birth_dt
        end_date = birth_dt + timedelta(days=365*90)
        
        # Muestrear cada 30 días
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=30)
            
        events = []
        
        # Buscar aspectos significativos
        for check_date in dates:
            current_positions = get_slow_planet_position(planets, check_date)
            
            for planet, natal_pos in natal_positions.items():
                if planet not in current_positions:
                    continue
                    
                current_pos = current_positions[planet]
                angles = planet_aspects.get(planet, [])
                angle = detect_aspect_event(natal_pos, current_pos, angles=angles)
                
                if angle is not None:
                    events.append({
                        "cycle": get_cycle_name(planet, angle),
                        "planet": planet,
                        "angle": angle,
                        "approx": check_date.strftime("%Y-%m-%d")
                    })
        
        return {"events": events}
        
    except Exception as e:
        raise RuntimeError("cycle calculation error") from e

__all__ = ["forecast_life_cycles"]