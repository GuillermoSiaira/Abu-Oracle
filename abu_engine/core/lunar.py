"""
Módulo lunar: fase actual, próximas lunaciones, aspecto Sol-Luna.
"""

try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:
    SWE_AVAILABLE = False

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from .houses_swiss import calculate_houses, longitude_to_sign_degree, HOUSE_SYSTEM_PLACIDUS
from .transits import calculate_transits


# J2000.0 como ancla para conversión JD ↔ datetime
_J2000_JD = 2451545.0
_J2000_DT = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

# ── Eclipse type bitmasks (Swiss Ephemeris swephexp.h) ────────────────────────
_SE_ECL_TOTAL         = 4    # solar total + lunar total
_SE_ECL_ANNULAR       = 8    # solar annular
_SE_ECL_PARTIAL       = 16   # solar partial + lunar partial
_SE_ECL_ANNULAR_TOTAL = 32   # solar hybrid (annular-total)
_SE_ECL_PENUMBRAL     = 64   # lunar penumbral


def _solar_eclipse_type(retval: int) -> str:
    if retval & _SE_ECL_ANNULAR_TOTAL:
        return "hybrid"
    if retval & _SE_ECL_TOTAL:
        return "total"
    if retval & _SE_ECL_ANNULAR:
        return "annular"
    return "partial"


def _lunar_eclipse_type(retval: int) -> str:
    if retval & _SE_ECL_TOTAL:
        return "total"
    if retval & _SE_ECL_PARTIAL:
        return "partial"
    return "penumbral"


def _find_next_solar_eclipse(
    dt: datetime, birth_dt: datetime, lat: float, natal_lon: float
) -> Optional[Dict[str, Any]]:
    """
    Próximo eclipse solar desde dt usando swe.sol_eclipse_when_glob().
    Retorna { dt, type, lon, sign, natal_house } o None si falla.
    """
    try:
        jd_start = _to_jd(dt) + 1.0
        retval, tret = swe.sol_eclipse_when_glob(jd_start, 0)
        jd_max = tret[0]
        if jd_max <= 0:
            return None
        eclipse_dt = _from_jd(jd_max)
        sun_lon = _planet_lon(jd_max, swe.SUN)
        sign, _ = longitude_to_sign_degree(sun_lon)
        return {
            "dt": eclipse_dt.isoformat(),
            "type": _solar_eclipse_type(retval),
            "lon": round(sun_lon, 4),
            "sign": sign,
            "natal_house": _natal_house(sun_lon, birth_dt, lat, natal_lon),
        }
    except Exception:
        return None


def _find_next_lunar_eclipse(
    dt: datetime, birth_dt: datetime, lat: float, natal_lon: float
) -> Optional[Dict[str, Any]]:
    """
    Próximo eclipse lunar desde dt usando swe.lun_eclipse_when().
    Retorna { dt, type, lon, sign, natal_house } o None si falla.
    """
    try:
        jd_start = _to_jd(dt) + 1.0
        retval, tret = swe.lun_eclipse_when(jd_start, 0)
        jd_max = tret[0]
        if jd_max <= 0:
            return None
        eclipse_dt = _from_jd(jd_max)
        moon_lon = _planet_lon(jd_max, swe.MOON)
        sign, _ = longitude_to_sign_degree(moon_lon)
        return {
            "dt": eclipse_dt.isoformat(),
            "type": _lunar_eclipse_type(retval),
            "lon": round(moon_lon, 4),
            "sign": sign,
            "natal_house": _natal_house(moon_lon, birth_dt, lat, natal_lon),
        }
    except Exception:
        return None


_PHASE_BANDS = [
    (0.0,   22.5,  "New Moon"),
    (22.5,  67.5,  "Waxing Crescent"),
    (67.5,  112.5, "First Quarter"),
    (112.5, 157.5, "Waxing Gibbous"),
    (157.5, 202.5, "Full Moon"),
    (202.5, 247.5, "Waning Gibbous"),
    (247.5, 292.5, "Last Quarter"),
    (292.5, 360.0, "Waning Crescent"),
]


def _to_jd(dt: datetime) -> float:
    dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def _from_jd(jd: float) -> datetime:
    return _J2000_DT + timedelta(days=jd - _J2000_JD)


def _planet_lon(jd: float, body: int) -> float:
    pos, _ = swe.calc_ut(jd, body)
    return float(pos[0]) % 360.0


def _elongation(jd: float) -> float:
    """Separación Moon − Sun en [0, 360)."""
    return (_planet_lon(jd, swe.MOON) - _planet_lon(jd, swe.SUN)) % 360.0


def _phase_name(elong: float) -> str:
    for lo, hi, name in _PHASE_BANDS:
        if lo <= elong < hi:
            return name
    return "Waning Crescent"


