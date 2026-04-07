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
from demand_model import SyntheticAbuOracleDemandModel
from milp_solver import MILPInstance, CRITICAL_ROUTES, SECONDARY_ROUTES


def get_recommendations(
    b_total: float = 3000.0,
    b_produccion: float | None = None,
) -> dict:
    demand = SyntheticAbuOracleDemandModel()

    # --- Escenario 1: Sonnet everywhere ---
    orig_critical  = frozenset(ms.CRITICAL_ROUTES)
    orig_secondary = frozenset(ms.SECONDARY_ROUTES)
    ms.CRITICAL_ROUTES  = orig_critical | orig_secondary
    ms.SECONDARY_ROUTES = set()
    result_sonnet = MILPInstance('abu_oracle', demand, b_total=b_total, b_produccion=b_produccion).solve()
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
