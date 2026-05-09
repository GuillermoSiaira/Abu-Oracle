#!/usr/bin/env python3
"""
KG Experiment Runner - Condition A vs B.

Compares the baseline JSON timeline section with a serialized NetworkX
subgraph built from the same natal chart.
"""

from __future__ import annotations

import json
import os
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))
sys.path.insert(0, str(REPO_ROOT))

from core.chart_graph import build_chart_graph, get_key_planets, serialize_subgraph  # noqa: E402
from scripts.kg_experiment.assemble_context import build_timeline_section_a  # noqa: E402
from scripts.kg_experiment.config import ABU_ENGINE_URL, EVAL_PROMPT, SUBJECTS  # noqa: E402
from scripts.kg_experiment.judge import evaluate_pair  # noqa: E402

ABU_HEADERS: dict[str, str] = {}


def fetch_natal(subject: dict) -> dict:
    url = f"{ABU_ENGINE_URL}/analyze"
    payload = {
        "birthDate": subject["birthDate"],
        "lat": subject["lat"],
        "lon": subject["lon"],
        "name": subject["name"],
    }
    res = requests.post(url, json=payload, headers=ABU_HEADERS, timeout=30)
    res.raise_for_status()
    return res.json()


def fetch_biography(subject: dict) -> dict:
    url = f"{ABU_ENGINE_URL}/api/astro/biography"
    params = {
        "birthDate": subject["birthDate"].split("T")[0],
        "birthLat": subject["lat"],
        "birthLon": subject["lon"],
        "window_months": "18",
    }
    res = requests.get(url, params=params, headers=ABU_HEADERS, timeout=30)
    res.raise_for_status()
    return res.json()


def build_context_a(natal: dict, bio: dict) -> str:
    return build_timeline_section_a(bio, natal)


def build_context_b(natal: dict) -> str:
    graph = build_chart_graph(natal)
    derived = natal.get("derived", {})
    key_planets = get_key_planets(graph, derived)
    subgraph = serialize_subgraph(graph, key_planets)

    if not subgraph:
        subgraph = "[sin datos de senorios]"

    return "\n".join(
        [
            "=== SENORIOS ACTIVOS (KG) ===",
            subgraph,
            "==============================",
        ]
    )


def _text_from_response(response: object) -> str:
    content = getattr(response, "content", None) or []
    chunks: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            chunks.append(text)
    return "".join(chunks)


def call_lilly(context: str, subject: dict) -> str:
    del subject

    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")

    client = anthropic.Anthropic(api_key=api_key)
    system = (
        "Eres Lilly, astrologo clasico formado en la tradicion helenistica y persa. "
        "Interpretas cartas natales siguiendo la doctrina de Ptolomeo, Al-Biruni y William Lilly."
    )
    user_msg = f"{EVAL_PROMPT}\n\nContexto de la carta:\n{context}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )

    return _text_from_response(response)


def run_experiment() -> Path:
    results: list[dict] = []

    for subject in SUBJECTS:
        print(f"\n{'=' * 60}")
        print(f"Sujeto: {subject['name']} ({subject['id']})")
        print("=" * 60)

        try:
            print("  Fetching natal + biography...")
            natal = fetch_natal(subject)
            bio = fetch_biography(subject)
            time.sleep(1)

            print("  Building contexts A and B...")
            ctx_a = build_context_a(natal, bio)
            ctx_b = build_context_b(natal)

            print("  Calling Lilly with context A...")
            resp_a = call_lilly(ctx_a, subject)
            time.sleep(2)

            print("  Calling Lilly with context B...")
            resp_b = call_lilly(ctx_b, subject)
            time.sleep(2)

            print("  Evaluating pair...")
            scores = evaluate_pair(ctx_a, ctx_b, resp_a, resp_b)

            result = {
                "subject_id": subject["id"],
                "subject_name": subject["name"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_a": ctx_a,
                "context_b": ctx_b,
                "response_a": resp_a,
                "response_b": resp_b,
                "responses_distinct": resp_a.strip() != resp_b.strip(),
                "scores": scores,
            }
            results.append(result)

            print(f"  Scores A: {scores.get('total_a', '?')} | B: {scores.get('total_b', '?')}")
        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append(
                {
                    "subject_id": subject["id"],
                    "subject_name": subject["name"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                }
            )

    output_path = (
        REPO_ROOT
        / "data"
        / "kg_experiment"
        / f"results_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nResultados guardados en {output_path}")

    valid = [result for result in results if "scores" in result]
    if valid:
        avg_a = sum(float(result["scores"].get("total_a", 0)) for result in valid) / len(valid)
        avg_b = sum(float(result["scores"].get("total_b", 0)) for result in valid) / len(valid)
        print(f"\nResumen: {len(valid)}/{len(SUBJECTS)} sujetos evaluados")
        print(f"  Promedio Condicion A (JSON): {avg_a:.2f}")
        print(f"  Promedio Condicion B (KG):   {avg_b:.2f}")
        print(f"  Delta (B - A): {avg_b - avg_a:+.2f}")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="KG experiment runner: condition A vs B")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate local imports/config without calling Abu Engine or Anthropic.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print(f"Configured subjects: {len(SUBJECTS)}")
        print(f"Abu Engine URL: {ABU_ENGINE_URL}")
        return

    run_experiment()


if __name__ == "__main__":
    main()
