from __future__ import annotations

import csv
import json
from pathlib import Path

from cartanatal.parser import parse_profile
from cartanatal.scraper import CartanatalClient, BASE_URL

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
IDS_CSV = RAW_DIR / "ids.csv"
OUTPUT_JSONL = RAW_DIR / "raw_birthdata.jsonl"


def load_ids() -> list[int]:
    if not IDS_CSV.exists():
        raise FileNotFoundError(f"Missing ids file: {IDS_CSV}. Run crawl_ids.py first.")
    ids = []
    with IDS_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ids.append(int(row["id"]))
            except Exception:
                continue
    return ids


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    ids = load_ids()
    client = CartanatalClient(cache_dir=CACHE_DIR)

    with OUTPUT_JSONL.open("w", encoding="utf-8") as out:
        for idx, pid in enumerate(ids, start=1):
            url = f"{BASE_URL}astrodata/famosos/carta.php?id={pid}"
            html = client.fetch_profile(pid)
            record = parse_profile(html, pid, url)
            out.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            if idx % 50 == 0:
                print(f"Parsed {idx}/{len(ids)} profiles...")

    print(f"Wrote {len(ids)} records to {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
