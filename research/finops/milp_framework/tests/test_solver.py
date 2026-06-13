"""Tests del solver MILP."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from demand_model import EmpiricalAbuOracleDemandModel, SyntheticAbuOracleDemandModel, SyntheticPaperclipDemandModel
from milp_solver import MILPInstance, CRITICAL_ROUTES, T_DOMAIN


# ---------------------------------------------------------------------------
# Helper compartido — evita repetir la construcción del solver en cada test
# ---------------------------------------------------------------------------
def solve_paperclip():
    from adapters.paperclip_adapter import get_agent_config
    return get_agent_config()


def test_synthetic_demand_loads():
    d = SyntheticAbuOracleDemandModel()
    assert len(d.get_units()) == 9
    for u in d.get_units():
        assert d.get_frequency(u) > 0
        assert d.get_tokens_input(u) > 0


def test_empirical_demand_loads():
    d = EmpiricalAbuOracleDemandModel()
    assert d.get_source() == 'empirical-A2b'
    assert len(d.get_units()) == 9
    for u in d.get_units():
        dist = d.get_output_dist(u)
        assert dist['mean'] > 0
        assert dist['std'] > 0
        assert dist['p99'] >= dist['mean']


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


def test_paperclip_quality_via_adapter():
    """CEO, investigador y redactor deben ser Sonnet — verificado via adaptador."""
    from adapters.paperclip_adapter import get_agent_config
    cfg = get_agent_config()
    for agent in ['ceo', 'investigador', 'redactor']:
        assert cfg['agents'][agent]['model'] == 'sonnet', \
            f"{agent} debería ser sonnet (quality constraint)"
        assert cfg['agents'][agent]['forced'] is True, \
            f"{agent} debería tener forced=True"
    for agent in ['revisor', 'rutinario']:
        assert cfg['agents'][agent]['forced'] is False, \
            f"{agent} debería tener forced=False (libre)"


def test_output_config_produces_files():
    """--output-config genera JSON válido y parseable para ambas instancias."""
    import subprocess, json
    framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        [sys.executable, 'run_milp.py', '--instance', 'both', '--output-config'],
        capture_output=True, text=True, cwd=framework_dir,
    )
    assert result.returncode == 0, f"CLI falló: {result.stderr}"

    for fname, required_keys in [
        ('output/abu_oracle_config.json', ['scenarios', 'active_scenario', 'generated_at', 'data_source']),
        ('output/paperclip_config.json',  ['agents', 'heartbeat_hours', 'b_interno_used', 'b_interno_limit']),
    ]:
        path = os.path.join(framework_dir, fname)
        assert os.path.exists(path), f"Archivo no generado: {fname}"
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        assert isinstance(data, dict), f"{fname} no es un dict"
        for k in required_keys:
            assert k in data, f"Clave '{k}' faltante en {fname}"

    # Verificar estructura interna de abu_oracle_config
    path = os.path.join(framework_dir, 'output/abu_oracle_config.json')
    with open(path, encoding='utf-8') as f:
        abu = json.load(f)
    assert 'sonnet_everywhere' in abu['scenarios']
    assert 'milp_optimized'    in abu['scenarios']
    for scenario in abu['scenarios'].values():
        assert 'routes' in scenario
        assert 'cost_monthly' in scenario
        assert 'pricing' in scenario


# ---------------------------------------------------------------------------
# Ajuste 3 — tests quality constraints, bin tiebreak y output config
# ---------------------------------------------------------------------------

def test_paperclip_quality_constraints():
    """CEO, investigador y redactor deben ser Sonnet por quality constraints."""
    result = solve_paperclip()
    for agent in ['ceo', 'investigador', 'redactor']:
        assert result['agents'][agent]['model'] == 'sonnet'
        assert result['agents'][agent]['forced'] == True


def test_paperclip_free_agents_haiku():
    """Revisor y rutinario deben ser Haiku — MILP decide libremente."""
    result = solve_paperclip()
    for agent in ['revisor', 'rutinario']:
        assert result['agents'][agent]['model'] == 'haiku'
        assert result['agents'][agent]['forced'] == False


def test_bin_tiebreak_minimum():
    """Con bins de costo idéntico, el solver debe elegir el bin mínimo válido."""
    result = solve_paperclip()
    assert result['agents']['revisor']['max_tokens'] == 1024
    assert result['agents']['rutinario']['max_tokens'] == 512


def test_output_config_produces_valid_json():
    """--output-config genera JSON parseable para ambas instancias."""
    import json, subprocess
    framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for instance in ['abu_oracle', 'paperclip']:
        proc = subprocess.run(
            [sys.executable, 'run_milp.py', '--instance', instance, '--output-config'],
            capture_output=True, text=True, cwd=framework_dir,
        )
        assert proc.returncode == 0, f"CLI falló ({instance}): {proc.stderr}"
    abu = json.loads(open(os.path.join(framework_dir, 'output/abu_oracle_config.json'), encoding='utf-8').read())
    pc  = json.loads(open(os.path.join(framework_dir, 'output/paperclip_config.json'),  encoding='utf-8').read())
    assert 'scenarios' in abu
    assert 'agents'    in pc


def test_abu_oracle_both_scenarios_present():
    """JSON de Abu Oracle debe contener ambos escenarios."""
    import json
    framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = json.loads(open(os.path.join(framework_dir, 'output/abu_oracle_config.json'), encoding='utf-8').read())
    assert 'sonnet_everywhere' in config['scenarios']
    assert 'milp_optimized'    in config['scenarios']
    assert config['active_scenario'] == 'sonnet_everywhere'
