"""
core/mundana.py — Motor de configuraciones planetarias mundanas.

Basado en resultados confirmados de H_mundana_A (commit 51e2bac):
  - Conjunción Júpiter-Saturno: p=5×10⁻⁶, densidad 4.3x baseline
  - Oposición Marte-Saturno: p=0.016, densidad 1.6x baseline

Usa swisseph (ya disponible en el engine) con Moshier como fallback.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import json
import swisseph as swe

# ---------------------------------------------------------------------------
# Configuración de efemérides — mismo patrón que extended_calc.py
# ---------------------------------------------------------------------------

_EPHE_DIR = Path(__file__).resolve().parents[1] / "data" / "ephe"
if (_EPHE_DIR / "sepl_18.se1").exists() or (_EPHE_DIR / "sepl_m54.se1").exists():
    swe.set_ephe_path(str(_EPHE_DIR))
    _FLAGS = swe.FLG_SWIEPH
else:
    _FLAGS = swe.FLG_MOSEPH

_PLANETS = {
    "sun":     swe.SUN,
    "moon":    swe.MOON,
    "mercury": swe.MERCURY,
    "venus":   swe.VENUS,
    "mars":    swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn":  swe.SATURN,
    "neptune": swe.NEPTUNE,
}

# ---------------------------------------------------------------------------
# Configuraciones mundanas + estadísticas empíricas
# ---------------------------------------------------------------------------

CONFIGURATIONS = [
    {
        "type":          "conjunction_JS",
        "label":         "Conjunción Júpiter-Saturno",
        "planets":       ["jupiter", "saturn"],
        "aspect_deg":    0.0,
        "orb":           8.0,
        "p_value":       5e-6,
        "density_ratio": 4.3,
        "significance":  "high",
    },
    {
        "type":          "conjunction_MS",
        "label":         "Conjunción Marte-Saturno",
        "planets":       ["mars", "saturn"],
        "aspect_deg":    0.0,
        "orb":           8.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    {
        "type":          "opposition_MS",
        "label":         "Oposición Marte-Saturno",
        "planets":       ["mars", "saturn"],
        "aspect_deg":    180.0,
        "orb":           8.0,
        "p_value":       0.016,
        "density_ratio": 1.6,
        "significance":  "medium",
    },
    {
        "type":          "conjunction_MJ",
        "label":         "Conjunción Marte-Júpiter",
        "planets":       ["mars", "jupiter"],
        "aspect_deg":    0.0,
        "orb":           8.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "low",
    },
    {
        "type":          "opposition_MJ",
        "label":         "Oposición Marte-Júpiter",
        "planets":       ["mars", "jupiter"],
        "aspect_deg":    180.0,
        "orb":           8.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "low",
    },
]

_STELLIUM_PLANETS   = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "neptune"]
_STELLIUM_MIN_COUNT = 4
_STELLIUM_ORB       = 30.0

_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_positions(year: int, month: int, day: int, hour: float = 12.0) -> dict:
    jd = swe.julday(year, month, day, hour)
    result = {}
    for name, pid in _PLANETS.items():
        pos, _ = swe.calc_ut(jd, pid, _FLAGS)
        result[name] = pos[0]
    return result


def _aspect_distance(lon1: float, lon2: float, aspect_deg: float) -> float:
    diff = abs(lon1 - lon2) % 360
    diff = min(diff, 360 - diff)
    if aspect_deg == 0.0:
        return diff
    return abs(diff - aspect_deg)


def _dt_to_jd(dt: datetime) -> float:
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


def _jd_to_parts(jd: float) -> tuple:
    y, mo, d, h = swe.revjul(jd)
    return (y, mo, d, h)


def _find_exact_date(config: dict, start_jd: float, end_jd: float, step: float = 1.0) -> Optional[str]:
    p1, p2 = config["planets"]
    target  = config["aspect_deg"]
    orb     = config["orb"]

    best_jd, best_dist = None, orb + 1
    jd = start_jd
    while jd <= end_jd:
        pos  = _get_positions(*_jd_to_parts(jd))
        dist = _aspect_distance(pos[p1], pos[p2], target)
        if dist < best_dist:
            best_dist, best_jd = dist, jd
        jd += step

    if best_dist > orb or best_jd is None:
        return None

    lo, hi = best_jd - step, best_jd + step
    for _ in range(20):
        mid = (lo + hi) / 2
        pos  = _get_positions(*_jd_to_parts(mid))
        dist_mid = _aspect_distance(pos[p1], pos[p2], target)
        dist_lo  = _aspect_distance(
            _get_positions(*_jd_to_parts(lo))[p1],
            _get_positions(*_jd_to_parts(lo))[p2],
            target,
        )
        if dist_lo < dist_mid:
            hi = mid
        else:
            lo = mid

    y, mo, d, _ = swe.revjul((lo + hi) / 2)
    return f"{y:04d}-{mo:02d}-{d:02d}"


def _detect_stellium(positions: dict) -> Optional[dict]:
    lons = {p: positions[p] for p in _STELLIUM_PLANETS if p in positions}
    sorted_planets = sorted(lons.items(), key=lambda x: x[1])

    for i in range(len(sorted_planets)):
        base_lon  = sorted_planets[i][1]
        in_window = [
            name for name, lon in sorted_planets
            if (lon - base_lon) % 360 <= _STELLIUM_ORB
        ]
        if len(in_window) >= _STELLIUM_MIN_COUNT:
            span      = max((lons[p] - base_lon) % 360 for p in in_window)
            center    = (base_lon + span / 2) % 360
            sign      = _SIGNS[int(center / 30)]
            return {
                "type":          "stellium",
                "label":         f"Stellium en {sign} ({len(in_window)} planetas)",
                "planets":       in_window,
                "orb":           round(span, 2),
                "exact_date":    None,
                "p_value":       None,
                "density_ratio": None,
                "significance":  "high" if len(in_window) >= 5 else "medium",
            }
    return None


# ---------------------------------------------------------------------------
# API principal
# ---------------------------------------------------------------------------

def get_current_sky() -> dict:
    now = datetime.now(timezone.utc)
    positions = _get_positions(now.year, now.month, now.day, float(now.hour))

    active = []
    for config in CONFIGURATIONS:
        p1, p2 = config["planets"]
        dist = _aspect_distance(positions[p1], positions[p2], config["aspect_deg"])
        if dist <= config["orb"]:
            active.append({
                "type":          config["type"],
                "label":         config["label"],
                "planets":       config["planets"],
                "orb":           round(dist, 2),
                "exact_date":    None,
                "p_value":       config["p_value"],
                "density_ratio": config["density_ratio"],
                "significance":  config["significance"],
            })

    stellium = _detect_stellium(positions)
    if stellium:
        active.append(stellium)

    return {
        "date":                  now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planets":               {k: round(v, 4) for k, v in positions.items()},
        "active_configurations": active,
    }


def get_upcoming_configurations(days_ahead: int = 90) -> list:
    now    = datetime.now(timezone.utc)
    end    = now + timedelta(days=days_ahead)
    now_jd = _dt_to_jd(now)
    end_jd = _dt_to_jd(end)

    results = []
    for config in CONFIGURATIONS:
        p1, p2 = config["planets"]
        step   = 1.0 if "mars" in config["planets"] else 2.0

        jd, in_orb, entry_jd = now_jd, False, None

        while jd <= end_jd:
            pos  = _get_positions(*_jd_to_parts(jd))
            dist = _aspect_distance(pos[p1], pos[p2], config["aspect_deg"])

            if dist <= config["orb"] and not in_orb:
                in_orb, entry_jd = True, jd
            elif dist > config["orb"] and in_orb:
                in_orb    = False
                exact_iso = _find_exact_date(config, entry_jd, jd, step)
                pos_e     = _get_positions(*_jd_to_parts(entry_jd))
                orb_e     = _aspect_distance(pos_e[p1], pos_e[p2], config["aspect_deg"])
                results.append(_build_entry(config, exact_iso, orb_e))
            jd += step

        if in_orb and entry_jd is not None:
            exact_iso = _find_exact_date(config, entry_jd, end_jd, step)
            pos_e     = _get_positions(*_jd_to_parts(entry_jd))
            orb_e     = _aspect_distance(pos_e[p1], pos_e[p2], config["aspect_deg"])
            results.append(_build_entry(config, exact_iso, orb_e))

    results.sort(key=lambda x: x.get("exact_date") or "9999")
    return results


def _build_entry(config: dict, exact_iso: Optional[str], orb: float) -> dict:
    entry: dict = {
        "type":          config["type"],
        "label":         config["label"],
        "planets":       config["planets"],
        "orb":           round(orb, 2),
        "exact_date":    exact_iso,
        "p_value":       config["p_value"],
        "density_ratio": config["density_ratio"],
        "significance":  config["significance"],
    }
    if exact_iso:
        try:
            delta = (
                datetime.strptime(exact_iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                - datetime.now(timezone.utc)
            )
            entry["days_to_exact"] = max(0, delta.days)
        except ValueError:
            entry["days_to_exact"] = None
    else:
        entry["days_to_exact"] = None
    return entry


def get_historical_context(config_type: str, limit: int = 5) -> dict:
    """
    Retorna estadísticas empíricas + eventos de muestra del corpus.
    El corpus (eventos_raw.jsonl) no está en el container de producción,
    así que devuelve los datos estadísticos hardcodeados y una lista vacía
    si el archivo no existe.
    """
    _STATS = {
        "conjunction_JS": {"density_ratio": 4.3,  "p_value": 5e-6},
        "opposition_MS":  {"density_ratio": 1.6,  "p_value": 0.016},
    }
    stats = _STATS.get(config_type, {"density_ratio": None, "p_value": None})

    # El corpus no está disponible en Cloud Run — retorna vacío, no error
    return {
        "config_type":   config_type,
        "sample_events": [],
        "density_ratio": stats["density_ratio"],
        "p_value":       stats["p_value"],
    }
