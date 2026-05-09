"""
Generate social copy for upcoming mundana calendar events.

Used when no high-priority current-sky configuration qualifies, or as a
calendar-driven fallback for eclipses, Mercury stations, and slow ingresses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

import anthropic
from anthropic import AnthropicVertex

try:
    from .content_generator import MODEL, PLATFORM_LIMITS, _lilly_system
except ImportError:
    from content_generator import MODEL, PLATFORM_LIMITS, _lilly_system


CalendarEventType = Literal[
    "eclipse_solar",
    "eclipse_lunar",
    "mercury_retrograde",
    "mercury_direct",
    "planet_ingress",
]


@dataclass
class CalendarEvent:
    type: CalendarEventType
    date: str
    description: str
    significance: str
    details: dict = field(default_factory=dict)


def should_announce(event: CalendarEvent, today_str: str) -> bool:
    """Announce if event is within the next 7 days."""
    event_date = date.fromisoformat(event.date[:10])
    today = date.fromisoformat(today_str)
    return timedelta(0) <= (event_date - today) <= timedelta(days=7)


def _get_client():
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    return AnthropicVertex(
        project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "abu-oracle"),
        region=os.environ.get("VERTEX_REGION", "us-east5"),
    )


def _lang_instruction(lang: str) -> str:
    return {
        "es": "Escribe en espanol.",
        "en": "Write in English.",
        "fr": "Ecris en francais.",
        "pt": "Escreve em portugues.",
    }.get(lang, "Escribe en espanol.")


def generate_calendar_post(event: CalendarEvent, platform: str, lang: str) -> dict:
    """
    Use Claude to write a short post about an upcoming calendar event.
    Returns the same content shape used by publishers.publish_all().
    """
    limit = PLATFORM_LIMITS.get(platform, 300)
    prompt = (
        f"Upcoming celestial event on {event.date}: {event.description}.\n"
        f"Event type: {event.type}. Significance: {event.significance}.\n"
        f"Details: {event.details}\n\n"
        f"Write a {platform} post, maximum {limit} characters. "
        f"2-3 sentences max. No hashtags unless the platform requires them. "
        f"{_lang_instruction(lang)}"
    )

    client = _get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=_lilly_system(lang),
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip() if response.content else ""

    return {
        "text": text,
        "hashtags": [],
        "thread": None,
        "reddit_title": None,
        "image_prompt": "",
        "image_bytes": None,
        "image_alt": None,
        "platform": platform,
        "config_type": f"calendar_{event.type}",
        "style": "calendar",
        "lang": lang,
        "calendar_date": event.date,
    }
