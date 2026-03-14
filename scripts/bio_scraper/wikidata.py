"""Wikidata SPARQL queries → structured biographical events."""
from __future__ import annotations
import logging
import time
from typing import List

from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON

from .models import BioEvent, Location

logger = logging.getLogger(__name__)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "AIOracleBioScraper/1.0 (research; contact@ai-oracle.dev)"

# ── Individual SPARQL queries (split for reliability) ──

_QUERIES: list[tuple[str, str, str]] = [
    # (event_type, query_fragment, valence)
    ("death", """
SELECT ?date ?placeLabel ?coord WHERE {{
  wd:{qid} wdt:P570 ?date .
  OPTIONAL {{ wd:{qid} wdt:P20 ?place . ?place wdt:P625 ?coord . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
""", "negative"),
    ("marriage", """
SELECT ?date ?spouseLabel WHERE {{
  wd:{qid} wdt:P26 ?spouse .
  OPTIONAL {{ wd:{qid} p:P26 ?stmt . ?stmt pq:P580 ?date . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
""", "positive"),
    ("birth_child", """
SELECT ?date ?childLabel WHERE {{
  wd:{qid} wdt:P40 ?child .
  OPTIONAL {{ ?child wdt:P569 ?date . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
""", "positive"),
    ("award", """
SELECT ?date ?awardLabel WHERE {{
  wd:{qid} p:P166 ?stmt .
  ?stmt ps:P166 ?award .
  OPTIONAL {{ ?stmt pq:P585 ?date . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} LIMIT 15
""", "positive"),
    ("education_start", """
SELECT ?date ?eduLabel WHERE {{
  wd:{qid} p:P69 ?stmt .
  ?stmt ps:P69 ?edu .
  OPTIONAL {{ ?stmt pq:P580 ?date . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
""", "neutral"),
]


def _parse_coord(wkt: str | None) -> tuple[float, float] | None:
    """Parse WKT Point string like 'Point(7.45 46.95)' → (lat, lon)."""
    if not wkt:
        return None
    try:
        inner = wkt.replace("Point(", "").replace(")", "").strip()
        lon_s, lat_s = inner.split()
        return float(lat_s), float(lon_s)
    except Exception:
        return None


def _sparql_date_to_iso(raw: str) -> str | None:
    """Extract YYYY-MM-DD from Wikidata datetime string."""
    if not raw:
        return None
    return raw[:10]


def _run_one(sparql_text: str) -> list[dict]:
    """Execute one SPARQL query and return bindings."""
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.addCustomHttpHeader("User-Agent", USER_AGENT)
    sparql.setQuery(sparql_text)
    sparql.setReturnFormat(SPARQL_JSON)
    sparql.setTimeout(30)
    results = sparql.query().convert()
    return results.get("results", {}).get("bindings", [])


def query_wikidata(qid: str) -> List[BioEvent]:
    """Run individual SPARQL queries and return a list of BioEvent objects."""
    events: list[BioEvent] = []
    seen: set[str] = set()

    for event_type, query_tmpl, valence in _QUERIES:
        query_text = query_tmpl.format(qid=qid)
        try:
            rows = _run_one(query_text)
        except Exception as exc:
            logger.warning("Wikidata query '%s' failed for %s: %s", event_type, qid, exc)
            time.sleep(1)
            continue

        for row in rows:
            raw_date = row.get("date", {}).get("value")
            date_iso = _sparql_date_to_iso(raw_date)

            # Build description from available labels
            if event_type == "death":
                desc = "Fallecimiento."
            elif event_type == "marriage":
                spouse = row.get("spouseLabel", {}).get("value", "?")
                desc = f"Matrimonio con {spouse}."
            elif event_type == "birth_child":
                child = row.get("childLabel", {}).get("value", "?")
                desc = f"Nacimiento de hijo/a: {child}."
            elif event_type == "award":
                award = row.get("awardLabel", {}).get("value", "?")
                desc = f"Premio: {award}."
            elif event_type == "education_start":
                edu = row.get("eduLabel", {}).get("value", "?")
                desc = f"Inicio de estudios en {edu}."
            else:
                desc = ""

            # Dedup key
            key = f"{event_type}|{date_iso}|{desc[:40]}"
            if key in seen:
                continue
            seen.add(key)

            location = None
            place_label = row.get("placeLabel", {}).get("value")
            coord_wkt = row.get("coord", {}).get("value")
            if place_label:
                lat_lon = _parse_coord(coord_wkt)
                location = Location(
                    city=place_label, country="",
                    lat=lat_lon[0] if lat_lon else None,
                    lon=lat_lon[1] if lat_lon else None,
                )

            confidence = "high" if date_iso and len(date_iso) == 10 else "low"
            if not date_iso:
                date_iso = "0000-01-01"
                confidence = "low"

            events.append(BioEvent(
                date=date_iso,
                event_type=event_type,
                description=desc,
                valence=valence,
                confidence=confidence,
                location=location,
            ))

        # Rate-limit between queries
        time.sleep(0.5)

    logger.info("Wikidata returned %d events for %s", len(events), qid)
    return events
