
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import warnings
import httpx
from core.llm import generate_interpretation, Language
from core.assistants import generate_interpretation_assistants
from core.context_manager import save_context
from json_maestro import build_json_maestro
from narrative_engine import generate_narrative

# Models
class AstroData(BaseModel):
    events: Optional[List[Dict[str, Any]]] = None
    transits: Optional[List[Dict[str, Any]]] = None
    planets: Optional[List[Dict[str, Any]]] = None
    aspects: Optional[List[Dict[str, Any]]] = None
    timeseries: Optional[List[Dict[str, Any]]] = None
    peaks: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = "es"
    question: Optional[str] = None
    tone: Optional[str] = None

class InterpretResponseMaestro(BaseModel):
    maestro: Dict[str, Any]
    narrative: Optional[str] = None

class MaestroRequest(BaseModel):
    birthDate: str
    lat: float
    lon: float
    language: Optional[str] = "es"
    include_transits: Optional[bool] = False
    include_solar_return: Optional[bool] = False
    solar_return_year: Optional[int] = None
    include_narrative: Optional[bool] = False

class FullInterpretRequest(BaseModel):
    analysis: Dict[str, Any]
    question: Optional[str] = None
    language: Optional[str] = "es"

class FullInterpretResponse(BaseModel):
    maestro: Dict[str, Any]
    narrative: Optional[str] = None
    ai: Optional[Dict[str, Any]] = None

class SolarReturnData(BaseModel):
    natal_chart: Dict[str, Any]
    solar_chart: Dict[str, Any]
    language: Optional[str] = "es"

class SolarReturnResponse(BaseModel):
    best_locations: List[str]
    location_details: List[Dict[str, Any]]
    reasoning: str
    natal_ascendant: Dict[str, Any]
    solar_ascendant: Dict[str, Any]
    astro_metadata: Dict[str, Any]

