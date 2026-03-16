# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import requests
import json
from pathlib import Path
from core.forecast import forecast_for_locations, forecast_timeseries, detect_peaks
from core.life_cycles import forecast_life_cycles
from core.chart import chart_json, ChartDTO, solar_return_chart, EphemerisSingleton
from core.extended_calc import (
    calculate_detailed_positions, 
    calculate_part_of_fortune,
    get_lunar_nodes,
    format_position,
    get_sign_name,
    normalize_lon
)
from skyfield.api import load
import logging
from core.solar_return_ranking import rank_solar_return_locations, RELOCATION_CITIES
from services.relocation import compute_relocation
import logging
import time
from services.logging import init_logging, log_event

# ── Cities cache (loaded once at startup) ──────────────────────────────────
_CITIES_CACHE: list = []

def _load_cities() -> list:
    base_dir = Path(__file__).resolve().parent
    cities_file = base_dir / "data" / "cities.json"
    try:
        with open(cities_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"[Abu] Error loading cities.json: {e}")
        return []

_CITIES_CACHE = _load_cities()
logging.info(f"[Abu] Cities cache loaded: {len(_CITIES_CACHE)} entries")


def send_to_lilly(data: dict) -> dict:
    """Envía datos a Lilly Engine para interpretación."""
    try:
        response = requests.post(
            "http://lilly_engine:8001/api/ai/interpret",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return response.json()
    except (requests.RequestException, ValueError):
        return {"error": "Lilly not available"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm-up heavy resources on startup to avoid cold-start latency/errors."""
    # Startup
    try:
        logging.info("[Abu] Warm-up starting…")
        # Ensure SPICE kernel (de440s.bsp) is loaded
        EphemerisSingleton()

        # Run a tiny chart calculation to prime Skyfield internals
        from datetime import timezone
        sample_dt = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        chart_json(-34.6, -58.4, sample_dt)

        # Also prime solar-return path (binary search + scoring)
        # Use a fixed year to keep it quick/predictable
        try:
            solar_return_chart(sample_dt, -34.6, -58.4, sample_dt.year + 1)
        except Exception:
            # If anything fails here, it's just warm-up; don't block startup
            pass
        logging.info("[Abu] Warm-up complete.")
    except Exception as err:
        logging.error(f"[Abu] Warm-up failed: {err}")
        raise
    
    yield
    # Shutdown (if needed in future)


init_logging()  # initialize structured logging (JSON if ABU_VERBOSE=1)
app = FastAPI(title="Abu Engine", lifespan=lifespan)
app.swagger_ui_parameters = {"defaultModelsExpandDepth": -1}

# Configurar CORS
# allow_origins=["*"] — dev local y staging. Producción (Cloud Run) gestiona CORS por configuración GCP.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Simple HTTP timing middleware
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        status = getattr(response, "status_code", 200)
    except Exception as e:
        status = 500
        raise e
    finally:
        dur_ms = round((time.perf_counter() - start) * 1000, 2)
        try:
            log_event("request", {
                "path": request.url.path,
                "method": request.method,
                "status": status,
                "dur_ms": dur_ms
            })
        except Exception:
            pass
    return response

@app.get("/")
def root():
    return {"message": "Abu Engine is running correctly!"}


@app.get(
    "/analyze/contract",
    responses={
        200: {
            "description": "JSON Schema for /analyze response structure - use for frontend validation (Zod, TypeScript types, etc.)",
            "content": {
                "application/json": {
                    "example": {
                        "title": "AnalyzeResponse",
                        "type": "object",
                        "required": ["chart", "derived"],
                        "properties": {
                            "chart": {
                                "type": "object",
                                "description": "Natal chart with planetary positions and house cusps"
                            },
                            "derived": {
                                "type": "object",
                                "description": "Traditional timing techniques: sect, firdaria, profections, lunar transits"
                            },
                            "life_cycles": {
                                "type": "object",
                                "description": "Major life cycles (Saturn Return, Uranus Opposition, etc.)"
                            },
                            "forecast": {
                                "type": "object",
                                "description": "Astrological forecast timeseries with peak detection"
                            }
                        }
                    }
                }
            }
        }
    }
)
def get_analyze_contract():
    """
    **JSON Schema del contrato de /analyze**
    
    Este endpoint retorna el schema formal que define la estructura de respuesta del endpoint POST /analyze.
    
    **Casos de uso**:
    - Validación de tipos en frontend (TypeScript, Zod)
    - Generación automática de tipos cliente
    - Testing de integración (verificar que response cumple schema)
    - Documentación de contrato para consumidores externos
    
    **Campos principales**:
    - `chart.planets`: Array con posiciones, signos, casas y dignidades esenciales
    - `chart.houses`: Sistema de casas (Placidus) con ASC/MC
    - `derived.sect`: "diurnal" o "nocturnal" (determina interpretación de planetas)
    - `derived.firdaria`: Período planetario actual (técnica persa)
    - `derived.profection`: Casa anual activada (técnica helenística)
    - `life_cycles.events`: Ciclos mayores con fechas aproximadas
    - `forecast.timeseries`: Scores diarios/semanales para período futuro
    
    **Ejemplo de uso con Zod**:
    ```typescript
    import { z } from 'zod';
    const schema = await fetch('/analyze/contract').then(r => r.json());
    // Convertir JSON Schema a Zod schema
    ```
    """
    return {
        "title": "AnalyzeResponse",
        "type": "object",
        "required": ["chart", "derived"],
        "properties": {
            "chart": {
                "type": "object",
                "required": ["planets", "houses"],
                "properties": {
                    "planets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "lon", "lat", "speed", "sign", "dignity"],
                            "properties": {
                                "name": {"type": "string"},
                                "lon": {"type": "number"},
                                "lat": {"type": "number"},
                                "speed": {"type": "number"},
                                "sign": {"type": "string"},
                                "dignity": {
                                    "type": "object",
                                    "required": ["domicile", "exaltation", "detriment", "fall", "score"],
                                    "properties": {
                                        "domicile": {"type": "boolean"},
                                        "exaltation": {"type": "boolean"},
                                        "detriment": {"type": "boolean"},
                                        "fall": {"type": "boolean"},
                                        "score": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "houses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["number", "cusp_lon", "sign"],
                            "properties": {
                                "number": {"type": "integer"},
                                "cusp_lon": {"type": "number"},
                                "sign": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "derived": {
                "type": "object",
                "required": ["sect", "firdaria", "profection", "lunar_transit"],
                "properties": {
                    "sect": {
                        "type": "string",
                        "enum": ["diurnal", "nocturnal"]
                    },
                    "firdaria": {
                        "type": "object",
                        "required": ["current"],
                        "properties": {
                            "current": {
                                "type": "object",
                                "required": ["major", "minor", "start", "end"],
                                "properties": {
                                    "major": {"type": "string"},
                                    "minor": {"type": "string"},
                                    "start": {"type": "string", "format": "date"},
                                    "end": {"type": "string", "format": "date"}
                                }
                            }
                        }
                    },
                    "profection": {
                        "type": "object",
                        "required": ["age", "house", "sign", "lord"],
                        "properties": {
                            "age": {"type": "integer"},
                            "house": {"type": "integer"},
                            "sign": {"type": "string"},
                            "lord": {"type": "string"}
                        }
                    },
                    "lunar_transit": {
                        "type": "object",
                        "required": ["moon_sign", "moon_house"],
                        "properties": {
                            "moon_sign": {"type": "string"},
                            "moon_house": {"type": "integer"}
                        }
                    }
                }
            },
            "life_cycles": {
                "type": "object",
                "properties": {
                    "events": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["cycle", "planet", "angle", "approx"],
                            "properties": {
                                "cycle": {"type": "string"},
                                "planet": {"type": "string"},
                                "angle": {"type": "number"},
                                "approx": {"type": "string", "format": "date"}
                            }
                        }
                    },
                    "error": {"type": "string"}
                }
            },
            "forecast": {
                "type": "object",
                "properties": {
                    "timeseries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["date", "score"],
                            "properties": {
                                "date": {"type": "string", "format": "date-time"},
                                "score": {"type": "number"}
                            }
                        }
                    },
                    "peaks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["date", "score", "type"],
                            "properties": {
                                "date": {"type": "string", "format": "date-time"},
                                "score": {"type": "number"},
                                "type": {"type": "string", "enum": ["high", "low"]}
                            }
                        }
                    },
                    "error": {"type": "string"}
                }
            }
        }
    }


@app.get(
    "/api/cities/search",
    response_model=None,
    responses={
        200: {
            "description": "Lista de ciudades que coinciden con la búsqueda",
            "content": {
                "application/json": {
                    "example": [
                        {"city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816},
                        {"city": "Madrid", "country": "España", "lat": 40.4168, "lon": -3.7038}
                    ]
                }
            }
        }
    }
)
def search_cities(q: str = Query("", description="Búsqueda de ciudad o país")):
    """
    Busca ciudades por nombre o país.
    Retorna hasta 20 resultados que coincidan con la query.
    Usa cache en memoria cargado al inicio del servidor.
    """
    if not q or len(q) < 2:
        return _CITIES_CACHE[:20]

    q_lower = q.lower()
    # Prioritize starts-with matches, then contains
    starts = [c for c in _CITIES_CACHE if c["city"].lower().startswith(q_lower)]
    contains = [c for c in _CITIES_CACHE if q_lower in c["city"].lower() and not c["city"].lower().startswith(q_lower)]
    matches = (starts + contains)[:20]
    return matches


@app.get(
    "/api/astro/forecast",
    response_model=None,
    responses={
        400: {"description": "Missing birthDate/lat/lon/start/end"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Serie temporal de pronóstico astrológico",
            "content": {
                "application/json": {
                    "example": {
                        "timeseries": [
                            {"t": "2026-01-01", "F": 0.23},
                            {"t": "2026-01-02", "F": 0.45}
                        ],
                        "peaks": [
                            {"t": "2026-08-12", "F": 0.89, "kind": "peak"},
                            {"t": "2027-03-04", "F": -0.72, "kind": "valley"}
                        ]
                    }
                }
            }
        }
    }
)
def forecast_timeseries_endpoint(
    birthDate: str = Query(..., description="Fecha de nacimiento en formato ISO (ej: 1990-01-01T12:00:00Z)"),
    lat: float = Query(..., description="Latitud en grados decimales"),
    lon: float = Query(..., description="Longitud en grados decimales"),
    start: str = Query(..., description="Fecha de inicio en formato ISO (ej: 2026-01-01T00:00:00Z)"),
    end: str = Query(..., description="Fecha de fin en formato ISO (ej: 2027-01-01T00:00:00Z)"),
    step: str = Query("1d", description="Paso temporal, por defecto 1d"),
    horizon: str = Query("year", description="Horizonte de pronóstico")
):
    """
    Serie temporal de pronóstico astrológico y detección de picos.
    """
    if not all([birthDate, lat, lon, start, end]):
        raise HTTPException(status_code=400, detail="Missing birthDate/lat/lon/start/end")
    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format")
    result = forecast_timeseries(birth_dt, lat, lon, start_dt, end_dt, step, horizon)
    return result

@app.get(
    "/api/astro/life-cycles",
    responses={
        400: {"description": "Missing birthDate"},
        422: {"description": "Invalid date format"},
        500: {"description": "Cycle calculation error"},
        200: {
            "description": "Ciclos vitales planetarios",
            "content": {
                "application/json": {
                    "example": {
                        "events": [
                            {"cycle": "Saturn Return", "planet": "Saturn", "angle": 0, "approx": "2007-07-15"},
                            {"cycle": "Uranus Opposition", "planet": "Uranus", "angle": 180, "approx": "2020-03-12"}
                        ]
                    }
                }
            }
        }
    }
)
def life_cycles(
    birthDate: str = Query(..., description="Fecha de nacimiento en formato ISO (ej: 1990-01-01T12:00:00Z)")
):
    """
    Calcula los ciclos vitales mayores:
    - Saturn Return (~29, ~58 años)
    - Uranus Opposition (~42 años)
    - Neptune Square (~41 años)
    - Pluto Square (~37 años)
    - Chiron Return (~50 años)
    """
    if not birthDate:
        raise HTTPException(status_code=400, detail="Missing birthDate")
    try:
        # Calcular eventos astrológicos
        result = forecast_life_cycles(birthDate)
        
        # Obtener interpretación de Lilly
        lilly_response = send_to_lilly(result)
        
        # Devolver datos y su interpretación
        return {
            "astro_data": result,
            "interpretation": lilly_response
        }
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="cycle calculation error")


@app.get(
    "/api/astro/chart",
    response_model=ChartDTO,
    responses={
        400: {"description": "Missing lat/lon/date"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Carta astral calculada",
            "content": {
                "application/json": {
                    "example": {
                        "datetime": "2026-07-05T12:00:00+00:00",
                        "location": {"lat": -34.6, "lon": -58.4},
                        "planets": [
                            {"name": "Sun", "lon": 103.12, "sign": "Cancer", "house": None},
                            {"name": "Mars", "lon": 92.0, "sign": "Cancer", "house": None}
                        ],
                        "aspects": [
                            {"a": "Sun", "b": "Mars", "type": "square", "orb": 1.2, "angle": 90}
                        ]
                    }
                }
            }
        }
    }
)
def get_chart(
    date: str = Query(..., description="Fecha y hora en formato ISO (ej: 2026-07-05T12:00:00Z)"),
    lat: float = Query(..., description="Latitud en grados decimales"),
    lon: float = Query(..., description="Longitud en grados decimales")
):
    """
    Obtiene la carta astral para una ubicación y fecha dadas.
    """
    if lat is None or lon is None or date is None:
        raise HTTPException(status_code=400, detail="Missing lat/lon/date")
    try:
        date_utc = datetime.fromisoformat(date.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format")
    result = chart_json(lat, lon, date_utc)
    return result


@app.get(
    "/api/astro/chart-detailed",
    response_model=None,
    responses={
        400: {"description": "Missing lat/lon/date"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Carta astral con detalles completos: posiciones, dignidades, nodos, partes arábicas",
            "content": {
                "application/json": {
                    "example": {
                        "datetime": "2026-07-05T12:00:00+00:00",
                        "location": {"lat": -34.6, "lon": -58.4},
                        "planets": [
                            {
                                "name": "Sun",
                                "longitude": 103.12,
                                "sign": "Cancer",
                                "degree_in_sign": 13.12,
                                "formatted": "13°07' Cancer",
                                "house": 10,
                                "dignity": {
                                    "domicile": False,
                                    "exaltation": False,
                                    "detriment": False,
                                    "fall": False,
                                    "peregrine": True,
                                    "score": 0
                                }
                            }
                        ],
                        "aspects": [],
                        "arabic_parts": {
                            "part_of_fortune": {
                                "longitude": 245.67,
                                "sign": "Sagittarius",
                                "formatted": "25°40' Sagittarius"
                            }
                        },
                        "lunar_nodes": {
                            "north_node": {
                                "longitude": 123.45,
                                "sign": "Leo",
                                "formatted": "3°27' Leo"
                            },
                            "south_node": {
                                "longitude": 303.45,
                                "sign": "Aquarius",
                                "formatted": "3°27' Aquarius"
                            }
                        }
                    }
                }
            }
        }
    }
)
def get_chart_detailed(
    date: str = Query(..., description="Fecha y hora en formato ISO (ej: 2026-07-05T12:00:00Z)"),
    lat: float = Query(..., description="Latitud en grados decimales"),
    lon: float = Query(..., description="Longitud en grados decimales")
):
    """
    Obtiene la carta astral detallada con:
    - Posiciones exactas (grados, minutos)
    - Dignidades esenciales (domicilio, exaltación, caída, exilio)
    - Nodos lunares (Norte y Sur)
    - Partes arábicas (Parte de la Fortuna)
    - Asignación de casas (si houses están disponibles)
    """
    if lat is None or lon is None or date is None:
        raise HTTPException(status_code=400, detail="Missing lat/lon/date")
    try:
        date_utc = datetime.fromisoformat(date.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format")
    
    # Get base chart (Skyfield positions and aspects)
    base_chart = chart_json(lat, lon, date_utc)

    # Build planets dict for extended calculations
    planets_dict = {p.name: p.lon for p in base_chart.planets}

    # Calculate lunar nodes (approximation in extended_calc)
    north_node_lon, south_node_lon = get_lunar_nodes(date_utc)
    planets_dict["North Node"] = north_node_lon
    planets_dict["South Node"] = south_node_lon

    # Calculate houses with pyswisseph (if available)
    houses_block = None
    asc_lon = None
    mc_lon = None
    try:
        from core.houses_swiss import calculate_houses, format_houses_output, HOUSE_SYSTEM_PLACIDUS
        houses_data = calculate_houses(date_utc, lat, lon, HOUSE_SYSTEM_PLACIDUS)
        houses_formatted = format_houses_output(houses_data)
        houses_block = houses_formatted
        asc_lon = houses_data["asc"]
        mc_lon = houses_data["mc"]
    except Exception as e:
        houses_block = {"note": f"Houses not available: {str(e)}"}

    # Get detailed positions (with dignities) and assign houses if available
    cusps = None
    if isinstance(houses_block, dict) and "houses" in houses_block:
        # houses_data["cusps"] is already a list of floats, not dicts
        cusps = houses_data.get("cusps")
    detailed_planets = calculate_detailed_positions(planets_dict, houses=cusps)

    # Calculate Part of Fortune with real Ascendant
    sun_lon = planets_dict.get("Sun", 0)
    moon_lon = planets_dict.get("Moon", 0)
    if asc_lon is None:
        asc_lon = 0.0
    # Determine sect (diurnal/nocturnal)
    try:
        from core.lots import is_diurnal
        is_day = is_diurnal(sun_lon, asc_lon)
    except Exception:
        is_day = True
    pof_lon = calculate_part_of_fortune(sun_lon, moon_lon, asc_lon, is_day_chart=is_day)

    response = {
        "datetime": base_chart.datetime,
        "location": base_chart.location,
        "planets": detailed_planets,
        "aspects": [a.model_dump() for a in base_chart.aspects],
        "arabic_parts": {
            "part_of_fortune": {
                "longitude": round(pof_lon, 4),
                "sign": get_sign_name(pof_lon),
                "formatted": format_position(pof_lon)
            }
        },
        "lunar_nodes": {
            "north_node": {
                "longitude": round(north_node_lon, 4),
                "sign": get_sign_name(north_node_lon),
                "formatted": format_position(north_node_lon)
            },
            "south_node": {
                "longitude": round(south_node_lon, 4),
                "sign": get_sign_name(south_node_lon),
                "formatted": format_position(south_node_lon)
            }
        }
    }
    if isinstance(houses_block, dict) and "houses" in houses_block:
        response["houses"] = houses_block["houses"]
        response["asc"] = houses_block["asc"]
        response["mc"] = houses_block["mc"]
        response["asc_longitude"] = asc_lon
        response["mc_longitude"] = mc_lon
    else:
        response["houses"] = houses_block
    return response


@app.get(
    "/api/astro/chart/extended",
    response_model=None,
    responses={
        400: {"description": "Missing lat/lon/date"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Unified extended chart with all Persian/classical calculations in a single response",
            "content": {
                "application/json": {
                    "example": {
                        "chart": {
                            "datetime": "2026-07-05T12:00:00+00:00",
                            "location": {"lat": -34.6, "lon": -58.4},
                            "planets": [],
                            "aspects": []
                        },
                        "extended": {
                            "dignities": {},
                            "lots": [],
                            "fardars": {},
                            "profections": {},
                            "lunar_mansion": {},
                            "fixed_stars": [],
                            "solar_return": {},
                            "solar_return_ranking": {},
                            "transits": []
                        }
                    }
                }
            }
        }
    }
)
def get_chart_extended(
    date: str = Query(..., description="Fecha y hora en formato ISO (ej: 2026-07-05T12:00:00Z)"),
    lat: float = Query(..., description="Latitud en grados decimales"),
    lon: float = Query(..., description="Longitud en grados decimales"),
    include_transits: bool = Query(False, description="Incluir tránsitos vs natal (opcional)"),
    include_solar_return: bool = Query(False, description="Incluir Solar Return (opcional)"),
    solar_return_year: int = Query(None, description="Año para Solar Return (opcional, por defecto año actual)"),
    include_ranking: bool = Query(False, description="Incluir ranking de ciudades para Solar Return (opcional)")
):
    """
    Endpoint unificado que retorna carta natal + todas las técnicas persas/clásicas en un solo JSON.
    
    Este endpoint es la **fuente única de verdad** para Lilly Engine.
    
    Incluye:
    - Carta base (planetas, aspectos, casas)
    - Dignidades esenciales y accidentales
    - Lotes (Fortuna, Espíritu, Eros, Necesidad)
    - Firdaria (períodos planetarios)
    - Profecciones (anual y mensual)
    - Mansión lunar
    - Estrellas fijas
    - Solar Return (opcional)
    - Ranking de ciudades para Solar Return (opcional)
    - Tránsitos (opcional)
    
    Manejo resiliente: si algún sub-cálculo falla, retorna {"error": "..."} sin abortar el endpoint.
    """
    if lat is None or lon is None or date is None:
        raise HTTPException(status_code=400, detail="Missing lat/lon/date")
    
    try:
        date_utc = datetime.fromisoformat(date.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format")
    
    # 1. Get base chart (chart-detailed internally for houses/dignities)
    chart_detailed = None
    try:
        chart_detailed = get_chart_detailed(date, lat, lon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart calculation failed: {str(e)}")
    
    # Extract core values for sub-calculations
    planets_raw = chart_detailed.get("planets") or []
    by_name = {(p.get("name") or ""): p for p in planets_raw}
    
    def get_lon(planet_entry: dict):
        for k in ("longitude", "lon"):
            if k in planet_entry and isinstance(planet_entry[k], (int, float)):
                return float(planet_entry[k])
        return None
    
    sun_lon = get_lon(by_name.get("Sun", {})) or 0.0
    moon_lon = get_lon(by_name.get("Moon", {})) or 0.0
    venus_lon = get_lon(by_name.get("Venus", {}))
    mercury_lon = get_lon(by_name.get("Mercury", {}))
    
    asc_str = (chart_detailed.get("asc") or chart_detailed.get("houses", {}).get("asc"))
    asc_sign = None
    if isinstance(asc_str, str) and asc_str.strip():
        asc_sign = asc_str.split(" ")[0]
    
    asc_lon = chart_detailed.get("asc_longitude") or chart_detailed.get("ascLong") or chart_detailed.get("ascLon")
    if asc_lon is None:
        asc_lon = chart_detailed.get("houses", {}).get("asc_longitude")
    
    # Cusps for lots
    cusps = None
    houses = chart_detailed.get("houses")
    if isinstance(houses, dict) and isinstance(houses.get("houses"), list):
        cusps = [h.get("longitude") for h in houses["houses"] if isinstance(h.get("longitude"), (int, float))]
    elif isinstance(houses, list):
        cusps = [h.get("longitude") for h in houses if isinstance(h.get("longitude"), (int, float))]
    
    # Planets list for fixed stars and transits
    planets_list = []
    for p in planets_raw:
        lon_val = get_lon(p)
        if lon_val is None:
            continue
        name = p.get("name") or "?"
        planets_list.append({"name": name, "longitude": float(lon_val)})
    
    # Build extended block (resilient sub-calls)
    extended = {}
    
    # Dignities (already in chart_detailed planets, extract summary)
    extended["dignities"] = {"note": "Dignities included per-planet in chart.planets[].dignity"}
    
    # Lots
    try:
        from core.lots import calculate_all_lots
        if sun_lon and moon_lon and asc_lon:
            planets_dict = {
                "Sun": sun_lon,
                "Moon": moon_lon,
                "Venus": venus_lon if venus_lon else 0,
                "Mercury": mercury_lon if mercury_lon else 0
            }
            extended["lots"] = calculate_all_lots(planets_dict, asc_lon, cusps)
        else:
            extended["lots"] = {"error": "Missing sun/moon/asc for lots calculation"}
    except Exception as e:
        extended["lots"] = {"error": f"Lots calculation failed: {str(e)}"}
    
    # Fardars
    try:
        from core.fardars import calculate_fardars, get_current_fardar, is_diurnal_chart
        if sun_lon and asc_lon:
            is_diurnal = is_diurnal_chart(sun_lon, asc_lon)
            fardars = calculate_fardars(date_utc, is_diurnal)
            current = get_current_fardar(date_utc, is_diurnal, None)
            extended["fardars"] = {
                "fardars": fardars,
                "current": current,
                "is_diurnal": is_diurnal
            }
        else:
            extended["fardars"] = {"error": "Missing sun/asc for fardars"}
    except Exception as e:
        extended["fardars"] = {"error": f"Fardars calculation failed: {str(e)}"}
    
    # Profections
    try:
        from core.profections import calculate_annual_profection, calculate_monthly_profection
        if asc_sign:
            annual = calculate_annual_profection(date_utc, asc_sign, None)
            monthly = calculate_monthly_profection(date_utc, asc_sign, None)
            extended["profections"] = {**annual, "monthly": monthly}
        else:
            extended["profections"] = {"error": "Missing asc_sign for profections"}
    except Exception as e:
        extended["profections"] = {"error": f"Profections calculation failed: {str(e)}"}
    
    # Lunar mansion
    try:
        from core.lunar_mansions import get_lunar_mansion, get_mansion_interpretation
        if moon_lon:
            mansion = get_lunar_mansion(moon_lon)
            interpretation = get_mansion_interpretation(mansion)
            extended["lunar_mansion"] = {**mansion, "interpretation": interpretation}
        else:
            extended["lunar_mansion"] = {"error": "Missing moon for lunar mansion"}
    except Exception as e:
        extended["lunar_mansion"] = {"error": f"Lunar mansion calculation failed: {str(e)}"}
    
    # Fixed stars
    try:
        from core.fixed_stars import get_all_fixed_star_contacts, format_fixed_stars_output
        if planets_list:
            contacts = get_all_fixed_star_contacts(planets_list)
            formatted = format_fixed_stars_output(contacts)
            extended["fixed_stars"] = formatted
        else:
            extended["fixed_stars"] = {"error": "No planets for fixed stars"}
    except Exception as e:
        extended["fixed_stars"] = {"error": f"Fixed stars calculation failed: {str(e)}"}
    
    # Solar Return (optional)
    if include_solar_return:
        try:
            result = solar_return_chart(date_utc, lat, lon, solar_return_year)
            extended["solar_return"] = result
        except Exception as e:
            extended["solar_return"] = {"error": f"Solar return calculation failed: {str(e)}"}
    else:
        extended["solar_return"] = None
    
    # Solar Return Ranking (optional)
    if include_ranking:
        try:
            from core.solar_return_ranking import rank_solar_return_cities
            # Use birthDate = date for ranking (assumes natal chart as birth)
            rankings = rank_solar_return_cities(date_utc, solar_return_year, cities=None, top_n=3)
            extended["solar_return_ranking"] = rankings
        except Exception as e:
            extended["solar_return_ranking"] = {"error": f"Ranking calculation failed: {str(e)}"}
    else:
        extended["solar_return_ranking"] = None
    
    # Transits (optional)
    if include_transits:
        try:
            from core.transits import calculate_transits, filter_major_transits
            # Calculate current chart for transits
            current_chart = chart_json(lat, lon, datetime.utcnow())
            transit_planets_list = [
                {"name": p.name, "longitude": p.lon, "speed": 0}
                for p in current_chart.planets
            ]
            transits = calculate_transits(planets_list, transit_planets_list)
            transits = filter_major_transits(transits, major_planets_only=True, max_orb=3.0)
            extended["transits"] = transits
        except Exception as e:
            extended["transits"] = {"error": f"Transits calculation failed: {str(e)}"}
    else:
        extended["transits"] = None
    
    # Build unified response
    return {
        "chart": chart_detailed,
        "extended": extended
    }


@app.get(
    "/api/astro/solar-return",
    response_model=None,
    responses={
        400: {"description": "Missing birthDate/lat/lon"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Solar Return chart calculated",
            "content": {
                "application/json": {
                    "example": {
                        "solar_return_datetime": "2025-07-05T14:23:45+00:00",
                        "birth_date": "1990-07-05T12:00:00+00:00",
                        "location": {"lat": 40.7128, "lon": -74.0060},
                        "year": 2025,
                        "planets": [
                            {"name": "Sun", "lon": 103.12, "sign": "Cancer", "house": None},
                            {"name": "Moon", "lon": 245.8, "sign": "Sagittarius", "house": None}
                        ],
                        "aspects": [
                            {"a": "Sun", "b": "Mars", "type": "trine", "orb": 2.1, "angle": 120}
                        ],
                        "score_summary": {
                            "total_score": 4.5,
                            "num_aspects": 3,
                            "interpretation": "favorable"
                        }
                    }
                }
            }
        }
    }
)
def get_solar_return(
    birthDate: str = Query(..., description="Fecha de nacimiento en formato ISO (ej: 1990-07-05T12:00:00Z)"),
    lat: float = Query(..., description="Latitud para el Solar Return"),
    lon: float = Query(..., description="Longitud para el Solar Return"),
    year: int = Query(None, description="Año del Solar Return (opcional, por defecto año actual)")
):
    """
    Calcula la carta de Solar Return (Revolución Solar).
    
    El Solar Return ocurre cuando el Sol transita regresa exactamente a su posición natal.
    Este endpoint calcula el momento preciso y genera la carta astral para ese instante.
    
    Ejemplo de request:
        GET /api/astro/solar-return?birthDate=1990-07-05T12:00:00Z&lat=40.7128&lon=-74.0060&year=2025
    
    Returns:
        JSON con:
        - solar_return_datetime: momento exacto del retorno solar
        - planets: posiciones planetarias en ese momento
        - aspects: aspectos entre planetas
        - score_summary: resumen de favorabilidad (total_score, num_aspects, interpretation)
    """
    if not birthDate or lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Missing birthDate/lat/lon")
    
    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birthDate format")
    
    try:
        result = solar_return_chart(birth_dt, lat, lon, year)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar return calculation error: {str(e)}")


@app.get(
    "/api/astro/solar-return/ranking",
    response_model=None,
    responses={
        400: {"description": "Missing birthDate"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Solar Return location ranking (Persian/Hellenistic astrology)",
            "content": {
                "application/json": {
                    "example": {
                        "top_recommendations": ["London", "Zurich", "Singapore"],
                        "rankings": [
                            {
                                "city": "London",
                                "coordinates": {"lat": 51.5074, "lon": -0.1278},
                                "region": "Europe",
                                "total_score": 67.5,
                                "breakdown": {
                                    "dignities": {"total": 28.0, "asc_ruler_dignity": {"planet": "Venus", "dignity": "domicile", "score": 10.0}},
                                    "angularity": {"total": 18.0, "angular_planets": [{"planet": "Jupiter", "house": 10, "score": 8}]},
                                    "solar_conditions": {"total": 10.0, "conditions": [{"planet": "Mercury", "state": "cazimi", "score": 10}]},
                                    "aspects_reception": {"total": 8.5, "aspects": []},
                                    "sect": {"total": 3.0, "sect": "diurnal", "jupiter_favorable": True}
                                },
                                "chart_summary": {
                                    "asc_sign": "Libra",
                                    "mc_sign": "Cancer",
                                    "solar_return_datetime": "2025-07-05T12:34:56+00:00"
                                }
                            }
                        ],
                        "criteria": "Persian/Hellenistic (dignities, angularity, sect, reception, solar conditions)",
                        "cities_analyzed": 16,
                        "year": 2025
                    }
                }
            }
        }
    }
)
def get_solar_return_ranking(
    birthDate: str = Query(..., description="Fecha de nacimiento en formato ISO (ej: 1990-07-05T12:00:00Z)"),
    year: int = Query(None, description="Año del Solar Return (opcional, por defecto año actual)"),
    cities: str = Query(None, description="Lista de ciudades separadas por comas (opcional, por defecto las 16 predefinidas)"),
    top_n: int = Query(3, description="Número de mejores recomendaciones a mostrar")
):
    """
    Ranking de ciudades para reubicación de Solar Return usando astrología persa.
    
    Calcula el Solar Return para cada ciudad candidata y las clasifica según:
    - **Dignidades esenciales (35%)**: domicilio, exaltación, destierro, caída de planetas clave
    - **Angularidad (25%)**: planetas benéficos en casas angulares (1, 4, 7, 10)
    - **Condiciones solares (15%)**: cazimi (+10), combustión (-10), bajo rayos (-5)
    - **Aspectos con recepción (15%)**: aspectos armónicos/tensos con recepción mutua
    - **Secta (10%)**: planetas sect en casas favorables
    
    Ciudades predefinidas (16 en total):
    - Fire: Dubai, Los Angeles, Barcelona, Sydney
    - Earth: Zurich, Singapore, Toronto, Copenhagen
    - Air: London, Amsterdam, San Francisco, Berlin
    - Water: Venice, Rio de Janeiro, Lisbon, Buenos Aires
    
    Ejemplo de request:
        GET /api/astro/solar-return/ranking?birthDate=1990-07-05T12:00:00Z&year=2025&cities=London,Paris,Tokyo&top_n=3
    
    Returns:
        JSON con:
        - top_recommendations: lista de nombres de ciudades mejor rankeadas
        - rankings: lista completa de ciudades con scores y breakdowns
        - criteria: descripción de criterios de clasificación
        - cities_analyzed: número total de ciudades analizadas
        - year: año del Solar Return
    """
    if not birthDate:
        raise HTTPException(status_code=400, detail="Missing birthDate")
    
    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birthDate format")
    
    # Parse city names if provided
    city_names = None
    if cities:
        city_names = [c.strip() for c in cities.split(",")]
        # Validate that cities exist in our database
        invalid_cities = [c for c in city_names if c not in RELOCATION_CITIES]
        if invalid_cities:
            available = ", ".join(RELOCATION_CITIES.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid cities: {invalid_cities}. Available cities: {available}"
            )
    
    try:
        result = rank_solar_return_locations(birth_dt, year, city_names, top_n)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar return ranking error: {str(e)}")


@app.get(
    "/api/astro/relocation",
    response_model=None,
    responses={
        400: {"description": "Missing birthDate/lat/lon"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Relocation HF field + city ranking",
            "content": {
                "application/json": {
                    "example": {
                        "geojson": {"type": "FeatureCollection", "features": []},
                        "rankings": [{"city": "Zurich", "country": "Switzerland", "hf_total_v3": 21.4}],
                        "natal_hf": 15.3,
                        "max_hf": 21.4,
                        "grid_points": 2409
                    }
                }
            }
        }
    }
)
def get_relocation(
    birthDate: str = Query(..., description="Fecha de nacimiento en formato ISO (ej: 1990-01-01T12:00:00Z)"),
    lat: float = Query(..., description="Latitud natal en grados decimales"),
    lon: float = Query(..., description="Longitud natal en grados decimales"),
    step: float = Query(5.0, description="Paso del grid en grados (default 5.0, min 2.5)"),
    top_n: int = Query(20, description="Número de ciudades en el ranking (default 20)"),
):
    """
    Calcula el campo de armonía (HF) de relocalización para una carta natal.

    Genera un grid global, recalcula casas/ángulos en cada punto, y devuelve:
    - GeoJSON con el campo HF (para heatmap)
    - Ranking de ciudades deduplicado (mejor HF por ciudad)
    - HF natal y máximo del grid
    """
    if not birthDate or lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Missing birthDate/lat/lon")

    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birthDate format")

    # Clamp step to minimum 2.5° to prevent abuse
    step = max(step, 2.5)
    top_n = min(max(top_n, 1), 50)

    t0 = time.perf_counter()
    try:
        result = compute_relocation(birth_dt, lat, lon, step, top_n)
    except Exception as e:
        logging.error(f"[Abu] Relocation error: {e}")
        raise HTTPException(status_code=500, detail=f"Relocation computation error: {str(e)}")

    dur_ms = round((time.perf_counter() - t0) * 1000, 2)
    try:
        log_event("relocation", {
            "dur_ms": dur_ms,
            "step": step,
            "grid_points": result["grid_points"],
            "top_n": top_n,
        })
    except Exception:
        pass

    return JSONResponse(content=result)


# Domain → house number mapping (matches DomainSelector keys in the frontend)
_DOMAIN_TO_HOUSE: dict[str, int] = {
    "h1": 1, "h2": 2, "h4": 4, "h5": 5,
    "h6": 6, "h7": 7, "h9": 9, "h10": 10,
}


@app.get("/api/astro/relocation-field", response_model=None)
def get_relocation_field(
    birthDate: str = Query(..., description="Fecha de nacimiento ISO"),
    lat: float = Query(..., description="Latitud natal"),
    lon: float = Query(..., description="Longitud natal"),
    domain: str = Query("global", description="global|h1|h2|h4|h5|h6|h7|h9|h10"),
    step: float = Query(2.5, description="Paso del grid en grados (min 2.5)"),
):
    """
    Calcula el campo HF de relocalización filtrado por dominio de casa.
    Con domain='global' → todos los planetas (mismo que /relocation).
    Con domain='h10' → solo significadores de casa 10.
    Devuelve GeoJSON con propiedades hf_total/delta_hf.
    """
    if not birthDate or lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Missing birthDate/lat/lon")

    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birthDate format")

    step = max(step, 2.5)

    planet_subset = None
    if domain != "global":
        house_num = _DOMAIN_TO_HOUSE.get(domain)
        if house_num:
            from harmony.houses import house_significators
            from core.chart import chart_json as _chart_json
            from core.houses_swiss import calculate_houses as _calc_houses, HOUSE_SYSTEM_PLACIDUS as _HPS
            chart = _chart_json(lat, lon, birth_dt)
            planet_pos = {p.name: float(p.lon) for p in chart.planets}
            natal_h = _calc_houses(birth_dt, lat, lon, _HPS)
            natal_for_sig = {**planet_pos, "cusps": list(natal_h["cusps"])}
            planet_subset = house_significators(natal_for_sig, house_num)

    try:
        from services.relocation import make_grid, compute_field, build_geojson
        grid = make_grid(step)
        natal_metrics, rows = compute_field(birth_dt, lat, lon, grid, planet_subset=planet_subset)
        geojson = build_geojson(rows)
        geojson["properties"] = {
            "natal_latitude": lat,
            "natal_longitude": lon,
            "natal_hf": natal_metrics["hf_total_v3"],
            "domain": domain,
        }
    except Exception as e:
        logging.error(f"[Abu] relocation-field error: {e}")
        raise HTTPException(status_code=500, detail=f"relocation-field error: {str(e)}")

    return JSONResponse(content=geojson)


@app.get("/api/astro/sr-relocation-field", response_model=None)
def get_sr_relocation_field(
    birthDate: str = Query(..., description="Fecha de nacimiento ISO"),
    lat: float = Query(..., description="Latitud natal"),
    lon: float = Query(..., description="Longitud natal"),
    year: int = Query(None, description="Año del Retorno Solar (default: año actual)"),
    step: float = Query(2.5, description="Paso del grid en grados (min 2.5)"),
):
    """
    Campo HF de relocalización usando planetas del Retorno Solar.

    Para cada punto del grid, calcula el HF con las posiciones planetarias
    del momento exacto del RS + ASC/MC local. Muestra qué ubicaciones
    activan mejor la configuración celeste de ese año.
    """
    if not birthDate or lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Missing birthDate/lat/lon")

    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birthDate format")

    step = max(step, 2.5)
    if year is None:
        year = datetime.now().year

    try:
        from services.relocation import make_grid, compute_sr_field, build_geojson
        grid = make_grid(step)
        natal_metrics, rows, sr_dt = compute_sr_field(birth_dt, lat, lon, grid, year=year)
        geojson = build_geojson(rows)
        geojson["properties"] = {
            "natal_latitude": lat,
            "natal_longitude": lon,
            "natal_hf": natal_metrics["hf_total_v3"],
            "sr_datetime": sr_dt.isoformat(),
            "year": year,
            "mode": "solar_return",
        }
    except Exception as e:
        logging.error(f"[Abu] sr-relocation-field error: {e}")
        raise HTTPException(status_code=500, detail=f"sr-relocation-field error: {str(e)}")

    return JSONResponse(content=geojson)


@app.get("/health")
def health_check():
    """
    Health check endpoint para monitoreo y orchestración.
    """
    return {
        "status": "healthy",
        "service": "Abu Engine",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/api/astro/profections",
    response_model=None,
    responses={
        400: {"description": "Missing birthDate"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Profecciones anuales y mensuales",
            "content": {
                "application/json": {
                    "example": {
                        "year": 35,
                        "profected_sign": "Scorpio",
                        "time_lord": "Mars",
                        "sign_offset": 11,
                        "monthly": {
                            "month": 3,
                            "monthly_sign": "Aquarius",
                            "monthly_lord": "Saturn"
                        }
                    }
                }
            }
        }
    }
)
def get_profections(
    birthDate: str = Query(..., description="Fecha de nacimiento en formato ISO"),
    ascSign: str = Query(..., description="Signo del Ascendente natal (ej: Gemini, Leo, etc.)"),
    currentDate: str = Query(None, description="Fecha actual (opcional, por defecto hoy)")
):
    """
    Calcula las profecciones anuales y mensuales.
    
    La profección es un sistema de direcciones primarias donde el Ascendente
    avanza un signo por cada año de vida, determinando el "regente del año".
    """
    if not birthDate or not ascSign:
        raise HTTPException(status_code=400, detail="Missing birthDate or ascSign")
    
    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
        current_dt = None
        if currentDate:
            current_dt = datetime.fromisoformat(currentDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format")
    
    try:
        from core.profections import calculate_annual_profection, calculate_monthly_profection
        
        annual = calculate_annual_profection(birth_dt, ascSign, current_dt)
        monthly = calculate_monthly_profection(birth_dt, ascSign, current_dt)
        
        return {
            **annual,
            "monthly": monthly
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profection calculation error: {str(e)}")


@app.get(
    "/api/astro/fardars",
    response_model=None,
    responses={
        400: {"description": "Missing birthDate"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Períodos de Fardars (Firdaria)",
            "content": {
                "application/json": {
                    "example": {
                        "fardars": [
                            {
                                "major": "Sun",
                                "years": 10,
                                "start": "1990-01-01T12:00:00",
                                "end": "2000-01-01T12:00:00",
                                "sub": [
                                    {"planet": "Sun", "start": "...", "end": "...", "duration_years": 1.33}
                                ]
                            }
                        ],
                        "current": {
                            "major": "Venus",
                            "sub": "Mercury",
                            "start": "...",
                            "end": "..."
                        }
                    }
                }
            }
        }
    }
)
def get_fardars(
    birthDate: str = Query(..., description="Fecha de nacimiento en formato ISO"),
    sunLon: float = Query(..., description="Longitud del Sol natal (para determinar secta)"),
    ascLon: float = Query(..., description="Longitud del Ascendente natal (para determinar secta)"),
    currentDate: str = Query(None, description="Fecha actual (opcional, por defecto hoy)")
):
    """
    Calcula los períodos de Fardars (Firdaria), un sistema de períodos planetarios persas.
    
    Cada planeta rige un período mayor (de 7 a 13 años), con subperíodos internos.
    La secuencia cambia según la carta sea diurna o nocturna.
    """
    if not birthDate or sunLon is None or ascLon is None:
        raise HTTPException(status_code=400, detail="Missing birthDate, sunLon, or ascLon")
    
    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
        current_dt = None
        if currentDate:
            current_dt = datetime.fromisoformat(currentDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format")
    
    try:
        from core.fardars import calculate_fardars, get_current_fardar, is_diurnal_chart
        
        is_diurnal = is_diurnal_chart(sunLon, ascLon)
        fardars = calculate_fardars(birth_dt, is_diurnal)
        current = get_current_fardar(birth_dt, is_diurnal, current_dt)
        
        return {
            "fardars": fardars,
            "current": current,
            "is_diurnal": is_diurnal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fardar calculation error: {str(e)}")


@app.get(
    "/api/astro/lots",
    response_model=None,
    responses={
        400: {"description": "Missing planet positions"},
        200: {
            "description": "Lotes (Partes) calculados",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "name": "Fortuna",
                            "longitude": 245.67,
                            "sign": "Sagittarius",
                            "degree": 25.7,
                            "house": 3
                        }
                    ]
                }
            }
        }
    }
)
def get_lots(
    sunLon: float = Query(..., description="Longitud del Sol"),
    moonLon: float = Query(..., description="Longitud de la Luna"),
    ascLon: float = Query(..., description="Longitud del Ascendente"),
    venusLon: float = Query(0, description="Longitud de Venus (opcional)"),
    mercuryLon: float = Query(0, description="Longitud de Mercurio (opcional)"),
    cusps: str = Query(None, description="Cúspides de casas (JSON array opcional)")
):
    """
    Calcula los Lotes (Partes) principales:
    - Fortuna (Pars Fortunae)
    - Espíritu (Pars Spiritus)
    - Eros
    - Necesidad (Némesis)
    """
    if sunLon is None or moonLon is None or ascLon is None:
        raise HTTPException(status_code=400, detail="Missing sunLon, moonLon, or ascLon")
    
    try:
        from core.lots import calculate_all_lots
        import json as json_lib
        
        planets = {
            "Sun": sunLon,
            "Moon": moonLon,
            "Venus": venusLon,
            "Mercury": mercuryLon
        }
        
        cusps_list = None
        if cusps:
            cusps_list = json_lib.loads(cusps)
        
        lots = calculate_all_lots(planets, ascLon, cusps_list)
        return lots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lots calculation error: {str(e)}")


@app.get(
    "/api/astro/lunar-mansions",
    response_model=None,
    responses={
        400: {"description": "Missing moonLon"},
        200: {
            "description": "Mansión lunar calculada",
            "content": {
                "application/json": {
                    "example": {
                        "index": 11,
                        "name": "Al-Zubrah",
                        "start": 128.571,
                        "end": 141.428,
                        "nature": "fortunate",
                        "ruler": "Jupiter",
                        "position_in_mansion": 5.3
                    }
                }
            }
        }
    }
)
def get_lunar_mansion(
    moonLon: float = Query(..., description="Longitud de la Luna")
):
    """
    Determina la mansión lunar (Manzil árabe) según la posición de la Luna.
    
    Las 28 mansiones lunares dividen el zodíaco en segmentos de ~12°51'.
    """
    if moonLon is None:
        raise HTTPException(status_code=400, detail="Missing moonLon")
    
    try:
        from core.lunar_mansions import get_lunar_mansion, get_mansion_interpretation
        
        mansion = get_lunar_mansion(moonLon)
        interpretation = get_mansion_interpretation(mansion)
        
        return {
            **mansion,
            "interpretation": interpretation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lunar mansion calculation error: {str(e)}")


@app.get(
    "/api/astro/fixed-stars",
    response_model=None,
    responses={
        200: {
            "description": "Conjunciones con estrellas fijas",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "star": "Regulus",
                            "mag": 1.4,
                            "long": "Leo 29°",
                            "planet": "Sun",
                            "match": True,
                            "orb": 0.8,
                            "nature": "Mars-Jupiter",
                            "notes": "Corazón del León, realeza, honor, éxito"
                        }
                    ]
                }
            }
        }
    }
)
def get_fixed_stars(
    planets: str = Query(..., description="JSON array de planetas [{name, longitude}]")
):
    """
    Encuentra conjunciones con estrellas fijas principales.
    
    Catálogo incluye: Regulus, Aldebaran, Antares, Fomalhaut, Spica, Algol, Sirius, etc.
    Los orbes varían según la magnitud de la estrella.
    """
    try:
        from core.fixed_stars import get_all_fixed_star_contacts, format_fixed_stars_output
        import json as json_lib
        
        planets_list = json_lib.loads(planets)
        contacts = get_all_fixed_star_contacts(planets_list)
        formatted = format_fixed_stars_output(contacts)
        
        return formatted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fixed stars calculation error: {str(e)}")


def _compute_planet_speeds_deg_per_day(date: datetime) -> dict:
    """
    Calcula velocidad geocéntrica aproximada (°/día) para cada planeta usando diferencia central de 24h.
    Útil para marcar directo/retrógrado y determinar si un tránsito es aplicativo.
    """
    planets = EphemerisSingleton()
    ts = load.timescale()
    t_prev = ts.from_datetime(date - timedelta(hours=12))
    t_next = ts.from_datetime(date + timedelta(hours=12))

    earth = planets["earth"]
    bodies = {
        "Sun": planets["sun"],
        "Moon": planets["moon"],
        "Mercury": planets["mercury barycenter"],
        "Venus": planets["venus barycenter"],
        "Mars": planets["mars barycenter"],
        "Jupiter": planets["jupiter barycenter"],
        "Saturn": planets["saturn barycenter"],
        "Uranus": planets["uranus barycenter"],
        "Neptune": planets["neptune barycenter"],
        "Pluto": planets["pluto barycenter"],
    }

    speeds = {}
    for name, body in bodies.items():
        lon_prev = normalize_lon(earth.at(t_prev).observe(body).ecliptic_latlon()[1].degrees)
        lon_next = normalize_lon(earth.at(t_next).observe(body).ecliptic_latlon()[1].degrees)
        diff = (lon_next - lon_prev + 540) % 360 - 180  # [-180, 180]
        speeds[name] = diff  # grados por día (ventana de 24h)

    return speeds


def _build_transit_planets(lat: float, lon: float, dt: datetime) -> list:
    """Calcula posiciones y velocidades de tránsito para alimentar calculate_transits."""
    transit_chart = chart_json(lat, lon, dt)
    planet_speeds = _compute_planet_speeds_deg_per_day(dt)

    return [
        {
            "name": p.name,
            "longitude": p.lon,
            "speed": planet_speeds.get(p.name, 0),
        }
        for p in transit_chart.planets
    ]


@app.get(
    "/api/astro/transits",
    response_model=None,
    responses={
        400: {"description": "Missing parameters"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Tránsitos calculados",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "natal_planet": "Moon",
                            "transit_planet": "Saturn",
                            "aspect": "square",
                            "orb": 2.3,
                            "applying": True,
                            "exactness": "approaching"
                        }
                    ]
                }
            }
        }
    }
)
def get_transits(
    natalPlanets: str = Query(..., description="JSON array de planetas natales [{name, longitude}]"),
    date: str = Query(..., description="Fecha de los tránsitos en formato ISO"),
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    includeMajorOnly: bool = Query(True, description="Filtrar solo planetas exteriores"),
    includeMinor: bool = Query(False, description="Incluir aspectos menores")
):
    """
    Calcula tránsitos comparando posiciones actuales con la carta natal.
    
    Detecta aspectos entre planetas en tránsito y planetas natales,
    indicando si son aplicativos o separativos.
    """
    if not natalPlanets or not date:
        raise HTTPException(status_code=400, detail="Missing natalPlanets or date")
    
    try:
        import json as json_lib
        natal_planets_list = json_lib.loads(natalPlanets)
        
        transit_dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
        
        transit_planets_list = _build_transit_planets(lat, lon, transit_dt)

        from core.transits import calculate_transits, filter_major_transits

        transits = calculate_transits(
            natal_planets_list,
            transit_planets_list,
            include_minor=includeMinor,
        )
        
        if includeMajorOnly:
            transits = filter_major_transits(transits, major_planets_only=True, max_orb=3.0)
        
        return transits
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transits calculation error: {str(e)}")


class TransitsWithNatalRequest(BaseModel):
    birthDate: str = Field(..., description="Fecha/hora natal en ISO, UTC")
    birthLat: float = Field(..., description="Latitud natal")
    birthLon: float = Field(..., description="Longitud natal")
    transitDate: str = Field(..., description="Fecha/hora del tránsito en ISO, UTC")
    transitLat: float = Field(..., description="Latitud para el tránsito")
    transitLon: float = Field(..., description="Longitud para el tránsito")
    includeMajorOnly: bool = Field(True, description="Filtrar solo planetas exteriores")
    includeMinor: bool = Field(False, description="Incluir aspectos menores")


@app.post(
    "/api/astro/transits/with-natal",
    response_model=None,
    responses={
        400: {"description": "Missing parameters"},
        422: {"description": "Invalid date format"},
        200: {"description": "Tránsitos calculados"},
    },
)
def get_transits_with_natal(body: TransitsWithNatalRequest):
    """Conveniencia: genera planetas natales y de tránsito a partir de fechas/lugares y calcula aspectos."""
    try:
        from core.transits import calculate_transits, filter_major_transits

        birth_dt = datetime.fromisoformat(body.birthDate.replace("Z", "+00:00"))
        transit_dt = datetime.fromisoformat(body.transitDate.replace("Z", "+00:00"))

        natal_chart = chart_json(body.birthLat, body.birthLon, birth_dt)
        natal_planets_list = [
            {"name": p.name, "longitude": p.lon}
            for p in natal_chart.planets
        ]

        transit_planets_list = _build_transit_planets(body.transitLat, body.transitLon, transit_dt)

        transits = calculate_transits(
            natal_planets_list,
            transit_planets_list,
            include_minor=body.includeMinor,
        )

        if body.includeMajorOnly:
            transits = filter_major_transits(transits, major_planets_only=True, max_orb=3.0)

        return transits
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transits calculation error: {str(e)}")


# ==========================
# Domain Ranking endpoints
# ==========================

@app.get(
    "/api/astro/domain-score",
    response_model=None,
    responses={
        422: {"description": "Invalid date format or unknown domain"},
    },
)
def get_domain_score(
    birthDate: str = Query(..., description="Fecha de nacimiento ISO (ej: 1990-07-05T12:00:00Z)"),
    lat: float = Query(..., description="Latitud de la ciudad a evaluar"),
    lon: float = Query(..., description="Longitud de la ciudad a evaluar"),
    domain: str = Query(..., description="Dominio: career|love|health|family|resources|creativity|expansion"),
    year: int = Query(None, description="Año del Solar Return (None = año actual)"),
    mode: str = Query("solar_return", description="solar_return | natal"),
    city_name: str = Query(None, description="Nombre descriptivo de la ciudad"),
):
    """
    Calcula el score de una ciudad especifica para un dominio de vida.

    Implementa el Axioma 8 de Abu Oracle (Especificidad de Dominio):
    el campo geografico debe filtrarse por los significadores del dominio
    consultado para ser interpretable.

    Modos:
    - solar_return: usa la Revolucion Solar del año indicado en esa ciudad
    - natal: usa la carta natal en esa ubicacion
    """
    from core.domain_ranking import score_city_for_domain

    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birthDate format")

    result = score_city_for_domain(
        birth_dt=birth_dt,
        lat=lat,
        lon=lon,
        domain=domain,
        year=year,
        mode=mode,
        city_name=city_name,
    )

    if result.get("error") and "Unknown domain" in str(result.get("error")):
        raise HTTPException(status_code=422, detail=result["error"])

    return result


@app.post(
    "/api/astro/domain-ranking",
    response_model=None,
    responses={
        422: {"description": "Invalid date format or unknown domain"},
    },
)
def get_domain_ranking(
    birthDate: str = Query(..., description="Fecha de nacimiento ISO (ej: 1990-07-05T12:00:00Z)"),
    domain: str = Query(..., description="Dominio: career|love|health|family|resources|creativity|expansion"),
    year: int = Query(None, description="Año del Solar Return (None = año actual)"),
    mode: str = Query("solar_return", description="solar_return | natal"),
    top_n: int = Query(5, description="Numero de ciudades top a destacar"),
    cities: list = Body(..., description="Lista de ciudades [{name, lat, lon, country}]"),
):
    """
    Rankea una lista de ciudades para un dominio de vida.

    Las ciudades se reciben en el mismo formato que devuelve /api/cities/search.
    No hay lista fija — el usuario elige las ciudades desde el frontend.

    Implementa el Axioma 8.2: la geografia optima para la carrera no es
    la misma que para la salud, y ambas difieren de la de maxima actividad total.
    """
    from core.domain_ranking import rank_cities_for_domain

    try:
        birth_dt = datetime.fromisoformat(birthDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birthDate format")

    result = rank_cities_for_domain(
        birth_dt=birth_dt,
        cities=cities,
        domain=domain,
        year=year,
        mode=mode,
        top_n=top_n,
    )

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    return result


# ==========================
# Analyze endpoint (core API)
# ==========================

class PersonInput(BaseModel):
    name: Optional[str] = Field(default=None)
    question: Optional[str] = Field(default="")


class BirthData(BaseModel):
    date: str = Field(description="ISO datetime, e.g. 1990-01-01T12:00:00Z")
    lat: float
    lon: float


class CurrentData(BaseModel):
    lat: float
    lon: float
    date: Optional[str] = Field(default=None, description="ISO datetime for current/transit time; defaults to now UTC if omitted")


class AnalyzeRequest(BaseModel):
    person: Optional[PersonInput] = Field(default_factory=PersonInput)
    birth: BirthData
    current: CurrentData


@app.post(
    "/analyze",
    response_model=None,
    responses={
        400: {"description": "Missing/invalid input"},
        422: {"description": "Invalid date format"},
        200: {
            "description": "Aggregated astrological analysis combining natal chart, derived techniques, life cycles, and forecast",
            "content": {
                "application/json": {
                    "example": {
                        "person": {
                            "name": "María González",
                            "question": "¿Qué energías se activan este mes?"
                        },
                        "chart": {
                            "planets": [
                                {
                                    "name": "Sun",
                                    "lon": 103.45,
                                    "lat": 0.0,
                                    "speed": 0.9856,
                                    "sign": "Cancer",
                                    "degree_in_sign": 13.45,
                                    "formatted": "13°27' Cancer",
                                    "house": 10,
                                    "dignity": {
                                        "domicile": False,
                                        "exaltation": False,
                                        "detriment": False,
                                        "fall": False,
                                        "peregrine": True,
                                        "score": 0
                                    }
                                },
                                {
                                    "name": "Moon",
                                    "lon": 245.82,
                                    "lat": 2.1,
                                    "speed": 13.2,
                                    "sign": "Sagittarius",
                                    "degree_in_sign": 25.82,
                                    "formatted": "25°49' Sagittarius",
                                    "house": 3,
                                    "dignity": {
                                        "domicile": False,
                                        "exaltation": False,
                                        "detriment": False,
                                        "fall": False,
                                        "peregrine": True,
                                        "score": 0
                                    }
                                }
                            ],
                            "houses": {
                                "houses": [
                                    {"house": 1, "start": 278.45, "end": 308.23},
                                    {"house": 2, "start": 308.23, "end": 338.12}
                                ],
                                "asc": 278.45,
                                "mc": 188.67
                            }
                        },
                        "derived": {
                            "sect": "diurnal",
                            "firdaria": {
                                "current": {
                                    "major": "Venus",
                                    "sub": "Mercury",
                                    "start": "2024-07-05",
                                    "end": "2025-08-05"
                                }
                            },
                            "profection": {
                                "house": 7
                            },
                            "lunar_transit": {
                                "moon_position": 125.34,
                                "aspects": [
                                    {"planet": "Sun", "type": "trine", "orb": 2.1},
                                    {"planet": "Mars", "type": "square", "orb": 3.5}
                                ]
                            }
                        },
                        "life_cycles": {
                            "events": [
                                {"cycle": "Saturn Return", "planet": "Saturn", "angle": 0, "approx": "2007-07-15"},
                                {"cycle": "Uranus Opposition", "planet": "Uranus", "angle": 180, "approx": "2020-03-12"}
                            ]
                        },
                        "forecast": {
                            "timeseries": [
                                {"date": "2025-11-08T00:00:00Z", "score": 0.23},
                                {"date": "2025-11-15T00:00:00Z", "score": 0.67}
                            ],
                            "peaks": [
                                {"date": "2025-12-12T00:00:00Z", "score": 0.89, "type": "high"}
                            ]
                        },
                        "question": "¿Qué energías se activan este mes?"
                    }
                }
            }
        }
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "buenos-aires": {
                            "summary": "Consulta Buenos Aires (5 Julio 1978, 18:15)",
                            "description": "Análisis completo para persona nacida en Buenos Aires",
                            "value": {
                                "person": {"name": "María González", "question": "¿Qué energías se activan este mes?"},
                                "birth": {"date": "1978-07-05T18:15:00Z", "lat": -34.6037, "lon": -58.3816},
                                "current": {"lat": -34.6037, "lon": -58.3816, "date": "2025-11-07T12:00:00Z"}
                            }
                        },
                        "new-york-en": {
                            "summary": "English example (New York)",
                            "description": "Analysis request for person born in New York (July 5 1978, 2:15 PM UTC)",
                            "value": {
                                "person": {"name": "John Doe", "question": "What themes activate this month?", "language": "en"},
                                "birth": {"date": "1978-07-05T18:15:00Z", "lat": 40.7128, "lon": -74.0060},
                                "current": {"lat": 40.7128, "lon": -74.0060, "date": "2025-11-07T12:00:00Z"}
                            }
                        }
                    }
                }
            }
        }
    }
)
def analyze(payload: AnalyzeRequest = Body(
    ...,
    examples={
        "buenos-aires": {
            "summary": "Consulta Buenos Aires (5 Julio 1978, 18:15)",
            "description": "Análisis completo para persona nacida en Buenos Aires",
            "value": {
                "person": {"name": "María González", "question": "¿Qué energías se activan este mes?"},
                "birth": {"date": "1978-07-05T18:15:00Z", "lat": -34.6037, "lon": -58.3816},
                "current": {"lat": -34.6037, "lon": -58.3816, "date": "2025-11-07T12:00:00Z"}
            }
        },
        "new-york-en": {
            "summary": "English example (New York)",
            "description": "Analysis request for person born in New York (July 5 1978, 2:15 PM UTC)",
            "value": {
                "person": {"name": "John Doe", "question": "What themes activate this month?", "language": "en"},
                "birth": {"date": "1978-07-05T18:15:00Z", "lat": 40.7128, "lon": -74.0060},
                "current": {"lat": 40.7128, "lon": -74.0060, "date": "2025-11-07T12:00:00Z"}
            }
        }
    }
)):
    """
    **Endpoint unificado de análisis astrológico**
    
    Combina múltiples técnicas tradicionales y modernas:
    
    **Carta Natal (chart)**:
    - `planets`: Posiciones planetarias con dignidades esenciales (domicilio, exaltación, caída, exilio)
    - `houses`: Sistema Placidus con cúspides, ASC y MC
    
    **Técnicas Derivadas (derived)**:
    - `sect`: Determina si la carta es diurna o nocturna (clave para interpretación de benéficos/maléficos)
    - `firdaria`: Período planetario actual (sistema persa de cronología vital)
      - `major`: Planeta regente del período mayor (7-10 años)
      - `sub`: Subregente del período menor (~1 año)
    - `profection`: Casa anual activada (técnica helenística, rota 30° por año)
    - `lunar_transit`: Aspectos de la Luna en tránsito a planetas natales
    
    **Ciclos Vitales (life_cycles)**:
    - Saturn Return (~29, ~58 años): madurez, estructura
    - Uranus Opposition (~42 años): crisis de medio camino
    - Neptune Square (~41 años): despertar espiritual
    - Pluto Square (~37 años): transformación profunda
    - Chiron Return (~50 años): sanación de heridas
    
    **Pronóstico (forecast)**:
    - `timeseries`: Serie temporal de scores astrológicos (transits + progressions)
    - `peaks`: Fechas de máxima/mínima intensidad energética
    
    **Errores comunes**:
    - 422: Formato de fecha inválido (usar ISO8601 con sufijo Z o timezone)
    - 400: Parámetros faltantes (birth o current)
    """
    # Internals (functions map):
    # - chart_json: posiciones + aspectos
    # - calculate_houses: ASC/MC/cúspides
    # - calculate_detailed_positions: dignidades + asignación de casas
    # - get_current_fardar + is_diurnal_chart: firdaria actual + secta
    # - calculate_annual_profection: casa anual (por signo desplazado)
    # - calculate_transits: aspectos Luna en tránsito a planetas natales
    t0_total = time.perf_counter()
    try:
        birth_dt = datetime.fromisoformat(payload.birth.date.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birth date format")

    # Current date defaults to now UTC
    try:
        from datetime import timezone
        if payload.current.date:
            current_dt = datetime.fromisoformat(payload.current.date.replace("Z", "+00:00"))
        else:
            current_dt = datetime.now(tz=timezone.utc)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid current date format")

    # 1) Base natal chart (positions + aspects)
    t0_chart = time.perf_counter()
    natal_chart = chart_json(payload.birth.lat, payload.birth.lon, birth_dt)
    t1_chart = time.perf_counter()

    # 2) Houses (ASC/MC/cusps) using Swiss Ephemeris
    houses_block = None
    asc_lon = None
    mc_lon = None
    cusps = None
    t0_houses = time.perf_counter()
    try:
        from core.houses_swiss import calculate_houses, format_houses_output, HOUSE_SYSTEM_PLACIDUS
        houses_data = calculate_houses(birth_dt, payload.birth.lat, payload.birth.lon, HOUSE_SYSTEM_PLACIDUS)
        houses_formatted = format_houses_output(houses_data)
        houses_block = houses_formatted
        asc_lon = houses_data["asc"]
        mc_lon = houses_data["mc"]
        cusps = houses_data.get("cusps")
    except Exception as e:
        houses_block = {"note": f"Houses not available: {str(e)}"}
    t1_houses = time.perf_counter()

    # 3) Detailed positions with dignities, assign houses if available
    planets_dict = {p.name: p.lon for p in natal_chart.planets}
    t0_positions = time.perf_counter()
    try:
        detailed_planets = calculate_detailed_positions(planets_dict, houses=cusps)
    except Exception:
        detailed_planets = calculate_detailed_positions(planets_dict, houses=None)
    t1_positions = time.perf_counter()

    # 4) Firdaria actual (major/sub) - requires diurnal/nocturnal from natal Sun/ASC
    firdaria_current = None
    sect_label = None
    t0_firdaria = time.perf_counter()
    try:
        from core.fardars import get_current_fardar, is_diurnal_chart
        sun_lon = planets_dict.get("Sun", 0.0)
        if asc_lon is None:
            asc_lon = 0.0
        is_diurnal = is_diurnal_chart(sun_lon, asc_lon)
        current_f = get_current_fardar(birth_dt, is_diurnal, current_dt)
        # Fallback for historical subjects outside the 75-year fardar cycle
        if isinstance(current_f, dict) and current_f.get("major") == "N/A":
            from datetime import timedelta
            fallback_dt = birth_dt + timedelta(days=74 * 365.25)
            current_f_fb = get_current_fardar(birth_dt, is_diurnal, fallback_dt)
            if isinstance(current_f_fb, dict) and current_f_fb.get("major") != "N/A":
                current_f = current_f_fb
                current_f["historical_fallback"] = True
        if isinstance(current_f, dict):
            firdaria_current = {
                "major": current_f.get("major"),
                "sub": current_f.get("sub"),
                "start": current_f.get("start"),
                "end": current_f.get("end"),
                "historical_fallback": current_f.get("historical_fallback", False),
            }
        sect_label = "diurnal" if is_diurnal else "nocturnal"
    except Exception:
        firdaria_current = None
        sect_label = None
    t1_firdaria = time.perf_counter()

    # 5) Profección anual → casa (1..12). Derivamos ASC natal en signo.
    profection_house_num = None
    t0_profection = time.perf_counter()
    try:
        asc_sign = get_sign_name(asc_lon or 0.0)
        from core.profections import calculate_annual_profection
        annual_prof = calculate_annual_profection(birth_dt, asc_sign, current_dt)
        sign_offset = annual_prof.get("sign_offset")
        if isinstance(sign_offset, int):
            profection_house_num = (sign_offset % 12) + 1
    except Exception:
        profection_house_num = None
    t1_profection = time.perf_counter()

    # 6) Tránsito lunar actual y aspectos a planetas natales
    transit_planets = []  # Inicializar para robustez
    lunar_transit = {"aspects": []}
    t0_lunar = time.perf_counter()
    try:
        transit_chart = chart_json(payload.current.lat, payload.current.lon, current_dt)
        transit_planets = [
            {"name": p.name, "longitude": p.lon, "speed": 0} for p in transit_chart.planets
        ]
        natal_planets = [
            {"name": p.name, "longitude": p.lon} for p in natal_chart.planets
        ]
        from core.transits import calculate_transits
        all_transits = calculate_transits(natal_planets, transit_planets)
        lunar_aspects_full = [t for t in all_transits if t.get("transit_planet") == "Moon"]
        simplified = [
            {"planet": t.get("natal_planet"), "type": t.get("aspect"), "orb": t.get("orb")}
            for t in lunar_aspects_full
        ]
        lunar_transit = {
            "moon_position": next((pp["longitude"] for pp in transit_planets if pp["name"] == "Moon"), None),
            "aspects": simplified
        }
    except Exception:
        pass
    t1_lunar = time.perf_counter()

    # Calcular posiciones detalladas de planetas de tránsito (robusto)
    try:
        # preferimos el objeto transit_chart si existe
        transit_planets_dict = {p.name: p.lon for p in transit_chart.planets}
        detailed_transit_planets = calculate_detailed_positions(transit_planets_dict, houses=None)
    except Exception:
        # fallback: si solo tenemos transit_planets como lista de dicts
        try:
            transit_planets_dict = {p["name"]: p["longitude"] for p in transit_planets}
            detailed_transit_planets = calculate_detailed_positions(transit_planets_dict, houses=None)
        except Exception:
            detailed_transit_planets = []

    # Assemble houses block to strict contract: { houses:[{house,start,end}], asc:number, mc:number }
    def _houses_contract(cusps_list: Optional[List[float]], asc_value: Optional[float], mc_value: Optional[float]):
        try:
            houses_list: List[Dict[str, Any]] = []
            if isinstance(cusps_list, list) and len(cusps_list) >= 12:
                for i in range(12):
                    start = normalize_lon(float(cusps_list[i]))
                    end = normalize_lon(float(cusps_list[(i + 1) % 12]))
                    houses_list.append({
                        "house": i + 1,
                        "start": round(start, 6),
                        "end": round(end, 6),
                    })
            return {
                "houses": houses_list,
                "asc": round(float(asc_value), 6) if asc_value is not None else None,
                "mc": round(float(mc_value), 6) if mc_value is not None else None,
            }
        except Exception:
            return {"houses": [], "asc": asc_value, "mc": mc_value}
    houses_out = _houses_contract(cusps, asc_lon, mc_lon)

    # 6b) Lots (Partes Arábicas)
    lots_block = None
    try:
        from core.lots import calculate_all_lots
        sun_lon_lots = planets_dict.get("Sun", 0.0)
        moon_lon_lots = planets_dict.get("Moon", 0.0)
        venus_lon_lots = planets_dict.get("Venus", 0.0)
        mercury_lon_lots = planets_dict.get("Mercury", 0.0)
        asc_for_lots = asc_lon if asc_lon is not None else 0.0
        planets_for_lots = {
            "Sun": sun_lon_lots,
            "Moon": moon_lon_lots,
            "Venus": venus_lon_lots,
            "Mercury": mercury_lon_lots,
        }
        lots_block = calculate_all_lots(planets_for_lots, asc_for_lots, cusps)
    except Exception:
        lots_block = None

    # 7) Life cycles (optional block)
    life_cycles_block = None
    t0_cycles = time.perf_counter()
    try:
        life_cycles_block = forecast_life_cycles(payload.birth.date)
    except Exception:
        life_cycles_block = {"error": "module not available"}
    t1_cycles = time.perf_counter()

    # 8) Forecast timeseries (optional block)
    forecast_block = None
    t0_forecast = time.perf_counter()
    try:
        from datetime import timedelta
        start_forecast = current_dt
        end_forecast = current_dt + timedelta(days=365)
        forecast_block = forecast_timeseries(
            birth_dt, payload.birth.lat, payload.birth.lon,
            start_forecast, end_forecast, step="7d", horizon="year"
        )
    except Exception:
        forecast_block = {"error": "module not available"}
    t1_forecast = time.perf_counter()

    # 9) Solar Return summary (optional block, conditional on near birthday)
    solar_return_block = None
    t0_solar_return = time.perf_counter()
    try:
        from core.solar_return_summary import summarize_solar_return, is_near_birthday
        # Include if within 30 days of birthday
        if is_near_birthday(birth_dt, current_dt, window_days=30):
            solar_return_block = summarize_solar_return(
                birth_dt, payload.birth.lat, payload.birth.lon, year=current_dt.year, lang="es"
            )
    except Exception as e:
        # Fail silently to avoid breaking full analysis
        solar_return_block = None
    t1_solar_return = time.perf_counter()

    response = {
        "person": {
            "name": payload.person.name if payload.person else None,
            "question": payload.person.question if payload.person else ""
        },
        "chart": {
            "planets": detailed_planets,
            "houses": houses_out
        },
        "derived": {
            "sect": sect_label,
            "firdaria": {"current": firdaria_current} if firdaria_current is not None else {"current": None},
            "profection": {"house": profection_house_num},
            "lunar_transit": lunar_transit,
            "solar_return": solar_return_block,
            "lots": lots_block,
        },
        "life_cycles": life_cycles_block,
        "forecast": forecast_block,
        "transits": {
            "planets": detailed_transit_planets
        },
        "question": (payload.person.question if payload.person else "")
    }

    t1_total = time.perf_counter()
    try:
        log_event("analyze.blocks", {
            "dur_ms": round((t1_total - t0_total) * 1000, 2),
            "chart_ms": round((t1_chart - t0_chart) * 1000, 2),
            "houses_ms": round((t1_houses - t0_houses) * 1000, 2),
            "positions_ms": round((t1_positions - t0_positions) * 1000, 2),
            "firdaria_ms": round((t1_firdaria - t0_firdaria) * 1000, 2),
            "profection_ms": round((t1_profection - t0_profection) * 1000, 2),
            "lunar_ms": round((t1_lunar - t0_lunar) * 1000, 2),
            "cycles_ms": round((t1_cycles - t0_cycles) * 1000, 2),
            "forecast_ms": round((t1_forecast - t0_forecast) * 1000, 2),
            "solar_return_ms": round((t1_solar_return - t0_solar_return) * 1000, 2),
        })
    except Exception:
        pass
    return response


# ============================
# Interpret endpoint (Abu → Lilly)
# ============================

class InterpretInput(BaseModel):
    birthDate: str = Field(description="ISO datetime, e.g. 1990-01-01T12:00:00Z")
    lat: float
    lon: float
    language: Optional[str] = Field(default="es", description="Idioma de la interpretación (por defecto 'es')")


@app.post(
    "/api/astro/interpret",
    response_model=None,
    responses={
        400: {"description": "Missing/invalid input"},
        422: {"description": "Invalid date format"},
        502: {"description": "Lilly Engine unreachable or LLM error"},
        200: {
            "description": "Interpretación astrológica generada por LLM (GPT-4) basada en análisis técnico de Abu",
            "content": {
                "application/json": {
                    "example": {
                        "headline": "Venus-Mercurio: Creatividad y Comunicación Estratégica",
                        "narrative": "Este período de Firdaria Venus/Mercurio (vigente hasta agosto 2025) activa fuertemente el eje relacional y comunicativo. La profección anual en casa 7 refuerza temas de pareja, asociaciones y negociación. Con la Luna transitando en aspecto armónico al Sol natal, es momento propicio para iniciar conversaciones importantes que combinen diplomacia (Venus) con claridad mental (Mercurio). Los próximos picos energéticos en diciembre señalan oportunidades para concretar acuerdos o proyectos creativos que venís gestando.",
                        "actions": [
                            "Iniciar diálogos estratégicos en relaciones clave (pareja, socios)",
                            "Aprovechar inspiración creativa para proyectos artísticos o de diseño",
                            "Revisar contratos o acuerdos pendientes antes del pico de diciembre"
                        ],
                        "astro_metadata": {
                            "source": "openai",
                            "language": "es",
                            "model": "gpt-4",
                            "techniques_used": ["firdaria", "profections", "lunar_transits", "forecast_peaks"]
                        }
                    }
                }
            }
        }
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "es-buenos-aires": {
                            "summary": "Consulta en español (Buenos Aires)",
                            "description": "Interpretación completa para persona nacida en Buenos Aires, 5 Julio 1978",
                            "value": {
                                "birthDate": "1978-07-05T18:15:00Z",
                                "lat": -34.6037,
                                "lon": -58.3816,
                                "language": "es"
                            }
                        },
                        "en-new-york": {
                            "summary": "English query (New York)",
                            "description": "Full interpretation for person born in New York, July 5, 1978",
                            "value": {
                                "birthDate": "1978-07-05T18:15:00Z",
                                "lat": 40.7128,
                                "lon": -74.0060,
                                "language": "en"
                            }
                        },
                        "pt-sao-paulo": {
                            "summary": "Consulta em português (São Paulo)",
                            "description": "Interpretação em português para pessoa nascida em São Paulo, 5 Julho 1978",
                            "value": {
                                "birthDate": "1978-07-05T18:15:00Z",
                                "lat": -23.5505,
                                "lon": -46.6333,
                                "language": "pt"
                            }
                        }
                    }
                }
            }
        }
    }
)
def interpret_endpoint(data: InterpretInput = Body(
    ...,
    examples={
        "es-buenos-aires": {
            "summary": "Consulta en español (Buenos Aires)",
            "description": "Interpretación completa para persona nacida en Buenos Aires, 5 Julio 1978",
            "value": {
                "birthDate": "1978-07-05T18:15:00Z",
                "lat": -34.6037,
                "lon": -58.3816,
                "language": "es"
            }
        },
        "en-new-york": {
            "summary": "English query (New York)",
            "description": "Full interpretation for person born in New York, July 5, 1978",
            "value": {
                "birthDate": "1978-07-05T18:15:00Z",
                "lat": 40.7128,
                "lon": -74.0060,
                "language": "en"
            }
        },
        "pt-sao-paulo": {
            "summary": "Consulta em português (São Paulo)",
            "description": "Interpretação em português para pessoa nascida em São Paulo, 5 Julho 1978",
            "value": {
                "birthDate": "1978-07-05T18:15:00Z",
                "lat": -23.5505,
                "lon": -46.6333,
                "language": "pt"
            }
        }
    }
)):
    """
    **Interpretación astrológica impulsada por LLM**
    
    Este endpoint orquesta el flujo completo: cálculo astrológico técnico (Abu) + interpretación narrativa (Lilly/GPT-4).
    
    **Flujo interno**:
    1. Llama internamente a POST /analyze con los datos de nacimiento
    2. Envía el análisis técnico completo a Lilly Engine (GPT-4 con contexto astrológico)
    3. Lilly genera interpretación sintética combinando:
       - Período de Firdaria actual (timing persa)
       - Casa de Profección anual (timing helenístico)
       - Tránsitos lunares recientes (activaciones)
       - Picos de forecast (oportunidades/desafíos venideros)
    
    **Respuesta**:
    - `headline`: Título sintético del momento astrológico (máx 80 caracteres)
    - `narrative`: Interpretación detallada en 2-3 párrafos (150-250 palabras)
    - `actions`: 3 acciones concretas recomendadas para el período
    - `astro_metadata.source`: "openai" si LLM responde, "fallback" si usa arquetipos JSON
    
    **Idiomas soportados**:
    - `es`: Español (default)
    - `en`: English
    - `pt`: Português
    - `fr`: Français
    
    **Fallback behavior**:
    Si Lilly Engine no está disponible o OPENAI_API_KEY falta, retorna interpretación basada en arquetipos predefinidos (source="fallback").
    
    **Errores**:
    - 422: Fecha de nacimiento en formato inválido (usar ISO8601)
    - 502: Lilly Engine caído o error de OpenAI API
    """
    logger = logging.getLogger(__name__)
    t_pipeline_start = time.perf_counter()

    if not data or data.birthDate is None or data.lat is None or data.lon is None:
        raise HTTPException(status_code=400, detail="Missing birthDate/lat/lon")

    # Validar formato de fecha
    try:
        _ = datetime.fromisoformat(data.birthDate.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format")

    # 1) Construir payload usando la misma lógica de analyze()
    try:
        analyze_payload = AnalyzeRequest(
            person=PersonInput(name=None, question=""),
            birth=BirthData(date=data.birthDate, lat=data.lat, lon=data.lon),
            current=CurrentData(lat=data.lat, lon=data.lon, date=None),
        )
        t0_analyze = time.perf_counter()
        payload = analyze(analyze_payload)  # type: ignore
        t1_analyze = time.perf_counter()
        if isinstance(payload, JSONResponse):
            import json as _json
            payload = _json.loads(payload.body.decode("utf-8"))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Analyze composition failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal analyze composition error")

    # 2) Llamar a Lilly a través del cliente interno
    try:
        from core.interpreter_llm import interpret_analysis
        t0_lilly = time.perf_counter()
        result = interpret_analysis(payload=payload, language=data.language or "es")
        t1_lilly = time.perf_counter()
        if isinstance(result, dict) and result.get("error") == "Lilly unreachable":
            logger.warning("/api/astro/interpret → Lilly unreachable")
            raise HTTPException(status_code=502, detail="Lilly unreachable")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Lilly interpretation error: %s", str(e))
        raise HTTPException(status_code=502, detail="Lilly error")

    try:
        log_event("interpret.pipeline", {
            "dur_ms": round((time.perf_counter() - t_pipeline_start) * 1000, 2),
            "analyze_ms": round((t1_analyze - t0_analyze) * 1000, 2),
            "lilly_ms": round((t1_lilly - t0_lilly) * 1000, 2)
        })
    except Exception:
        pass

    return JSONResponse(content=result)


# ============================================================
# IGP (Predictive Geographic Intelligence) — Sprint 1
# ============================================================

class IGPBirthData(BaseModel):
    """Birth data for IGP optimization."""
    date: str = Field(..., description="Birth datetime (ISO8601, UTC preferred)")
    lat: float = Field(..., description="Birth latitude (decimal degrees)")
    lon: float = Field(..., description="Birth longitude (decimal degrees)")


class IGPPreferences(BaseModel):
    """User preferences for IGP search."""
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum score filter (0.0–1.0)")
    exclude_regions: Optional[List[str]] = Field(None, description="Regions to exclude (e.g., ['ocean'])")
    max_candidates: Optional[int] = Field(50, ge=1, le=500, description="Max cities to return")
    continents: Optional[List[str]] = Field(None, description="Continent allowlist (optional)")


class IGPOptimizeRequest(BaseModel):
    """Request body for /api/rs/optimize endpoint."""
    birth: IGPBirthData
    target_year: int = Field(..., description="Year for Solar Return (e.g., 2026)")
    intent: str = Field("general", description="Scoring intent: general|health|career|relationships|creative")
    preferences: Optional[IGPPreferences] = None
    refine: bool = Field(False, description="Apply local refinement (Sprint 2, currently ignored)")
    diversity: bool = Field(False, description="Apply geographic diversity (Sprint 2, currently ignored)")
    language: str = Field("es", description="Response language: es|en|pt|fr")


@app.post(
    "/api/rs/optimize",
    summary="IGP — Find optimal Solar Return locations",
    description="Phase 1 (Sprint 1): Batch evaluation of cities for optimal SR relocation. Refinement and diversity deferred to Sprint 2.",
    tags=["IGP"]
)
def igp_optimize(data: IGPOptimizeRequest):
    """
    IGP optimization endpoint — Sprint 1 implementation.
    
    Evaluates multiple cities in parallel to find optimal Solar Return locations.
    
    Returns:
        JSON with best_locations, score_summary, astro_metadata
    
    Sprint 1 scope:
        - Batch evaluation of cities (Phase 1)
        - Parallel processing with multiprocessing
        - Basic caching (in-memory LRU)
    
    Sprint 2 additions:
        - Local refinement (refine flag)
        - Geographic diversity clustering (diversity flag)
        - Intent-based weighting
        - Lilly narrative reasoning
    """
    from core.igp_optimizer import (
        compute_sr_instant,
        batch_evaluate_cities,
        load_cities_dataset
    )
    from core.igp_cache import get_global_cache
    
    t0 = time.perf_counter()
    
    # Parse birth datetime
    try:
        birth_date = datetime.fromisoformat(data.birth.date.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birth date format")
    
    # Validate target year
    if data.target_year < birth_date.year:
        raise HTTPException(
            status_code=400,
            detail=f"Target year {data.target_year} cannot be before birth year {birth_date.year}"
        )
    
    # Compute SR instant
    try:
        t0_sr = time.perf_counter()
        sr_datetime = compute_sr_instant(
            birth_date,
            data.birth.lat,
            data.birth.lon,
            data.target_year
        )
        t1_sr = time.perf_counter()
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.exception("SR instant computation failed: %s", str(e))
        raise HTTPException(status_code=500, detail="SR computation error")
    
    # Load cities dataset (MVP: use existing RELOCATION_CITIES)
    # TODO: Switch to external cities.json when available
    try:
        from core.solar_return_ranking import RELOCATION_CITIES
        cities = [
            {
                'name': name,
                'lat': data['lat'],
                'lon': data['lon'],
                'country': data.get('region', 'Unknown')
            }
            for name, data in RELOCATION_CITIES.items()
        ]
    except Exception as e:
        logging.exception("Cities dataset load failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Cities dataset unavailable")
    
    # Get cache instance
    cache = get_global_cache(max_size=10000)
    
    # Batch evaluate cities
    try:
        t0_batch = time.perf_counter()
        results = batch_evaluate_cities(
            sr_datetime=sr_datetime,
            cities=cities,
            weights=None,  # Sprint 2
            intent=data.intent,
            cache=cache,  # Currently not used in batch_evaluate_cities, Sprint 1 TODO
            max_workers=8
        )
        t1_batch = time.perf_counter()
    except Exception as e:
        logging.exception("Batch evaluation failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Evaluation error")
    
    # Apply preferences filters
    if data.preferences and data.preferences.min_score is not None:
        results = [r for r in results if r['score'] >= data.preferences.min_score]
    
    if data.preferences and data.preferences.max_candidates:
        results = results[:data.preferences.max_candidates]
    
    # Format response
    best_locations = results[:10]  # Top 10 for display
    
    # Compute score summary (aggregate stats)
    scores = [r['score'] for r in results]
    score_summary = {
        'mean': sum(scores) / len(scores) if scores else 0.0,
        'max': max(scores) if scores else 0.0,
        'min': min(scores) if scores else 0.0,
        'top_10_avg': sum(s['score'] for s in best_locations) / len(best_locations) if best_locations else 0.0
    }
    
    t1 = time.perf_counter()
    
    # Log event
    try:
        log_event("igp.optimize", {
            "dur_ms": round((t1 - t0) * 1000, 2),
            "sr_instant_ms": round((t1_sr - t0_sr) * 1000, 2),
            "batch_eval_ms": round((t1_batch - t0_batch) * 1000, 2),
            "cities_evaluated": len(results),
            "top_score": best_locations[0]['score'] if best_locations else 0.0
        })
    except Exception:
        pass
    
    response = {
        "best_locations": best_locations,
        "alternatives": results[10:20] if len(results) > 10 else [],
        "clusters": [],  # Sprint 2
        "score_summary": score_summary,
        "astro_metadata": {
            "source": "igp",
            "sr_datetime": sr_datetime.isoformat(),
            "refinement_applied": False,  # Sprint 2
            "cities_evaluated": len(results),
            "refinement_iterations": 0,  # Sprint 2
            "duration_ms": round((t1 - t0) * 1000, 2)
        },
        "reasoning": "Narrative generation deferred to Sprint 2"  # Lilly integration
    }
    
    return JSONResponse(content=response)
