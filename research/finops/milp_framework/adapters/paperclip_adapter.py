"""
Adaptador Paperclip — produce config de agentes y señal de heartbeat.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from demand_model import SyntheticPaperclipDemandModel
from milp_solver import MILPInstance


def get_agent_config(
    b_interno: float = 200.0,
    heartbeat_hours: float = 1.0,
    b_total: float = 3000.0,
) -> dict:
    demand = SyntheticPaperclipDemandModel(heartbeat_hours=heartbeat_hours)
    instance = MILPInstance(
        'paperclip',
        demand,
        b_total=b_total,
        b_interno=b_interno,
        heartbeat_hours=heartbeat_hours,
    )
    result = instance.solve()

    agents = {
        u: {
            'model':      result.model_by_unit[u],
            'max_tokens': result.max_tokens_by_unit[u],
            'forced':     result.forced_by_unit.get(u, False),
        }
        for u in result.model_by_unit
    }

    return {
        'agents':                       agents,
        'heartbeat_recommended_hours':  result.heartbeat_recommended_hours,
        'b_interno_monthly':            result.total_cost_monthly,
        'b_interno_budget':             result.b_interno,
        'utilization_pct':              round(result.total_cost_monthly / max(result.b_interno, 1) * 100, 1),
        'congestion_signal':            result.congestion_signal,
        'status':                       result.status,
        'shadow_prices':                result.shadow_prices,
        'data_source':                  result.data_source,
        'generated_at':                 result.generated_at,
    }


def get_config_json(
    b_interno: float = 500.0,
    heartbeat_hours: float = 1.0,
    b_total: float = 3000.0,
) -> dict:
    """Produce el JSON ejecutable para Paperclip (formato spec Ajuste 2)."""
    cfg = get_agent_config(b_interno=b_interno, heartbeat_hours=heartbeat_hours, b_total=b_total)
    return {
        'generated_at':      cfg['generated_at'],
        'data_source':       cfg['data_source'],
        'agents':            cfg['agents'],
        'heartbeat_hours':   heartbeat_hours,
        'b_interno_used':    cfg['b_interno_monthly'],
        'b_interno_limit':   cfg['b_interno_budget'],
        'utilization_pct':   cfg['utilization_pct'],
        'congestion_signal': cfg['congestion_signal'],
    }
