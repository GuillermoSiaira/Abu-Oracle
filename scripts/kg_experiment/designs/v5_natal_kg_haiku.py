"""
Diseño v5 — "Natal KG sobre Haiku"

Pregunta científica:
    ¿El formato KG ayuda más a Haiku que a Sonnet?

    v3 mostró que KG sobre Sonnet aporta +6.8% (Claude) / +10.7% (Gemini).
    v5 mide el mismo contraste de formato pero con Haiku como lector
    en ambas condiciones — pregunta si Haiku se beneficia más (o menos)
    del scaffolding estructural del KG.

Diseño:
    A: JSON narrativo + Haiku 4.5
    B: KG tripletas   + Haiku 4.5

Contextos reutilizados íntegramente de v3 — varía SOLO el formato.
"""

from __future__ import annotations

from scripts.kg_experiment.designs.v3_natal_full_kg import (  # noqa: F401
    build_context_a,
    build_context_b,
    SUBJECTS,
    EVAL_PROMPT,
)


DESIGN_ID = "v5_natal_kg_haiku"
DESIGN_DESCRIPTION = (
    "Test del formato KG en modelo barato: misma información en A y B "
    "(10 planetas + 4 ángulos + 4 partes + 12 señoríos + aspectos + recepciones), "
    "ambos leídos por Haiku 4.5. Pregunta: ¿el formato KG ayuda más a Haiku que a Sonnet? "
    "Si delta_v5 > delta_v3, el KG es scaffolding especialmente útil para modelos menores."
)

READER_MODEL_A = "claude-haiku-4-5-20251001"
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
