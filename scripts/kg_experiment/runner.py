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

ABU_HEADERS: dict[str, str] = {"Authorization": "Bearer dev-bypass"}

# Public Anthropic pricing (USD per million tokens) — update if Anthropic changes.
PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input_per_m": 3.00, "output_per_m": 15.00},
    "claude-haiku-4-5":  {"input_per_m": 0.80, "output_per_m": 4.00},
}


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = PRICING.get(model, PRICING["claude-sonnet-4-6"])
    return (input_tokens * prices["input_per_m"] + output_tokens * prices["output_per_m"]) / 1_000_000


def _extract_usage(response: object, model: str, latency_ms: int) -> dict:
    usage_obj = getattr(response, "usage", None)
    input_tokens = int(getattr(usage_obj, "input_tokens", 0) or 0) if usage_obj else 0
    output_tokens = int(getattr(usage_obj, "output_tokens", 0) or 0) if usage_obj else 0
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(_calculate_cost(model, input_tokens, output_tokens), 6),
        "latency_ms": latency_ms,
    }


def fetch_natal(subject: dict) -> dict:
    url = f"{ABU_ENGINE_URL}/analyze"
    payload = {
        "person": {"name": subject["name"]},
        "birth": {
            "date": subject["birthDate"],
            "lat": subject["lat"],
            "lon": subject["lon"],
        },
        "current": {
            "lat": subject["lat"],
            "lon": subject["lon"],
        },
    }
    res = requests.post(url, json=payload, headers=ABU_HEADERS, timeout=30)
    res.raise_for_status()
    return res.json()


def fetch_biography(subject: dict) -> dict:
    url = f"{ABU_ENGINE_URL}/api/astro/biography"
    params = {
        "birthDate": subject["birthDate"],
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


def call_lilly(context: str, subject: dict) -> tuple[str, dict]:
    del subject

    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")

    client = anthropic.Anthropic(api_key=api_key)
    model = "claude-sonnet-4-6"
    system = (
        "Eres Lilly, astrologo clasico formado en la tradicion helenistica y persa. "
        "Interpretas cartas natales siguiendo la doctrina de Ptolomeo, Al-Biruni y William Lilly."
    )
    user_msg = f"{EVAL_PROMPT}\n\nContexto de la carta:\n{context}"

    t0 = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)

    usage = _extract_usage(response, model, latency_ms)
    return _text_from_response(response), usage


def _accumulate(totals: dict, key: str, usage: dict) -> None:
    bucket = totals[key]
    bucket["input_tokens"] += usage.get("input_tokens", 0)
    bucket["output_tokens"] += usage.get("output_tokens", 0)
    bucket["cost_usd"] += usage.get("cost_usd", 0.0)
    bucket["latency_ms"] += usage.get("latency_ms", 0)
    bucket["n"] += 1


