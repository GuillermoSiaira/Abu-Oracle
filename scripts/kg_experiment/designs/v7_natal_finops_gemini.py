"""
Diseño v7 — "Natal FinOps cross-familia" (test FinOps con Gemini Flash)

Pregunta científica:
    Réplica del experimento v4 (FinOps puro) pero con Gemini Flash en lugar
    de Haiku: ¿el KG+Flash compensa el downgrade Sonnet→Flash?

    v4 (Sonnet vs Haiku) mostró que NO: −24% calidad en ambos jueces.
    v7 mide si Gemini Flash con KG se comporta igual o distinto.

Diseño:
    A: JSON narrativo + Sonnet 4.6           (techo Anthropic)
    B: KG tripletas   + Gemini 2.5 Flash     (modelo barato cross-familia)

Si v7 muestra A ganador como en v4 -> el downgrade-con-KG no compensa NI
intra-familia NI cross-familia (resultado coherente).
Si v7 muestra B ganador -> Gemini Flash con KG es mejor que Haiku con KG
para este task; revisión del Pareto frontier.

Contextos reutilizados íntegramente de v3 — varía SOLO el modelo lector.
"""

from __future__ import annotations

from scripts.kg_experiment.designs.v3_natal_full_kg import (  # noqa: F401
    build_context_a,
    build_context_b,
    SUBJECTS,
    EVAL_PROMPT,
)


DESIGN_ID = "v7_natal_finops_gemini"
DESIGN_DESCRIPTION = (
    "FinOps cross-familia: misma información en A y B (10 planetas + 4 "
    "ángulos + 4 partes + 12 señoríos + aspectos + recepciones), pero A usa "
    "Sonnet 4.6 (Anthropic) y B usa Gemini 2.5 Flash (Vertex). "
    "Pregunta: ¿el formato KG compensa el downgrade cross-familia? "
    "Si B >= A -> KG + modelo barato es palanca FinOps real."
)

READER_MODEL_A = "claude-sonnet-4-6"
READER_MODEL_B = "gemini-2.5-flash"
READER_PROVIDER_A = "anthropic"
READER_PROVIDER_B = "vertex_gemini"


__all__ = [
    "DESIGN_ID",
    "DESIGN_DESCRIPTION",
    "EVAL_PROMPT",
    "SUBJECTS",
    "build_context_a",
    "build_context_b",
    "READER_MODEL_A",
    "READER_MODEL_B",
    "READER_PROVIDER_A",
    "READER_PROVIDER_B",
]
