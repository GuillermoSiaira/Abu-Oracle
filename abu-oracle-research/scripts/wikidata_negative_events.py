"""
Wikidata Negative Events Scraper for Abu Oracle Research
=========================================================
Searches Wikidata for career-negative events for each subject in the corpus.
Outputs wikidata_candidates.csv with anonymised event candidates.

Usage:
    python wikidata_negative_events.py

Requirements:
    pip install SPARQLWrapper pandas
"""

import csv
import hashlib
import json
import os
import time
from datetime import datetime

import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON

# --- Subject mapping: subject_id -> (name, Wikidata QID) ------------------
# QIDs sourced from Wikidata (verified manually for each subject)
SUBJECTS = {
    "106715": ("Jim Morrison",     "Q72389"),
    "113610": ("Edith Piaf",       "Q1631"),
    "12145":  ("Jorge Luis Borges","Q80183"),
    "14525":  ("Ingrid Bergman",   "Q55185"),
    "16510":  ("Marilyn Monroe",   "Q4616"),
    "2280":   ("Neil Armstrong",   "Q1615"),
    "232580": ("Elvis Presley",    "Q303"),
    "232650": ("David Bowie",      "Q5383"),
    "239610": ("Muhammad Ali",     "Q36107"),
    "240895": ("Janis Joplin",     "Q1443"),
    "288130": ("James Dean",       "Q83359"),
    "308660": ("Albert Einstein",  "Q937"),
    "317785": ("Vincent van Gogh", "Q5582"),
    "336770": ("Audrey Hepburn",   "Q4345"),
    "337730": ("Sigmund Freud",    "Q9215"),
    "349770": ("Miles Davis",      "Q93341"),
    "35255":  ("Frida Kahlo",      "Q5588"),
    "61360":  ("Mohandas Gandhi",  "Q1001"),
    "70110":  ("Oscar Wilde",      "Q30875"),
    "76835":  ("Pablo Picasso",    "Q5593"),
    "9945":   ("Coco Chanel",      "Q45661"),
    "99810":  ("Bruce Lee",        "Q83287"),
    "99835":  ("Jimi Hendrix",     "Q5928"),
    "GS_001": ("Carl Gustav Jung", "Q131814"),
    "GS_002": ("Nikola Tesla",     "Q9036"),
    "GS_003": ("Alan Turing",      "Q7251"),
}

# Wikidata endpoint
ENDPOINT = "https://query.wikidata.org/sparql"
RATE_LIMIT_SLEEP = 1.5  # seconds between requests

# --- SPARQL templates -------------------------------------------------------

SPARQL_SIGNIFICANT_EVENTS = """
SELECT DISTINCT ?event ?eventLabel ?date ?typeLabel WHERE {{
  wd:{qid} p:P793 ?stmt .
  ?stmt ps:P793 ?event .
  OPTIONAL {{ ?stmt pq:P585 ?date }}
  OPTIONAL {{ ?event wdt:P31 ?type }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,es" }}
}}
ORDER BY ?date
"""

SPARQL_NOMINATIONS = """
SELECT DISTINCT ?award ?awardLabel ?date WHERE {{
  wd:{qid} wdt:P1411 ?award .
  OPTIONAL {{ wd:{qid} p:P1411 ?stmt .
             ?stmt ps:P1411 ?award .
             ?stmt pq:P585 ?date }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
"""

SPARQL_LEGAL = """
SELECT DISTINCT ?offenseLabel ?date WHERE {{
  wd:{qid} p:P1399 ?stmt .
  ?stmt ps:P1399 ?offense .
  OPTIONAL {{ ?stmt pq:P585 ?date }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
"""

# Keywords that suggest negative career outcomes
NEGATIVE_KEYWORDS = [
    "cancel", "fail", "reject", "banned", "controversy", "lawsuit",
    "fired", "resign", "bankrupt", "loss", "defeat", "acquit", "arrest",
    "convict", "suspend", "flop", "withdrawal", "dismiss", "discharg",
    "expel", "prohibit", "censor", "banned", "closure",
]

# Keywords that suggest health/death (exclude from H10)
HEALTH_DEATH_KEYWORDS = [
    "death", "died", "illness", "disease", "hospital", "surgery",
    "overdose", "suicide", "accident", "injury", "diagnosis",
]


def event_id(subject_id: str, date: str) -> str:
    """Create anonymised event ID from subject_id + date."""
    raw = f"{subject_id}_{date}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def is_negative_career(label: str) -> bool:
    label_lower = label.lower()
    has_negative = any(kw in label_lower for kw in NEGATIVE_KEYWORDS)
    has_health = any(kw in label_lower for kw in HEALTH_DEATH_KEYWORDS)
    return has_negative and not has_health


def parse_wikidata_date(date_str: str) -> tuple:
    """Parse Wikidata date string. Returns (date_str_clean, precision)."""
    if not date_str:
        return None, None
    # Wikidata dates: "+1943-11-15T00:00:00Z" or "1943-11-15T00:00:00Z"
    date_str = date_str.lstrip("+").rstrip("Z")
    if "T" in date_str:
        date_str = date_str.split("T")[0]
    # Check precision
    parts = date_str.split("-")
    if len(parts) >= 3 and all(p != "00" for p in parts):
        return date_str, "day"
    elif len(parts) >= 2 and parts[1] != "00":
        return f"{parts[0]}-{parts[1]}", "month"
    elif len(parts) >= 1:
        return parts[0], "year"
    return date_str, "unknown"


