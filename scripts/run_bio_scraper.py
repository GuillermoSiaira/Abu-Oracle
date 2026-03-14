"""Run the bio scraper pipeline for all 13 subjects."""
import sys
import os
import logging

sys.path.insert(0, ".")

# Load .env if present (for OPENAI_API_KEY)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
    stream=sys.stdout,
)

from scripts.bio_scraper.pipeline import run_pipeline

summary = run_pipeline()

print("\n" + "=" * 55)
print(f"{'Subject':<25} {'Events':>7} {'High':>6} {'w/Loc':>6}")
print("-" * 55)
for slug, info in summary.items():
    print(f"{info['name']:<25} {info['n_events']:>7} {info['n_high_confidence']:>6} {info['n_with_location']:>6}")
print("=" * 55)
