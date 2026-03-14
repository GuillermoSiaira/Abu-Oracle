"""Pipeline: orchestrate Wikidata + Wikipedia/LLM → merge → dedup → geocode → export."""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from .models import BioEvent, BioEventFile, SubjectMeta, VALID_EVENT_TYPES
from .subjects import Subject, SUBJECTS
from .wikidata import query_wikidata
from .wikipedia import fetch_article
from .llm_extractor import extract_events
from .geocoder import enrich_events

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "biographical_events"
GOLD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "gold_standard"


def _parse_date(d: str) -> datetime | None:
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d")
    except Exception:
        return None


def _merge_and_dedup(wikidata_events: List[BioEvent], llm_events: List[BioEvent]) -> List[BioEvent]:
    """Merge two event lists, deduplicating by date proximity + event_type."""
    merged: list[BioEvent] = []
    used_llm: set[int] = set()

    for wd_evt in wikidata_events:
        wd_date = _parse_date(wd_evt.date)
        duplicate_idx = None

        if wd_date:
            for i, llm_evt in enumerate(llm_events):
                if i in used_llm:
                    continue
                llm_date = _parse_date(llm_evt.date)
                if llm_date and wd_evt.event_type == llm_evt.event_type:
                    if abs((wd_date - llm_date).days) <= 7:
                        duplicate_idx = i
                        break

        if duplicate_idx is not None:
            # Prefer the richer one (LLM usually has better description)
            llm_dup = llm_events[duplicate_idx]
            used_llm.add(duplicate_idx)
            # Keep Wikidata's date (more reliable) but LLM's description if present
            best = BioEvent(
                date=wd_evt.date,
                event_type=wd_evt.event_type,
                description=llm_dup.description or wd_evt.description,
                valence=llm_dup.valence if llm_dup.valence != "neutral" else wd_evt.valence,
                confidence=wd_evt.confidence,  # Wikidata dates are reliable
                location=wd_evt.location or llm_dup.location,
                validation_target=wd_evt.validation_target,
            )
            merged.append(best)
        else:
            merged.append(wd_evt)

    # Add remaining LLM events
    for i, llm_evt in enumerate(llm_events):
        if i not in used_llm:
            merged.append(llm_evt)

    # Sort by date
    merged.sort(key=lambda e: e.date)

    # Remove events with invalid types
    merged = [e for e in merged if e.event_type in VALID_EVENT_TYPES]

    # Remove undated placeholder events
    merged = [e for e in merged if e.date != "0000-01-01"]

    return merged


def _load_gold_standard_events(subject: Subject) -> List[BioEvent]:
    """Load existing gold standard events to preserve them in merge."""
    gs_map = {
        "GS_001": "GS_001_JUNG.json",
        "GS_002": "GS_002_TESLA.json",
        "GS_003": "GS_003_TURING.json",
    }
    filename = gs_map.get(subject.id)
    if not filename:
        return []

    gs_path = GOLD_DIR / filename
    if not gs_path.exists():
        return []

    with open(gs_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    events: list[BioEvent] = []
    for item in data.get("biographical_events", []):
        from .models import Location, ValidationTarget
        loc = None
        if "location" in item:
            loc = Location(**item["location"])
        vt = None
        if "validation_target" in item:
            vt = ValidationTarget(**item["validation_target"])
        events.append(BioEvent(
            date=item["date"],
            event_type=item["event_type"],
            description=item["description"],
            valence=item.get("valence", "neutral"),
            confidence=item.get("confidence", "high"),
            location=loc,
            validation_target=vt,
        ))
    return events


def process_subject(subject: Subject) -> BioEventFile:
    """Run full pipeline for one subject."""
    logger.info("━━━ Processing: %s (%s) ━━━", subject.name, subject.slug)

    # 1. Wikidata SPARQL
    logger.info("  [1/5] Querying Wikidata for %s …", subject.wikidata_qid)
    wd_events = query_wikidata(subject.wikidata_qid)
    logger.info("  → %d events from Wikidata", len(wd_events))

    # 2. Wikipedia → LLM extraction
    logger.info("  [2/5] Downloading Wikipedia article …")
    try:
        article = fetch_article(subject.wikipedia_title, lang="en")
        logger.info("  → Article length: %d chars", len(article))
    except Exception as exc:
        logger.warning("  → Wikipedia download failed: %s", exc)
        article = ""

    llm_events: list[BioEvent] = []
    if article:
        logger.info("  [3/5] Extracting events via LLM …")
        llm_events = extract_events(subject.name, article)
        logger.info("  → %d events from LLM", len(llm_events))
    else:
        logger.info("  [3/5] Skipping LLM (no article)")

    # 3. Load gold standard events if applicable
    gs_events = _load_gold_standard_events(subject)
    if gs_events:
        logger.info("  → %d events from gold standard", len(gs_events))

    # 4. Merge + dedup
    logger.info("  [4/5] Merging and deduplicating …")
    all_events = _merge_and_dedup(wd_events, llm_events)

    # Ensure gold standard events are preserved (match by date+type)
    gs_dates_types = {(e.date, e.event_type) for e in all_events}
    for gs_evt in gs_events:
        if (gs_evt.date, gs_evt.event_type) not in gs_dates_types:
            all_events.append(gs_evt)
    all_events.sort(key=lambda e: e.date)

    logger.info("  → %d events after merge", len(all_events))

    # 5. Geocoding
    logger.info("  [5/5] Geocoding locations …")
    all_events = enrich_events(all_events)

    # Validate
    for evt in all_events:
        errors = evt.validate()
        if errors:
            logger.warning("  Validation: %s — %s", evt.date, errors)

    meta = SubjectMeta(id=subject.id, name=subject.name)
    return BioEventFile(meta=meta, biographical_events=all_events)


def run_pipeline(subjects: list[Subject] | None = None) -> dict[str, dict]:
    """Run pipeline for all (or selected) subjects. Returns summary dict."""
    if subjects is None:
        subjects = SUBJECTS

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary: dict[str, dict] = {}
    for subj in subjects:
        result = process_subject(subj)

        # Determine filename
        if subj.id.startswith("GS_"):
            gs_names = {"GS_001": "GS_001_JUNG", "GS_002": "GS_002_TESLA", "GS_003": "GS_003_TURING"}
            fname = gs_names.get(subj.id, f"{subj.id}_{subj.slug}") + ".json"
        else:
            fname = f"{subj.id}_{subj.slug}.json"

        out_path = OUTPUT_DIR / fname
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result.to_json())

        n_events = len(result.biographical_events)
        n_high = sum(1 for e in result.biographical_events if e.confidence == "high")
        n_with_loc = sum(1 for e in result.biographical_events if e.location is not None)

        summary[subj.slug] = {
            "name": subj.name,
            "n_events": n_events,
            "n_high_confidence": n_high,
            "n_with_location": n_with_loc,
            "output_file": str(out_path),
        }
        logger.info("  ✓ Saved %s → %d events (high=%d, loc=%d)",
                     fname, n_events, n_high, n_with_loc)

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    summary = run_pipeline()
    print("\n═══ SUMMARY ═══")
    print(f"{'Subject':<20} {'Events':>7} {'High':>6} {'w/Loc':>6}")
    print("─" * 45)
    for slug, info in summary.items():
        print(f"{info['name']:<20} {info['n_events']:>7} {info['n_high_confidence']:>6} {info['n_with_location']:>6}")
