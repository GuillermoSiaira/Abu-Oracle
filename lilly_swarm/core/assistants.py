# -*- coding: utf-8 -*-
"""
Assistants API integration for Lilly Engine.

This module encapsulates interactions with OpenAI Assistants (Agent Builder)
including:
- Assistant creation or usage of an existing assistant (via OPENAI_ASSISTANT_ID)
- Tool/function definitions that the assistant can call to fetch astro data from Abu Engine
- Run/Thread lifecycle with tool call handling loop

Contract: returns JSON with keys { headline, narrative, actions[], astro_metadata{} }
Default language: Spanish ('es').

Environment variables:
- OPENAI_API_KEY: OpenAI API key
- OPENAI_ASSISTANT_ID: Optional, use a pre-created assistant ID
- LILLY_MODEL: Optional model (default: 'gpt-4o-mini')
- ABU_URL: Base URL for Abu Engine (default: http://abu_engine:8000; for local dev: http://127.0.0.1:8000)
- LILLY_INCLUDE_REASONING: 'true'/'false' include reasoning in the JSON
"""
from __future__ import annotations

import os
import json
import time
from typing import Any, Dict, Optional, List

import requests
from openai import OpenAI

DEFAULT_MODEL = os.getenv("LILLY_MODEL", "gpt-4o-mini")
ABU_URL = os.getenv("ABU_ENGINE_URL") or os.getenv("ABU_URL", "http://abu_engine:8000")

# Polling utility
_DEF_TIMEOUT = 60  # seconds
_DEF_POLL_INTERVAL = 0.5


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=api_key)


