"""Tarea 2.2 — Enrich biographical events with house_domain.

Reads all JSON files from data/biographical_events/,
adds field `house_domain: int | null` to each event using config/event_house_map.json,
and writes enriched files to data/biographical_events_v2/.

Events whose event_type is not in the map receive house_domain: null.
Analysis/output files (correlation_results.json, optimization_results.json,
cross_validation_results.json) are skipped.

Usage:
    python scripts/enrich_events.py

Output:
    data/biographical_events_v2/<original_filename>
        Same structure as source, with `house_domain` added to each event.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR   = REPO_ROOT / "data" / "biographical_events"
DST_DIR   = REPO_ROOT / "data" / "biographical_events_v2"
MAP_PATH  = REPO_ROOT / "config" / "event_house_map.json"

# These files live in biographical_events/ but are analysis outputs, not subject files.
SKIP_FILES = {
    "correlation_results.json",
    "optimization_results.json",
    "cross_validation_results.json",
}


def main() -> None:
    house_map: dict[str, int] = {
        k: v for k, v in json.loads(MAP_PATH.read_text(encoding="utf-8")).items()
        if not k.startswith("_")
    }

    DST_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(SRC_DIR.glob("*.json"))
    if not files:
        print(f"No JSON files found in {SRC_DIR}")
        return

    total_events = 0
    total_mapped = 0
    house_distribution: dict[int, int] = defaultdict(int)
    unmapped_log: list[tuple[str, str]] = []  # (slug, event_type)

    for src_path in files:
        if src_path.name in SKIP_FILES:
            print(f"  SKIP (analysis file): {src_path.name}")
            continue

        try:
            data = json.loads(src_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  SKIP {src_path.name}: {e}")
            continue

        slug = src_path.stem  # e.g. "12145_borges"

        # Support both key conventions used across the dataset
        events_key = "biographical_events" if "biographical_events" in data else "events"
        events: list[dict] = data.get(events_key, [])

        enriched = 0
        for event in events:
            event_type = event.get("event_type") or event.get("type") or ""
            # None (JSON null) for unmapped types — intentional per spec
            house: int | None = house_map.get(event_type)
            event["house_domain"] = house

            total_events += 1
            if house is not None:
                enriched += 1
                total_mapped += 1
                house_distribution[house] += 1
            else:
                unmapped_log.append((slug, event_type))

        dst_path = DST_DIR / src_path.name
        dst_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  {src_path.name}: {len(events)} events, {enriched} mapped")

    # -----------------------------------------------------------------------
    # Summary report
    # -----------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"Files written to: {DST_DIR}")
    print(f"Total events processed:        {total_events}")
    print(f"Events with house_domain:      {total_mapped}  "
          f"({100 * total_mapped / total_events:.1f}%)" if total_events else "")
    print(f"Events with house_domain null: {len(unmapped_log)}")

    print("\nDistribution by house_domain (sorted by house number):")
    for house in sorted(house_distribution.keys()):
        count = house_distribution[house]
        bar = "#" * (count // 3)
        print(f"  H{house:02d}  {count:>4}  {bar}")

    if unmapped_log:
        # Group by event_type for a concise display, then by slug
        from collections import defaultdict as dd
        by_type: dict[str, list[str]] = dd(list)
        for slug, event_type in unmapped_log:
            by_type[event_type].append(slug)

        print(f"\nEvents with house_domain: null — {len(unmapped_log)} events "
              f"across {len(by_type)} unmapped type(s):")
        for event_type in sorted(by_type.keys()):
            slugs = by_type[event_type]
            print(f"\n  event_type: '{event_type}'  ({len(slugs)} events)")
            for slug in sorted(set(slugs)):
                n = slugs.count(slug)
                print(f"    {slug}  ×{n}")
    else:
        print("\nNo unmapped events — all event types covered.")

    print("\nDone.")


if __name__ == "__main__":
    main()
