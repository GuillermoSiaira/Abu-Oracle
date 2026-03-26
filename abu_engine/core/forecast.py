# -*- coding: utf-8 -*-

from core.coords import get_planet_positions
from core.aspects import aspect_between
from core.transits import calculate_transits as _calc_transits
from core.scoring import compute_score
from datetime import datetime, timedelta
from typing import List, Dict, Any
from core.chart import EphemerisSingleton

# Module-level timescale cache — avoids repeated disk reads (each call to
# load.timescale() reads leap-second data, adding ~200–500 ms per call).
_ts_cache = None

def _get_timescale():
    global _ts_cache
    if _ts_cache is None:
        from skyfield.api import load
        _ts_cache = load.timescale()
    return _ts_cache


def get_planet_positions_batch(dates_utc: list, lat: float, lon: float) -> List[Dict[str, float]]:
    """
    Vectorized: compute ecliptic longitudes for all dates in a single skyfield call per planet.
    Returns list of dicts (one per date), each mapping planet name → longitude in degrees.
    Reduces N_dates × N_planets skyfield calls to N_planets calls.
    """
    from skyfield.api import Topos
    planets_loader = EphemerisSingleton()
    ts = _get_timescale()

    t_array = ts.from_datetimes(dates_utc)
    earth = planets_loader['earth']
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)

    planet_names = [
        'sun', 'moon', 'mercury barycenter', 'venus barycenter',
        'mars barycenter', 'jupiter barycenter', 'saturn barycenter',
    ]

    # Initialize result list
    results: List[Dict[str, float]] = [{} for _ in dates_utc]

    for name in planet_names:
        pos = observer.at(t_array).observe(planets_loader[name])
        _, lon_vals, _ = pos.ecliptic_latlon()
        key = name.split()[0].capitalize() if ' ' in name else name.capitalize()
        for i, lon_val in enumerate(lon_vals.degrees):
            results[i][key] = lon_val

    return results


def get_planet_positions(date_utc, lat, lon):
    """
    Single-date wrapper (used by non-forecast callers).
    Uses cached timescale to avoid disk reads.
    """
    from skyfield.api import Topos
    planets_loader = EphemerisSingleton()
    ts = _get_timescale()
    t = ts.from_datetime(date_utc)
    earth = planets_loader['earth']
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    planet_names = ['sun', 'moon', 'mercury barycenter', 'venus barycenter', 'mars barycenter', 'jupiter barycenter', 'saturn barycenter']
    positions = {}
    for name in planet_names:
        pos = observer.at(t).observe(planets_loader[name])
        _, lon_val, _ = pos.ecliptic_latlon()
        key = name.split()[0].capitalize() if ' ' in name else name.capitalize()
        positions[key] = lon_val.degrees
    return positions


def forecast_for_locations(date_utc, lat, lon):
    natal_positions = {"sun": 103.2, "moon": 45.8}  # TODO: fix natal_positions — requiere birth_dt como parámetro adicional
    current_positions = get_planet_positions(date_utc, lat, lon)
    aspects = []
    for natal_name, natal_lon in natal_positions.items():
        for planet, lon_val in current_positions.items():
            asp, diff = aspect_between(lon_val, natal_lon, orb=6)
            if asp:
                aspects.append({"planet": planet, "type": asp, "to": natal_name, "orb_deg": diff})
    score = compute_score(aspects)
    return {"score": score, "aspects": aspects}


# Max date range to prevent timeout — requests larger than this are capped.
_MAX_FORECAST_DAYS = 90


def forecast_timeseries(birth_dt, lat, lon, start_dt, end_dt, step='1d', horizon='year',
                        natal_positions: dict | None = None):
    """
    Calcula F(t) cada step usando posiciones vectorizadas (batch skyfield).
    Rango máximo: _MAX_FORECAST_DAYS días para evitar timeout.
    """
    if step.endswith('d'):
        step_days = int(step[:-1])
        delta = timedelta(days=step_days)
    else:
        delta = timedelta(days=1)

    # Cap range to avoid timeout
    max_end = start_dt + timedelta(days=_MAX_FORECAST_DAYS)
    if end_dt > max_end:
        end_dt = max_end

    times = []
    t = start_dt
    while t <= end_dt:
        times.append(t)
        t += delta

    if not times:
        return {"timeseries": [], "peaks": []}

    if natal_positions is None:
        natal_positions = get_planet_positions(birth_dt, lat, lon)

    # Vectorized batch computation — one skyfield call per planet across all dates
    all_positions = get_planet_positions_batch(times, lat, lon)

    series = []
    for i, t in enumerate(times):
        current_positions = all_positions[i]
        natal_list   = [{"name": k, "longitude": v} for k, v in natal_positions.items()]
        transit_list = [{"name": k, "longitude": v, "speed": 0} for k, v in current_positions.items()]
        _custom_orbs = {asp: 6.0 for asp in ["conjunction", "sextile", "square", "trine", "opposition"]}
        raw_transits = _calc_transits(natal_list, transit_list, orbs=_custom_orbs)
        aspects = [{"planet": t["transit_planet"], "type": t["aspect"],
                    "to": t["natal_planet"], "orb_deg": t["orb"]} for t in raw_transits]
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
    peaks = sorted(peaks, key=lambda x: abs(x["F"]), reverse=True)[:top_k]
    return peaks
