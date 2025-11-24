# -*- coding: utf-8 -*-

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from skyfield.api import load, Topos
from threading import Lock
from pathlib import Path
import urllib.request
import logging
from core.aspects import aspect_between
from core.cache import cache_ephemeris_positions

# Singleton para efemérides
class EphemerisSingleton:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        """
        Ensure the JPL DE440s ephemeris is available locally and load it.

        Changes introduced:
        - Create a local "data" directory (adjacent to this module) if missing.
        - Check for data/de440s.bsp, and download from NAIF if it's not present.
        - Load the local BSP file via Skyfield's load().
        - Print clear messages on download success/failure.
        """
        with cls._lock:
            if cls._instance is None:
                # Resolve data directory next to the package root (…/abu_engine/data)
                base_dir = Path(__file__).resolve().parent.parent
                data_dir = base_dir / "data"
                data_dir.mkdir(parents=True, exist_ok=True)

                bsp_path = data_dir / "de440s.bsp"
                if not bsp_path.exists():
                    url = (
                        "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp"
                    )
                    try:
                        print(f"[Abu] Downloading ephemeris: {url} -> {bsp_path}")
                        urllib.request.urlretrieve(url, bsp_path.as_posix())
                        print(f"[Abu] Ephemeris downloaded to {bsp_path}")
                    except Exception as e:
                        # Log and re-raise so warm-up can report it; runtime may try again later
                        logging.warning(f"[Abu] Failed to download ephemeris: {e}")
                        raise

                # Load the local BSP file
                cls._instance = load(bsp_path.as_posix())
            return cls._instance

def normalize_lon(lon: float) -> float:
    return lon % 360.0

def get_sign(lon: float) -> str:
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    idx = int(normalize_lon(lon) // 30)
    return signs[idx]

class PlanetDTO(BaseModel):
    name: str
    lon: float
    sign: str
    house: Optional[int] = None

class AspectDTO(BaseModel):
    a: str
    b: str
    type: str
    orb: float
    angle: float

class ChartDTO(BaseModel):
    datetime: str
    location: Dict[str, float]
    planets: List[PlanetDTO]
    aspects: List[AspectDTO]

SUPPORTED_ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180
}
ASPECT_ORB = 6.0

def _compute_planet_positions(date: datetime) -> Dict[str, float]:
    """Inner computation of planetary longitudes (ecliptic) for caching."""
    planets = EphemerisSingleton()
    ts = load.timescale()
    t = ts.from_datetime(date)
    earth = planets['earth']
    bodies = {
        'Sun': planets['sun'],
        'Moon': planets['moon'],
        'Mercury': planets['mercury barycenter'],
        'Venus': planets['venus barycenter'],
        'Mars': planets['mars barycenter'],
        'Jupiter': planets['jupiter barycenter'],
        'Saturn': planets['saturn barycenter'],
        'Uranus': planets['uranus barycenter'],
        'Neptune': planets['neptune barycenter'],
        'Pluto': planets['pluto barycenter']
    }
    positions: Dict[str, float] = {}
    for name, body in bodies.items():
        pos = earth.at(t).observe(body)
        _, lon_val, _ = pos.ecliptic_latlon()
        lon_norm = normalize_lon(lon_val.degrees)
        positions[name] = lon_norm
    return positions


