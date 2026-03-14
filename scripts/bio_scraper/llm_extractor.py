"""Send Wikipedia text to GPT-4o-mini for structured event extraction."""
from __future__ import annotations
import json
import logging
import os
import time
from typing import List

from openai import OpenAI

from .models import BioEvent, Location

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Eres un extractor de eventos biográficos. Dado el texto de un artículo de Wikipedia, \
extrae todos los eventos fechados relevantes. Devuelve SOLO un JSON object con la clave \
"events" que contenga un JSON array.

Cada evento debe tener:
- date: "YYYY-MM-DD" (si solo se conoce el año, usar "YYYY-01-01")
- event_type: uno de [death, birth_child, marriage, divorce, relocation, \
professional_milestone, award, publication, exhibition, health_critical, \
psychological_crisis, accident, political_event, arrest, exile, legal, \
artistic_creation, discovery, invention, financial_crisis, financial_success, \
relationship_start, relationship_end, education_start, education_end, \
military_service, retirement]
- description: 1-2 frases en español describiendo el evento
- valence: "positive" | "negative" | "neutral"
- confidence: "high" si la fecha exacta aparece en el texto, \
"medium" si se infiere del contexto, "low" si solo se conoce el año
- location: {"city": "...", "country": "..."} si se menciona en el texto (omitir si no)

No incluyas el nacimiento del sujeto. Prioriza eventos con fechas precisas.
Devuelve entre 8 y 25 eventos, cubriendo distintas etapas de la vida.\
"""


def extract_events(name: str, article_text: str) -> List[BioEvent]:
    """Call GPT-4o-mini to extract biographical events from article text."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set — skipping LLM extraction")
        return []

    client = OpenAI(api_key=api_key)

    user_msg = f"Artículo sobre {name}:\n\n{article_text}"

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            )
            raw = response.choices[0].message.content
            break
        except Exception as exc:
            logger.warning("LLM call attempt %d failed: %s", attempt + 1, exc)
            if attempt == 0:
                time.sleep(3)
            else:
                return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("LLM returned invalid JSON for %s", name)
        return []

    raw_events = data.get("events", data.get("biographical_events", []))
    if isinstance(raw_events, dict):
        raw_events = [raw_events]

    events: list[BioEvent] = []
    for item in raw_events:
        if not isinstance(item, dict):
            continue
        loc = None
        if "location" in item and isinstance(item["location"], dict):
            loc = Location(
                city=item["location"].get("city", ""),
                country=item["location"].get("country", ""),
            )
        evt = BioEvent(
            date=str(item.get("date", "0000-01-01")),
            event_type=str(item.get("event_type", "professional_milestone")),
            description=str(item.get("description", "")),
            valence=str(item.get("valence", "neutral")),
            confidence=str(item.get("confidence", "medium")),
            location=loc,
        )
        # Normalise invalid values
        if evt.valence not in ("positive", "negative", "neutral"):
            evt.valence = "neutral"
        if evt.confidence not in ("high", "medium", "low"):
            evt.confidence = "medium"
        events.append(evt)

    logger.info("LLM extracted %d events for %s", len(events), name)
    return events
