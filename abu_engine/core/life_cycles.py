# -*- coding: utf-8 -*-
"""
life_cycles.py — Ciclos Vitales Planetarios

Detecta los grandes ciclos astronómicos que estructuran la biografía:
retornos, oposiciones y cuadraturas de planetas lentos respecto a sus
posiciones natales. Usado en el endpoint GET /api/astro/life-cycles y
en el campo `life_cycles` del response de /analyze.

Ciclos detectados:
  Jupiter Return   ~12 años   — renovación de propósito y expansión
  Saturn Return    ~29/58 años — prueba de estructura y madurez
  Saturn Opposition ~44 años  — punto de máxima tensión del ciclo saturno
  Uranus Opposition ~42 años  — crisis de individualización (mid-life)
  Neptune Square   ~41 años   — disolución de ilusiones / llamado espiritual
  Pluto Square     ~37 años   — transformación de poder y sombra

Algoritmo:
  1. Calcular posiciones natales de los planetas lentos.
  2. Muestrear cada 30 días durante 90 años desde el nacimiento.
  3. Detectar aspectos dentro de orbe ±1° en cada muestra.
  4. Deduplicar por (planeta, ciclo, año) — el muestreo grueso puede
     detectar el mismo tránsito en múltiples puntos del mismo año.
  5. Devolver lista ordenada cronológicamente.

Nota de performance: ~1,095 fechas × 5 planetas = ~5,475 llamadas a
Skyfield. Tiempo típico: 3-8 segundos. Candidato a cacheo por birth_dt.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from skyfield.api import load
from core.chart import EphemerisSingleton


def get_slow_planet_position(planets, date: datetime) -> Dict[str, float]:
    """
    Calcula las longitudes eclípticas de los planetas lentos para una fecha.

    Args:
        planets: EphemerisSingleton — objeto de efemérides compartido.
        date:    datetime con tzinfo UTC.

    Returns:
        Dict {nombre_planeta: longitud_eclíptica_0-360°}.
        Los planetas que fallen silenciosamente se omiten del dict.

    Planetas y aspectos que les son relevantes (informativo, no usado aquí):
        Jupiter  → Return (0°)
        Saturn   → Return (0°), Opposition (180°)
        Uranus   → Opposition (180°)
        Neptune  → Square (90°)
        Pluto    → Square (90°)
    """
    ts = load.timescale()
    t = ts.from_datetime(date)
    earth = planets['earth']

    planet_list = {
        'Jupiter': ('jupiter barycenter', [0]),
        'Saturn':  ('saturn barycenter', [0, 180]),
        'Uranus':  ('uranus barycenter', [180]),
        'Neptune': ('neptune barycenter', [90]),
        'Pluto':   ('pluto barycenter', [90]),
    }

    positions = {}
    for planet_name, (sky_name, _) in planet_list.items():
        try:
            planet = planets[sky_name]
            pos = earth.at(t).observe(planet)
            _, lon, _ = pos.ecliptic_latlon()
            positions[planet_name] = lon.degrees % 360
        except Exception:
            # Falla silenciosa: efemérides fuera de rango u otro error puntual
            continue

    return positions


def detect_aspect_event(
    natal_pos: float,
    current_pos: float,
    orb: float = 1.0,
    angles: List[int] = None,
) -> int | None:
    """
    Detecta si la posición actual de un planeta forma un aspecto exacto
    con su posición natal, dentro del orbe especificado.

    La distancia se calcula como el arco mínimo entre las dos longitudes
    (siempre ≤ 180°), lo que hace el test simétrico para aplicación y
    separación.

    Args:
        natal_pos:   Longitud natal del planeta (0-360°).
        current_pos: Longitud actual del planeta (0-360°).
        orb:         Tolerancia en grados (default 1.0°).
        angles:      Lista de ángulos a detectar. Default [0, 90, 180].

    Returns:
        El ángulo del aspecto detectado (int), o None si no hay aspecto.
    """
    if angles is None:
        angles = [0, 90, 180]

    diff = abs(current_pos - natal_pos) % 360
    if diff > 180:
        diff = 360 - diff  # arco mínimo

    for angle in angles:
        if abs(diff - angle) <= orb:
            return angle
    return None


def get_cycle_name(planet: str, angle: int) -> str:
    """
    Genera la etiqueta del ciclo a partir del planeta y el ángulo.

    Examples:
        get_cycle_name('Saturn', 0)   → 'Saturn Return'
        get_cycle_name('Saturn', 180) → 'Saturn Opposition'
        get_cycle_name('Neptune', 90) → 'Neptune Square'
    """
    if angle == 0:
        return f"{planet} Return"
    elif angle == 90:
        return f"{planet} Square"
    else:
        return f"{planet} Opposition"


def forecast_life_cycles(birth_dt: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calcula los ciclos vitales mayores para una fecha de nacimiento.

    Escanea 90 años desde el nacimiento en pasos de 30 días, detectando
    aspectos de retorno, oposición y cuadratura de los planetas lentos
    respecto a sus posiciones natales. El resultado se deduplica por año
    para eliminar múltiples detecciones del mismo tránsito.

    Args:
        birth_dt: Fecha/hora de nacimiento en formato ISO 8601 UTC.
                  Ejemplos: "1978-07-06T00:15:00Z", "1990-01-01T12:00:00+00:00"

    Returns:
        {"events": [ {cycle, planet, angle, approx}, ... ]}
        ordenado cronológicamente, un evento por (planeta, ciclo, año).

        Campos de cada evento:
            cycle:  str  — Etiqueta legible, ej. "Saturn Return"
            planet: str  — Nombre del planeta
            angle:  int  — Ángulo del aspecto (0, 90 o 180)
            approx: str  — Fecha aproximada YYYY-MM-DD (primer disparo del año)

    Raises:
        RuntimeError: Si el cálculo falla por cualquier causa.
    """
    try:
        if isinstance(birth_dt, str):
            birth_dt = datetime.fromisoformat(birth_dt.replace("Z", "+00:00"))

        # Efemérides compartidas (DE440s, singleton, auto-descarga si no existe)
        planets = EphemerisSingleton()

        # Aspectos relevantes por planeta (subconjunto de los 5 mayores)
        planet_aspects = {
            'Jupiter': [0],       # Return ~12 años
            'Saturn':  [0, 180],  # Return ~29/58 años, Opposition ~44 años
            'Uranus':  [180],     # Opposition ~42 años (crisis mid-life)
            'Neptune': [90],      # Square ~41 años
            'Pluto':   [90],      # Square ~37 años
        }

        natal_positions = get_slow_planet_position(planets, birth_dt)

        # Generar fechas de muestreo: cada 30 días durante 90 años
        end_date = birth_dt + timedelta(days=365 * 90)
        dates = []
        current = birth_dt
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=30)

        events = []
        for check_date in dates:
            current_positions = get_slow_planet_position(planets, check_date)

            for planet, natal_pos in natal_positions.items():
                if planet not in current_positions:
                    continue

                current_pos = current_positions[planet]
                angles = planet_aspects.get(planet, [])
                angle = detect_aspect_event(natal_pos, current_pos, orb=3.0, angles=angles)

                if angle is not None:
                    events.append({
                        "cycle":   get_cycle_name(planet, angle),
                        "planet":  planet,
                        "angle":   angle,
                        "approx":  check_date.strftime("%Y-%m-%d"),
                    })

        # Deduplicar: el muestreo grueso (30d) puede detectar el mismo tránsito
        # varias veces dentro del mismo año. Conservamos el primer disparo.
        seen = {}
        for event in events:
            year = event['approx'][:4]
            key = (event['planet'], event['cycle'], year)
            if key not in seen:
                seen[key] = event

        deduped = list(seen.values())
        deduped.sort(key=lambda x: x['approx'])

        return {"events": deduped}

    except Exception as e:
        raise RuntimeError("cycle calculation error") from e


__all__ = ["forecast_life_cycles"]
