"""
Diseño v6 — "Natal KG sobre Gemini Flash" (Hipótesis 1 cross-familia)

Pregunta científica:
    ¿El efecto KG-mejora-modelo-barato (v5) se replica con modelos de otra
    familia? Si SÍ, la tesis se vuelve universal y no Anthropic-específica.

Diseño:
    A: JSON narrativo + Gemini 2.5 Flash (Vertex)
    B: KG tripletas   + Gemini 2.5 Flash (Vertex)

v5 mostró que el KG agrega +15.8% (Claude judge) / +18.1% (Gemini judge) al
output de Haiku 4.5 con n=5. Si v6 muestra delta comparable con Gemini Flash,
la H1 ("KG es scaffolding doctrinal para modelos menores") generaliza
cross-familia y se convierte en finding publicable.

Contextos reutilizados íntegramente de v3 — varía SOLO el modelo lector.
"""

from __future__ import annotations

from scripts.kg_experiment.designs.v3_natal_full_kg import (  # noqa: F401
    build_context_a,
    build_context_b,
    SUBJECTS,
    EVAL_PROMPT,
)


DESIGN_ID = "v6_natal_kg_gemini_flash"
DESIGN_DESCRIPTION = (
    "H1 cross-familia: misma información en A y B (10 planetas + 4 ángulos + "
    "4 partes + 12 señoríos + aspectos + recepciones), ambos leídos por "
    "Gemini 2.5 Flash via Vertex AI. Pregunta: ¿el formato KG mejora a Flash "
    "como mejoró a Haiku en v5? Si delta_v6 ~= delta_v5 -> tesis cross-familia."
)

READER_MODEL_A = "gemini-2.5-flash"
READER_MODEL_B = "gemini-2.5-flash"
READER_PROVIDER_A = "vertex_gemini"
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
