"""
Diseño v4 — "Natal FinOps"

Pregunta científica:
    ¿El formato KG (tripletas estructuradas + relaciones tipadas) compensa
    el downgrade de modelo lector de Sonnet 4.6 a Haiku 4.5?

    Si Calidad(KG+Haiku) >= Calidad(JSON+Sonnet), el KG es palanca FinOps
    real — permite ahorrar ~85% en costo del lector manteniendo la calidad.

Diseño:
    A: JSON narrativo + Sonnet 4.6  (baseline producción actual)
    B: KG tripletas    + Haiku 4.5  (downgrade compensado por formato)

Contextos reutilizados íntegramente de v3 — varía SOLO el modelo lector.
"""

from __future__ import annotations

# Reusar build_context_a / build_context_b / SUBJECTS / EVAL_PROMPT del v3.
from scripts.kg_experiment.designs.v3_natal_full_kg import (  # noqa: F401
    build_context_a,
    build_context_b,
    SUBJECTS,
    EVAL_PROMPT,
)


DESIGN_ID = "v4_natal_finops"
DESIGN_DESCRIPTION = (
    "Test FinOps puro: misma información en A y B (10 planetas + 4 ángulos + "
    "4 partes + 12 señoríos + aspectos + recepciones), pero A usa Sonnet 4.6 "
    "y B usa Haiku 4.5. Pregunta: ¿el formato KG compensa el downgrade de modelo? "
    "Si B >= A en calidad doctrinal -> KG es palanca FinOps real (~85% más barato)."
)

READER_MODEL_A = "claude-sonnet-4-6"
READER_MODEL_B = "claude-haiku-4-5-20251001"


__all__ = [
    "DESIGN_ID",
    "DESIGN_DESCRIPTION",
    "EVAL_PROMPT",
    "SUBJECTS",
    "build_context_a",
    "build_context_b",
    "READER_MODEL_A",
    "READER_MODEL_B",
]
