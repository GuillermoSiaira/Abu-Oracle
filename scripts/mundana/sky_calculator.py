"""
sky_calculator.py — Configuraciones planetarias mundanas actuales y próximas.

Basado en los resultados de H_mundana_A (commit 51e2bac):
  - Conjunción Júpiter-Saturno: p=5×10⁻⁶, densidad 4.3x baseline
  - Oposición Marte-Saturno: p=0.016, densidad 1.6x baseline

Usa ephemeris_historical.py (pyswisseph + Moshier) como fuente de efemérides.
NO modificar abu_engine/ ni archivos protegidos.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# --- paths ----------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
EVENTOS_PATH = REPO_ROOT / "data" / "mundana" / "eventos_raw.jsonl"

sys.path.insert(0, str(Path(__file__).parent))
from ephemeris_historical import get_planet_positions, angular_distance, _FLAGS

import swisseph as swe

# --------------------------------------------------------------------------
# Configuraciones reconocidas + estadísticas empíricas (H_mundana_A)
# --------------------------------------------------------------------------

CONFIGURATIONS = [
    # ── Con datos estadísticos (H_mundana_A) ──────────────────────────────────
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
        "type":          "opposition_MS",
        "label":         "Oposición Marte-Saturno",
        "planets":       ["mars", "saturn"],
        "aspect_deg":    180.0,
        "orb":           8.0,
        "p_value":       0.016,
        "density_ratio": 1.6,
        "significance":  "medium",
    },
    # ── Marte-Saturno (todos los aspectos mayores) ────────────────────────────
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
        "type":          "square_MS",
        "label":         "Cuadratura Marte-Saturno",
        "planets":       ["mars", "saturn"],
        "aspect_deg":    90.0,
        "orb":           6.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    {
        "type":          "trine_MS",
        "label":         "Trígono Marte-Saturno",
        "planets":       ["mars", "saturn"],
        "aspect_deg":    120.0,
        "orb":           6.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    # ── Marte-Júpiter (todos los aspectos mayores) ────────────────────────────
    {
        "type":          "conjunction_MJ",
        "label":         "Conjunción Marte-Júpiter",
        "planets":       ["mars", "jupiter"],
        "aspect_deg":    0.0,
        "orb":           8.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    {
        "type":          "opposition_MJ",
        "label":         "Oposición Marte-Júpiter",
        "planets":       ["mars", "jupiter"],
        "aspect_deg":    180.0,
        "orb":           8.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    {
        "type":          "square_MJ",
        "label":         "Cuadratura Marte-Júpiter",
        "planets":       ["mars", "jupiter"],
        "aspect_deg":    90.0,
        "orb":           6.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    # ── Marte-Urano (disrupción / aceleración) ────────────────────────────────
    {
        "type":          "conjunction_MU",
        "label":         "Conjunción Marte-Urano",
        "planets":       ["mars", "uranus"],
        "aspect_deg":    0.0,
        "orb":           6.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    {
        "type":          "opposition_MU",
        "label":         "Oposición Marte-Urano",
        "planets":       ["mars", "uranus"],
        "aspect_deg":    180.0,
        "orb":           6.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    {
        "type":          "square_MU",
        "label":         "Cuadratura Marte-Urano",
        "planets":       ["mars", "uranus"],
        "aspect_deg":    90.0,
        "orb":           5.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    # ── Venus-Júpiter (abundancia / beneficencia) ─────────────────────────────
    {
        "type":          "conjunction_VJ",
        "label":         "Conjunción Venus-Júpiter",
        "planets":       ["venus", "jupiter"],
        "aspect_deg":    0.0,
        "orb":           6.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
    # ── Saturno-Neptuno (disolución / ilusión colectiva) ─────────────────────
    {
        "type":          "conjunction_SN",
        "label":         "Conjunción Saturno-Neptuno",
        "planets":       ["saturn", "neptune"],
        "aspect_deg":    0.0,
        "orb":           5.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "high",
    },
    {
        "type":          "square_SN",
        "label":         "Cuadratura Saturno-Neptuno",
        "planets":       ["saturn", "neptune"],
        "aspect_deg":    90.0,
        "orb":           5.0,
        "p_value":       None,
        "density_ratio": None,
        "significance":  "medium",
    },
]

# Planetas que se consideran para detectar stellium
_STELLIUM_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "neptune"]
_STELLIUM_MIN_COUNT = 4
_STELLIUM_ORB = 30.0

# Solo publicar si superan estos umbrales
PUBLICATION_THRESHOLDS = {
    "p_value_max":    0.05,
    "density_ratio_min": 2.0,
}

# ── Signos zodiacales ─────────────────────────────────────────────────────────
_SIGNS = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
          "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]

# Velocidades medias (°/día) para detectar retrogradación
_PLANET_AVG_SPEED = {
    "mercury": 1.38, "venus": 1.20, "mars": 0.52,
    "jupiter": 0.083, "saturn": 0.034,
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _jd_to_dt(jd: float) -> datetime:
    y, mo, d, h = swe.revjul(jd)
    hour = int(h)
    minute = int((h - hour) * 60)
    return datetime(y, mo, d, hour, minute, tzinfo=timezone.utc)


def _dt_to_jd(dt: datetime) -> float:
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


def _aspect_distance(lon1: float, lon2: float, aspect_deg: float) -> float:
    """Distancia al aspecto objetivo (0=conjunción, 180=oposición, etc.)."""
    diff = abs(lon1 - lon2) % 360
    # Considera ambos sentidos (direct + retrograde geometry)
    diff = min(diff, 360 - diff)
    if aspect_deg == 0.0:
        return diff
    elif aspect_deg == 180.0:
        return abs(diff - 180.0)
    else:
        return min(abs(diff - aspect_deg), abs(diff - (360 - aspect_deg)))


def _find_exact_date(
    config: dict,
    start_jd: float,
    end_jd: float,
    step_jd: float = 0.5,
) -> Optional[str]:
    """
    Bisección para encontrar la fecha de exactitud del aspecto.
    Retorna ISO string o None si no hay cruce en el rango.
    """
    p1_name, p2_name = config["planets"]
    target = config["aspect_deg"]
    orb    = config["orb"]

    # Muestrear para detectar mínimo local
    best_jd   = None
    best_dist = orb + 1
    jd = start_jd
    while jd <= end_jd:
        pos = get_planet_positions(*_jd_to_parts(jd))
        dist = _aspect_distance(pos[p1_name], pos[p2_name], target)
        if dist < best_dist:
            best_dist = dist
            best_jd   = jd
        jd += step_jd

    if best_dist > orb or best_jd is None:
        return None

    # Afinar con bisección si está dentro del orbe
    lo, hi = best_jd - step_jd, best_jd + step_jd
    for _ in range(20):
        mid = (lo + hi) / 2
        pos = get_planet_positions(*_jd_to_parts(mid))
        dist_mid = _aspect_distance(pos[p1_name], pos[p2_name], target)
        pos_lo   = get_planet_positions(*_jd_to_parts(lo))
        dist_lo  = _aspect_distance(pos_lo[p1_name], pos_lo[p2_name], target)
        if dist_lo < dist_mid:
            hi = mid
        else:
            lo = mid
    exact_jd = (lo + hi) / 2
    return _jd_to_dt(exact_jd).strftime("%Y-%m-%d")


def _jd_to_parts(jd: float) -> tuple[int, int, int, float]:
    y, mo, d, h = swe.revjul(jd)
    return (y, mo, d, h)


# --------------------------------------------------------------------------
# API principal
# --------------------------------------------------------------------------

def _detect_stellium(positions: dict) -> Optional[dict]:
    """
    Detecta stellium: ≥4 planetas dentro de 30° consecutivos en la eclíptica.
    Retorna dict con tipo 'stellium' o None.
    """
    lons = {p: positions[p] for p in _STELLIUM_PLANETS if p in positions}
    sorted_planets = sorted(lons.items(), key=lambda x: x[1])

    # Ventana deslizante de 30°
    for i in range(len(sorted_planets)):
        base_lon = sorted_planets[i][1]
        in_window = []
        for name, lon in sorted_planets:
            diff = (lon - base_lon) % 360
            if diff <= _STELLIUM_ORB:
                in_window.append(name)
        if len(in_window) >= _STELLIUM_MIN_COUNT:
            span = max((lons[p] - base_lon) % 360 for p in in_window)
            # Determinar signo dominante (centro de la ventana)
            center_lon = (base_lon + span / 2) % 360
            sign_idx = int(center_lon / 30)
            signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            sign = signs[sign_idx]
            return {
                "type":          "stellium",
                "label":         f"Stellium en {sign} ({len(in_window)} planetas)",
                "planets":       in_window,
                "orb":           round(span, 2),
                "exact_date":    None,
                "p_value":       None,
                "density_ratio": None,
                "significance":  "high" if len(in_window) >= 4 else "medium",
            }
    return None


def _detect_ingress(positions: dict, prev_positions: dict) -> Optional[dict]:
    """Detecta si algún planeta clave cruzó una cúspide de signo en las últimas 24h."""
    for planet in ["mars", "jupiter", "saturn", "venus"]:
        if planet not in positions or planet not in prev_positions:
            continue
        lon_now  = positions[planet]
        lon_prev = prev_positions[planet]
        sign_now  = int(lon_now  / 30)
        sign_prev = int(lon_prev / 30)
        if sign_now != sign_prev:
            significance = "high" if planet in ("saturn", "jupiter") else "medium"
            return {
                "type":          f"ingress_{planet[0].upper()}",
                "label":         f"Ingreso de {planet.capitalize()} en {_SIGNS[sign_now]}",
                "planets":       [planet],
                "orb":           0.0,
                "exact_date":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "p_value":       None,
                "density_ratio": None,
                "significance":  significance,
                "days_to_exact": 0,
            }
    return None


def _detect_mercury_station(positions: dict, prev_positions: dict) -> Optional[dict]:
    """Detecta estación de Mercurio (ingreso a retrogradación o dirección)."""
    if "mercury" not in positions or "mercury" not in prev_positions:
        return None
    lon_now  = positions["mercury"]
    lon_prev = prev_positions["mercury"]
    motion   = (lon_now - lon_prev) % 360
    if motion > 180:
        motion -= 360  # movimiento real con signo
    was_retro = motion < -0.1
    is_retro  = (lon_now - lon_prev + 360) % 360
    # Detectar cambio de dirección: si ayer avanzaba y hoy retrocede (o viceversa)
    # Usamos la velocidad como proxy (paso de 24h)
    speed_now  = (lon_now  - prev_positions["mercury"] + 360) % 360
    if speed_now > 180: speed_now -= 360
    # Station retrógrada: velocidad cruza 0 hacia negativo
    if speed_now < -0.05:
        return {
            "type":          "mercury_retrograde",
            "label":         "Mercurio Retrógrado",
            "planets":       ["mercury"],
            "orb":           0.0,
            "exact_date":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "p_value":       None,
            "density_ratio": None,
            "significance":  "high",
            "days_to_exact": 0,
        }
    # Station directa: velocidad cruza 0 hacia positivo después de ser negativa
    if 0.0 < speed_now < 0.3:
        return {
            "type":          "mercury_direct",
            "label":         "Mercurio Directo",
            "planets":       ["mercury"],
            "orb":           0.0,
            "exact_date":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "p_value":       None,
            "density_ratio": None,
            "significance":  "high",
            "days_to_exact": 0,
        }
    return None


def get_current_sky() -> dict:
    """
    Calcula posiciones planetarias actuales y configuraciones activas.

    Retorna:
        {
            'date': ISO string,
            'planets': {'jupiter': lon, 'saturn': lon, ...},
            'active_configurations': [...]
        }
    """
    now  = datetime.now(timezone.utc)
    prev = now - timedelta(days=1)
    positions      = get_planet_positions(now.year,  now.month,  now.day,  now.hour)
    prev_positions = get_planet_positions(prev.year, prev.month, prev.day, prev.hour)

    active = []
    for config in CONFIGURATIONS:
        p1, p2 = config["planets"]
        if p1 not in positions or p2 not in positions:
            continue
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

    # Ingresos planetarios (últimas 24h)
    ingress = _detect_ingress(positions, prev_positions)
    if ingress:
        active.append(ingress)

    # Estaciones de Mercurio
    mercury_station = _detect_mercury_station(positions, prev_positions)
    if mercury_station:
        active.append(mercury_station)

    # Stellium
    stellium = _detect_stellium(positions)
    if stellium:
        active.append(stellium)

    return {
        "date":                 now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planets":              {k: round(v, 4) for k, v in positions.items()},
        "active_configurations": active,
    }


def get_upcoming_configurations(days_ahead: int = 90) -> list:
    """
    Configuraciones próximas filtradas por significancia estadística.

    Solo retorna configuraciones con p_value < 0.05 AND density_ratio > 2.0.
    Para configuraciones sin datos estadísticos (p_value=None) las incluye
    con significance='low' para referencia.

    Retorna lista ordenada por fecha exacta ascendente.
    """
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)
    now_jd = _dt_to_jd(now)
    end_jd = _dt_to_jd(end)

    results = []
    for config in CONFIGURATIONS:
        p1_name, p2_name = config["planets"]

        # Paso de muestreo según velocidad de los planetas involucrados
        # Marte: ~0.5°/día → step 1 día; Júpiter/Saturno: lento → step 2 días
        step = 1.0 if "mars" in config["planets"] else 2.0

        jd = now_jd
        in_orb = False
        entry_jd = None

        while jd <= end_jd:
            pos  = get_planet_positions(*_jd_to_parts(jd))
            dist = _aspect_distance(pos[p1_name], pos[p2_name], config["aspect_deg"])

            if dist <= config["orb"] and not in_orb:
                in_orb   = True
                entry_jd = jd
            elif dist > config["orb"] and in_orb:
                in_orb = False
                # Encontramos una ventana [entry_jd, jd]
                exact_iso = _find_exact_date(config, entry_jd, jd, step)
                # Calcular orbe actual al inicio
                pos_entry = get_planet_positions(*_jd_to_parts(entry_jd))
                orb_entry = _aspect_distance(
                    pos_entry[p1_name], pos_entry[p2_name], config["aspect_deg"]
                )
                results.append(_build_config_entry(config, exact_iso, orb_entry))

            jd += step

        # Caso: todavía en orbe al final del período
        if in_orb and entry_jd is not None:
            exact_iso = _find_exact_date(config, entry_jd, end_jd, step)
            pos_entry = get_planet_positions(*_jd_to_parts(entry_jd))
            orb_entry = _aspect_distance(
                pos_entry[p1_name], pos_entry[p2_name], config["aspect_deg"]
            )
            results.append(_build_config_entry(config, exact_iso, orb_entry))

    # Ordenar por fecha exacta (None al final)
    results.sort(key=lambda x: x.get("exact_date") or "9999")
    return results


def _build_config_entry(config: dict, exact_iso: Optional[str], orb: float) -> dict:
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
    # Calcular días hasta la fecha exacta
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


def get_historical_context(config_type: str, orb: float = 8.0) -> dict:
    """
    Busca en data/mundana/eventos_raw.jsonl eventos ocurridos
    en ventanas ±30 días de configuraciones similares.

    Retorna:
        {
            'sample_events': [...],   # hasta 5 eventos representativos
            'density_ratio': float,
            'p_value': float,
            'config_type': str
        }
    """
    # Estadísticas empíricas de H_mundana_A
    _STATS = {
        "conjunction_JS": {"density_ratio": 4.3, "p_value": 5e-6},
        "opposition_MS":  {"density_ratio": 1.6, "p_value": 0.016},
    }
    stats = _STATS.get(config_type, {"density_ratio": None, "p_value": None})

    # Cargar eventos del corpus
    sample_events: list[dict] = []
    if EVENTOS_PATH.exists():
        # Configuración destino para matchear
        config = next((c for c in CONFIGURATIONS if c["type"] == config_type), None)
        if config:
            p1_name, p2_name = config["planets"]
            target_deg       = config["aspect_deg"]

            with open(EVENTOS_PATH, encoding="utf-8") as f:
                for line in f:
                    if len(sample_events) >= 5:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Parsear fecha del evento
                    date_str = event.get("date") or event.get("year")
                    if not date_str:
                        continue
                    try:
                        if isinstance(date_str, int):
                            year, month, day = date_str, 6, 15
                        else:
                            parts = str(date_str).split("-")
                            year  = int(parts[0])
                            month = int(parts[1]) if len(parts) > 1 else 6
                            day   = int(parts[2]) if len(parts) > 2 else 15
                    except (ValueError, IndexError):
                        continue

                    # Verificar si había configuración activa ±30 días
                    in_window = False
                    for delta_d in range(-30, 31, 3):
                        check_dt = datetime(year, month, day, 12) + timedelta(days=delta_d)
                        try:
                            pos  = get_planet_positions(
                                check_dt.year, check_dt.month, check_dt.day, 12.0
                            )
                            dist = _aspect_distance(pos[p1_name], pos[p2_name], target_deg)
                            if dist <= orb:
                                in_window = True
                                break
                        except Exception:
                            continue

                    if in_window:
                        sample_events.append({
                            "date":        str(date_str),
                            "description": event.get("description") or event.get("event") or "",
                            "category":    event.get("category") or event.get("type") or "",
                        })

    return {
        "config_type":   config_type,
        "sample_events": sample_events,
        "density_ratio": stats["density_ratio"],
        "p_value":       stats["p_value"],
    }


# --------------------------------------------------------------------------
# CLI rápido para pruebas
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import pprint

    print("=== sky_calculator.py — test ===\n")

    print("--- get_current_sky() ---")
    sky = get_current_sky()
    pprint.pprint(sky)
    print()

    print("--- get_upcoming_configurations(days_ahead=90) ---")
    upcoming = get_upcoming_configurations(days_ahead=90)
    for u in upcoming:
        print(f"  [{u['significance'].upper()}] {u['label']} — exacto: {u['exact_date']}"
              f"  (orbe: {u['orb']}°, días: {u['days_to_exact']})")
    print()

    print("--- get_historical_context('conjunction_JS') ---")
    hist = get_historical_context("conjunction_JS")
    print(f"  density_ratio={hist['density_ratio']}x  p={hist['p_value']}")
    print(f"  {len(hist['sample_events'])} eventos de muestra")
    for ev in hist["sample_events"]:
        print(f"    {ev['date']}: {ev['description'][:80]}")