def _find_next_lunation(dt: datetime, target: float) -> datetime:
    """
    Próxima fecha en que elongation(Moon-Sun) == target (0=Luna Nueva, 180=Luna Llena).
    Escaneo cada 6h + bisección para precisión ~1 min.
    Arranca 12h adelante para evitar la posición actual si ya estamos cerca del target.
    """
    step = 0.25  # días (6 horas)
    jd = _to_jd(dt) + 0.5  # +12h para saltear posición actual

    # Para target=0 (Luna Nueva), signed_dist tiene un falso cruce de cero en
    # elongation=180° (Luna Llena) porque (180-0)%360=180 cruza el umbral.
    # Si la elongación actual es < 180°, saltamos hasta pasarla.
    if target == 0.0:
        e_now = _elongation(jd)
        if e_now < 180.0:
            # días hasta 180° a velocidad media 13.18°/día + 1 día de margen
            jd += (180.0 - e_now) / 13.18 + 1.0

    def signed_dist(jd_x: float) -> float:
        e = _elongation(jd_x)
        d = (e - target) % 360.0
        return d if d <= 180.0 else d - 360.0

    # Escaneo hacia adelante — máx 60 días
    for _ in range(60 * 4):
        d0 = signed_dist(jd)
        d1 = signed_dist(jd + step)
        if d0 * d1 <= 0:
            break
        jd += step

    # Bisección — 20 iteraciones → precisión ~0.001° ≈ 5 segundos
    lo, hi = jd, jd + step
    for _ in range(20):
        mid = (lo + hi) / 2.0
        if signed_dist(lo) * signed_dist(mid) <= 0:
            hi = mid
        else:
            lo = mid

    return _from_jd((lo + hi) / 2.0)


def _natal_house(lon: float, birth_dt: datetime, lat: float, natal_lon: float) -> int:
    """Casa natal en la que cae una longitud dada."""
    houses = calculate_houses(birth_dt, lat, natal_lon, HOUSE_SYSTEM_PLACIDUS)
    cusps = [c % 360.0 for c in houses["cusps"]]
    lon = lon % 360.0
    for i in range(12):
        s = cusps[i]
        e = cusps[(i + 1) % 12]
        if e > s:
            if s <= lon < e:
                return i + 1
        else:  # cruce 0°/360°
            if lon >= s or lon < e:
                return i + 1
    return 1


def calculate_lunar_data(
    birth_dt: datetime,
    lat: float,
    lon: float,
    query_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Fase lunar actual, aspecto Sol-Luna y próximas lunaciones para un nativo.

    Args:
        birth_dt:  Datetime de nacimiento (UTC)
        lat:       Latitud natal
        lon:       Longitud natal
        query_dt:  Momento de consulta (UTC). Si None → ahora.

    Returns:
        dict con sun, moon, phase, sun_moon_aspect, next_new_moon, next_full_moon
    """
    if not SWE_AVAILABLE:
        raise RuntimeError("pyswisseph no disponible")

    if query_dt is None:
        query_dt = datetime.now(timezone.utc)

    jd = _to_jd(query_dt)
    sun_lon  = _planet_lon(jd, swe.SUN)
    moon_lon = _planet_lon(jd, swe.MOON)

    sun_sign,  sun_deg  = longitude_to_sign_degree(sun_lon)
    moon_sign, moon_deg = longitude_to_sign_degree(moon_lon)

    elongation = (moon_lon - sun_lon) % 360.0

    # Aspecto Sol-Luna vía calculate_transits (Sol=natal, Luna=tránsito)
    raw = calculate_transits(
        natal_planets=[{"name": "Sun", "longitude": sun_lon}],
        transit_planets=[{"name": "Moon", "longitude": moon_lon, "speed": 13.0}],
    )
    aspect_data: Dict[str, Any] = {"type": None, "orb": None, "applying": None}
    if raw:
        t = raw[0]
        aspect_data = {"type": t["aspect"], "orb": t["orb"], "applying": t["applying"]}

    # Próximas lunaciones
    next_new  = _find_next_lunation(query_dt, 0.0)
    next_full = _find_next_lunation(query_dt, 180.0)

    new_lon   = _planet_lon(_to_jd(next_new),  swe.MOON)
    full_lon  = _planet_lon(_to_jd(next_full), swe.MOON)
    new_sign,  _ = longitude_to_sign_degree(new_lon)
    full_sign, _ = longitude_to_sign_degree(full_lon)

    # Próximos eclipses
    next_solar_eclipse = _find_next_solar_eclipse(query_dt, birth_dt, lat, lon)
    next_lunar_eclipse = _find_next_lunar_eclipse(query_dt, birth_dt, lat, lon)

    return {
        "sun": {
            "lon": round(sun_lon, 4),
            "sign": sun_sign,
            "sign_degree": round(sun_deg, 4),
        },
        "moon": {
            "lon": round(moon_lon, 4),
            "sign": moon_sign,
            "sign_degree": round(moon_deg, 4),
            "sign_pct": round(moon_deg / 30.0 * 100.0, 1),
        },
        "phase": {
            "separation": round(elongation, 4),
            "name": _phase_name(elongation),
            "pct": round(elongation / 360.0 * 100.0, 1),
        },
        "sun_moon_aspect": aspect_data,
        "next_new_moon": {
            "dt": next_new.isoformat(),
            "lon": round(new_lon, 4),
            "sign": new_sign,
            "natal_house": _natal_house(new_lon, birth_dt, lat, lon),
        },
        "next_full_moon": {
            "dt": next_full.isoformat(),
            "lon": round(full_lon, 4),
            "sign": full_sign,
            "natal_house": _natal_house(full_lon, birth_dt, lat, lon),
        },
        "next_solar_eclipse": next_solar_eclipse,
        "next_lunar_eclipse": next_lunar_eclipse,
    }
