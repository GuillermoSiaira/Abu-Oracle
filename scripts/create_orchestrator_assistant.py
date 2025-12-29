"""Create or update the Abu Orchestrator Assistant with function tools.

Context:
UI no muestra sección "Actions". Usamos la API de Assistants para registrar
las funciones (cada endpoint Abu/Lilly) como tools de tipo function. Esto es
el fallback cuando la interfaz gráfica aún no habilita carga de OpenAPI.

Requisitos:
- OPENAI_API_KEY en entorno.
- openai>=1.40.0 (ya está en requirements de Lilly).

Estrategia:
1. Definimos JSON Schemas mínimos (solo parámetros necesarios) para evitar
   sobre-especificar (el modelo se apoya en instrucciones).
2. Creamos (o actualizamos si existe ASSISTANT_ID en env) el Assistant.
3. Instrucciones del Assistant: orquestar llamadas, NO interpretar; delegar
   interpretación final a Lilly vía interpret endpoints.

Nota: El Assistant no ejecuta HTTP; el cliente debe procesar tool_calls
      y hacer requests reales (ver run_orchestrated_query.py).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI


INSTRUCTIONS = (
    "Eres Abu Oracle, un orquestador astrológico. Tu misión es:"
    " (1) recuperar datos con funciones (chart, forecast, life-cycles, solar-return, optimize),"
    " (2) solicitar interpretación final a Lilly y"
    " (3) responder SOLO JSON válido: {headline, narrative, actions[], astro_metadata{source}}."
    " Reglas estrictas:"
    " - Nunca respondas sin haber llamado como mínimo a get_chart."
    " - Si la pregunta menciona un año/periodo futuro: considera get_solar_return u optimize_sr_locations;"
    "   para panoramas de evolución anual usa get_forecast."
    " - La interpretación final debe generarla Lilly vía interpret_astrological_data."
    " - No inventes datos planetarios ni arquetipos; obtén observaciones por funciones."
    " - Idioma por defecto: español."
)


def function_tools() -> List[Dict[str, Any]]:
    """Return tool definitions for the Assistant (function style)."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_chart",
                "description": "Obtener carta (planetas, aspectos, casas) para fecha y coordenadas.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "ISO8601 timestamp"},
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                    },
                    "required": ["date", "lat", "lon"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_forecast",
                "description": "Series temporales de transitos y picos (start-end).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthDate": {"type": "string"},
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                        "step": {"type": "string"},
                        "horizon": {"type": "string"},
                    },
                    "required": ["birthDate", "lat", "lon", "start", "end"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_life_cycles",
                "description": "Eventos de ciclos de vida (Saturn Return, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthDate": {"type": "string"},
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                    },
                    "required": ["birthDate"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_solar_return",
                "description": "Carta de retorno solar para el año dado.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthDate": {"type": "string"},
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                        "year": {"type": "integer"},
                    },
                    "required": ["birthDate", "lat", "lon"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "optimize_sr_locations",
                "description": "Ranking de ubicaciones para retorno solar (internamente evalúa múltiples ciudades).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthDate": {"type": "string"},
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                        "target_year": {"type": "integer"},
                    },
                    "required": ["birthDate", "lat", "lon", "target_year"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "interpret_astrological_data",
                "description": "Interpretación final narrativa JSON (usa datos recopilados).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "events": {"type": "array", "items": {"type": "object"}},
                        "transits": {"type": "array", "items": {"type": "object"}},
                        "planets": {"type": "array", "items": {"type": "object"}},
                        "aspects": {"type": "array", "items": {"type": "object"}},
                        "timeseries": {"type": "array", "items": {"type": "object"}},
                        "peaks": {"type": "array", "items": {"type": "object"}},
                        "language": {"type": "string"},
                        "question": {"type": "string"},
                    },
                },
            },
        },
    ]


def main() -> None:
    # Cargar .env del repo si existe (sin dependencias externas)
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY faltante en entorno.")

    client = OpenAI(api_key=api_key)
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")

    tools = function_tools()

    if assistant_id:
        # Update existing assistant
        updated = client.beta.assistants.update(
            assistant_id,
            instructions=INSTRUCTIONS,
            tools=tools,
        )
        print("Assistant actualizado:", updated.id)
    else:
        created = client.beta.assistants.create(
            name="Abu Oracle",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",  # Modelo liviano para orquestación
            tools=tools,
        )
        print("Assistant creado:", created.id)
        print("Exporta este ID y guárdalo como OPENAI_ASSISTANT_ID en tu .env")


if __name__ == "__main__":
    main()
