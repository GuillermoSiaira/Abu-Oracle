"""
load_simulator.py — Simulador de carga FinOps para Abu Oracle / Lilly.

Simula 500 usuarios simultáneos durante 60 minutos y compara dos políticas
de asignación de modelo:

  1. static_baseline   — réplica exacta de selectModel.ts (hardcoded)
  2. greedy_approximation — heurístico derivado de la estructura del MILP:
       prioriza margen por plan, degrada a Haiku cuando TPM > 85% saturación,
       y aplica restricción R5 (min_margin por sesión).

Ajustes incorporados (spec 2026-04-02):
  A. completeLilly() modelado: P_CONTINUATION=0.15 → segunda llamada API
  B. Genesis revenue: $100/3000 sesiones = $0.0333/sesión
  C. Output tokens: Normal(max_tokens×0.65, max_tokens×0.15) trunc [100, max_tokens]
  D. Nomenclatura: "greedy_approximation" (no "MILP greedy")
  E. requests_dropped: 429 explícito, cost=0, revenue=0, revenue_lost_usd registrado
  R5: min_margin_monthly=$0.010, min_margin_annual=$0.008 (binding en alta carga)

Output:
  research/finops/load_simulation_results.json
  research/finops/load_simulation_summary.md

Uso:
  python scripts/finops/load_simulator.py

  # Subset rapido para verificar:
  N_USERS=50 SIM_MINUTES=10 python scripts/finops/load_simulator.py

  # Seed reproducible:
  SIM_SEED=123 python scripts/finops/load_simulator.py
"""

import json
import math
import os
import random
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Configuracion ─────────────────────────────────────────────────────────────

REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "research" / "finops"

N_USERS          = int(os.environ.get("N_USERS",      "500"))
SIM_MINUTES      = int(os.environ.get("SIM_MINUTES",  "60"))
REQ_PER_HOUR     = int(os.environ.get("REQ_PER_HOUR", "10"))
RANDOM_SEED      = int(os.environ.get("SIM_SEED",     "42"))

# Anthropic Tier 2 limits (shared across all users)
TIER2_RPM = 1_000
TIER2_TPM = 450_000

# P(stop_reason == max_tokens) -> segundo llamado API (completeLilly loop)
P_CONTINUATION = 0.15

# Plan distribution: genesis 10%, annual 30%, monthly 60%
PLAN_WEIGHTS = {"genesis": 0.10, "annual": 0.30, "monthly": 0.60}

# Revenue por sesion (10 requests = 1 sesion)
# genesis: $100 one-time / 3000 sesiones esperadas de vida util
# annual:  $45/yr / 365 dias / 10 req/dia
# monthly: $5/mo / 30 dias / 10 req/dia
REVENUE_PER_REQUEST = {
    "genesis": 100.0 / 3000 / 10,     # $0.003333/req
    "annual":  45.0  / 365  / 10,     # $0.001233/req
    "monthly":  5.0  /  30  / 10,     # $0.001667/req
}

# R5: margen minimo por sesion (10 requests) — binding en alta carga
MIN_MARGIN_PER_SESSION = {
    "genesis": None,       # sin restriccion (plan lifetime)
    "annual":  0.008,      # $0.008/sesion
    "monthly": 0.010,      # $0.010/sesion
}
MIN_MARGIN_PER_REQUEST = {
    plan: (v / 10 if v is not None else None)
    for plan, v in MIN_MARGIN_PER_SESSION.items()
}

# Precios Anthropic (USD por 1M tokens)
PRICING = {
    "claude-sonnet-4-6": {
        "input":       3.00,
        "output":     15.00,
        "cache_write": 3.75,
        "cache_read":  0.30,
    },
    "claude-haiku-4-5-20251001": {
        "input":       0.80,
        "output":      4.00,
        "cache_write": 1.00,
        "cache_read":  0.08,
    },
}

# System prompt aproximado (cacheado con cache_control: ephemeral)
SYSTEM_PROMPT_TOKENS = 3_200   # tokens del LILLY_SYSTEM_PROMPT
CONTEXT_NONCACHED_TOKENS_MU  = 850   # natal + timeline (no cacheados)
CONTEXT_NONCACHED_TOKENS_STD = 100
INPUT_COLD_MU  = 4_050   # primer request del usuario (sin cache)
INPUT_COLD_STD =   150

# Probabilidad de cache hit en request >= 2 del mismo usuario
P_CACHE_HIT = 0.70

