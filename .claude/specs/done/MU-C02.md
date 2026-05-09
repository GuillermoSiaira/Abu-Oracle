# MU-C02 — Daily Content Pipeline: Calendar-driven + Multilingual

## Context

The mundana publisher (`scripts/mundana/`) currently runs daily via Cloud Run Job and publishes
single-language (Spanish) posts based on *current sky configurations only*. Two problems:

1. **Only posts when a significant config is found** — with the new 13-config detector this happens
   more often, but it still misses the rich calendar data: upcoming eclipses, Mercury Rx stations,
   Jupiter/Saturn ingresses. These are always happening and have editorial value.
2. **Only Spanish** — the app serves ES/EN/FR/PT users. Content should match the audience.

Goal: enhance the publisher to (a) draw content from the mundana calendar endpoint, and (b)
generate and publish in multiple languages.

## Files to modify / create

```
scripts/mundana/content_generator.py         MODIFY — add lang param + calendar input
scripts/mundana/main_publisher.py            MODIFY — fetch calendar, enrich content_input
scripts/mundana/calendar_content.py          NEW    — calendar event → platform copy
scripts/mundana/publishers/__init__.py       MODIFY — add lang tag to published posts
scripts/mundana/Dockerfile                   no change
requirements-mundana.txt                     no change
```

## Spec

### 1. `calendar_content.py` — New module

```python
"""
Generate social copy for upcoming calendar events (eclipses, Mercury Rx, ingresses).
Called when no high-priority current-sky config is found, or to supplement the daily post.
"""

from dataclasses import dataclass
from typing import Literal

CalendarEventType = Literal[
    "eclipse_solar", "eclipse_lunar",
    "mercury_retrograde", "mercury_direct",
    "planet_ingress"
]

@dataclass
class CalendarEvent:
    type: CalendarEventType
    date: str           # YYYY-MM-DD
    description: str    # already formatted in Spanish from the endpoint
    significance: str   # "high" | "medium"
    details: dict

def should_announce(event: CalendarEvent, today_str: str) -> bool:
    """Announce if event is within the next 7 days."""
    from datetime import date, timedelta
    event_date = date.fromisoformat(event.date)
    today = date.fromisoformat(today_str)
    return timedelta(0) <= (event_date - today) <= timedelta(days=7)

def generate_calendar_post(event: CalendarEvent, platform: str, lang: str) -> str:
    """
    Use Claude to write a short post about an upcoming calendar event.
    System prompt: Lilly's voice, doctrinal, ~2-3 sentences.
    max_tokens: 300
    """
    import anthropic
    from .content_generator import _get_client, _platform_limits

    system = (
        "Eres Lilly, astrólogo intérprete de Abu Oracle. "
        "Escribe en primera persona del plural astrologico. "
        "Breve, directo, doctrinal. Sin hashtags. Sin emojis a menos que la plataforma lo requiera."
    ) if lang == "es" else (
        "You are Lilly, Abu Oracle's astrological interpreter. "
        "Write in a doctrinal, precise voice. No hashtags. "
        "2-3 sentences max."
    )

    prompt = (
        f"Upcoming celestial event in {event.date}: {event.description}.\n"
        f"Write a {platform} post (max {_platform_limits[platform]} chars) "
        f"in {lang} about this event's astrological significance."
    )

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
```

### 2. `content_generator.py` — Add `lang` parameter

```python
# Add to generate_post() signature:
def generate_post(config: dict, platform: str, history: list, lang: str = "es") -> str:
    ...
    # System prompt now ends with:
    lang_instruction = {
        "es": "Escribe en español.",
        "en": "Write in English.",
        "fr": "Écris en français.",
        "pt": "Escreve em português.",
    }.get(lang, "Write in Spanish.")
    system = LILLY_VOICE_PROMPT + f"\n\n{lang_instruction}"
    ...
```

### 3. `main_publisher.py` — Fetch calendar + multi-lang loop