def chart_json(lat: float, lon: float, date: datetime) -> ChartDTO:
    # Use cache for planetary positions
    planet_positions = cache_ephemeris_positions(
        date,
        lat,
        lon,
        lambda: _compute_planet_positions(date)
    )
    planet_dtos = [
        PlanetDTO(name=name, lon=lon_val, sign=get_sign(lon_val), house=None)
        for name, lon_val in planet_positions.items()
    ]
    # Compute aspects from cached positions
    aspects: List[AspectDTO] = []
    names = list(planet_positions.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a_name, b_name = names[i], names[j]
            angle = abs(planet_positions[a_name] - planet_positions[b_name])
            angle = min(angle, 360 - angle)
            for asp_type, asp_angle in SUPPORTED_ASPECTS.items():
                orb = abs(angle - asp_angle)
                if orb <= ASPECT_ORB:
                    aspects.append(
                        AspectDTO(
                            a=a_name,
                            b=b_name,
                            type=asp_type,
                            orb=round(orb, 2),
                            angle=round(angle, 2),
                        )
                    )
    return ChartDTO(
        datetime=date.isoformat(),
        location={"lat": lat, "lon": lon},
        planets=planet_dtos,
        aspects=aspects,
    )


def find_solar_return(birth_date: datetime, lat: float, lon: float, year: Optional[int] = None) -> datetime:
    """
    Finds the exact datetime when the Sun returns to its natal longitude.
    
    Args:
        birth_date: Natal birth datetime
        lat: Latitude for the solar return location
        lon: Longitude for the solar return location
        year: Target year for solar return (defaults to current year)
    
    Returns:
        Datetime of solar return
    """
    from datetime import datetime as dt, timedelta, timezone
    
    planets = EphemerisSingleton()
    ts = load.timescale()
    earth = planets['earth']
    sun = planets['sun']
    
    # Get natal Sun longitude
    t_birth = ts.from_datetime(birth_date)
    natal_sun_pos = earth.at(t_birth).observe(sun)
    _, natal_sun_lon, _ = natal_sun_pos.ecliptic_latlon()
    natal_lon = normalize_lon(natal_sun_lon.degrees)
    
    # Determine target year
    if year is None:
        year = dt.now().year
    
    # Start search around birthday in target year (use UTC-aware datetimes)
    search_start = dt(year, birth_date.month, birth_date.day, 0, 0, 0, tzinfo=timezone.utc)
    
    # Binary search for exact return time (within 1 day window)
    start_time = search_start - timedelta(days=2)
    end_time = search_start + timedelta(days=2)
    
    # Iterative refinement
    for _ in range(20):  # 20 iterations gives ~1 minute precision
        mid_time = start_time + (end_time - start_time) / 2
        
        t_mid = ts.from_datetime(mid_time)
        current_pos = earth.at(t_mid).observe(sun)
        _, current_lon, _ = current_pos.ecliptic_latlon()
        current_lon_norm = normalize_lon(current_lon.degrees)
        
        # Calculate angular difference (accounting for 360° wrap)
        diff = current_lon_norm - natal_lon
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        
        if abs(diff) < 0.001:  # Close enough (~3.6 seconds of arc)
            return mid_time
        
        # Adjust search window
        if diff < 0:
            start_time = mid_time
        else:
            end_time = mid_time
    
    # Return best approximation
    return start_time + (end_time - start_time) / 2


def solar_return_chart(birth_date: datetime, lat: float, lon: float, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculates a Solar Return chart for a given birth date and location.
    
    Args:
        birth_date: Natal birth datetime
        lat: Latitude for the solar return location
        lon: Longitude for the solar return location  
        year: Target year for solar return (defaults to current year)
    
    Returns:
        Dictionary with solar return datetime, planets, aspects, and score summary
    """
    from core.scoring import compute_score
    
    # Find exact solar return time
    sr_datetime = find_solar_return(birth_date, lat, lon, year)
    
    # Calculate chart for that moment
    chart = chart_json(lat, lon, sr_datetime)
    
    # Compute score summary (reuse scoring logic)
    aspects_for_score = [
        {
            "type": asp.type,
            "planet": asp.a,  # Use first planet for scoring
            "orb_deg": asp.orb
        }
        for asp in chart.aspects
    ]
    
    score = compute_score(aspects_for_score) if aspects_for_score else 0.0
    
    return {
        "solar_return_datetime": sr_datetime.isoformat(),
        "birth_date": birth_date.isoformat(),
        "location": {"lat": lat, "lon": lon},
        "year": year or sr_datetime.year,
        "planets": [p.model_dump() for p in chart.planets],
        "aspects": [a.model_dump() for a in chart.aspects],
        "score_summary": {
            "total_score": score,
            "num_aspects": len(chart.aspects),
            "interpretation": "favorable" if score > 0 else "challenging" if score < 0 else "neutral"
        }
    }