def _assistant_tools() -> List[Dict[str, Any]]:
    """Function tool schemas that the assistant can call.
    We expose a minimal set of Abu endpoints.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "abu_get_chart",
                "description": "Obtiene posiciones, aspectos y casas para una fecha y lugar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "ISO datetime (UTC)"},
                        "lat": {"type": "number"},
                        "lon": {"type": "number"}
                    },
                    "required": ["date", "lat", "lon"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "abu_get_solar_return_ranking",
                "description": "Ranking persa de ciudades para Relocalización de RS (Abu)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthDate": {"type": "string", "description": "ISO datetime of birth (UTC)"},
                        "year": {"type": "integer", "nullable": True},
                        "cities": {"type": "string", "nullable": True, "description": "Comma-separated city list"},
                        "top_n": {"type": "integer", "nullable": True}
                    },
                    "required": ["birthDate"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "abu_get_forecast",
                "description": "Obtiene forecast de tránsitos (timeseries, peaks)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthDate": {"type": "string", "description": "ISO datetime of birth (UTC)"},
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                        "step": {"type": "string", "nullable": True},
                        "horizon": {"type": "string", "nullable": True}
                    },
                    "required": ["birthDate", "lat", "lon", "start", "end"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "abu_get_life_cycles",
                "description": "Calcula ciclos de vida (eventos) de Abu",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthDate": {"type": "string", "description": "ISO datetime of birth (UTC)"}
                    },
                    "required": ["birthDate"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "abu_get_solar_return",
                "description": "Calcula la carta del Retorno Solar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthDate": {"type": "string"},
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                        "year": {"type": "integer", "nullable": True}
                    },
                    "required": ["birthDate", "lat", "lon"]
                }
            }
        }
    ]


def _ensure_assistant(client: OpenAI) -> str:
    """Return an assistant id using provided or creating ephemeral if missing."""
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    if assistant_id:
        return assistant_id
    # Create a transient assistant with our tools
    asst = client.beta.assistants.create(
        name="Lilly – Intérprete Astrológica",
        instructions=(
            "Eres Lilly, una inteligencia astrológica. Responde SOLO en JSON válido con las claves: "
            "abu_line, lilly_line, headline, narrative, actions, reasoning, astro_metadata. "
            "Si necesitas datos astrológicos, usa las funciones (tools) disponibles para pedirlos a Abu. "
            "Responde conciso y con español claro por defecto."
        ),
        model=DEFAULT_MODEL,
        tools=_assistant_tools()
    )
    return asst.id


# --- Abu tool runners ------------------------------------------------------

def _abu_get(path: str, params: Dict[str, Any]) -> Any:
    url = f"{ABU_URL}{path}"
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def run_tool_call(name: str, arguments_json: str) -> str:
    """Execute a tool call and return a JSON-serializable string as output."""
    try:
        args = json.loads(arguments_json or "{}")
    except Exception:
        args = {}

    if name == "abu_get_chart":
        data = _abu_get("/api/astro/chart", args)
    elif name == "abu_get_solar_return_ranking":
        data = _abu_get("/api/astro/solar-return/ranking", args)
    elif name == "abu_get_forecast":
        data = _abu_get("/api/astro/forecast", args)
    elif name == "abu_get_life_cycles":
        data = _abu_get("/api/astro/life-cycles", args)
    elif name == "abu_get_solar_return":
        data = _abu_get("/api/astro/solar-return", args)
    else:
        data = {"error": f"Unknown tool: {name}"}

    # Return as compact JSON string
    return json.dumps(data, ensure_ascii=False)


# --- Public entry point ----------------------------------------------------

def generate_interpretation_assistants(
    events: Optional[List[Dict[str, Any]]] = None,
    language: Optional[str] = "es",
    question: Optional[str] = None,
    tone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Use Assistants API to generate an interpretation. The assistant may call
    Abu tools; we execute them and feed results back until completion.

    Returns a dict matching Lilly's contract.
    """
    client = _client()
    assistant_id = _ensure_assistant(client)

    # Build a concise user message. We keep it short to favor latency.
    user_payload = {
        "language": language or "es",
        "tone": tone or "psicológico",
        "events": events or [],
        "question": question or None,
        "contract": {
            "json_only": True,
            "keys": [
                "abu_line", "lilly_line", "headline", "narrative", "actions", "reasoning", "astro_metadata"
            ]
        }
    }

    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": (
                    "Interpreta estos datos en español. Sigue el contrato JSON. "
                    "Si necesitas datos faltantes, usa las tools de Abu.\n" + json.dumps(user_payload, ensure_ascii=False)
                )
            }
        ]
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
        model=DEFAULT_MODEL
    )

    deadline = time.time() + _DEF_TIMEOUT
    while time.time() < deadline:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        status = run.status
        if status in ("completed", "failed", "cancelled", "expired"):
            break
        if status == "requires_action":
            tool_outputs = []
            for tc in run.required_action.submit_tool_outputs.tool_calls:
                name = tc.function.name
                arguments = tc.function.arguments
                output = run_tool_call(name, arguments)
                tool_outputs.append({"tool_call_id": tc.id, "output": output})
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
        else:
            time.sleep(_DEF_POLL_INTERVAL)

    # Fetch the latest assistant message
    msgs = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
    content_text = ""
    if msgs.data:
        parts = msgs.data[0].content
        # Concatenate text parts only
        for p in parts:
            if getattr(p, "type", None) == "text":
                content_text += p.text.value

    # Parse content as JSON
    data = {}
    try:
        data = json.loads(content_text)
    except Exception:
        # Try to extract a JSON object
        import re
        m = re.search(r"\{[\s\S]*\}", content_text)
        if m:
            try:
                data = json.loads(m.group(0))
            except Exception:
                data = {}

    # Normalize response to contract
    headline = data.get("headline", "Interpretación")
    narrative = data.get("narrative", "")
    actions = data.get("actions", [])
    abu_line = data.get("abu_line", "")
    lilly_line = data.get("lilly_line", "")
    reasoning = data.get("reasoning", "")

    return {
        "abu_line": abu_line,
        "lilly_line": lilly_line,
        "headline": headline,
        "narrative": narrative,
        "actions": actions if isinstance(actions, list) else [],
        "reasoning": reasoning,
        "astro_metadata": {
            "source": "assistants",
            "model": DEFAULT_MODEL,
            "language": language or "es"
        }
    }