def run_experiment() -> Path:
    results: list[dict] = []
    totals: dict[str, dict] = {
        "a":     {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": 0, "n": 0},
        "b":     {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": 0, "n": 0},
        "judge": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": 0, "n": 0},
    }

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
            resp_a, usage_a = call_lilly(ctx_a, subject)
            print(
                f"    A: {usage_a['input_tokens']:>5} in / {usage_a['output_tokens']:>4} out / "
                f"${usage_a['cost_usd']:.6f} / {usage_a['latency_ms']:>4} ms"
            )
            time.sleep(2)

            print("  Calling Lilly with context B...")
            resp_b, usage_b = call_lilly(ctx_b, subject)
            print(
                f"    B: {usage_b['input_tokens']:>5} in / {usage_b['output_tokens']:>4} out / "
                f"${usage_b['cost_usd']:.6f} / {usage_b['latency_ms']:>4} ms"
            )
            time.sleep(2)

            print("  Evaluating pair...")
            evaluation = evaluate_pair(ctx_a, ctx_b, resp_a, resp_b)
            judge_usage = evaluation.pop("judge_usage", None)
            scores = evaluation

            _accumulate(totals, "a", usage_a)
            _accumulate(totals, "b", usage_b)
            if judge_usage:
                _accumulate(totals, "judge", judge_usage)

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
                "usage_a": usage_a,
                "usage_b": usage_b,
                "judge_usage": judge_usage,
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
    _print_extended_summary(results, totals)
    return output_path


def _print_extended_summary(results: list[dict], totals: dict) -> None:
    valid = [r for r in results if "scores" in r]
    n = len(valid)
    if n == 0:
        print("\nSin resultados válidos para resumir.")
        return

    avg_quality_a = sum(float(r["scores"].get("total_a", 0)) for r in valid) / n
    avg_quality_b = sum(float(r["scores"].get("total_b", 0)) for r in valid) / n

    print(f"\n{'=' * 60}")
    print("RESUMEN KG-C03")
    print("=" * 60)
    print(f"Sujetos evaluados: {n}/{len(SUBJECTS)}")

    print("\nCALIDAD DOCTRINAL (juez LLM, 1-5 × 5 ejes, max 25):")
    print(f"  Condicion A (JSON plano): {avg_quality_a:>6.2f}")
    print(f"  Condicion B (KG):         {avg_quality_b:>6.2f}")
    delta_q = avg_quality_b - avg_quality_a
    delta_q_pct = (delta_q / avg_quality_a * 100) if avg_quality_a > 0 else 0.0
    print(f"  Delta:                    {delta_q:+6.2f}  ({delta_q_pct:+.1f}%)")

    a_tot = totals["a"]
    b_tot = totals["b"]
    if a_tot["n"] == 0 or b_tot["n"] == 0:
        return

    avg_in_a = a_tot["input_tokens"] / a_tot["n"]
    avg_in_b = b_tot["input_tokens"] / b_tot["n"]
    avg_out_a = a_tot["output_tokens"] / a_tot["n"]
    avg_out_b = b_tot["output_tokens"] / b_tot["n"]
    avg_cost_a = a_tot["cost_usd"] / a_tot["n"]
    avg_cost_b = b_tot["cost_usd"] / b_tot["n"]
    avg_lat_a = a_tot["latency_ms"] / a_tot["n"]
    avg_lat_b = b_tot["latency_ms"] / b_tot["n"]

    def _pct(new: float, old: float) -> str:
        if old <= 0:
            return "n/a"
        return f"{(new - old) / old * 100:+.1f}%"

    print("\nTOKENS INPUT (contexto + prompt enviado a Lilly):")
    print(f"  Condicion A: avg {avg_in_a:>7,.0f} tokens")
    print(f"  Condicion B: avg {avg_in_b:>7,.0f} tokens")
    print(f"  Delta:            {_pct(avg_in_b, avg_in_a)}")

    print("\nTOKENS OUTPUT (respuesta de Lilly):")
    print(f"  Condicion A: avg {avg_out_a:>7,.0f} tokens")
    print(f"  Condicion B: avg {avg_out_b:>7,.0f} tokens")
    print(f"  Delta:            {_pct(avg_out_b, avg_out_a)}")

    print("\nCOSTO USD (por lectura, Sonnet 4.6 directo Anthropic):")
    print(f"  Condicion A: ${avg_cost_a:>10.6f}")
    print(f"  Condicion B: ${avg_cost_b:>10.6f}")
    print(f"  Delta:            {_pct(avg_cost_b, avg_cost_a)}")

    print("\nLATENCIA:")
    print(f"  Condicion A: avg {avg_lat_a:>6.0f} ms")
    print(f"  Condicion B: avg {avg_lat_b:>6.0f} ms")
    print(f"  Delta:            {_pct(avg_lat_b, avg_lat_a)}")

    print("\nPROYECCION MENSUAL (asumiendo 10,000 lecturas/mes):")
    proj_a = avg_cost_a * 10_000
    proj_b = avg_cost_b * 10_000
    print(f"  Costo A: ${proj_a:>9,.2f}")
    print(f"  Costo B: ${proj_b:>9,.2f}")
    print(f"  Ahorro:  ${proj_a - proj_b:>+9,.2f} / mes")

    j_tot = totals["judge"]
    print(f"\nCOSTO TOTAL DEL EXPERIMENTO (n={n} sujetos):")
    print(f"  Lilly A:   ${a_tot['cost_usd']:.6f}")
    print(f"  Lilly B:   ${b_tot['cost_usd']:.6f}")
    if j_tot["n"] > 0:
        print(f"  Judge:     ${j_tot['cost_usd']:.6f}  ({j_tot['n']} llamadas)")
    grand_total = a_tot["cost_usd"] + b_tot["cost_usd"] + j_tot["cost_usd"]
    print(f"  TOTAL:     ${grand_total:.6f}")


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
