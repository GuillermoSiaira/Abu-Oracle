"""Tests mínimos del solver MILP."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from demand_model import SyntheticAbuOracleDemandModel, SyntheticPaperclipDemandModel
from milp_solver import MILPInstance, CRITICAL_ROUTES, T_DOMAIN


def test_synthetic_demand_loads():
    d = SyntheticAbuOracleDemandModel()
    assert len(d.get_units()) == 9
    for u in d.get_units():
        assert d.get_frequency(u) > 0
        assert d.get_tokens_input(u) > 0


def test_paperclip_demand_loads():
    d = SyntheticPaperclipDemandModel(heartbeat_hours=1.0)
    assert len(d.get_units()) == 5
    for u in d.get_units():
        assert d.get_frequency(u) > 0


def test_abu_oracle_solves():
    d = SyntheticAbuOracleDemandModel()
    r = MILPInstance('abu_oracle', d, b_total=3000.0).solve()
    assert r.status == 'Optimal'


def test_paperclip_solves():
    d = SyntheticPaperclipDemandModel()
    r = MILPInstance('paperclip', d, b_interno=200.0).solve()
    assert r.status == 'Optimal'


def test_critical_routes_are_sonnet():
    d = SyntheticAbuOracleDemandModel()
    r = MILPInstance('abu_oracle', d).solve()
    for u in CRITICAL_ROUTES:
        if u in r.model_by_unit:
            assert r.model_by_unit[u] == 'sonnet', f"Ruta crítica {u} no es Sonnet"


def test_no_truncation():
    """max_tokens debe cubrir P99 para ε=0.01 en rutas críticas."""
    from scipy.stats import norm
    from milp_solver import EPS_CRITICAL
    d = SyntheticAbuOracleDemandModel()
    r = MILPInstance('abu_oracle', d).solve()
    for u in CRITICAL_ROUTES:
        if u not in r.max_tokens_by_unit:
            continue
        dist = d.get_output_dist(u)
        t_min = norm.ppf(1.0 - EPS_CRITICAL, dist['mean'], dist['std'])
        assert r.max_tokens_by_unit[u] >= t_min - 1, \
            f"{u}: max_tokens={r.max_tokens_by_unit[u]} < t_min={t_min:.0f}"


def test_shadow_prices_exist():
    d = SyntheticAbuOracleDemandModel()
    r = MILPInstance('abu_oracle', d).solve()
    sp = r.shadow_prices
    assert isinstance(sp, dict)
    # Supply constraint siempre existe (puede ser 0 si no binding)
    # Solo verificamos que se devuelve el dict sin error
