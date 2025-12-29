# -*- coding: utf-8 -*-
from skyfield.api import load, Topos
from pathlib import Path

ts = load.timescale()

# Carga el archivo local directamente
path = Path(__file__).parent.parent / "data" / "de440s.bsp"
planets = load(path.as_posix())

def get_planet_positions(date_utc, lat, lon, elev=0):
    earth = planets["earth"]
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elev)
    t = ts.from_datetime(date_utc)
    result = {}
    for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter barycenter", "saturn barycenter"]:
        astrometric = observer.observe(planets[name]).apparent()
        lon, lat_ecl, dist = astrometric.ecliptic_latlon()
        result[name] = float(lon.degrees)
    return result
