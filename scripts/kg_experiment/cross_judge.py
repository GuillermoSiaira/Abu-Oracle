#!/usr/bin/env python3
"""
KG-C03 Cross-Model Judge

Re-evalúa las MISMAS responses de Lilly (guardadas por runner.py) usando un
LLM distinto como juez, para validar que B > A no es sesgo de auto-evaluación.

READER MODEL (Lilly):  claude-sonnet-4-6   (Anthropic API)  ← lectura original
JUDGE MODEL (este):    gemini-2.5-pro      (Vertex AI)      ← evaluador independiente

No re-ejecuta Lilly (lecturas ya hechas, $0.052 gastados). Solo re-evalúa.
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# ── Modelos involucrados ────────────────────────────────────────────────
READER_MODEL = "claude-sonnet-4-6"
READER_PROVIDER = "Anthropic API directa"
JUDGE_MODEL = "gemini-2.5-pro"
JUDGE_PROVIDER = "Vertex AI (GCP credits)"

# Pricing Vertex Gemini 2.5 Pro (≤ 200K context) — USD per million tokens
GEMINI_PRICING = {"input_per_m": 1.25, "output_per_m": 10.00}

# Mismo template que el judge.py original — comparación justa
JUDGE_PROMPT_TEMPLATE = """
Eres un evaluador experto en astrologia helenistica clasica.
Evalua estas dos interpretaciones de carta natal en una escala del 1 al 5 para cada criterio.
NO sabes cual interpretacion fue generada con que metodo; evalua solo el contenido.

INTERPRETACION X:
{resp_x}

INTERPRETACION Y:
{resp_y}

Criterios (1=malo, 5=excelente):
1. coherencia_doctrinal: usa correctamente senorios y firdaria segun la doctrina clasica.
2. especificidad: menciona planetas, casas y fechas concretas.
3. multi_hop_reasoning: conecta senor del ano -> posicion natal -> dignidad -> implicancia.
4. ausencia_de_generico: evita frases vacias y lugares comunes.
5. sintesis: produce una lectura integrada, no una lista desconectada.

Responde SOLO con JSON, sin texto extra:
{{
  "x": {{"coherencia_doctrinal":N,"especificidad":N,"multi_hop_reasoning":N,"ausencia_de_generico":N,"sintesis":N,"total":N}},
  "y": {{"coherencia_doctrinal":N,"especificidad":N,"multi_hop_reasoning":N,"ausencia_de_generico":N,"sintesis":N,"total":N}}
}}
"""


def _gemini_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * GEMINI_PRICING["input_per_m"]
        + output_tokens * GEMINI_PRICING["output_per_m"]
    ) / 1_000_000


def _clean_json_block(raw: str) -> str:
    """Strip markdown fences (Gemini también puede envolver en ```json...```)."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    if not cleaned.startswith("{"):
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
    return cleaned


def _normalize_scores(scores: dict) -> dict:
    total = scores.get("total")
    if not isinstance(total, (int, float)):
        total = sum(
            v for k, v in scores.items()
            if k != "total" and isinstance(v, (int, float))
        )
        scores["total"] = total
    return scores


def evaluate_pair_gemini(resp_a: str, resp_b: str) -> dict:
    """Re-evalúa el par (resp_a, resp_b) con Gemini 2.5 Pro vía Vertex AI."""
    from google import genai

    client = genai.Client(
        vertexai=True,
        project=os.environ.get("VERTEXAI_PROJECT", "abu-oracle"),
        location=os.environ.get("VERTEXAI_LOCATION", "us-central1"),
    )

    # Orden aleatorio para evitar sesgo posicional
    x_is_a = random.random() < 0.5
    resp_x, resp_y = (resp_a, resp_b) if x_is_a else (resp_b, resp_a)
    prompt = JUDGE_PROMPT_TEMPLATE.format(resp_x=resp_x, resp_y=resp_y)

    t0 = time.perf_counter()
    response = client.models.generate_content(model=JUDGE_MODEL, contents=prompt)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    usage = getattr(response, "usage_metadata", None)
    input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0) if usage else 0
    output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0) if usage else 0

    judge_usage = {
        "model": JUDGE_MODEL,
        "provider": JUDGE_PROVIDER,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(_gemini_cost(input_tokens, output_tokens), 6),
        "latency_ms": latency_ms,
    }

    raw = (response.text or "{}").strip()
    cleaned = _clean_json_block(raw)

    try:
        scores = json.loads(cleaned)
        x_scores = _normalize_scores(scores.get("x", {}))
        y_scores = _normalize_scores(scores.get("y", {}))
        scores_a = x_scores if x_is_a else y_scores
        scores_b = y_scores if x_is_a else x_scores
        return {
            "scores_a": scores_a,
            "scores_b": scores_b,
            "total_a": scores_a.get("total", 0),
            "total_b": scores_b.get("total", 0),
            "judge_order": "x=A,y=B" if x_is_a else "x=B,y=A",
            "judge_usage": judge_usage,
        }
    except json.JSONDecodeError:
        return {
            "raw_judge_output": raw,
            "total_a": 0,
            "total_b": 0,
            "judge_usage": judge_usage,
        }


def _find_latest_results() -> Path:
    results_dir = REPO_ROOT / "data" / "kg_experiment"
    if not results_dir.exists():
        raise SystemExit("ERROR: data/kg_experiment/ no existe. Corré runner.py primero.")
    files = sorted(results_dir.glob("results_*.json"))
    if not files:
        raise SystemExit("ERROR: No hay results_*.json en data/kg_experiment/")
    return files[-1]


