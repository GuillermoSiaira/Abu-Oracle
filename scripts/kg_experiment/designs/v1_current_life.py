"""
Diseño v1 — "Current Life"

Pregunta científica:
    ¿El contexto KG (relaciones afirmadas) produce mejor lectura que el contexto
    JSON timeline cuando se pide a Lilly interpretar la vida del nativo HOY?

Caveat conocido: 3 de 4 sujetos están muertos (Einstein, Jung, Tesla).
Para ellos el frame "hoy" es ficcional doctrinalmente; el motor genera datos
extrapolados (firdaria post-mortem, profección fuera de tabla de 90 años).
GS_004 es el único sujeto vivo donde la pregunta tiene validez plena.

Primera corrida: 2026-05-18 (commits 78e1fae + 299c0dc).
Hallazgos en RESULTS_2026-05-18.md.

Esta es la versión preservada del experimento original. Para diseños nuevos,
crear un módulo aparte (vN_<nombre>.py) — no modificar éste.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Path setup — el módulo puede ser importado desde runner.py o standalone
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ABU = _REPO_ROOT / "abu_engine"
if str(_ABU) not in sys.path:
    sys.path.insert(0, str(_ABU))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.chart_graph import build_chart_graph, get_key_planets, serialize_subgraph  # noqa: E402
from scripts.kg_experiment.assemble_context import build_timeline_section_a  # noqa: E402


DESIGN_ID = "v1_current_life"
DESIGN_DESCRIPTION = (
    "Comparación A=JSON timeline / B=KG sobre 'vida del nativo ahora mismo'. "
    "Incluye contexto temporal (profección + firdaria + tránsitos). "
    "Caveat: 3 de 4 sujetos están muertos."
)

EVAL_PROMPT = """Un astrologo clasico recibe el siguiente contexto sobre una carta natal.
Responde como lo haria: menciona el senor del ano, la firdaria activa,
y como se relacionan con la vida del nativo ahora mismo. Maximo 200 palabras."""


SUBJECTS = [
    {
        "id": "einstein",
        "birthDate": "1879-03-14T11:30:00Z",
        "lat": 48.4,
        "lon": 10.0,
        "name": "Einstein",
    },
    {
        "id": "jung",
        "birthDate": "1875-07-26T19:32:00Z",
        "lat": 47.5,
        "lon": 7.5,
        "name": "Jung",
    },
    {
        "id": "tesla",
        "birthDate": "1856-07-10T00:00:00Z",
        "lat": 44.3,
        "lon": 19.8,
        "name": "Tesla",
    },
    {
        "id": "gs004",
        "birthDate": "1983-10-10T08:20:00Z",  # 05:20 local Buenos Aires (UTC-3)
        "lat": -34.6,
        "lon": -58.4,
        "name": "GS_004",
    },
]


def build_context_a(natal: dict, bio: dict) -> str:
    """Condición A — JSON timeline plano (profección + firdaria + tránsitos lentos)."""
    return build_timeline_section_a(bio, natal)


def build_context_b(natal: dict, bio: dict) -> str:
    """Condición B — KG: señoríos + dignidades + activadores temporales."""
    del bio  # KG v1 no usa biography externa; calcula activadores desde natal+derived
    graph = build_chart_graph(natal)
    derived = natal.get("derived", {})
    key_planets = get_key_planets(graph, derived)
    subgraph = serialize_subgraph(graph, key_planets)
    if not subgraph:
        subgraph = "[sin datos de senorios]"
    return "\n".join([
        "=== SENORIOS ACTIVOS (KG) ===",
        subgraph,
        "==============================",
    ])
