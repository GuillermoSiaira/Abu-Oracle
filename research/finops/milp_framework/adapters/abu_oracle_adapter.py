"""
Adaptador Abu Oracle — tres escenarios comparables:
  1. Sonnet everywhere  → costo X → precio mínimo $Y/mes
  2. MILP optimizado    → costo X' → precio mínimo $Y'/mes
  3. Diferencia cuantificada (el resultado publicable)
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import milp_solver as ms
from demand_model import EmpiricalAbuOracleDemandModel, SyntheticAbuOracleDemandModel
from milp_solver import MILPInstance


def _run_recommendations(
    demand,
    b_total: float = 3000.0,
    b_produccion: float | None = None,
) -> dict:
    # --- Escenario 1: Sonnet everywhere ---
    orig_critical  = frozenset(ms.CRITICAL_ROUTES)
    orig_secondary = frozenset(ms.SECONDARY_ROUTES)
    try:
        ms.CRITICAL_ROUTES  = set(orig_critical | orig_secondary)
        ms.SECONDARY_ROUTES = set()
        result_sonnet = MILPInstance('abu_oracle', demand, b_total=b_total, b_produccion=b_produccion).solve()
    finally:
        ms.CRITICAL_ROUTES  = set(orig_critical)
        ms.SECONDARY_ROUTES = set(orig_secondary)

    # --- Escenario 2: MILP libre (críticas=Sonnet, secundarias=decide) ---
    result_milp = MILPInstance('abu_oracle', demand, b_total=b_total, b_produccion=b_produccion).solve()

    def _fmt_routes(result) -> dict:
        return {
            u: {
                'model':       result.model_by_unit[u],
                'max_tokens':  result.max_tokens_by_unit[u],
                'is_critical': u in orig_critical,
            }
            for u in result.model_by_unit
        }

    # Diferencia de precio mínimo entre escenarios
    pricing_comparison = {}
    for plan in result_milp.pricing:
        s1 = result_sonnet.pricing[plan]
        s2 = result_milp.pricing[plan]
        key = 'min_sustainable'
        pricing_comparison[plan] = {
            'current':               s1['current'],
            'sonnet_everywhere_min': s1[key],
            'milp_optimized_min':    s2[key],
            'saving_per_user':       round(s1[key] - s2[key], 2),
        }

    return {
        'scenario_sonnet_everywhere': {
            'routes':             _fmt_routes(result_sonnet),
            'pricing':            result_sonnet.pricing,
            'total_cost_monthly': result_sonnet.total_cost_monthly,
            'status':             result_sonnet.status,
        },
        'scenario_milp_optimized': {
            'routes':             _fmt_routes(result_milp),
            'pricing':            result_milp.pricing,
            'total_cost_monthly': result_milp.total_cost_monthly,
            'status':             result_milp.status,
            'shadow_prices':      result_milp.shadow_prices,
        },
        'pricing_comparison':  pricing_comparison,
        'data_source':         demand.get_source(),
        'generated_at':        result_milp.generated_at,
    }


def get_recommendations(
    b_total: float = 3000.0,
    b_produccion: float | None = None,
) -> dict:
    return _run_recommendations(
        SyntheticAbuOracleDemandModel(),
        b_total=b_total,
        b_produccion=b_produccion,
    )


def get_recommendations_empirical(
    b_total: float = 3000.0,
    b_produccion: float | None = None,
) -> dict:
    """Igual que get_recommendations() pero con datos empiricos Fase A-2b."""
    return _run_recommendations(
        EmpiricalAbuOracleDemandModel(),
        b_total=b_total,
        b_produccion=b_produccion,
    )


def get_config_json(
    b_total: float = 3000.0,
    b_produccion: float | None = None,
    use_empirical: bool = False,
) -> dict:
    """
    Produce el JSON ejecutable para el dashboard de Fase 5.
    Ambos escenarios en un solo dict — el dashboard togglea sin recalcular.
    """
    get_rec = get_recommendations_empirical if use_empirical else get_recommendations
    rec = get_rec(b_total=b_total, b_produccion=b_produccion)

    def _fmt_scenario(key: str) -> dict:
        s = rec[key]
        # Reformatear pricing: min_sustainable → min_viable + margin_pct
        pricing_out = {}
        for plan, p in s['pricing'].items():
            cur  = p['current']
            minv = p.get('min_sustainable', p.get('min_viable', 0.0))
            margin_pct = round((cur / minv - 1) * 100) if minv > 0 else None
            pricing_out[plan] = {
                'min_viable':  round(minv, 2),
                'current':     cur,
                'margin_pct':  margin_pct,
            }
        return {
            'routes':        s['routes'],
            'cost_monthly':  s['total_cost_monthly'],
            'pricing':       pricing_out,
        }

    return {
        'scenarios': {
            'sonnet_everywhere': _fmt_scenario('scenario_sonnet_everywhere'),
            'milp_optimized':    _fmt_scenario('scenario_milp_optimized'),
        },
        'active_scenario': 'sonnet_everywhere',
        'generated_at':    rec['generated_at'],
        'data_source':     rec['data_source'],
    }
