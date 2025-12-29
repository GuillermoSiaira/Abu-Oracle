# -*- coding: utf-8 -*-
"""
Módulo: interpreter_llm

Cliente interno para Lilly Engine (LLM) usado por Abu.

Función principal:
- interpret_analysis(payload: dict, language: str = "es") -> dict

Uso previsto:
- Invocado desde endpoints de Abu (por ejemplo, /api/astro/interpret)
  para enviar el resultado agregado de /analyze a Lilly y obtener una
  interpretación en JSON.

Contrato:
- Envía el payload (output de /analyze) al endpoint remoto de Lilly
  agregando el campo "language".
- Valida que la respuesta contenga las claves requeridas:
  ["headline", "narrative", "actions", "astro_metadata"].
- Devuelve la respuesta tal cual si es válida.
- Ante timeout o errores de conexión, devuelve {"error": "Lilly unreachable"}.
- Si la respuesta no cumple el contrato, levanta RuntimeError.

Configuración:
- URL base configurable vía variable de entorno LILLY_API_URL.
  Defaults: "http://lilly_engine:8001" (compatible con Docker Compose)
  Endpoint: "{LILLY_API_URL}/api/ai/interpret"
"""
from __future__ import annotations

import os
from typing import Any, Dict

import requests


def interpret_analysis(payload: Dict[str, Any], language: str = "es") -> Dict[str, Any]:
    """Envía un análisis astrológico agregado a Lilly para obtener una interpretación.

    Args:
        payload: Diccionario con el output de /analyze (chart, derived, firdaria/profection opcionales,
                 cycles/forecast si existen, etc.).
        language: Código de idioma para Lilly ("es" por defecto).

    Returns:
        dict: Respuesta JSON de Lilly con las claves:
              - headline (str)
              - narrative (str)
              - actions (list)
              - astro_metadata (dict)

    Raises:
        RuntimeError: Si la respuesta no contiene las claves requeridas o si el cuerpo no es JSON válido.

    Notas:
        - Diseñado para uso interno por endpoints como /api/astro/interpret,
          que toman el payload consolidado de Abu y lo envían a Lilly.
        - En caso de timeout o problemas de red, se devuelve {"error": "Lilly unreachable"}.
    """
    base_url = os.getenv("LILLY_API_URL", "http://lilly_engine:8001").rstrip("/")
    url = f"{base_url}/api/ai/interpret"

    # Construir cuerpo: payload + language (no sobrescribe si ya viene)
    body: Dict[str, Any] = dict(payload or {})
    body.setdefault("language", language or "es")

    try:
        resp = requests.post(
            url,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
    except (requests.Timeout, requests.ConnectionError):
        return {"error": "Lilly unreachable"}
    except requests.RequestException as e:
        # Errores HTTP distintos a conexión/timeout: elevar como RuntimeError
        status = getattr(getattr(e, "response", None), "status_code", "unknown")
        raise RuntimeError(f"Lilly HTTP error: {status}") from e

    # Parse y validación de contrato
    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError("Invalid JSON returned by Lilly") from e

    required = ("headline", "narrative", "actions", "astro_metadata")
    if not isinstance(data, dict) or not all(k in data for k in required):
        raise RuntimeError("Lilly response missing required fields")

    return data