# Shadow price threshold
SHADOW_PRICE_THRESHOLD = 0.95   # 95% saturacion

# Routes: (name, static_model, max_tokens)
# Source: FINOPS_MILP_VARIABLES.md
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

ROUTE_NAMES    = [r[0] for r in ROUTES]
ROUTE_MODEL    = {r[0]: r[1] for r in ROUTES}
ROUTE_MAXTOK   = {r[0]: r[2] for r in ROUTES}

# Rutas que permiten degradacion a Haiku en la politica greedy
HAIKU_ELIGIBLE = {"technique_lot", "technique_firdaria", "technique_lunar",
                  "city", "domain", "house", "transit"}
HAIKU_MODEL    = "claude-haiku-4-5-20251001"
SONNET_MODEL   = "claude-sonnet-4-6"

# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class RequestRecord:
    request_id:     int
    user_id:        int
    plan:           str
    route:          str
    arrival_time:   float    # segundos desde t=0
    minute_bucket:  int

    model:          str
    max_tokens:     int
    routing_reason: str

    tokens_input:   int
    tokens_output:  int
    cache_hit:      bool
    continuation:   bool     # segunda llamada por max_tokens
    dropped:        bool     # 429 por rate limit

    cost_usd:       float
    revenue_usd:    float
    margin_usd:     float
    revenue_lost_usd: float  # solo si dropped=True

    r5_applied:     bool     # greedy: R5 cambio el modelo

# ── Helpers de distribucion ───────────────────────────────────────────────────

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def _normal_int(mu: float, sigma: float, lo: int, hi: int, rng: random.Random) -> int:
    """Gaussian truncada, retorna entero."""
    raw = rng.gauss(mu, sigma)
    return int(_clamp(raw, lo, hi))

def _sample_tokens_input(cache_hit: bool, rng: random.Random) -> int:
    """
    Input tokens por request.
    cache_hit=True  → system prompt viene del cache; solo se cobran los tokens
                      del bloque no cacheado (natal + timeline).
    cache_hit=False → request frio: Normal(4050, 150).
    """
    if cache_hit:
        return _normal_int(
            CONTEXT_NONCACHED_TOKENS_MU,
            CONTEXT_NONCACHED_TOKENS_STD,
            lo=200, hi=2000, rng=rng
        )
    else:
        return _normal_int(INPUT_COLD_MU, INPUT_COLD_STD, lo=500, hi=8000, rng=rng)

def _sample_tokens_output(max_tokens: int, rng: random.Random) -> int:
    """Normal(max_tokens*0.65, max_tokens*0.15) truncada en [100, max_tokens]."""
    mu    = max_tokens * 0.65
    sigma = max_tokens * 0.15
    return _normal_int(mu, sigma, lo=100, hi=max_tokens, rng=rng)

def _compute_cost(
    model: str,
    tokens_input: int,
    tokens_output: int,
    cache_hit: bool,
    continuation: bool,
) -> float:
    """
    Calcula costo en USD.
    cache_hit: SYSTEM_PROMPT_TOKENS se cobran a cache_read_price.
    continuation: agrega costo de segunda llamada API (completeLilly loop).
    """
    p = PRICING[model]

    if cache_hit:
        input_cost = (
            (SYSTEM_PROMPT_TOKENS / 1e6) * p["cache_read"] +
            (tokens_input          / 1e6) * p["input"]
        )
    else:
        input_cost = (tokens_input / 1e6) * p["input"]

    output_cost = (tokens_output / 1e6) * p["output"]
    base_cost   = input_cost + output_cost

    if continuation:
        # Segunda llamada: ~misma longitud de output, input es el fragmento previo
        continuation_output = _normal_int(
            tokens_output * 0.30, tokens_output * 0.10,
            lo=50, hi=tokens_output, rng=random.Random()
        )
        continuation_cost = (
            (tokens_output      / 1e6) * p["input"] +   # fragmento previo = input
            (continuation_output / 1e6) * p["output"]
        )
        base_cost += continuation_cost

    return base_cost

# ── Politicas de modelo ───────────────────────────────────────────────────────

def _static_policy(route: str, plan: str) -> Tuple[str, int, str]:
    """
    Replica exacta de selectModel.ts.
    technique_* y city → Haiku. Resto → Sonnet.
    """
    model     = ROUTE_MODEL[route]
    max_tok   = ROUTE_MAXTOK[route]
    reason    = "static_baseline"
    return model, max_tok, reason

