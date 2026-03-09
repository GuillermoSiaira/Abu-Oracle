from __future__ import annotations

import csv
from pathlib import Path

from cartanatal.scraper import CartanatalClient

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
IDS_CSV = RAW_DIR / "ids.csv"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    client = CartanatalClient(cache_dir=CACHE_DIR)
    ids = client.crawl_ids()

    with IDS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id"])
        for pid in ids:
            writer.writerow([pid])

    print(f"Discovered {len(ids)} profile ids. Written to {IDS_CSV}")


if __name__ == "__main__":
    main()