def run_sparql(query: str, endpoint: str = ENDPOINT) -> list:
    """Execute SPARQL query and return results."""
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomHttpHeader("User-Agent", "AbuOracleResearch/1.0 (research; contact: research@abu-oracle.com)")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        print(f"  SPARQL error: {e}")
        return []


def scrape_subject(subject_id: str, name: str, qid: str) -> list:
    """Scrape negative events for one subject. Returns list of candidate dicts."""
    candidates = []

    print(f"  Scraping {name} ({qid})...")

    # 1. Significant events (P793)
    results = run_sparql(SPARQL_SIGNIFICANT_EVENTS.format(qid=qid))
    time.sleep(RATE_LIMIT_SLEEP)
    for r in results:
        label = r.get("eventLabel", {}).get("value", "")
        date_raw = r.get("date", {}).get("value", "")
        date_clean, precision = parse_wikidata_date(date_raw)
        event_url = r.get("event", {}).get("value", "")
        if label and is_negative_career(label):
            candidates.append({
                "subject_id": subject_id,
                "subject_name": name,
                "event_date": date_clean or "",
                "event_type_wikidata": "significant_event_P793",
                "event_description": label,
                "wikidata_url": event_url,
                "date_precision": precision or "unknown",
                "needs_manual_review": True,
            })

    # 2. Nominations (P1411) — nominated but presumably did not win
    results = run_sparql(SPARQL_NOMINATIONS.format(qid=qid))
    time.sleep(RATE_LIMIT_SLEEP)
    for r in results:
        label = r.get("awardLabel", {}).get("value", "")
        date_raw = r.get("date", {}).get("value", "")
        date_clean, precision = parse_wikidata_date(date_raw)
        award_url = r.get("award", {}).get("value", "")
        # Nominations without a corresponding win (P166) are potential "losses"
        candidates.append({
            "subject_id": subject_id,
            "subject_name": name,
            "event_date": date_clean or "",
            "event_type_wikidata": "nomination_not_won_P1411",
            "event_description": f"Nominated for: {label}",
            "wikidata_url": award_url,
            "date_precision": precision or "unknown",
            "needs_manual_review": True,
        })

    # 3. Legal convictions (P1399)
    results = run_sparql(SPARQL_LEGAL.format(qid=qid))
    time.sleep(RATE_LIMIT_SLEEP)
    for r in results:
        label = r.get("offenseLabel", {}).get("value", "")
        date_raw = r.get("date", {}).get("value", "")
        date_clean, precision = parse_wikidata_date(date_raw)
        if label:
            candidates.append({
                "subject_id": subject_id,
                "subject_name": name,
                "event_date": date_clean or "",
                "event_type_wikidata": "legal_conviction_P1399",
                "event_description": f"Convicted of: {label}",
                "wikidata_url": f"https://www.wikidata.org/wiki/{qid}#P1399",
                "date_precision": precision or "unknown",
                "needs_manual_review": False,
            })

    return candidates


def main():
    os.makedirs("abu-oracle-research/data/corpus", exist_ok=True)
    output_path = "abu-oracle-research/data/corpus/wikidata_candidates.csv"

    all_candidates = []
    summary = []

    for subject_id, (name, qid) in SUBJECTS.items():
        candidates = scrape_subject(subject_id, name, qid)

        # Filter: require date with at least year precision
        valid = [c for c in candidates if c["event_date"] and c["event_date"] != ""]
        no_date = len(candidates) - len(valid)

        # Anonymise: remove subject_name, compute event_id
        for c in valid:
            c["event_id"] = event_id(c["subject_id"], c["event_date"])
            del c["subject_name"]
            del c["subject_id"]

        all_candidates.extend(valid)
        summary.append({
            "subject_id": subject_id,
            "name": name,
            "qid": qid,
            "candidates_found": len(candidates),
            "with_date": len(valid),
            "needs_review": sum(1 for c in valid if c["needs_manual_review"]),
            "no_date_discarded": no_date,
        })
        print(f"    -> {len(candidates)} candidates, {len(valid)} with date")

    # Save candidates CSV
    if all_candidates:
        fieldnames = ["event_id", "event_date", "event_type_wikidata",
                      "event_description", "wikidata_url", "date_precision",
                      "needs_manual_review"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_candidates)

    # Save summary JSON
    summary_path = "abu-oracle-research/data/corpus/wikidata_scrape_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_date": datetime.utcnow().isoformat(),
            "total_candidates": len(all_candidates),
            "subjects": summary,
        }, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n=== SCRAPER SUMMARY ===")
    print(f"Total candidates with date: {len(all_candidates)}")
    needs_review = sum(1 for c in all_candidates if c["needs_manual_review"])
    ready = len(all_candidates) - needs_review
    print(f"  Ready (legal convictions): {ready}")
    print(f"  Needs manual review: {needs_review}")
    print(f"\nPer subject:")
    for s in sorted(summary, key=lambda x: -x["candidates_found"]):
        print(f"  {s['name']:25s}: {s['candidates_found']:3d} found, {s['with_date']:3d} with date")
    print(f"\nOutputs:")
    print(f"  {output_path}")
    print(f"  {summary_path}")


if __name__ == "__main__":
    main()