def _greedy_policy(
    route: str,
    plan: str,
    tpm_used: int,
    rpm_used: int,
    rng: random.Random,
) -> Tuple[str, int, str, bool]:
    """
    Greedy approximation derivado de la estructura del MILP.

    Logica:
    1. Punto de partida: modelo estatico de selectModel.ts.
    2. Si TPM > 85% saturacion Y ruta es Haiku-eligible → degradar a Haiku.
    3. Si R5 activo: verificar que margin >= MIN_MARGIN_PER_REQUEST.
       Si no cumple con Haiku, mantener Sonnet (calidad protegida).
       Si no cumple con Sonnet, reducir max_tokens al minimo admisible.

    Retorna (model, max_tokens, routing_reason, r5_applied).
    """
    model    = ROUTE_MODEL[route]
    max_tok  = ROUTE_MAXTOK[route]
    r5_applied = False
    reason_parts = ["greedy_approximation"]

    tpm_utilization = tpm_used / TIER2_TPM

    # Paso 1: degradacion por presion de TPM
    if tpm_utilization > 0.85 and route in HAIKU_ELIGIBLE:
        model  = HAIKU_MODEL
        reason_parts.append("tpm_pressure")

    # Paso 2: R5 — verificar margen minimo
    min_margin = MIN_MARGIN_PER_REQUEST.get(plan)
    if min_margin is not None:
        revenue   = REVENUE_PER_REQUEST[plan]
        # Estimacion rapida de costo con distribucion esperada
        est_output  = max_tok * 0.65
        est_input   = CONTEXT_NONCACHED_TOKENS_MU  # conservador
        p_          = PRICING[model]
        est_cost    = (est_input / 1e6) * p_["input"] + (est_output / 1e6) * p_["output"]
        est_cost   *= (1 + P_CONTINUATION * 0.3)   # factor de continuacion

        if revenue - est_cost < min_margin:
            # Intentar con Haiku si la ruta lo permite
            if route in HAIKU_ELIGIBLE and model != HAIKU_MODEL:
                p_h     = PRICING[HAIKU_MODEL]
                cost_h  = (est_input / 1e6) * p_h["input"] + (est_output / 1e6) * p_h["output"]
                cost_h *= (1 + P_CONTINUATION * 0.3)
                if revenue - cost_h >= min_margin:
                    model      = HAIKU_MODEL
                    r5_applied = True
                    reason_parts.append("r5_haiku")
            # Si Sonnet y margen insuficiente: reducir max_tokens
            elif model == SONNET_MODEL:
                # Despejar max_tokens de: revenue - (input_cost + output/1e6 * price) >= min_margin
                p_s = PRICING[SONNET_MODEL]
                budget_for_output = (revenue - min_margin) - (est_input / 1e6) * p_s["input"]
                if budget_for_output > 0:
                    new_max = int((budget_for_output / p_s["output"]) * 1e6)
                    max_tok = max(256, min(new_max, max_tok))
                    r5_applied = True
                    reason_parts.append("r5_token_reduce")

    reason = "+".join(reason_parts)
    return model, max_tok, reason, r5_applied

# ── Generacion de llegadas ────────────────────────────────────────────────────

def _generate_arrivals(
    n_users: int,
    duration_min: int,
    req_per_hour: int,
    rng: random.Random,
) -> List[Tuple[float, int, str]]:
    """
    Poisson arrivals por usuario.
    Retorna lista de (arrival_time_seconds, user_id, plan) ordenada por tiempo.
    """
    plans = list(PLAN_WEIGHTS.keys())
    weights = list(PLAN_WEIGHTS.values())

    # Asignar plan a cada usuario una sola vez
    user_plans = {uid: rng.choices(plans, weights=weights, k=1)[0] for uid in range(n_users)}

    arrivals = []
    lam = (req_per_hour / 60.0) * duration_min   # lambda total en la ventana

    for uid, plan in user_plans.items():
        k = rng.poisson_approx(lam, rng)
        times = sorted(rng.uniform(0, duration_min * 60) for _ in range(k))
        for t in times:
            arrivals.append((t, uid, plan))

    arrivals.sort(key=lambda x: x[0])
    return arrivals

def _poisson_sample(lam: float, rng: random.Random) -> int:
    """Muestrea de Poisson(lam) con metodo de Knuth para lam pequeño."""
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= rng.random()
    return k - 1

# ── Rate limiter ──────────────────────────────────────────────────────────────