# App instance
app = FastAPI(title="Lilly Engine - Interpretación Astrológica")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Debug endpoints
@app.get("/debug/connectivity")
async def test_connectivity():
    import socket
    import ssl
    try:
        context = ssl.create_default_context()
        with socket.create_connection(("api.openai.com", 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname="api.openai.com") as ssock:
                return {"status": "ok", "openai_reachable": True, "message": "Successfully connected to api.openai.com"}
    except Exception as e:
        return {"status": "error", "openai_reachable": False, "error": str(e), "error_type": type(e).__name__}

@app.get("/debug/api-key")
async def check_api_key():
    from core.llm import get_openai_client
    api_key = os.getenv("OPENAI_API_KEY", "")
    has_key = bool(api_key)
    key_len = len(api_key)
    key_prefix = api_key[:10] + "..." if key_len > 10 else "N/A"
    try:
        client = get_openai_client()
        client_ok = True
    except Exception:
        client_ok = False
    return {
        "has_api_key": has_key,
        "key_length": key_len,
        "key_prefix": key_prefix,
        "client_initialized": client_ok
    }

# Load archetypes from JSON file
archetypes = {}
try:
    archetypes_path = os.path.join(os.path.dirname(__file__), "archetypes.json")
    with open(archetypes_path, encoding="utf-8") as f:
        archetypes = json.load(f)
except Exception:
    archetypes = {}

# Main endpoints
@app.post(
    "/api/ai/interpret/full",
    response_model=FullInterpretResponse,
    responses={
        400: {"description": "Invalid input data"},
        502: {"description": "Abu Engine error"},
        200: {
            "description": "Full interpretation response",
            "content": {
                "application/json": {
                    "example": {
                        "maestro": {"metadata": {"mode": "persian_cosmology"}},
                        "narrative": "Narrativa heurística...",
                        "ai": {
                            "headline": "...",
                            "narrative": "...",
                            "actions": ["...", "..."]
                        }
                    }
                }
            }
        }
    }
)
def interpret_full_endpoint(data: FullInterpretRequest):
    try:
        maestro = build_json_maestro(data.analysis, metadata_context={"language": data.language or "es"})
        try:
            narrative_text = generate_narrative(maestro, data.language or "es")
        except Exception:
            narrative_text = None
        try:
            ai_result = generate_interpretation(
                maestro,
                question=data.question or "",
                lang=data.language or "es"
            )
        except Exception as e:
            ai_result = {
                "headline": "No se pudo generar interpretación AI.",
                "narrative": str(e),
                "actions": []
            }
        return {
            "maestro": maestro,
            "narrative": narrative_text,
            "ai": ai_result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post(
    "/api/ai/interpret",
    response_model=InterpretResponseMaestro,
    responses={
        400: {"description": "Invalid input data"},
        502: {"description": "Abu Engine error"},
        200: {
            "description": "JSON Maestro response",
            "content": {
                "application/json": {
                    "example": {
                        "maestro": {
                            "metadata": {"mode": "persian_cosmology"},
                            "year_overview": {"year_element": "water"}
                        }
                    }
                }
            }
        }
    }
)
def interpret_astro_data(data: MaestroRequest):
    try:
        abu_base = os.getenv("ABU_BASE_URL") or os.getenv("NEXT_PUBLIC_ABU_URL") or "http://abu_engine:8000"

        params = {
            "date": data.birthDate,
            "lat": data.lat,
            "lon": data.lon,
        }
        if data.include_transits:
            params["include_transits"] = True
        if data.include_solar_return:
            params["include_solar_return"] = True
        if data.solar_return_year is not None:
            params["solar_return_year"] = data.solar_return_year
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(f"{abu_base}/api/astro/chart/extended", params=params)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Abu Engine error: {str(e)}")
        if resp.status_code == 500:
            raise HTTPException(status_code=502, detail="Abu Engine error")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Abu Engine error ({resp.status_code})")
        try:
            chart_extended = resp.json()
        except Exception:
            raise HTTPException(status_code=502, detail="Abu Engine error: invalid JSON")
        if not chart_extended or (not chart_extended.get("chart") and not chart_extended.get("extended")):
            raise HTTPException(status_code=400, detail="Extended chart data is empty")
        maestro = build_json_maestro(
            chart_extended,
            metadata_context={
                "language": data.language or "es",
                "birthDate": data.birthDate,
                "lat": data.lat,
                "lon": data.lon,
            },
        )
        narrative_text = None
        if data.include_narrative:
            try:
                narrative_text = generate_narrative(maestro, data.language or "es")
            except Exception as e:
                narrative_text = None
        return {"maestro": maestro, "narrative": narrative_text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post(
    "/api/ai/solar-return",
    response_model=SolarReturnResponse,
    responses={
        400: {"description": "Invalid chart data"},
        200: {
            "description": "Solar Return interpretation with relocation suggestions",
            "content": {
                "application/json": {
                    "example": {
                        "best_locations": ["Lisbon", "Rio de Janeiro", "Venice"],
                        "location_details": [
                            {
                                "city": "Lisbon",
                                "coordinates": {"lat": 38.7223, "lon": -9.1393},
                                "element": "water",
                                "region": "Europe",
                                "compatibility": "high"
                            }
                        ],
                        "reasoning": "El Ascendente natal... suggests favorable energies.",
                        "natal_ascendant": {"sign": "Cancer", "element": "water"},
                        "solar_ascendant": {"sign": "Pisces", "element": "water"},
                        "astro_metadata": {
                            "source": "heuristic",
                            "model": None,
                            "language": "es",
                            "cities_analyzed": 16
                        }
                    }
                }
            }
        }
    }
)
def interpret_solar_return_endpoint(data: SolarReturnData):
    try:
        from core.solar_return import interpret_solar_return
        result = interpret_solar_return(
            natal_chart=data.natal_chart,
            solar_chart=data.solar_chart,
            language=data.language
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error interpreting solar return: {str(e)}"
        )

@app.get("/")
def root():
    return {"message": "Lilly Engine is running correctly!"}