def main() -> None:
    input_file = _find_latest_results()

    # ── Banner inicial (esto es lo visible al grabar) ────────────────────
    print()
    print("=" * 72)
    print("  KG-C03 — CROSS-MODEL JUDGE")
    print("=" * 72)
    print(f"  READER MODEL (Lilly):  {READER_MODEL:<22}  [{READER_PROVIDER}]")
    print(f"  JUDGE MODEL (este):    {JUDGE_MODEL:<22}  [{JUDGE_PROVIDER}]")
    print("-" * 72)
    print(f"  Hipótesis a validar:   Si Gemini concuerda en que B > A,")
    print(f"                         el resultado NO es sesgo de auto-evaluación")
    print(f"                         (Claude evaluando salidas de Claude).")
    print("-" * 72)
    print(f"  Input file:  {input_file.name}")
    print("=" * 72)
    print()

    with open(input_file, encoding="utf-8") as f:
        prior_results = json.load(f)

    valid = [
        r for r in prior_results
        if r.get("response_a") and r.get("response_b") and "scores" in r
    ]

    if not valid:
        print("ERROR: No hay sujetos con responses + scores en el archivo.")
        return

    print(f"Sujetos a re-evaluar: {len(valid)}\n")

    cross_results: list[dict] = []
    sum_a, sum_b = 0.0, 0.0
    sum_cost = 0.0
    agreement_count = 0

    for idx, prior in enumerate(valid, start=1):
        subject_name = prior.get("subject_name", "?")
        prior_scores = prior.get("scores", {})
        prior_a = float(prior_scores.get("total_a", 0))
        prior_b = float(prior_scores.get("total_b", 0))

        print("─" * 72)
        print(f"  Sujeto {idx}/{len(valid)}: {subject_name}")
        print("─" * 72)
        print(f"    Llamando a {JUDGE_MODEL} ({JUDGE_PROVIDER})...")

        try:
            result = evaluate_pair_gemini(prior["response_a"], prior["response_b"])
        except Exception as exc:
            print(f"    ERROR: {exc}\n")
            continue

        ju = result.get("judge_usage", {})
        new_a = float(result.get("total_a", 0))
        new_b = float(result.get("total_b", 0))

        print(
            f"    Usage: {ju.get('input_tokens', 0):>5} in / "
            f"{ju.get('output_tokens', 0):>3} out / "
            f"${ju.get('cost_usd', 0):.6f} / "
            f"{ju.get('latency_ms', 0):>5} ms"
        )
        print()
        print(f"    {JUDGE_MODEL:<22} (Gemini):  A = {new_a:>4.0f}  |  B = {new_b:>4.0f}   delta {new_b - new_a:+.1f}")
        print(f"    {READER_MODEL:<22} (Claude):  A = {prior_a:>4.0f}  |  B = {prior_b:>4.0f}   delta {prior_b - prior_a:+.1f}")

        prior_winner = "B" if prior_b > prior_a else ("A" if prior_a > prior_b else "tie")
        new_winner = "B" if new_b > new_a else ("A" if new_a > new_b else "tie")
        agreement = prior_winner == new_winner
        if agreement:
            agreement_count += 1
            print(f"    Acuerdo:               SÍ — ambos votan {new_winner}")
        else:
            print(f"    Acuerdo:               NO — Claude:{prior_winner} vs Gemini:{new_winner}")
        print()

        sum_a += new_a
        sum_b += new_b
        sum_cost += ju.get("cost_usd", 0.0)

        cross_results.append({
            "subject_id": prior.get("subject_id"),
            "subject_name": subject_name,
            "reader_model": READER_MODEL,
            "judge_model_original": "claude-sonnet-4-6",
            "judge_model_cross": JUDGE_MODEL,
            "prior_scores_claude": prior_scores,
            "cross_scores_gemini": result,
            "agreement": agreement,
        })

    n = len(cross_results)

    output_path = (
        REPO_ROOT / "data" / "kg_experiment"
        / f"cross_judge_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(cross_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if n == 0:
        print("\nSin resultados válidos.")
        return

    avg_a = sum_a / n
    avg_b = sum_b / n
    delta = avg_b - avg_a
    pct = (delta / avg_a * 100) if avg_a > 0 else 0.0

    print()
    print("=" * 72)
    print("  RESUMEN CROSS-JUDGE")
    print("=" * 72)
    print(f"  Sujetos re-evaluados:  {n}")
    print()
    print(f"  CALIDAD según {JUDGE_MODEL} (escala 0–25):")
    print(f"    Avg A (JSON plano):  {avg_a:>6.2f}")
    print(f"    Avg B (KG):          {avg_b:>6.2f}")
    print(f"    Delta:               {delta:+6.2f}  ({pct:+.1f}%)")
    print()
    print(f"  ACUERDO ENTRE JUECES (Claude vs Gemini, ganador por sujeto):")
    print(f"    {agreement_count}/{n} sujetos coinciden")
    if agreement_count == n:
        print(f"    Veredicto: SEÑAL ROBUSTA — el delta B > A no es sesgo de auto-evaluación")
    elif agreement_count >= n - 1:
        print(f"    Veredicto: SEÑAL CASI ROBUSTA — 1 discrepancia, revisar caso")
    else:
        print(f"    Veredicto: SEÑAL DÉBIL — multiples discrepancias, hay sesgo o el delta es chico")
    print()
    print(f"  COSTO DE ESTE CROSS-JUDGE:")
    print(f"    Gemini 2.5 Pro:  ${sum_cost:.6f}")
    print(f"    Provider:        Vertex AI (consume créditos GCP, NO Anthropic)")
    print()
    print(f"  Resultados detallados: {output_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
