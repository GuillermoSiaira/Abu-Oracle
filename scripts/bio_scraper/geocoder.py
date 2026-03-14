"""Geocoder: resolve city+country → lat/lon via Nominatim (OSM)."""
from __future__ import annotations
import logging
import time

import requests

from .models import BioEvent

logger = logging.getLogger(__name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "AIOracleBioScraper/1.0 (research; contact@ai-oracle.dev)",
})

# In-memory cache to avoid repeated Nominatim calls
_cache: dict[str, tuple[float, float] | None] = {}


def geocode(city: str, country: str) -> tuple[float, float] | None:
    """Return (lat, lon) for a city+country pair, or None."""
    key = f"{city}|{country}".lower()
    if key in _cache:
        return _cache[key]

    query = f"{city}, {country}" if country else city
    try:
        resp = _SESSION.get(
            _NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": "1"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            _cache[key] = (lat, lon)
            return (lat, lon)
    except Exception as exc:
        logger.debug("Geocoding failed for '%s': %s", query, exc)

    _cache[key] = None
    return None


def enrich_events(events: list[BioEvent]) -> list[BioEvent]:
    """Add lat/lon to events that have city+country but no coordinates."""
    for evt in events:
        if evt.location and evt.location.city and evt.location.lat is None:
            coords = geocode(evt.location.city, evt.location.country)
            if coords:
                evt.location.lat, evt.location.lon = coords
            # Respect Nominatim rate limit: 1 req/sec
            time.sleep(1.1)
    return events
