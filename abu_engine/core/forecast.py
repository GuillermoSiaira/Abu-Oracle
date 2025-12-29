# -*- coding: utf-8 -*-

from core.coords import get_planet_positions
from core.aspects import aspect_between
from core.scoring import compute_score
from datetime import datetime, timedelta
from typing import List, Dict, Any
from core.chart import EphemerisSingleton

def forecast_for_locations(date_utc, lat, lon):
    # ...existing code...
    natal_positions = {"sun": 103.2, "moon": 45.8}
    current_positions = get_planet_positions(date_utc, lat, lon)
    aspects = []
    for natal_name, natal_lon in natal_positions.items():
        for planet, lon_val in current_positions.items():
            asp, diff = aspect_between(lon_val, natal_lon, orb=6)
            if asp:
                aspects.append({"planet": planet, "type": asp, "to": natal_name, "orb_deg": diff})
    score = compute_score(aspects)
    return {"score": score, "aspects": aspects}


# ...existing code...
def get_planet_positions(date_utc, lat, lon):
    """
    Devuelve las posiciones eclípticas de los planetas para una fecha y ubicación.
    """
    from skyfield.api import load, Topos
    # Use shared ephemeris loader that ensures local file and downloads if missing
    planets = EphemerisSingleton()
    ts = load.timescale()
    t = ts.from_datetime(date_utc)
    earth = planets['earth']
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    planet_names = ['sun', 'moon', 'mercury barycenter', 'venus barycenter', 'mars barycenter', 'jupiter barycenter', 'saturn barycenter']
    positions = {}
    for name in planet_names:
        pos = observer.at(t).observe(planets[name])
        _, lon_val, _ = pos.ecliptic_latlon()
        positions[name.split()[0] if ' ' in name else name.capitalize()] = lon_val.degrees
    return positions
# ...existing code...

def forecast_timeseries(birth_dt, lat, lon, start_dt, end_dt, step='1d', horizon='year'):
    """
    Calcula F(t) cada step reutilizando el scoring actual.
    """
    if step.endswith('d'):
        step_days = int(step[:-1])
        delta = timedelta(days=step_days)
    else:
        delta = timedelta(days=1)
    times = []
    t = start_dt
    while t <= end_dt:
        times.append(t)
        t += delta
    natal_positions = {"sun": 103.2, "moon": 45.8}  # Simulación
    series = []
    for t in times:
        current_positions = get_planet_positions(t, lat, lon)
        aspects = []
        for natal_name, natal_lon in natal_positions.items():
            for planet, lon_val in current_positions.items():
                asp, diff = aspect_between(lon_val, natal_lon, orb=6)
                if asp:
                    aspects.append({"planet": planet, "type": asp, "to": natal_name, "orb_deg": diff})
        score = compute_score(aspects)
        series.append({"t": t.strftime("%Y-%m-%d"), "F": round(score, 4)})
    peaks = detect_peaks(series)
    return {"timeseries": series, "peaks": peaks}

__all__ = ["forecast_timeseries", "detect_peaks"]

def detect_peaks(series: List[Dict[str, Any]], window: int = 3, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Detecta máximos y mínimos locales comparando vecinos.
    """
    peaks = []
    vals = [point["F"] for point in series]
    for i in range(window, len(series) - window):
        val = vals[i]
        left = vals[i-window:i]
        right = vals[i+1:i+window+1]
        if all(val > v for v in left + right):
            peaks.append({"t": series[i]["t"], "F": val, "kind": "peak"})
        if all(val < v for v in left + right):
            peaks.append({"t": series[i]["t"], "F": val, "kind": "valley"})
    # Top K por valor absoluto
    peaks = sorted(peaks, key=lambda x: abs(x["F"]), reverse=True)[:top_k]
    return peaks

