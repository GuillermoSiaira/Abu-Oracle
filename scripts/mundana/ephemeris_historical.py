"""
ephemeris_historical.py — Posiciones planetarias históricas vía pyswisseph.

Usa Moshier (integración numérica, sin archivos externos) como fuente primaria.
Cobertura: año -3000 a +3000, precisión < 1 arcsec — suficiente para orbe ±8°.

Upgrade opcional: si data/ephe/ contiene archivos DE431 (sepl_m54.se1, semo_m54.se1),
el script los usa automáticamente para mayor precisión histórica.

Para descargar DE431 manualmente (archivos de ~180 MB c/u):
  https://www.astro.com/ftp/swisseph/ephe/sepl_m54.se1
  https://www.astro.com/ftp/swisseph/ephe/semo_m54.se1

NO tocar: abu_engine/, harmony/, field_v3.py, angularity.py
"""

from pathlib import Path

import swisseph as swe

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
EPHE_DIR = REPO_ROOT / "data" / "ephe"

# Archivos DE431 que indicarían que el upgrade está disponible
_DE431_MARKER = "sepl_m54.se1"

# Planetas que nos interesan (IDs swisseph)
PLANETS = {
    "sun":     swe.SUN,
    "moon":    swe.MOON,
    "mercury": swe.MERCURY,
    "venus":   swe.VENUS,
    "mars":    swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn":  swe.SATURN,
    "uranus":  swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto":   swe.PLUTO,
}

# Modo de cálculo — se resuelve una vez al importar
_USE_DE431 = (EPHE_DIR / _DE431_MARKER).exists()

if _USE_DE431:
    swe.set_ephe_path(str(EPHE_DIR))
    _FLAGS = swe.FLG_SWIEPH   # Swiss Ephemeris (DE431)
    _EPHE_SOURCE = "DE431"
else:
    _FLAGS = swe.FLG_MOSEPH   # Moshier — sin archivos externos
    _EPHE_SOURCE = "Moshier"


# ---------------------------------------------------------------------------
# Conversión fecha → Día Juliano
# ---------------------------------------------------------------------------

def _date_to_jd(year: int, month: int, day: int, hour: float = 12.0) -> float:
    """
    Convierte fecha a Día Juliano.
    Usa calendario juliano para fechas anteriores a 1582-10-15.
    """
    if (year, month, day) < (1582, 10, 15):
        cal = swe.JUL_CAL
    else:
        cal = swe.GREG_CAL
    return swe.julday(year, month, day, hour, cal)


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def get_planet_positions(year: int, month: int, day: int, hour: float = 12.0) -> dict:
    """
    Calcula longitudes eclípticas de los planetas principales para una fecha.

    Parámetros
    ----------
    year  : año (puede ser negativo para AEC; año 0 = 1 AEC en astronomía)
    month : mes (1-12)
    day   : día (1-31)
    hour  : hora UT decimal (default: mediodía = 12.0)

    Retorna
    -------
    dict con claves: 'sun', 'moon', 'mercury', 'venus', 'mars',
                     'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'
    Valores: longitud eclíptica en grados [0, 360)
    """
    jd = _date_to_jd(year, month, day, hour)
    result = {}
    for name, planet_id in PLANETS.items():
        pos, _ = swe.calc_ut(jd, planet_id, _FLAGS)
        result[name] = pos[0]  # longitud eclíptica
    return result


# ---------------------------------------------------------------------------
# Utilidades de aspectos
# ---------------------------------------------------------------------------

def angular_distance(lon1: float, lon2: float) -> float:
    """Distancia angular mínima entre dos longitudes eclípticas [0, 180]."""
    diff = abs(lon1 - lon2) % 360
    return min(diff, 360 - diff)


def is_conjunction(lon1: float, lon2: float, orb: float = 8.0) -> bool:
    """True si los dos puntos están dentro del orbe de conjunción."""
    return angular_distance(lon1, lon2) <= orb


def is_opposition(lon1: float, lon2: float, orb: float = 8.0) -> bool:
    """True si los dos puntos están dentro del orbe de oposición."""
    diff = abs(lon1 - lon2) % 360
    dist_from_opp = min(abs(diff - 180), abs(diff + 180 - 360))
    return dist_from_opp <= orb


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== ephemeris_historical.py — test ===\n")
    print(f"Fuente de efemérides: {_EPHE_SOURCE}")
    if _USE_DE431:
        print(f"  Path: {EPHE_DIR}")
    else:
        print("  Moshier (integración numérica, sin archivos externos)")
        print("  Precisión < 1 arcsec para planetas exteriores — OK para orbe 8°")
    print()

    # Test canónico: 1347-10-01
    # Contexto histórico: La Peste Negra llegó a Europa en 1347.
    # Gran Conjunción Júpiter-Saturno anterior: 1345-03 en Acuario ~17°
    year, month, day = 1347, 10, 1
    print(f"Calculando posiciones para {year}-{month:02d}-{day:02d} (mediodía UT) …\n")

    positions = get_planet_positions(year, month, day)

    print(f"  Sol     : {positions['sun']:.4f}°")
    print(f"  Júpiter : {positions['jupiter']:.4f}°")
    print(f"  Saturno : {positions['saturn']:.4f}°")
    print(f"  Marte   : {positions['mars']:.4f}°")
    print()

    sep_js = angular_distance(positions["jupiter"], positions["saturn"])
    conj_js = is_conjunction(positions["jupiter"], positions["saturn"])
    print(f"  Separación Júpiter-Saturno : {sep_js:.2f}°  (conj activa orbe 8°: {conj_js})")

    opp_ms = is_opposition(positions["mars"], positions["saturn"])
    diff = abs(positions["mars"] - positions["saturn"]) % 360
    dist_opp = min(abs(diff - 180), abs(diff + 180 - 360))
    print(f"  Marte-Saturno dist. opos.  : {dist_opp:.2f}°  (opos activa orbe 8°: {opp_ms})")

    print()

    # Test cobertura: extremos del corpus mundana (año 8 y 2069)
    print("Test cobertura corpus mundana:")
    pos8 = get_planet_positions(8, 1, 1)
    print(f"  Año 8 CE   — Júpiter: {pos8['jupiter']:.2f}°  Saturno: {pos8['saturn']:.2f}°")
    pos2069 = get_planet_positions(2069, 12, 31)
    print(f"  Año 2069   — Júpiter: {pos2069['jupiter']:.2f}°  Saturno: {pos2069['saturn']:.2f}°")

    print("\nTest completado OK.")