def _is_dropped(
    bucket: int,
    est_tokens: int,
    rpm_counter: Dict[int, int],
    tpm_counter: Dict[int, int],
) -> bool:
    """Retorna True si el request supera los limites de Tier 2 (429)."""
    if rpm_counter[bucket] >= TIER2_RPM:
        return True
    if tpm_counter[bucket] + est_tokens > TIER2_TPM:
        return True
    return False

# ── Loop de simulacion ────────────────────────────────────────────────────────

def _run_policy(
    policy: str,
    arrivals: List[Tuple[float, int, str]],
    rng: random.Random,
) -> List[RequestRecord]:
    """Simula todos los requests de una politica y retorna los registros."""
    rpm_counter:       Dict[int, int] = defaultdict(int)
    tpm_counter:       Dict[int, int] = defaultdict(int)
    user_req_count:    Dict[int, int] = defaultdict(int)

    records: List[RequestRecord] = []

    for req_id, (arrival_t, uid, plan) in enumerate(arrivals):
        bucket = int(arrival_t // 60)
        route  = rng.choice(ROUTE_NAMES)

        # Decidir modelo segun politica
        if policy == "static_baseline":
            model, max_tok, reason = _static_policy(route, plan)
            r5_applied = False
        else:
            model, max_tok, reason, r5_applied = _greedy_policy(
                route, plan,
                tpm_used=tpm_counter[bucket],
                rpm_used=rpm_counter[bucket],
                rng=rng,
            )

        # Estimar tokens para rate limiter
        est_input  = INPUT_COLD_MU
        est_output = int(max_tok * 0.65)
        est_tokens = est_input + est_output

        # Verificar rate limit (429)
        dropped = _is_dropped(bucket, est_tokens, rpm_counter, tpm_counter)
        if dropped:
            revenue    = REVENUE_PER_REQUEST[plan]
            rev_lost   = revenue
            rec = RequestRecord(
                request_id=req_id, user_id=uid, plan=plan, route=route,
                arrival_time=arrival_t, minute_bucket=bucket,
                model=model, max_tokens=max_tok, routing_reason=reason,
                tokens_input=0, tokens_output=0,
                cache_hit=False, continuation=False, dropped=True,
                cost_usd=0.0, revenue_usd=0.0, margin_usd=0.0,
                revenue_lost_usd=rev_lost, r5_applied=r5_applied,
            )
            records.append(rec)
            continue

        # Cache hit: aplica si no es el primer request del usuario
        cache_hit = (user_req_count[uid] > 0) and (rng.random() < P_CACHE_HIT)

        # Muestrear tokens reales
        tokens_input  = _sample_tokens_input(cache_hit, rng)
        tokens_output = _sample_tokens_output(max_tok, rng)

        # Continuacion (completeLilly loop)
        continuation = rng.random() < P_CONTINUATION

        # Costo y margen
        cost_usd    = _compute_cost(model, tokens_input, tokens_output, cache_hit, continuation)
        revenue_usd = REVENUE_PER_REQUEST[plan]
        margin_usd  = revenue_usd - cost_usd

        # Actualizar contadores (1 call base + 1 si continuation)
        n_calls = 2 if continuation else 1
        rpm_counter[bucket] += n_calls
        tpm_counter[bucket] += tokens_input + tokens_output
        user_req_count[uid] += 1

        rec = RequestRecord(
            request_id=req_id, user_id=uid, plan=plan, route=route,
            arrival_time=arrival_t, minute_bucket=bucket,
            model=model, max_tokens=max_tok, routing_reason=reason,
            tokens_input=tokens_input, tokens_output=tokens_output,
            cache_hit=cache_hit, continuation=continuation, dropped=False,
            cost_usd=cost_usd, revenue_usd=revenue_usd, margin_usd=margin_usd,
            revenue_lost_usd=0.0, r5_applied=r5_applied,
        )
        records.append(rec)

    return records

# ── Agregacion de metricas ────────────────────────────────────────────────────

def _aggregate_per_minute(records: List[RequestRecord]) -> List[dict]:
    """Agrega metricas por ventana de 1 minuto."""
    buckets: Dict[int, List[RequestRecord]] = defaultdict(list)
    for r in records:
        buckets[r.minute_bucket].append(r)

    max_bucket = max(buckets.keys()) if buckets else 0
    result = []

    for bucket in range(max_bucket + 1):
        recs = buckets[bucket]
        served   = [r for r in recs if not r.dropped]
        dropped  = [r for r in recs if r.dropped]
        conts    = [r for r in served if r.continuation]
        cached   = [r for r in served if r.cache_hit]
        r5_recs  = [r for r in served if r.r5_applied]

        tpm_used = sum(r.tokens_input + r.tokens_output for r in served)
        rpm_used = sum((2 if r.continuation else 1) for r in served)

        tpm_util = tpm_used / TIER2_TPM
        rpm_util = rpm_used / TIER2_RPM

        # Shadow price: valor economico de 1 token adicional cuando saturacion > 95%
        # = (margen promedio por token) * tokens excedentes
        shadow_price_tpm = 0.0
        if tpm_util > SHADOW_PRICE_THRESHOLD and served:
            avg_margin_per_token = (
                sum(r.margin_usd for r in served) /
                max(sum(r.tokens_input + r.tokens_output for r in served), 1)
            )
            excess_tpm = tpm_used - SHADOW_PRICE_THRESHOLD * TIER2_TPM
            shadow_price_tpm = avg_margin_per_token * excess_tpm

        shadow_price_rpm = 0.0
        if rpm_util > SHADOW_PRICE_THRESHOLD and served:
            avg_margin_per_req = statistics.mean(r.margin_usd for r in served) if served else 0
            excess_rpm = rpm_used - SHADOW_PRICE_THRESHOLD * TIER2_RPM
            shadow_price_rpm = avg_margin_per_req * excess_rpm

        result.append({
            "minute":                bucket,
            "requests_total":        len(recs),
            "requests_served":       len(served),
            "requests_dropped":      len(dropped),
            "requests_continued":    len(conts),
            "requests_r5_applied":   len(r5_recs),
            "total_cost_usd":        round(sum(r.cost_usd    for r in served), 6),
            "total_revenue_usd":     round(sum(r.revenue_usd for r in served), 6),
            "total_margin_usd":      round(sum(r.margin_usd  for r in served), 6),
            "revenue_lost_usd":      round(sum(r.revenue_lost_usd for r in dropped), 6),
            "tpm_used":              tpm_used,
            "rpm_used":              rpm_used,
            "tpm_utilization_pct":   round(tpm_util * 100, 2),
            "rpm_utilization_pct":   round(rpm_util * 100, 2),
            "shadow_price_tpm_usd":  round(shadow_price_tpm, 8),
            "shadow_price_rpm_usd":  round(shadow_price_rpm, 8),
            "cache_hit_rate":        round(len(cached) / max(len(served), 1), 4),
            "continuation_rate":     round(len(conts)  / max(len(served), 1), 4),
        })

    return result

def _summary(records: List[RequestRecord], per_minute: List[dict], policy: str) -> dict:
    """Computa resumen global de la politica."""
    served  = [r for r in records if not r.dropped]
    dropped = [r for r in records if r.dropped]

    n_served  = len(served)
    n_dropped = len(dropped)
    n_total   = len(records)

    total_cost    = sum(r.cost_usd    for r in served)
    total_rev     = sum(r.revenue_usd for r in served)
    total_margin  = sum(r.margin_usd  for r in served)
    rev_lost      = sum(r.revenue_lost_usd for r in dropped)

    # Breakdown por plan
    plan_stats: Dict[str, dict] = {}
    for plan in PLAN_WEIGHTS:
        plan_recs   = [r for r in served if r.plan == plan]
        plan_dropped = [r for r in dropped if r.plan == plan]
        if not plan_recs:
            plan_stats[plan] = {}
            continue
        plan_stats[plan] = {
            "requests_served":  len(plan_recs),
            "requests_dropped": len(plan_dropped),
            "total_cost_usd":   round(sum(r.cost_usd    for r in plan_recs), 4),
            "total_revenue_usd":round(sum(r.revenue_usd for r in plan_recs), 4),
            "total_margin_usd": round(sum(r.margin_usd  for r in plan_recs), 4),
            "avg_margin_per_req":round(statistics.mean(r.margin_usd for r in plan_recs), 6),
        }

    # Breakdown por ruta
    route_stats: Dict[str, dict] = {}
    for route_name in ROUTE_NAMES:
        rr = [r for r in served if r.route == route_name]
        if not rr:
            continue
        models_used = {}
        for r in rr:
            models_used[r.model] = models_used.get(r.model, 0) + 1
        route_stats[route_name] = {
            "requests_served": len(rr),
            "avg_cost_usd":    round(statistics.mean(r.cost_usd for r in rr), 6),
            "models_used":     models_used,
            "continuation_rate": round(sum(1 for r in rr if r.continuation) / len(rr), 4),
        }

    max_shadow_tpm = max((m["shadow_price_tpm_usd"] for m in per_minute), default=0.0)
    max_shadow_rpm = max((m["shadow_price_rpm_usd"] for m in per_minute), default=0.0)
    max_tpm_util   = max((m["tpm_utilization_pct"]  for m in per_minute), default=0.0)
    max_rpm_util   = max((m["rpm_utilization_pct"]  for m in per_minute), default=0.0)

    return {
        "policy":                policy,
        "requests_total":        n_total,
        "requests_served":       n_served,
        "requests_dropped":      n_dropped,
        "drop_rate_pct":         round(n_dropped / max(n_total, 1) * 100, 2),
        "requests_continued":    sum(1 for r in served if r.continuation),
        "requests_r5_applied":   sum(1 for r in served if r.r5_applied),
        "total_cost_usd":        round(total_cost,   4),
        "total_revenue_usd":     round(total_rev,    4),
        "total_margin_usd":      round(total_margin, 4),
        "revenue_lost_usd":      round(rev_lost,     4),
        "avg_cost_per_req":      round(total_cost   / max(n_served, 1), 6),
        "avg_margin_per_req":    round(total_margin / max(n_served, 1), 6),
        "cache_hit_rate":        round(sum(1 for r in served if r.cache_hit) / max(n_served, 1), 4),
        "continuation_rate":     round(sum(1 for r in served if r.continuation) / max(n_served, 1), 4),
        "max_tpm_utilization_pct": max_tpm_util,
        "max_rpm_utilization_pct": max_rpm_util,
        "max_shadow_price_tpm_usd": max_shadow_tpm,
        "max_shadow_price_rpm_usd": max_shadow_rpm,
        "by_plan":               plan_stats,
        "by_route":              route_stats,
    }

# ── Markdown summary ──────────────────────────────────────────────────────────

def _write_markdown(results: dict, output_path: Path) -> None:
    meta = results["meta"]
    s_static = results["policies"]["static_baseline"]["summary"]
    s_greedy = results["policies"]["greedy_approximation"]["summary"]

    def pct_diff(g, s, key, invert=False):
        """% diferencia greedy vs static. invert=True si menor es mejor."""
        sv, gv = s.get(key, 0), g.get(key, 0)
        if sv == 0:
            return "N/A"
        d = (gv - sv) / abs(sv) * 100
        if invert:
            d = -d
        sign = "+" if d >= 0 else ""
        return f"{sign}{d:.1f}%"

    lines = [
        "# Load Simulation — Resultados",
        "",
        f"**Generado:** {meta['generated_at']}  ",
        f"**Usuarios:** {meta['n_users']} · **Duracion:** {meta['sim_minutes']} min · "
        f"**Req/usuario/hr:** {meta['req_per_hour']} · **Seed:** {meta['seed']}",
        "",
        "---",
        "",
        "## Comparacion de politicas",
        "",
        "| Metrica | static_baseline | greedy_approximation | Delta |",
        "|---------|----------------|----------------------|-------|",
        f"| Requests servidos | {s_static['requests_served']:,} | {s_greedy['requests_served']:,} | {pct_diff(s_greedy, s_static, 'requests_served')} |",
        f"| Requests dropped | {s_static['requests_dropped']:,} | {s_greedy['requests_dropped']:,} | {pct_diff(s_greedy, s_static, 'requests_dropped', invert=True)} |",
        f"| Drop rate | {s_static['drop_rate_pct']:.1f}% | {s_greedy['drop_rate_pct']:.1f}% | — |",
        f"| Costo total (USD) | ${s_static['total_cost_usd']:.4f} | ${s_greedy['total_cost_usd']:.4f} | {pct_diff(s_greedy, s_static, 'total_cost_usd', invert=True)} |",
        f"| Revenue total (USD) | ${s_static['total_revenue_usd']:.4f} | ${s_greedy['total_revenue_usd']:.4f} | {pct_diff(s_greedy, s_static, 'total_revenue_usd')} |",
        f"| Margen total (USD) | ${s_static['total_margin_usd']:.4f} | ${s_greedy['total_margin_usd']:.4f} | {pct_diff(s_greedy, s_static, 'total_margin_usd')} |",
        f"| Revenue lost (dropped) | ${s_static['revenue_lost_usd']:.4f} | ${s_greedy['revenue_lost_usd']:.4f} | — |",
        f"| Avg cost/req | ${s_static['avg_cost_per_req']:.6f} | ${s_greedy['avg_cost_per_req']:.6f} | {pct_diff(s_greedy, s_static, 'avg_cost_per_req', invert=True)} |",
        f"| Avg margin/req | ${s_static['avg_margin_per_req']:.6f} | ${s_greedy['avg_margin_per_req']:.6f} | {pct_diff(s_greedy, s_static, 'avg_margin_per_req')} |",
        f"| Cache hit rate | {s_static['cache_hit_rate']:.1%} | {s_greedy['cache_hit_rate']:.1%} | — |",
        f"| Continuation rate | {s_static['continuation_rate']:.1%} | {s_greedy['continuation_rate']:.1%} | — |",
        f"| Max TPM utilization | {s_static['max_tpm_utilization_pct']:.1f}% | {s_greedy['max_tpm_utilization_pct']:.1f}% | — |",
        f"| Max RPM utilization | {s_static['max_rpm_utilization_pct']:.1f}% | {s_greedy['max_rpm_utilization_pct']:.1f}% | — |",
        f"| Max shadow price TPM | ${s_static['max_shadow_price_tpm_usd']:.6f} | ${s_greedy['max_shadow_price_tpm_usd']:.6f} | — |",
        f"| R5 applications | {s_static['requests_r5_applied']:,} | {s_greedy['requests_r5_applied']:,} | — |",
        "",
        "---",
        "",
        "## Margen por plan",
        "",
        "| Plan | Politica | Requests | Costo | Revenue | Margen | Avg margin/req |",
        "|------|----------|----------|-------|---------|--------|----------------|",
    ]

    for plan in PLAN_WEIGHTS:
        for pol_key, pol_label in [
            ("static_baseline", "static"),
            ("greedy_approximation", "greedy"),
        ]:
            ps = results["policies"][pol_key]["summary"]["by_plan"].get(plan, {})
            if not ps:
                continue
            lines.append(
                f"| {plan} | {pol_label} | {ps.get('requests_served',0):,} | "
                f"${ps.get('total_cost_usd',0):.4f} | "
                f"${ps.get('total_revenue_usd',0):.4f} | "
                f"${ps.get('total_margin_usd',0):.4f} | "
                f"${ps.get('avg_margin_per_req',0):.6f} |"
            )

    lines += [
        "",
        "---",
        "",
        "## Shadow prices — interpretacion",
        "",
        (
            f"**static_baseline** max shadow price TPM: "
            f"${s_static['max_shadow_price_tpm_usd']:.6f}  "
        ),
        (
            f"**greedy_approximation** max shadow price TPM: "
            f"${s_greedy['max_shadow_price_tpm_usd']:.6f}"
        ),
        "",
        "El shadow price de TPM cuantifica el valor economico de 1 token adicional "
        "de capacidad cuando el sistema supera el 95% de saturacion.",
        "Un shadow price > 0 indica que subir de tier tiene valor economico medible.",
        "",
        "---",
        "",
        "## Costo de la limitacion de rate limit",
        "",
        f"**static_baseline** revenue lost por 429: ${s_static['revenue_lost_usd']:.4f}  ",
        f"**greedy_approximation** revenue lost por 429: ${s_greedy['revenue_lost_usd']:.4f}",
        "",
        "Revenue perdido = revenue que hubiera generado cada request dropped.",
        "Esto cuantifica el costo de no subir de tier en escenarios de alta carga.",
        "",
        "---",
        "",
        "_Nota: greedy_approximation es un heuristico derivado de la estructura del MILP,_",
        "_no una solucion LP exacta. Ver MILP_INITIATIVE.md para la formulacion completa._",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("FinOps Load Simulator — Abu Oracle / Lilly")
    print(f"  Usuarios: {N_USERS}  Duracion: {SIM_MINUTES} min  "
          f"Req/hr: {REQ_PER_HOUR}  Seed: {RANDOM_SEED}")
    print("=" * 60)

    rng = random.Random(RANDOM_SEED)

    # Generar llegadas Poisson (mismas para ambas politicas)
    arrivals = []
    plans_list = list(PLAN_WEIGHTS.keys())
    plan_weights_list = list(PLAN_WEIGHTS.values())
    user_plans = {
        uid: rng.choices(plans_list, weights=plan_weights_list, k=1)[0]
        for uid in range(N_USERS)
    }
    lam = (REQ_PER_HOUR / 60.0) * SIM_MINUTES
    for uid, plan in user_plans.items():
        k = _poisson_sample(lam, rng)
        times = sorted(rng.uniform(0, SIM_MINUTES * 60) for _ in range(k))
        for t in times:
            arrivals.append((t, uid, plan))
    arrivals.sort(key=lambda x: x[0])

    print(f"[arrivals] Total requests generados: {len(arrivals):,}")
    plan_counts = defaultdict(int)
    for _, _, p in arrivals:
        plan_counts[p] += 1
    for pl, cnt in sorted(plan_counts.items()):
        print(f"  {pl:<10} {cnt:>6,} requests  "
              f"({cnt/max(len(arrivals),1)*100:.1f}%)")

    results_by_policy = {}

    for policy in ["static_baseline", "greedy_approximation"]:
        print(f"\n[{policy}] Simulando {len(arrivals):,} requests...")
        # Usar sub-RNG con seed fijo para que las dos politicas
        # tengan los mismos valores de noise (cache_hit, output_tokens, continuation)
        policy_rng = random.Random(RANDOM_SEED + (0 if policy == "static_baseline" else 1))

        records = _run_policy(policy, arrivals, policy_rng)
        per_min = _aggregate_per_minute(records)
        summ    = _summary(records, per_min, policy)

        served  = sum(1 for r in records if not r.dropped)
        dropped = sum(1 for r in records if r.dropped)
        print(f"  Servidos: {served:,}  Dropped: {dropped:,}  "
              f"Drop rate: {dropped/max(len(records),1)*100:.1f}%")
        print(f"  Costo total:  ${summ['total_cost_usd']:.4f}")
        print(f"  Revenue total: ${summ['total_revenue_usd']:.4f}")
        print(f"  Margen total:  ${summ['total_margin_usd']:.4f}")
        print(f"  Cache hit rate: {summ['cache_hit_rate']:.1%}")
        print(f"  Continuation rate: {summ['continuation_rate']:.1%}")
        if summ["max_shadow_price_tpm_usd"] > 0:
            print(f"  [!] Shadow price TPM max: ${summ['max_shadow_price_tpm_usd']:.6f}")
        if summ["revenue_lost_usd"] > 0:
            print(f"  [!] Revenue lost por 429: ${summ['revenue_lost_usd']:.4f}")

        results_by_policy[policy] = {
            "summary":    summ,
            "per_minute": per_min,
            "requests":   [asdict(r) for r in records],
        }

    # Escribir JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_json = OUTPUT_DIR / "load_simulation_results.json"
    meta = {
        "n_users":       N_USERS,
        "sim_minutes":   SIM_MINUTES,
        "req_per_hour":  REQ_PER_HOUR,
        "seed":          RANDOM_SEED,
        "p_continuation": P_CONTINUATION,
        "p_cache_hit":    P_CACHE_HIT,
        "tier2_rpm":      TIER2_RPM,
        "tier2_tpm":      TIER2_TPM,
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "note": (
            "greedy_approximation es un heuristico derivado de la estructura del MILP, "
            "no una solucion LP exacta."
        ),
    }
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "policies": results_by_policy}, f,
                  indent=2, ensure_ascii=False)
    print(f"\n[OK] JSON: {output_json}")

    # Escribir Markdown
    output_md = OUTPUT_DIR / "load_simulation_summary.md"
    _write_markdown({"meta": meta, "policies": results_by_policy}, output_md)
    print(f"[OK] Markdown: {output_md}")

    # Comparacion rapida: margen greedy vs static
    s_static = results_by_policy["static_baseline"]["summary"]
    s_greedy = results_by_policy["greedy_approximation"]["summary"]
    delta_margin = s_greedy["total_margin_usd"] - s_static["total_margin_usd"]
    delta_cost   = s_greedy["total_cost_usd"]   - s_static["total_cost_usd"]
    print("\n" + "=" * 60)
    print("Resultado comparativo:")
    sign_m = "+" if delta_margin >= 0 else ""
    sign_c = "+" if delta_cost   >= 0 else ""
    print(f"  Margen greedy vs static: {sign_m}${delta_margin:.4f}")
    print(f"  Costo  greedy vs static: {sign_c}${delta_cost:.4f}")
    if s_greedy["requests_r5_applied"] > 0:
        print(f"  R5 aplicado en {s_greedy['requests_r5_applied']:,} requests")
    print("=" * 60)

if __name__ == "__main__":
    main()