```python
import os
import requests
from datetime import date

LANGUAGES = [l.strip() for l in os.environ.get("LANGUAGES", "es").split(",")]
ABU_ENGINE_URL = os.environ.get("ABU_ENGINE_URL", "http://localhost:8000")
CALENDAR_MONTHS = int(os.environ.get("CALENDAR_MONTHS", "3"))

def fetch_calendar() -> list[dict]:
    """GET /api/mundana/calendar?months=3 from Abu Engine."""
    try:
        r = requests.get(
            f"{ABU_ENGINE_URL}/api/mundana/calendar",
            params={"months": CALENDAR_MONTHS},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("events", [])
    except Exception as e:
        print(f"[calendar] fetch failed: {e}")
        return []

def run():
    today = date.today().isoformat()
    platforms = [p.strip() for p in os.environ.get("PLATFORMS", "bluesky").split(",")]
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    # 1. Get current sky config (existing logic)
    config = get_best_configuration()

    # 2. Get calendar events for upcoming announcements
    calendar_events = fetch_calendar()
    upcoming = [
        e for e in calendar_events
        if should_announce(CalendarEvent(**e), today)
        and e.get("significance") in ("high", "medium")
    ]

    for lang in LANGUAGES:
        for platform in platforms:
            if config and should_publish(config, registry):
                content = generate_post(config, platform, history, lang=lang)
                tag = f"[{lang}]" if len(LANGUAGES) > 1 else ""
                publish_all(platform, f"{tag} {content}".strip(), lang=lang)
                log_registry(config, platform, lang)

            elif upcoming:
                # Post about the most significant upcoming event
                event = max(upcoming, key=lambda e: e.get("significance") == "high")
                from calendar_content import generate_calendar_post, CalendarEvent
                content = generate_calendar_post(CalendarEvent(**event), platform, lang)
                publish_all(platform, content, lang=lang)
                print(f"[{lang}] calendar post for {event['date']}: {event['description']}")
            else:
                print(f"[{lang}/{platform}] nothing to publish today")
```

### 4. `publishers/__init__.py` — Add optional `lang` tag

```python
def publish_all(platform: str, content: str, lang: str = "es") -> None:
    """Dispatch to the right publisher. For multi-lang runs, content already has lang tag if needed."""
    if platform == "bluesky":
        from .bluesky_publisher import publish as bluesky_publish
        bluesky_publish(content)
    elif platform == "twitter":
        from .twitter_publisher import publish as twitter_publish
        twitter_publish(content)
    elif platform == "farcaster":
        from .farcaster_publisher import publish as farcaster_publish
        farcaster_publish(content)
    # reddit, instagram, etc.
```

### 5. Cloud Run Job env vars to add

```
LANGUAGES=es,en          # comma-separated; default "es"
CALENDAR_MONTHS=3        # how many months of calendar to check
```

## Acceptance criteria

- [ ] `calendar_content.py` exists with `should_announce()` and `generate_calendar_post()`
- [ ] `generate_post()` in `content_generator.py` accepts `lang` param and translates system prompt
- [ ] `main_publisher.py` fetches calendar and falls back to calendar event when no sky config qualifies
- [ ] `publish_all()` accepts optional `lang` param (no breaking change)
- [ ] `LANGUAGES=es,en` env var causes the pipeline to generate two posts per platform per run
- [ ] `DRY_RUN=true` still works with multi-lang content (prints to stdout, no network calls)
- [ ] No new Python dependencies required

## Notes

- Do NOT publish multiple languages to the same Bluesky account simultaneously — they should go
  to different accounts or be separate posts. For now, when `LANGUAGES` has multiple values,
  publish ONE post that alternates languages per day (modulo `date.today().toordinal() % len(LANGUAGES)`).
- The Abu Engine must be running and accessible at `ABU_ENGINE_URL` for calendar fetch to work.
  If the fetch fails, fall back to sky-only mode (existing behavior).
