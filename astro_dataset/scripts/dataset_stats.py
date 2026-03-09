from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
INPUT_JSONL = RAW_DIR / "raw_birthdata.jsonl"


def main() -> None:
    if not INPUT_JSONL.exists():
        raise FileNotFoundError(f"Missing dataset: {INPUT_JSONL}. Run parse_profiles.py first.")

    rr_counter: Counter[str] = Counter()
    tp_counter: Counter[str] = Counter()
    missing_coords = 0
    total = 0

    with INPUT_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            total += 1
            rr_counter[rec.get("rodden_rating") or "unknown"] += 1
            tp_counter[rec.get("time_precision") or "unknown"] += 1
            if rec.get("latitude") is None or rec.get("longitude") is None:
                missing_coords += 1

    print(f"Total profiles: {total}")
    print("RR distribution:")
    for rr, count in rr_counter.most_common():
        print(f"  {rr}: {count}")
    print("time_precision distribution:")
    for tp, count in tp_counter.most_common():
        print(f"  {tp}: {count}")
    print(f"Missing coords: {missing_coords}")


if __name__ == "__main__":
    main()
