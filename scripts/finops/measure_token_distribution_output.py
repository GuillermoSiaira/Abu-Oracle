"""
Fase A-2 — Medición de tokens de OUTPUT por ruta Lilly.
⚠️  TIENE COSTO: llamadas reales de generación a Anthropic.
Costo estimado: ~$5-6 (50 sujetos × 11 rutas, mix Haiku/Sonnet)

NO ejecutar sin confirmación explícita.
Ejecutar solo después de analizar los resultados de Fase A-1.

Flujo por sujeto:
  1. Llamar Abu Engine POST /analyze → abuData
  2. Llamar Abu Engine GET /api/astro/biography → timeline
  3. Para cada ruta: construir context block + llamar a Anthropic con
     los max_tokens actuales (tabla de FINOPS_MILP_VARIABLES.md)
  4. Registrar tokens_input y tokens_output reales del response.usage
  5. Calcular costo por llamada

Output: research/finops/token_distribution_output.json

Uso (solo con confirmación explícita):
  python scripts/finops/measure_token_distribution_output.py

  # Para ejecutar sobre un subset pequeño primero:
  N_SUBJECTS=5 python scripts/finops/measure_token_distribution_output.py
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import requests

# ── Configuración ─────────────────────────────────────────────────────────────

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
RAW_DATA    = REPO_ROOT / "data" / "raw" / "raw_birthdata_original.jsonl"
OUTPUT_DIR  = REPO_ROOT / "research" / "finops"
OUTPUT_FILE = OUTPUT_DIR / "token_distribution_output.json"
INPUT_FILE  = OUTPUT_DIR / "token_distribution_input.json"  # Fase A-1 results

ABU_URL     = os.environ.get("ABU_URL", "http://localhost:8000")
SAMPLE_N    = int(os.environ.get("N_SUBJECTS", "50"))
RANDOM_SEED = 42

# Routes table con max_tokens actuales.
# Source: obsidian_vault/06_engineering/FINOPS_MILP_VARIABLES.md
# ⚠️  Usar los max_tokens de la tabla — no 4096.
# Objetivo: medir cuántos tokens se usan realmente dentro del límite actual.
ROUTES = [
    ("screen-open",        "claude-sonnet-4-6",         1024),
    ("planet",             "claude-sonnet-4-6",         1024),
    ("technique_lot",      "claude-haiku-4-5-20251001", 2048),
    ("technique_firdaria", "claude-haiku-4-5-20251001", 2048),
    ("technique_lunar",    "claude-haiku-4-5-20251001", 1536),
    ("city",               "claude-haiku-4-5-20251001", 1024),
    ("domain",             "claude-sonnet-4-6",         1024),
    ("house",              "claude-sonnet-4-6",         1024),
    ("sky",                "claude-sonnet-4-6",         1536),
    ("transit",            "claude-sonnet-4-6",         1024),
    ("chat",               "claude-sonnet-4-6",         2500),
]

# Precios por 1M tokens (USD) — Anthropic pricing
PRICING = {
    "claude-sonnet-4-6":         {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output":  4.00},
}

# Rate limiting — conservative para evitar 429
SLEEP_BETWEEN_CALLS    = 1.2   # seconds between API calls
SLEEP_BETWEEN_SUBJECTS = 2.0   # seconds between subjects

# ── Importar helpers de Fase A-1 ──────────────────────────────────────────────
# El script A-2 reutiliza todas las funciones de A-1.
# Importar dinámicamente para evitar duplicación.

_A1_PATH = Path(__file__).parent / "measure_token_distribution_input.py"
import importlib.util
spec = importlib.util.spec_from_file_location("measure_input", _A1_PATH)
_a1  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_a1)

LILLY_SYSTEM_PROMPT = _a1.LILLY_SYSTEM_PROMPT
build_context_block = _a1.build_context_block
build_trigger_data  = _a1.build_trigger_data
call_analyze        = _a1.call_analyze
call_biography      = _a1.call_biography
parse_utc_offset    = _a1.parse_utc_offset

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY no está en el entorno.")
        sys.exit(1)

    # Safety gate: require explicit env var to prevent accidental execution
    if not os.environ.get("FINOPS_EXECUTE_A2"):
        print("=" * 60)
        print("⚠️  FASE A-2 — TIENE COSTO REAL (~$5-6)")
        print("Este script hace llamadas de generación a Anthropic.")
        print("Para ejecutar, setear: FINOPS_EXECUTE_A2=yes")
        print("Ejemplo:")
        print("  FINOPS_EXECUTE_A2=yes python scripts/finops/measure_token_distribution_output.py")
        print("=" * 60)
        sys.exit(0)

    # Verify Abu Engine
    try:
        r = requests.get(f"{ABU_URL}/health", timeout=5)
        r.raise_for_status()
        print(f"✓ Abu Engine reachable at {ABU_URL}")
    except Exception as e:
        print(f"ERROR: Abu Engine no responde en {ABU_URL}: {e}")
        sys.exit(1)

    # Load and sample subjects — same seed as A-1 for consistency
    all_subjects = []
    with open(RAW_DATA, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("latitude") and rec.get("longitude") and rec.get("birth_date") and rec.get("birth_time"):
                all_subjects.append(rec)

    random.seed(RANDOM_SEED)
    sample = random.sample(all_subjects, min(SAMPLE_N, len(all_subjects)))
    print(f"✓ Sampled {len(sample)} subjects (seed={RANDOM_SEED})")

    # Estimate cost before starting
    cost_sonnet_per_call = (4500 / 1e6) * 3.00 + (500 / 1e6) * 15.00
    cost_haiku_per_call  = (4000 / 1e6) * 0.80 + (300 / 1e6) * 4.00
    sonnet_routes = sum(1 for _, m, _ in ROUTES if "sonnet" in m)
    haiku_routes  = sum(1 for _, m, _ in ROUTES if "haiku"  in m)
    total_est = len(sample) * (sonnet_routes * cost_sonnet_per_call + haiku_routes * cost_haiku_per_call)
    print(f"Costo estimado: ${total_est:.2f} USD")
    print(f"Iniciando en 5 segundos... Ctrl+C para cancelar.")
    time.sleep(5)

    anthropic_client = anthropic.Anthropic(api_key=api_key)
    results = []
    skipped = 0
    total_cost = 0.0

    for i, subject in enumerate(sample):
        subject_id   = subject["id"]
        subject_name = subject.get("name", "?").split(" ::")[0]
        print(f"\n[{i+1}/{len(sample)}] {subject_id} — {subject_name}")

        abu_data = call_analyze(subject)
        if abu_data is None:
            skipped += 1
            continue

        timeline = call_biography(subject)

        for route_name, model, max_tokens in ROUTES:
            trigger = build_trigger_data(route_name, abu_data, timeline)
            context = build_context_block(abu_data, timeline, trigger, route_name, lang="es")

            try:
                resp = anthropic_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=LILLY_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": context}],
                )
                tokens_input  = resp.usage.input_tokens
                tokens_output = resp.usage.output_tokens
                stop_reason   = resp.stop_reason

                pricing = PRICING.get(model, {"input": 3.00, "output": 15.00})
                cost_usd = (tokens_input / 1e6) * pricing["input"] + \
                           (tokens_output / 1e6) * pricing["output"]
                total_cost += cost_usd

                truncated = stop_reason == "max_tokens"

            except Exception as e:
                print(f"  ✗ {route_name}: {e}")
                tokens_input = tokens_output = None
                cost_usd = 0.0
                truncated = None
                stop_reason = "error"

            record = {
                "subject_id":    subject_id,
                "subject_name":  subject_name,
                "route":         route_name,
                "model":         model,
                "max_tokens":    max_tokens,
                "tokens_input":  tokens_input,
                "tokens_output": tokens_output,
                "stop_reason":   stop_reason,
                "truncated":     truncated,
                "cost_usd":      round(cost_usd, 6),
                "timestamp":     datetime.now(timezone.utc).isoformat(),
            }
            results.append(record)
            trunc_flag = " ⚠️TRUNCATED" if truncated else ""
            status = f"{tokens_input:,} in / {tokens_output:,} out" if tokens_input else "ERROR"
            print(f"  {route_name:<25} {status}  ${cost_usd:.4f}{trunc_flag}")

            time.sleep(SLEEP_BETWEEN_CALLS)

        time.sleep(SLEEP_BETWEEN_SUBJECTS)

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "sample_n": len(sample), "skipped": skipped,
                "seed": RANDOM_SEED,
                "total_cost_usd": round(total_cost, 4),
                "generated_at":  datetime.now(timezone.utc).isoformat(),
            },
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"✓ Results written to {OUTPUT_FILE}")
    print(f"  Records: {len(results)}  |  Skipped: {skipped}  |  Total cost: ${total_cost:.4f}")

    # Summary per route: mean, p95, p99, truncation rate
    from collections import defaultdict
    import statistics
    route_out: dict[str, list] = defaultdict(list)
    route_trunc: dict[str, int] = defaultdict(int)
    for rec in results:
        if rec["tokens_output"] is not None:
            route_out[rec["route"]].append(rec["tokens_output"])
            if rec.get("truncated"):
                route_trunc[rec["route"]] += 1

    print(f"\n{'Route':<25} {'N':>4} {'mean':>6} {'p95':>6} {'p99':>6} {'max_cur':>8} {'trunc%':>8}")
    print("-" * 65)
    for route_name, model, max_tokens in ROUTES:
        vals = sorted(route_out.get(route_name, []))
        if not vals:
            continue
        n    = len(vals)
        mean = statistics.mean(vals)
        p95  = vals[min(int(n * 0.95), n-1)]
        p99  = vals[min(int(n * 0.99), n-1)]
        trunc_pct = route_trunc.get(route_name, 0) / n * 100
        flag = " ⚠️" if trunc_pct > 5 else ""
        print(f"{route_name:<25} {n:>4} {mean:>6.0f} {p95:>6} {p99:>6} {max_tokens:>8} {trunc_pct:>7.1f}%{flag}")

if __name__ == "__main__":
    main()
