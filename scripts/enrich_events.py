"""Tarea 2.2 — Enrich biographical events with house_domain.

Reads all JSON files from data/biographical_events/,
adds field `house_domain: int` to each event using config/event_house_map.json,
and writes enriched files to data/biographical_events_v2/.

Usage:
    python scripts/enrich_events.py

Output:
    data/biographical_events_v2/<original_filename>
        Same structure as source, with `house_domain` added to each event.
        Events with unmapped event_type get house_domain = 0.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR   = REPO_ROOT / "data" / "biographical_events"
DST_DIR   = REPO_ROOT / "data" / "biographical_events_v2"
MAP_PATH  = REPO_ROOT / "config" / "event_house_map.json"


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
    unmapped_types: set[str] = set()

    for src_path in files:
        try:
            data = json.loads(src_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  SKIP {src_path.name}: {e}")
            continue

        events = data.get("biographical_events", [])
        enriched = 0
        for event in events:
            event_type = event.get("event_type", "")
            house = house_map.get(event_type, 0)
            event["house_domain"] = house
            if house:
                enriched += 1
            else:
                unmapped_types.add(event_type)
            total_events += 1
            total_mapped += bool(house)

        dst_path = DST_DIR / src_path.name
        dst_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  {src_path.name}: {len(events)} events, {enriched} mapped")

    print(f"\nTotal: {total_mapped}/{total_events} events mapped "
          f"({100 * total_mapped / total_events:.1f}%)")
    if unmapped_types:
        print(f"Unmapped event_types: {sorted(unmapped_types)}")
    else:
        print("All event_types mapped.")
    print(f"Output: {DST_DIR}")


if __name__ == "__main__":
    main()
