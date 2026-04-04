"""
_run_scaling_empirical.py — Ejecuta load_simulator.py para múltiples N_USERS
con calibración empírica (Fase A-2b) y genera los archivos de output consolidados.

Output:
  research/finops/simulation_results_empirical.json  — resultados completos por N
  research/finops/scaling_analysis_empirical.md      — tabla comparativa con vs-synthetic

Uso:
  python scripts/finops/_run_scaling_empirical.py
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Importar el simulador directamente para reusar la lógica sin subprocess
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))

# Resultados sintéticos previos (Fase A-2, _scaling_raw.json) para comparación
SYNTHETIC_RESULTS = {
    500:   {"margin_static": -6.84,  "margin_greedy": 11.23, "shadow_tpm_greedy": 0.000000, "drop_rate_static": 0.0,  "cont_rate_static": 0.152},
    700:   {"margin_static": -9.98,  "margin_greedy": 15.84, "shadow_tpm_greedy": 0.005430, "drop_rate_static": 0.7,  "cont_rate_static": 0.152},
    800:   {"margin_static": -10.71, "margin_greedy": 18.07, "shadow_tpm_greedy": 0.018329, "drop_rate_static": 2.9,  "cont_rate_static": 0.152},
    1000:  {"margin_static": -11.01, "margin_greedy": 23.80, "shadow_tpm_greedy": 0.032966, "drop_rate_static": 11.5, "cont_rate_static": 0.152},
    5000:  {"margin_static": -23.00, "margin_greedy": 6.19,  "shadow_tpm_greedy": 0.018546, "drop_rate_static": 86.4, "cont_rate_static": 0.152},
    50000: {"margin_static": -4.98,  "margin_greedy": -0.95, "shadow_tpm_greedy": 0.000000, "drop_rate_static": 98.9, "cont_rate_static": 0.152},
}

N_VALUES = [500, 700, 800, 1000, 5000, 50000]
SIM_MINUTES = 60
SEED = 42
OUTPUT_SUFFIX = "_empirical"

OUTPUT_DIR = REPO_ROOT / "research" / "finops"


def run_single_n(n_users: int) -> dict:
    """Corre el simulador para un N dado y retorna el dict de resultados."""
    # Parchear las variables globales del módulo en tiempo de ejecución
    import load_simulator as sim

    # Guardar valores originales
    orig_n      = sim.N_USERS
    orig_min    = sim.SIM_MINUTES
    orig_seed   = sim.RANDOM_SEED
    orig_suffix = sim.OUTPUT_SUFFIX

    # Parchear
    sim.N_USERS       = n_users
    sim.SIM_MINUTES   = SIM_MINUTES
    sim.RANDOM_SEED   = SEED
    sim.OUTPUT_SUFFIX = ""   # no escribir archivos individuales

    import random
    from collections import defaultdict
    from dataclasses import asdict

    rng = random.Random(SEED)

    # Generar arrivals (copia del main())
    arrivals = []
    plans_list = list(sim.PLAN_WEIGHTS.keys())
    plan_weights_list = list(sim.PLAN_WEIGHTS.values())
    user_plans = {
        uid: rng.choices(plans_list, weights=plan_weights_list, k=1)[0]
        for uid in range(n_users)
    }
    lam = (sim.REQ_PER_HOUR / 60.0) * SIM_MINUTES
    for uid, plan in user_plans.items():
        k = sim._poisson_sample(lam, rng)
        times = sorted(rng.uniform(0, SIM_MINUTES * 60) for _ in range(k))
        for t in times:
            arrivals.append((t, uid, plan))
    arrivals.sort(key=lambda x: x[0])

    results_by_policy = {}
    for policy in ["static_baseline", "greedy_approximation"]:
        policy_rng = random.Random(SEED + (0 if policy == "static_baseline" else 1))
        records    = sim._run_policy(policy, arrivals, policy_rng)
        per_min    = sim._aggregate_per_minute(records)
        summ       = sim._summary(records, per_min, policy)
        results_by_policy[policy] = summ

    # Restaurar
    sim.N_USERS       = orig_n
    sim.SIM_MINUTES   = orig_min
    sim.RANDOM_SEED   = orig_seed
    sim.OUTPUT_SUFFIX = orig_suffix

    return results_by_policy


def main():
    print("=" * 60)
    print("FinOps Scaling — Calibración empírica Fase A-2b")
    print(f"N values: {N_VALUES}  SIM_MINUTES={SIM_MINUTES}  SEED={SEED}")
    print("=" * 60)

    all_results = {}

    for n in N_VALUES:
        print(f"\n[N={n:,}] Simulando...", end="", flush=True)
        res = run_single_n(n)
        s = res["static_baseline"]
        g = res["greedy_approximation"]
        all_results[str(n)] = {
            "n_users": n,
            "static_baseline":     s,
            "greedy_approximation": g,
        }
        print(f" static margin={s['total_margin_usd']:.2f}  "
              f"greedy margin={g['total_margin_usd']:.2f}  "
              f"cont_rate_static={s['continuation_rate']:.3f}")

    # Escribir JSON consolidado
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUTPUT_DIR / "simulation_results_empirical.json"
    meta = {
        "generated_at":      datetime.now(timezone.utc).isoformat(),
        "n_values":          N_VALUES,
        "sim_minutes":       SIM_MINUTES,
        "seed":              SEED,
        "calibration":       "empirical_phase_a2b",
        "continuation_model": "deterministic(tokens_output>=max_tokens)",
        "p_continuation":    0.036,
        "note": (
            "Output tokens: distribución empírica per-ruta (Fase A-2). "
            "Continuación determinística — models completeLilly() correctamente."
        ),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "results": all_results}, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] JSON: {out_json}")

    # Escribir Markdown
    out_md = OUTPUT_DIR / "scaling_analysis_empirical.md"
    _write_markdown(all_results, out_md, meta)
    print(f"[OK] Markdown: {out_md}")


def _write_markdown(all_results: dict, output_path: Path, meta: dict) -> None:
    syn = SYNTHETIC_RESULTS

    lines = [
        "# FinOps — Scaling Analysis Empírica (Fase A-2b)",
        "",
        f"**Generado:** {meta['generated_at']}  ",
        f"**Calibración:** empírica — distribución real de output tokens por ruta  ",
        f"**Continuación:** estocástica por ruta (ROUTE_CONTINUATION_RATE empírico)  ",
        f"**P_CONTINUATION:** 0.036 (medido) vs 0.150 (supuesto anterior)",
        "",
        "---",
        "",
        "## Tabla comparativa — Margen (empírico vs sintético)",
        "",
        "| N_USERS | Margen static | Margen greedy | Δ greedy-static | vs synthetic static | vs synthetic greedy |",
        "|---------|--------------|--------------|-----------------|---------------------|---------------------|",
    ]

    for n in [500, 700, 800, 1000, 5000, 50000]:
        key = str(n)
        if key not in all_results:
            continue
        s = all_results[key]["static_baseline"]
        g = all_results[key]["greedy_approximation"]
        ms = s["total_margin_usd"]
        mg = g["total_margin_usd"]
        delta = mg - ms

        # vs synthetic
        sy = syn.get(n, {})
        vs_s = f"{ms - sy.get('margin_static', ms):+.2f}" if n in syn else "—"
        vs_g = f"{mg - sy.get('margin_greedy', mg):+.2f}" if n in syn else "—"

        shadow_marker = " ← θ" if n == 700 else ""
        lines.append(
            f"| {n:,} | ${ms:.2f} | ${mg:.2f} | **${delta:.2f}** | {vs_s} | {vs_g} |{shadow_marker}"
        )

    lines += [
        "",
        "---",
        "",
        "## Continuation rate (empírico vs sintético)",
        "",
        "| N_USERS | Cont. rate static (empírico) | Cont. rate static (sintético) | Delta |",
        "|---------|------------------------------|-------------------------------|-------|",
    ]

    for n in [500, 700, 800, 1000, 5000, 50000]:
        key = str(n)
        if key not in all_results:
            continue
        s = all_results[key]["static_baseline"]
        emp_cont = s.get("continuation_rate", 0)
        syn_cont = syn.get(n, {}).get("cont_rate_static", 0.152)
        delta_cont = emp_cont - syn_cont
        lines.append(
            f"| {n:,} | {emp_cont:.3f} | {syn_cont:.3f} | {delta_cont:+.3f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Shadow price TPM (empírico)",
        "",
        "| N_USERS | Shadow TPM static | Shadow TPM greedy | θ activo |",
        "|---------|------------------|------------------|----------|",
    ]

    for n in [500, 700, 800, 1000, 5000, 50000]:
        key = str(n)
        if key not in all_results:
            continue
        s = all_results[key]["static_baseline"]
        g = all_results[key]["greedy_approximation"]
        sp_s = s.get("max_shadow_price_tpm_usd", 0)
        sp_g = g.get("max_shadow_price_tpm_usd", 0)
        theta = "**YES**" if sp_g > 0 else "no"
        lines.append(f"| {n:,} | ${sp_s:.6f} | ${sp_g:.6f} | {theta} |")

    lines += [
        "",
        "---",
        "",
        "## Drop rate y revenue perdido",
        "",
        "| N_USERS | Drop% static | Drop% greedy | Rev. lost static | Rev. lost greedy |",
        "|---------|-------------|-------------|-----------------|-----------------|",
    ]

    for n in [500, 700, 800, 1000, 5000, 50000]:
        key = str(n)
        if key not in all_results:
            continue
        s = all_results[key]["static_baseline"]
        g = all_results[key]["greedy_approximation"]
        lines.append(
            f"| {n:,} | {s['drop_rate_pct']:.1f}% | {g['drop_rate_pct']:.1f}% | "
            f"${s['revenue_lost_usd']:.2f} | ${g['revenue_lost_usd']:.2f} |"
        )

    # Número del abstract actualizado
    r1000 = all_results.get("1000")
    if r1000:
        ms_1k = r1000["static_baseline"]["total_margin_usd"]
        mg_1k = r1000["greedy_approximation"]["total_margin_usd"]
        delta_1k = mg_1k - ms_1k
        # Extrapolación: 720 horas/mes × 70% uptime
        monthly = delta_1k * 720 * 0.70
        lines += [
            "",
            "---",
            "",
            "## El número del abstract (calibrado empíricamente)",
            "",
            f"**A 1,000 usuarios simultáneos (60 minutos de carga sostenida):**",
            "",
            f"> La greedy_approximation genera **+${delta_1k:.2f} USD de margen adicional** "
            f"respecto a la política estática. Extrapolado a operación mensual (720h, 70% uptime): "
            f"**+${monthly:,.0f} USD/mes de margen adicional a N=1,000 usuarios.**",
            "",
            f"*Comparación: con supuestos sintéticos el número era +$34.81 USD/60min (+$17,524/mes).*",
            "",
        ]

    lines += [
        "",
        "---",
        "",
        "## Cambios respecto a calibración sintética",
        "",
        "| Parámetro | Sintético | Empírico (A-2b) | Impacto |",
        "|-----------|-----------|----------------|---------|",
        "| P_CONTINUATION | 0.150 | **0.036** | Costo sobreestimado ~12% en sintético |",
        "| Continuación | estocástica (P_CONT=0.15 global) | **estocástica por ruta (empírico)** | screen-open: 71.1%; técnicas: 0-2.2% |",
        "| screen-open output | Normal(665,154) | **Normal(960,39)** | Costo real 2× mayor para esta ruta |",
        "| technique_* output | Normal(1331,307) | **Normal(415-437,40-44)** | Costo sintético 3× sobreestimado |",
        "| domain output | Normal(665,154) | **Normal(660,147)** | Bien calibrado originalmente |",
        "",
        "---",
        "",
        "## Bug conocido — screen-open max_tokens",
        "",
        "Con mean=960 y max_tokens=1024, `screen-open` produce **71.1% de continuación** (32/45 records).",
        "En producción, `completeLilly()` detecta esto y hace una segunda llamada API,",
        "duplicando el costo de esa ruta. Solución: subir max_tokens a 1536 o 2048.",
        "**Estado: bug activo en producción. Pendiente fix.**",
        "",
        "## Oportunidad — technique_lot y technique_firdaria",
        "",
        "p95 real ≈ 497 tokens vs max_tokens=2048 actual. Reducir a 512 ahorra:",
        "- `(2048-512)/1e6 × $4.00/1M × n_requests ≈ $0.006/request` en Haiku",
        "- A N=1,000 con ~9% de requests en estas rutas: ahorro ~$0.5/hr o ~$250/mes",
        "",
        "---",
        "",
        "_Generado por `scripts/finops/_run_scaling_empirical.py`_  ",
        "_Datos A-2: `research/finops/token_distribution_output.json`_  ",
        "_Calibración: Fase A-2b, 2026-04-04_",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
