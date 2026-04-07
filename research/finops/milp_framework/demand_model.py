"""
Capa 1 — Modelos de demanda (intercambiables).
Todos implementan DemandModel. El solver no sabe qué modelo usa.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from scipy.stats import norm


class DemandModel(ABC):
    @abstractmethod
    def get_units(self) -> list[str]: ...
    @abstractmethod
    def get_frequency(self, unit: str) -> float: ...
    @abstractmethod
    def get_tokens_input(self, unit: str) -> float: ...
    @abstractmethod
    def get_output_dist(self, unit: str) -> dict:
        """{'mean': float, 'std': float, 'p99': float}"""
    @abstractmethod
    def get_source(self) -> str: ...

    # Helper compartido: cota inferior de t_u para P(trunc) ≤ ε
    def min_tokens_for_epsilon(self, unit: str, epsilon: float) -> float:
        d = self.get_output_dist(unit)
        return norm.ppf(1.0 - epsilon, loc=d['mean'], scale=d['std'])


# ---------------------------------------------------------------------------
# Instancia A — Abu Oracle (sintético)
# ---------------------------------------------------------------------------

_ROUTE_FREQ = {
    'screen-open': 0.10,
    'planet':      0.15,
    'technique':   0.10,
    'transit':     0.20,
    'domain':      0.15,
    'house':       0.10,
    'city':        0.05,
    'sky':         0.05,
    'chat':        0.10,
}

_TOKENS_INPUT = {
    'screen-open': 4200,
    'planet':      3800,
    'technique':   4500,
    'transit':     4100,
    'domain':      4000,
    'house':       3900,
    'city':        3600,
    'sky':         4300,
    'chat':        5000,
}

_OUTPUT_DIST: dict[str, dict] = {
    'screen-open': {'mean': 960,  'std': 39,  'p99': 1536},
    'transit':     {'mean': 800,  'std': 150, 'p99': 1200},
    'chat':        {'mean': 1200, 'std': 300, 'p99': 2000},
}
_DEFAULT_OUTPUT = {'mean': 700, 'std': 150, 'p99': 1100}

_SESSIONS_PER_MONTH = {'genesis': 40, 'annual': 20, 'monthly': 8}
_N_USERS            = {'genesis': 100, 'annual': 50, 'monthly': 200}


class SyntheticAbuOracleDemandModel(DemandModel):
    """
    Demanda sintética para Abu Oracle.
    freq(u) = Σ_k  session_freq(u) × sessions_per_month(k) × N_users(k)
    """

    def get_units(self) -> list[str]:
        return list(_ROUTE_FREQ.keys())

    def get_frequency(self, unit: str) -> float:
        route_share = _ROUTE_FREQ[unit]
        total = sum(
            route_share * _SESSIONS_PER_MONTH[k] * _N_USERS[k]
            for k in _SESSIONS_PER_MONTH
        )
        return total

    def get_tokens_input(self, unit: str) -> float:
        return _TOKENS_INPUT[unit]

    def get_output_dist(self, unit: str) -> dict:
        return _OUTPUT_DIST.get(unit, _DEFAULT_OUTPUT)

    def get_source(self) -> str:
        return 'synthetic'

    # Utilidades específicas de pricing
    def plans(self) -> list[str]:
        return list(_SESSIONS_PER_MONTH.keys())

    def n_users(self, plan: str) -> int:
        return _N_USERS[plan]

    def sessions_per_month(self, plan: str) -> int:
        return _SESSIONS_PER_MONTH[plan]


# ---------------------------------------------------------------------------
# Instancia B — Paperclip (sintético)
# ---------------------------------------------------------------------------

_HEARTBEAT_HOURS = 1.0

_AGENTS_PER_CYCLE = {
    'ceo':          1,
    'investigador': 2,
    'redactor':     1,
    'revisor':      2,
    'rutinario':    3,
}

_TOKENS_PER_TASK = {
    'ceo':          {'input': 6000, 'mean': 2000, 'std': 500},
    'investigador': {'input': 8000, 'mean': 3000, 'std': 800},
    'redactor':     {'input': 5000, 'mean': 4000, 'std': 1000},
    'revisor':      {'input': 4000, 'mean': 500,  'std': 100},
    'rutinario':    {'input': 2000, 'mean': 300,  'std': 50},
}


class SyntheticPaperclipDemandModel(DemandModel):
    """
    Demanda sintética para Paperclip.
    freq(agente) = ciclos_por_mes × agentes_por_ciclo
    """

    def __init__(self, heartbeat_hours: float = _HEARTBEAT_HOURS):
        self.heartbeat_hours = heartbeat_hours
        self._cycles_per_month = (24 / heartbeat_hours) * 30

    def get_units(self) -> list[str]:
        return list(_AGENTS_PER_CYCLE.keys())

    def get_frequency(self, unit: str) -> float:
        return self._cycles_per_month * _AGENTS_PER_CYCLE[unit]

    def get_tokens_input(self, unit: str) -> float:
        return _TOKENS_PER_TASK[unit]['input']

    def get_output_dist(self, unit: str) -> dict:
        t = _TOKENS_PER_TASK[unit]
        mean = t['mean']
        std  = t['std']
        p99  = mean + 2.326 * std
        return {'mean': mean, 'std': std, 'p99': p99}

    def get_source(self) -> str:
        return 'synthetic'
