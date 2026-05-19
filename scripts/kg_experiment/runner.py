#!/usr/bin/env python3
"""
KG Experiment Runner — Condition A vs B (multi-design).

Cada diseño experimental vive en `scripts/kg_experiment/designs/vN_*.py`
y exporta el contrato mínimo: DESIGN_ID, EVAL_PROMPT, SUBJECTS,
build_context_a(natal, bio), build_context_b(natal, bio).

Uso:
    python scripts/kg_experiment/runner.py --design v1_current_life
    python scripts/kg_experiment/runner.py --design v1_current_life --dry-run

Outputs:
    data/kg_experiment/<design_id>/results_YYYYMMDD_HHMMSS.json
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

import requests


# ── Modelos involucrados (visible en banner) ─────────────────────────────
READER_MODEL = "claude-sonnet-4-6"
READER_PROVIDER = "Anthropic API directa"
JUDGE_MODEL_DEFAULT = "claude-sonnet-4-6"
JUDGE_PROVIDER_DEFAULT = "Anthropic API directa"

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))
sys.path.insert(0, str(REPO_ROOT))

from scripts.kg_experiment.config import ABU_ENGINE_URL  # noqa: E402
from scripts.kg_experiment.judge import evaluate_pair  # noqa: E402


ABU_HEADERS: dict[str, str] = {"Authorization": "Bearer dev-bypass"}


# ── Conteo de entidades doctrinales (proxy de densidad/hops) ─────────────
# Cada categoría: regex compilados con flags IGNORECASE.
# Cuenta entidades ÚNICAS por categoría (mencionar "Marte" 3 veces = 1).
_DOCTRINAL_PATTERNS: dict[str, list[re.Pattern]] = {
    "planetas_clasicos": [re.compile(p, re.IGNORECASE) for p in [
        r"\bSol\b", r"\bSun\b",
        r"\bLuna\b", r"\bMoon\b",
        r"\bMercurio\b", r"\bMercury\b",
        r"\bVenus\b",
        r"\bMarte\b", r"\bMars\b",
        r"\bJ[uú]piter\b", r"\bJupiter\b",
        r"\bSaturno\b", r"\bSaturn\b",
    ]],
    "planetas_transpersonales": [re.compile(p, re.IGNORECASE) for p in [
        r"\bUrano\b", r"\bUranus\b",
        r"\bNeptuno\b", r"\bNeptune\b",
        r"\bPlut[oó]n\b", r"\bPluto\b",
        r"\bNodo (?:Norte|Sur|Lunar)\b", r"\b(?:North|South) Node\b",
    ]],
    "signos": [re.compile(p, re.IGNORECASE) for p in [
        r"\bAries\b", r"\bTauro\b", r"\bTaurus\b",
        r"\bG[eé]minis\b", r"\bGemini\b",
        r"\bC[aá]ncer\b", r"\bCancer\b",
        r"\bLeo\b", r"\bVirgo\b", r"\bLibra\b",
        r"\bEscorpio\b", r"\bScorpio\b",
        r"\bSagitario\b", r"\bSagittarius\b",
        r"\bCapricornio\b", r"\bCapricorn\b",
        r"\bAcuario\b", r"\bAquarius\b",
        r"\bPiscis\b", r"\bPisces\b",
    ]],
    "casas": [re.compile(p, re.IGNORECASE) for p in [
        r"\bCasa\s+(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|1[012]|[1-9])\b",
        r"\bHouse\s+\d+\b",
    ]],
    "dignidades": [re.compile(p, re.IGNORECASE) for p in [
        r"\bdomicilio\b", r"\bdomicile\b",
        r"\bexaltaci[oó]n\b", r"\bexaltation\b",
        r"\bdetrimento\b", r"\bdetriment\b",
        r"\bca[ií]da\b", r"\bfall\b",
        r"\bperegrin[oa]\b", r"\bperegrine\b",
        r"\btriplicidad\b", r"\btriplicity\b",
        r"\bt[eé]rmino\b", r"\bterm\b",
        r"\bfaz\b", r"\bdecan\b",
    ]],
    "partes_arabicas": [re.compile(p, re.IGNORECASE) for p in [
        r"\bParte de Fortuna\b", r"\bFortuna\b", r"\bPart of Fortune\b",
        r"\bParte del? Esp[ií]ritu\b", r"\bEsp[ií]ritu\b", r"\bSpirit\b",
        r"\bEros\b",
        r"\bNecesidad\b", r"\bNecessity\b",
    ]],
    "angulos": [re.compile(p, re.IGNORECASE) for p in [
        r"\bAscendente\b", r"\bASC\b", r"\bAscendant\b",
        r"\bMedio Cielo\b", r"\bMC\b", r"\bMidheaven\b",
        r"\bDescendente\b", r"\bDSC\b",
        r"\bFondo (?:de )?Cielo\b", r"\bIC\b",
    ]],
    "aspectos": [re.compile(p, re.IGNORECASE) for p in [
        r"\bconjunci[oó]n\b", r"\bconjunction\b",
        r"\bsextil\b", r"\bsextile\b",
        r"\bcuadratura\b", r"\bsquare\b",
        r"\btr[ií]gono\b", r"\btrine\b",
        r"\boposici[oó]n\b", r"\bopposition\b",
        r"\brecepci[oó]n\s+mutua\b", r"\bmutual reception\b",
    ]],
    "tecnicas_temporales": [re.compile(p, re.IGNORECASE) for p in [
        r"\bse[ñn]or del a[ñn]o\b", r"\blord of (?:the )?year\b",
        r"\bfirdaria\b", r"\bfirdar(?:es)?\b",
        r"\bprofecci[oó]n\b", r"\bprofection\b",
        r"\btr[aá]nsito\b", r"\btransit\b",
    ]],
}


def count_doctrinal_entities(text: str) -> dict:
    """
    Cuenta entidades doctrinales por categoría en el texto.

    - Por cada patrón que matchea al menos una vez, suma 1 a la categoría.
      (Proxy de "tipos de entidades doctrinales usadas" — no menciones totales.)
    - Devuelve dict con counts por categoría + total_unique + total_mentions
    """
    counts_unique: dict[str, int] = {}
    total_mentions = 0
    for category, patterns in _DOCTRINAL_PATTERNS.items():
        unique = 0
        for pat in patterns:
            matches = pat.findall(text)
            if matches:
                unique += 1
                total_mentions += len(matches)
        counts_unique[category] = unique
    counts_unique["_total_unique_entities"] = sum(
        v for k, v in counts_unique.items() if not k.startswith("_")
    )
    counts_unique["_total_mentions"] = total_mentions
    counts_unique["_text_chars"] = len(text)
    counts_unique["_density"] = (
        round(total_mentions / max(len(text), 1) * 1000, 2)  # menciones por 1000 chars
    )
    return counts_unique

# Public Anthropic pricing (USD per million tokens) — update if Anthropic changes.
PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6":           {"input_per_m": 3.00, "output_per_m": 15.00},
    "claude-haiku-4-5":            {"input_per_m": 0.80, "output_per_m": 4.00},
    "claude-haiku-4-5-20251001":   {"input_per_m": 0.80, "output_per_m": 4.00},
}


# ── Design loader ─────────────────────────────────────────────────────────

def _load_design(design_id: str) -> ModuleType:
    """Importa dinámicamente designs/<design_id>.py y valida el contrato."""
    try:
        module = importlib.import_module(f"scripts.kg_experiment.designs.{design_id}")
    except ImportError as exc:
        raise SystemExit(
            f"ERROR: No se puede importar el diseño '{design_id}'.\n"
            f"  Buscado en: scripts/kg_experiment/designs/{design_id}.py\n"
            f"  Detalle: {exc}"
        )

    required = ("DESIGN_ID", "EVAL_PROMPT", "SUBJECTS", "build_context_a", "build_context_b")
    missing = [attr for attr in required if not hasattr(module, attr)]
    if missing:
        raise SystemExit(
            f"ERROR: Diseño '{design_id}' incompleto. Faltan: {', '.join(missing)}"
        )
    return module


def _list_available_designs() -> list[str]:
    designs_dir = Path(__file__).parent / "designs"
    return sorted(
        p.stem for p in designs_dir.glob("v*_*.py")
        if not p.name.startswith("__")
    )


# ── Pricing helpers ───────────────────────────────────────────────────────

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


# ── Abu Engine fetchers ───────────────────────────────────────────────────

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


# ── Anthropic Lilly call ──────────────────────────────────────────────────

def _extract_text_and_thinking(response: object) -> tuple[str, str]:
    """
    Extrae text final + thinking block (si está presente) del response Anthropic.
    Devuelve (text, thinking). Si thinking no fue habilitado, thinking == "".
    """
    content = getattr(response, "content", None) or []
    text_chunks: list[str] = []
    thinking_chunks: list[str] = []
    for block in content:
        block_type = getattr(block, "type", None)
        if block_type == "thinking":
            t = getattr(block, "thinking", None)
            if isinstance(t, str):
                thinking_chunks.append(t)
        else:
            t = getattr(block, "text", None)
            if isinstance(t, str):
                text_chunks.append(t)
    return "".join(text_chunks), "".join(thinking_chunks)


def call_lilly(
    context: str,
    eval_prompt: str,
    enable_thinking: bool = False,
    thinking_budget: int = 4000,
    model: str = READER_MODEL,
) -> tuple[str, str, dict]:
    """
    Llama al modelo Anthropic indicado con system Lilly + eval_prompt + contexto.

    Si enable_thinking=True, activa extended thinking de Anthropic — la response
    incluye un bloque 'thinking' separado con el chain-of-thought interno.
    Los thinking tokens se facturan como output (precio del modelo).

    Returns:
        (text, thinking, usage) — thinking="" si no fue habilitado.
    """
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")

    client = anthropic.Anthropic(api_key=api_key)
    system = (
        "Eres Lilly, astrologo clasico formado en la tradicion helenistica y persa. "
        "Interpretas cartas natales siguiendo la doctrina de Ptolomeo, Al-Biruni y William Lilly."
    )
    user_msg = f"{eval_prompt}\n\nContexto de la carta:\n{context}"

    # Cuando se activa thinking, max_tokens debe ser > thinking_budget para dejar
    # espacio al texto final además del razonamiento.
    max_tokens = (thinking_budget + 400) if enable_thinking else 400

    request_kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_msg}],
    }
    if enable_thinking:
        request_kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}

    t0 = time.perf_counter()
    response = client.messages.create(**request_kwargs)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    text, thinking = _extract_text_and_thinking(response)
    usage = _extract_usage(response, model, latency_ms)
    usage["thinking_enabled"] = enable_thinking
    usage["thinking_chars"] = len(thinking)
    return text, thinking, usage


# ── Acumulación de métricas ───────────────────────────────────────────────

def _accumulate(totals: dict, key: str, usage: dict) -> None:
    bucket = totals[key]
    bucket["input_tokens"] += usage.get("input_tokens", 0)
    bucket["output_tokens"] += usage.get("output_tokens", 0)
    bucket["cost_usd"] += usage.get("cost_usd", 0.0)
    bucket["latency_ms"] += usage.get("latency_ms", 0)
    bucket["n"] += 1


# ── Loop principal del experimento ────────────────────────────────────────

def _print_response_block(label: str, text: str, color_indicator: str) -> None:
    """Imprime una respuesta de Lilly con separadores visibles para grabación."""
    print()
    print(f"  ┌─ RESPUESTA {label}  {color_indicator}{'─' * 50}")
    for line in text.strip().split("\n"):
        print(f"  │ {line}")
    print(f"  └{'─' * (60)}")


def _print_thinking_block(label: str, thinking: str) -> None:
    """Imprime el chain-of-thought interno (extended thinking) si está activo."""
    if not thinking:
        return
    print()
    print(f"  ┌─ THINKING {label}  (chain-of-thought interno){'─' * 24}")
    for line in thinking.strip().split("\n"):
        print(f"  │ {line}")
    print(f"  └{'─' * 60}")


def _print_entities_block(label: str, ent: dict) -> None:
    """Imprime el conteo de entidades doctrinales para una respuesta."""
    print(
        f"  ENT {label}: "
        f"planetas={ent['planetas_clasicos']} "
        f"transp={ent['planetas_transpersonales']} "
        f"signos={ent['signos']} "
        f"casas={ent['casas']} "
        f"dign={ent['dignidades']} "
        f"partes={ent['partes_arabicas']} "
        f"ang={ent['angulos']} "
        f"asp={ent['aspectos']} "
        f"tecn={ent['tecnicas_temporales']} "
        f"| ÚNICAS={ent['_total_unique_entities']} "
        f"MENC={ent['_total_mentions']} "
        f"DENS={ent['_density']}/1k chars"
    )


def run_experiment(
    design: ModuleType,
    enable_thinking: bool = False,
    show_responses: bool = True,
) -> Path:
    subjects = design.SUBJECTS
    eval_prompt = design.EVAL_PROMPT
    # Modelos por condición — opt-in del diseño; fallback a Sonnet para
    # retrocompatibilidad con v1/v2/v3.
    model_a = getattr(design, "READER_MODEL_A", READER_MODEL)
    model_b = getattr(design, "READER_MODEL_B", READER_MODEL)

    results: list[dict] = []
    totals: dict[str, dict] = {
        "a":     {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": 0, "n": 0},
        "b":     {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": 0, "n": 0},
        "judge": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": 0, "n": 0},
    }

    for subject in subjects:
        print(f"\n{'=' * 72}")
        print(f"  Sujeto: {subject['name']} ({subject['id']})")
        print("=" * 72)

        try:
            print("  Fetching natal + biography...")
            natal = fetch_natal(subject)
            bio = fetch_biography(subject)
            time.sleep(1)

            print("  Building contexts A and B...")
            ctx_a = design.build_context_a(natal, bio)
            ctx_b = design.build_context_b(natal, bio)

            print(f"  Calling Lilly [{model_a}] with context A (JSON)...")
            resp_a, thinking_a, usage_a = call_lilly(ctx_a, eval_prompt, enable_thinking, model=model_a)
            print(
                f"    A: {usage_a['input_tokens']:>5} in / {usage_a['output_tokens']:>4} out / "
                f"${usage_a['cost_usd']:.6f} / {usage_a['latency_ms']:>4} ms"
                + (f" / thinking {usage_a['thinking_chars']} chars" if enable_thinking else "")
            )
            if enable_thinking and thinking_a:
                _print_thinking_block("A", thinking_a)
            if show_responses:
                _print_response_block("A (JSON)", resp_a, "🟦")
            entities_a = count_doctrinal_entities(resp_a)
            _print_entities_block("A", entities_a)
            time.sleep(2)

            print(f"\n  Calling Lilly [{model_b}] with context B (KG)...")
            resp_b, thinking_b, usage_b = call_lilly(ctx_b, eval_prompt, enable_thinking, model=model_b)
            print(
                f"    B: {usage_b['input_tokens']:>5} in / {usage_b['output_tokens']:>4} out / "
                f"${usage_b['cost_usd']:.6f} / {usage_b['latency_ms']:>4} ms"
                + (f" / thinking {usage_b['thinking_chars']} chars" if enable_thinking else "")
            )
            if enable_thinking and thinking_b:
                _print_thinking_block("B", thinking_b)
            if show_responses:
                _print_response_block("B (KG)", resp_b, "🟩")
            entities_b = count_doctrinal_entities(resp_b)
            _print_entities_block("B", entities_b)
            time.sleep(2)

            print(f"\n  Evaluating pair with judge [{JUDGE_MODEL_DEFAULT}]...")
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
                "design_id": design.DESIGN_ID,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_a": ctx_a,
                "context_b": ctx_b,
                "response_a": resp_a,
                "response_b": resp_b,
                "thinking_a": thinking_a,
                "thinking_b": thinking_b,
                "responses_distinct": resp_a.strip() != resp_b.strip(),
                "scores": scores,
                "usage_a": usage_a,
                "usage_b": usage_b,
                "judge_usage": judge_usage,
                "entities_a": entities_a,
                "entities_b": entities_b,
            }
            results.append(result)

            print(f"\n  Scores: A = {scores.get('total_a', '?')}  |  B = {scores.get('total_b', '?')}")
        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append(
                {
                    "subject_id": subject["id"],
                    "subject_name": subject["name"],
                    "design_id": design.DESIGN_ID,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                }
            )

    output_path = (
        REPO_ROOT
        / "data"
        / "kg_experiment"
        / design.DESIGN_ID
        / f"results_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nResultados guardados en {output_path}")
    _print_extended_summary(design, results, totals)
    return output_path


def _print_extended_summary(design: ModuleType, results: list[dict], totals: dict) -> None:
    valid = [r for r in results if "scores" in r]
    n = len(valid)
    if n == 0:
        print("\nSin resultados válidos para resumir.")
        return

    avg_quality_a = sum(float(r["scores"].get("total_a", 0)) for r in valid) / n
    avg_quality_b = sum(float(r["scores"].get("total_b", 0)) for r in valid) / n

    print(f"\n{'=' * 72}")
    print(f"  RESUMEN — diseño: {design.DESIGN_ID}")
    print("=" * 72)
    print(f"  Sujetos evaluados: {n}/{len(design.SUBJECTS)}")

    print("\n  CALIDAD DOCTRINAL (juez LLM, 1-5 × 5 ejes, max 25):")
    print(f"  Condicion A: {avg_quality_a:>6.2f}")
    print(f"  Condicion B: {avg_quality_b:>6.2f}")
    delta_q = avg_quality_b - avg_quality_a
    delta_q_pct = (delta_q / avg_quality_a * 100) if avg_quality_a > 0 else 0.0
    print(f"  Delta:       {delta_q:+6.2f}  ({delta_q_pct:+.1f}%)")

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

    summary_model_a = getattr(design, "READER_MODEL_A", READER_MODEL)
    summary_model_b = getattr(design, "READER_MODEL_B", READER_MODEL)
    if summary_model_a == summary_model_b:
        print(f"\nCOSTO USD (por lectura, {summary_model_a} directo Anthropic):")
    else:
        print(f"\nCOSTO USD (A: {summary_model_a} | B: {summary_model_b}):")
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
    print(f"\n  COSTO TOTAL DEL EXPERIMENTO (n={n} sujetos):")
    print(f"    Lilly A:   ${a_tot['cost_usd']:.6f}")
    print(f"    Lilly B:   ${b_tot['cost_usd']:.6f}")
    if j_tot["n"] > 0:
        print(f"    Judge:     ${j_tot['cost_usd']:.6f}  ({j_tot['n']} llamadas)")
    grand_total = a_tot["cost_usd"] + b_tot["cost_usd"] + j_tot["cost_usd"]
    print(f"    TOTAL:     ${grand_total:.6f}")

    # ── Densidad doctrinal (proxy de hops) ─────────────────────────────
    ents_a = [r.get("entities_a") for r in valid if r.get("entities_a")]
    ents_b = [r.get("entities_b") for r in valid if r.get("entities_b")]
    if ents_a and ents_b:
        avg_uniq_a = sum(e["_total_unique_entities"] for e in ents_a) / len(ents_a)
        avg_uniq_b = sum(e["_total_unique_entities"] for e in ents_b) / len(ents_b)
        avg_dens_a = sum(e["_density"] for e in ents_a) / len(ents_a)
        avg_dens_b = sum(e["_density"] for e in ents_b) / len(ents_b)
        print("\n  DENSIDAD DOCTRINAL (proxy de hops / referencias en la respuesta):")
        print(f"    Tipos únicos de entidad doctrinal por lectura:")
        print(f"      A: avg {avg_uniq_a:>5.1f}   B: avg {avg_uniq_b:>5.1f}   delta {avg_uniq_b - avg_uniq_a:+.1f}")
        print(f"    Menciones por 1000 chars (densidad):")
        print(f"      A: avg {avg_dens_a:>5.1f}   B: avg {avg_dens_b:>5.1f}   delta {avg_dens_b - avg_dens_a:+.1f}")

    # ── Extended thinking (si fue habilitado) ──────────────────────────
    think_a = [r.get("thinking_a", "") for r in valid]
    think_b = [r.get("thinking_b", "") for r in valid]
    if any(think_a) or any(think_b):
        avg_think_a = sum(len(t) for t in think_a) / len(think_a)
        avg_think_b = sum(len(t) for t in think_b) / len(think_b)
        print("\n  EXTENDED THINKING (chain-of-thought interno):")
        print(f"    A: avg {avg_think_a:>6,.0f} chars   B: avg {avg_think_b:>6,.0f} chars")
        print(f"    Delta: {((avg_think_b - avg_think_a) / max(avg_think_a, 1) * 100):+.1f}%")
    print(f"  {'=' * 70}")


# ── CLI ───────────────────────────────────────────────────────────────────

def _print_banner(design: ModuleType, enable_thinking: bool, show_responses: bool) -> None:
    """Banner inicial visible para grabación."""
    print()
    print("=" * 72)
    print("  KG-C03 — EXPERIMENT RUNNER")
    print("=" * 72)
    print(f"  DESIGN:                {design.DESIGN_ID}")
    if hasattr(design, "DESIGN_DESCRIPTION"):
        # Wrap larga descripción en líneas de 60 chars
        desc = design.DESIGN_DESCRIPTION
        words = desc.split()
        line = "  DESCRIPCIÓN:           "
        prefix_len = len(line)
        current = line
        for word in words:
            if len(current) + len(word) + 1 > 90:
                print(current)
                current = " " * prefix_len + word
            else:
                current = current + " " + word if current.strip() else current + word
        print(current)
    print("-" * 72)
    banner_model_a = getattr(design, "READER_MODEL_A", READER_MODEL)
    banner_model_b = getattr(design, "READER_MODEL_B", READER_MODEL)
    if banner_model_a == banner_model_b:
        print(f"  READER MODEL (Lilly):  {banner_model_a:<22}  [{READER_PROVIDER}]")
    else:
        print(f"  READER MODEL A:        {banner_model_a:<22}  [{READER_PROVIDER}]")
        print(f"  READER MODEL B:        {banner_model_b:<22}  [{READER_PROVIDER}]")
    print(f"  JUDGE MODEL:           {JUDGE_MODEL_DEFAULT:<22}  [{JUDGE_PROVIDER_DEFAULT}]")
    print(f"  EXTENDED THINKING:     {'ENABLED — chain-of-thought visible' if enable_thinking else 'disabled (default)'}")
    print(f"  SHOW RESPONSES:        {'on' if show_responses else 'off'}")
    print("-" * 72)
    print(f"  SUJETOS:               {len(design.SUBJECTS)}  ({', '.join(s['name'] for s in design.SUBJECTS)})")
    print(f"  ABU ENGINE URL:        {ABU_ENGINE_URL}")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="KG experiment runner: condition A vs B")
    parser.add_argument(
        "--design",
        default="v1_current_life",
        help="Diseño experimental a correr (default: v1_current_life). "
             "Diseños disponibles: " + ", ".join(_list_available_designs()),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida diseño + imports + config sin llamar a Abu Engine ni Anthropic.",
    )
    parser.add_argument(
        "--list-designs",
        action="store_true",
        help="Lista los diseños disponibles y sale.",
    )
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Activa extended thinking de Anthropic. Captura el chain-of-thought "
             "interno como bloque separado. Aumenta el costo (~$0.03 extra por llamada).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suprime la impresión de respuestas en terminal (solo summary final).",
    )
    args = parser.parse_args()

    if args.list_designs:
        print("Diseños disponibles:")
        for d in _list_available_designs():
            print(f"  {d}")
        return

    design = _load_design(args.design)
    enable_thinking = args.thinking
    show_responses = not args.quiet

    _print_banner(design, enable_thinking, show_responses)

    if args.dry_run:
        print("\n(dry-run — no se ejecutan llamadas)")
        return

    run_experiment(design, enable_thinking=enable_thinking, show_responses=show_responses)


if __name__ == "__main__":
    main()
