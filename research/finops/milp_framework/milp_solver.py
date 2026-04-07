"""
Capa 2 — Solver MILP genérico.
Resuelve dos instancias configurables: 'abu_oracle' y 'paperclip'.

Reformulaciones clave para linealidad (PuLP/CBC):
  1. t_u discretizado en T_DOMAIN = [512, 1024, 1536, 2048, 2500]
     → z_{u,j} ∈ {0,1}: 1 si t_u = T_DOMAIN[j]
     → t_u = Σ_j z_{u,j} · T_DOMAIN[j]  con  Σ_j z_{u,j} = 1
  2. Constraint de no-truncación: t_u ≥ norm.ppf(1-ε, μ, σ)
     → equivale a seleccionar el bin j tal que T_DOMAIN[j] ≥ ppf.
  3. Costo de reintento aproximado: base_cost × (1 + ε_u)
     donde ε_u es el ε del constraint (cota superior de p_trunc).
  4. x_u ∈ {0=haiku, 1=sonnet} variable binaria.
     Abu Oracle: rutas críticas → x_u = 1 forzado.
                 rutas secundarias → MILP decide.
     Paperclip: sin restricción de modelo → MILP decide libremente.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from scipy.stats import norm

import pulp

from demand_model import DemandModel


# ---------------------------------------------------------------------------
# Precios Anthropic (abril 2026, USD por token)
# ---------------------------------------------------------------------------
MODEL_COSTS = {
    'sonnet': {'input': 3.00 / 1_000_000, 'output': 15.00 / 1_000_000},
    'haiku':  {'input': 0.80 / 1_000_000, 'output':  4.00 / 1_000_000},
}

T_DOMAIN = [512, 1024, 1536, 2048, 2500]

# Rutas Abu Oracle clasificadas por criticidad doctrinal
CRITICAL_ROUTES = {
    'screen-open', 'planet', 'transit', 'domain', 'house', 'sky', 'chat'
}
SECONDARY_ROUTES = {
    'technique', 'city'
}

# ε por posición en la cadena
EPS_CRITICAL  = 0.01   # cadena intermedia — máx 1% truncación
EPS_SECONDARY = 0.05   # terminal / bajo riesgo

# Precios actuales por plan (USD/mes)
CURRENT_PRICES = {'monthly': 5.00, 'annual': 45.00 / 12, 'genesis': 0.0}

# Margen mínimo absoluto por plan (USD/mes/usuario)
MARGIN_FLOOR   = {'monthly': 0.50, 'annual': 0.40, 'genesis': 0.0}

# Presupuesto interno Paperclip (USD/mes)
B_INTERNO_DEFAULT = 500.0


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------
@dataclass
class MILPResult:
    status: str                            # 'Optimal' | 'Infeasible' | ...
    instance_type: str
    model_by_unit: dict[str, str]          # unit → 'sonnet' | 'haiku'
    max_tokens_by_unit: dict[str, int]     # unit → t_u (valor del dominio)
    forced_by_unit: dict[str, bool]        # unit → True si modelo fue forzado
    pricing: dict[str, dict]               # solo abu_oracle
    total_cost_monthly: float
    b_interno: float                       # solo paperclip
    heartbeat_recommended_hours: float     # solo paperclip
    congestion_signal: bool
    shadow_prices: dict[str, float]
    data_source: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------
class MILPInstance:
    def __init__(
        self,
        instance_type: str,
        demand: DemandModel,
        b_total: float = 3000.0,
        b_produccion: float | None = None,
        b_interno: float = B_INTERNO_DEFAULT,
        heartbeat_hours: float = 1.0,
        quality_constraints: dict | None = None,
    ):
        assert instance_type in ('abu_oracle', 'paperclip')
        self.instance_type = instance_type
        self.demand = demand
        self.b_total = b_total
        self.b_produccion = b_produccion if b_produccion is not None else b_total * 0.93
        # Solo capeamos b_interno si se especificó b_produccion explícitamente (modo both)
        self.b_interno = min(b_interno, b_total - self.b_produccion - 50.0) \
            if b_produccion is not None else b_interno
        self.heartbeat_hours = heartbeat_hours
        self.quality_constraints = quality_constraints
        self._result: MILPResult | None = None

    # ------------------------------------------------------------------
    def solve(self) -> MILPResult:
        if self.instance_type == 'abu_oracle':
            self._result = self._solve_abu_oracle()
        else:
            self._result = self._solve_paperclip()
        return self._result

    def shadow_prices(self) -> dict[str, float]:
        if self._result is None:
            self.solve()
        return self._result.shadow_prices

    # ------------------------------------------------------------------
    # Helpers de costo (deterministas dado modelo y t_u bin j)
    # ------------------------------------------------------------------
    def _unit_cost(self, unit: str, model: str, t_val: int, epsilon: float) -> float:
        """Costo USD por ejecución, incluyendo reintento esperado."""
        d = self.demand.get_output_dist(unit)
        inp_cost = MODEL_COSTS[model]['input'] * self.demand.get_tokens_input(unit)
        out_tokens = min(d['mean'], t_val)
        out_cost = MODEL_COSTS[model]['output'] * out_tokens
        base = inp_cost + out_cost
        return base * (1.0 + epsilon)

    def _epsilon(self, unit: str) -> float:
        if self.instance_type == 'paperclip':
            return EPS_SECONDARY
        return EPS_CRITICAL if unit in CRITICAL_ROUTES else EPS_SECONDARY

    def _min_t(self, unit: str) -> int:
        """Bin mínimo de T_DOMAIN que satisface la constraint de truncación."""
        eps = self._epsilon(unit)
        t_min_cont = self.demand.min_tokens_for_epsilon(unit, eps)
        for t in T_DOMAIN:
            if t >= t_min_cont:
                return t
        return T_DOMAIN[-1]

    # ------------------------------------------------------------------
    # Instancia A — Abu Oracle
    # ------------------------------------------------------------------
    def _solve_abu_oracle(self) -> MILPResult:
        prob = pulp.LpProblem("AbuOracle_Pricing", pulp.LpMinimize)
        units = self.demand.get_units()         # type: ignore[attr-defined]
        plans = self.demand.plans()             # type: ignore[attr-defined]

        # Variables binarias: x[u] = 1 → Sonnet
        x = {u: pulp.LpVariable(f"x_{u}", cat='Binary') for u in units}

        # Variables de bin para t_u (one-hot sobre T_DOMAIN)
        z = {
            u: {j: pulp.LpVariable(f"z_{u}_{j}", cat='Binary')
                for j in range(len(T_DOMAIN))}
            for u in units
        }

        # ---- Constraint: one-hot z ----
        for u in units:
            prob += pulp.lpSum(z[u].values()) == 1

        # ---- Constraint: modelo forzado para rutas críticas ----
        for u in CRITICAL_ROUTES:
            if u in units:
                prob += x[u] == 1

        # ---- Constraint: no-truncación (bin mínimo por ε) ----
        for u in units:
            j_min = next(j for j, t in enumerate(T_DOMAIN) if t >= self._min_t(u))
            for j in range(j_min):
                prob += z[u][j] == 0

        # ---- Linealización de x[u] · z[u][j] (bilineal → MIP lineal) ----
        # Pre-computamos costo para cada (unit, model, bin) → constante
        cost_mat: dict[tuple, float] = {}
        for u in units:
            eps = self._epsilon(u)
            for m_idx, model in enumerate(['haiku', 'sonnet']):
                for j, t in enumerate(T_DOMAIN):
                    cost_mat[(u, m_idx, j)] = self._unit_cost(u, model, t, eps)

        # w[u][m_idx][j] = indicator(modelo=m_idx) · z[u][j]
        w = {
            u: {
                m_idx: {
                    j: pulp.LpVariable(f"w_{u}_{m_idx}_{j}", lowBound=0, upBound=1, cat='Continuous')
                    for j in range(len(T_DOMAIN))
                }
                for m_idx in range(2)
            }
            for u in units
        }

        for u in units:
            for j in range(len(T_DOMAIN)):
                # w[u][1][j] = x[u] · z[u][j]  (sonnet)
                prob += w[u][1][j] <= x[u]
                prob += w[u][1][j] <= z[u][j]
                prob += w[u][1][j] >= x[u] + z[u][j] - 1
                # w[u][0][j] = (1-x[u]) · z[u][j]  (haiku)
                prob += w[u][0][j] <= 1 - x[u]
                prob += w[u][0][j] <= z[u][j]
                prob += w[u][0][j] >= z[u][j] - x[u]

        # Costo mensual total (USD)
        cost_total = pulp.lpSum(
            cost_mat[(u, m_idx, j)] * self.demand.get_frequency(u) * w[u][m_idx][j]
            for u in units for m_idx in range(2) for j in range(len(T_DOMAIN))
        )

        # ---- Supply constraint ----
        prob += cost_total <= self.b_produccion, "supply"

        # ---- Objetivo: minimizar costo total mensual ----
        # Precio mínimo sostenible se deriva post-hoc:
        #   cost_per_session = total_cost / total_sessions
        #   min_price_k = cost_per_session × sessions_per_month_k + MARGIN_FLOOR_k
        prob += cost_total

        status = prob.solve(pulp.PULP_CBC_CMD(msg=0))

        # ---- Extraer solución ----
        model_by_unit, max_tokens_by_unit = {}, {}
        for u in units:
            model_by_unit[u] = 'sonnet' if round(pulp.value(x[u]) or 0) == 1 else 'haiku'
            for j, t in enumerate(T_DOMAIN):
                if round(pulp.value(z[u][j]) or 0) == 1:
                    max_tokens_by_unit[u] = t
                    break
            else:
                max_tokens_by_unit[u] = T_DOMAIN[-1]

        total_cost = pulp.value(cost_total) or 0.0

        # Precio mínimo sostenible por plan (derivado del costo óptimo)
        total_sessions = sum(
            self.demand.sessions_per_month(k) * self.demand.n_users(k)  # type: ignore[attr-defined]
            for k in plans
        )
        cost_per_session = total_cost / max(total_sessions, 1)

        pricing = {}
        for k in plans:
            if k == 'genesis':
                pricing[k] = {'current': CURRENT_PRICES[k], 'min_sustainable': 0.0, 'gap': 0.0}
            else:
                spm = self.demand.sessions_per_month(k)  # type: ignore[attr-defined]
                cost_user_k = cost_per_session * spm
                min_price = cost_user_k + MARGIN_FLOOR[k]
                cur = CURRENT_PRICES[k]
                pricing[k] = {
                    'current':         round(cur, 2),
                    'min_sustainable': round(min_price, 2),
                    'gap':             round(min_price - cur, 2),  # + = precio actual insuficiente
                }

        # Solo constraints con nombre explícito (no los auto-generados _C*)
        shadow = {}
        for name, c in prob.constraints.items():
            if not name.startswith('_') and c.pi is not None and abs(c.pi) > 1e-9:
                shadow[name] = round(c.pi, 6)

        forced_by_unit = {u: (u in CRITICAL_ROUTES) for u in units}

        return MILPResult(
            status=pulp.LpStatus[status],
            instance_type='abu_oracle',
            model_by_unit=model_by_unit,
            max_tokens_by_unit=max_tokens_by_unit,
            forced_by_unit=forced_by_unit,
            pricing=pricing,
            total_cost_monthly=round(total_cost, 2),
            b_interno=0.0,
            heartbeat_recommended_hours=0.0,
            congestion_signal=False,
            shadow_prices=shadow,
            data_source=self.demand.get_source(),
        )

    # ------------------------------------------------------------------
    # Instancia B — Paperclip
    # ------------------------------------------------------------------
    def _solve_paperclip(self) -> MILPResult:
        prob = pulp.LpProblem("Paperclip_Efficiency", pulp.LpMinimize)
        units = self.demand.get_units()

        x = {u: pulp.LpVariable(f"x_{u}", cat='Binary') for u in units}
        z = {
            u: {j: pulp.LpVariable(f"z_{u}_{j}", cat='Binary')
                for j in range(len(T_DOMAIN))}
            for u in units
        }

        # One-hot
        for u in units:
            prob += pulp.lpSum(z[u].values()) == 1

        # ---- Constraints de calidad (config override o paperclip_config.py) ----
        from config.paperclip_config import QUALITY_CONSTRAINTS as _DEFAULT_QC
        qc = self.quality_constraints or _DEFAULT_QC
        for u in units:
            forced = qc.get(u)
            if forced == 'sonnet':   prob += x[u] == 1, f"quality_{u}"
            elif forced == 'haiku':  prob += x[u] == 0, f"quality_{u}"

        # No-truncación
        for u in units:
            j_min = next(j for j, t in enumerate(T_DOMAIN) if t >= self._min_t(u))
            for j in range(j_min):
                prob += z[u][j] == 0

        # Pre-calcular costos
        cost_mat = {}
        for u in units:
            eps = self._epsilon(u)
            for m_idx, model in enumerate(['haiku', 'sonnet']):
                for j, t in enumerate(T_DOMAIN):
                    cost_mat[(u, m_idx, j)] = self._unit_cost(u, model, t, eps)

        # Variables auxiliares w (bilineal → lineal)
        w = {
            u: {
                m_idx: {
                    j: pulp.LpVariable(f"w_{u}_{m_idx}_{j}", lowBound=0, upBound=1)
                    for j in range(len(T_DOMAIN))
                }
                for m_idx in range(2)
            }
            for u in units
        }

        for u in units:
            for j in range(len(T_DOMAIN)):
                prob += w[u][1][j] <= x[u]
                prob += w[u][1][j] <= z[u][j]
                prob += w[u][1][j] >= x[u] + z[u][j] - 1
                prob += w[u][0][j] <= 1 - x[u]
                prob += w[u][0][j] <= z[u][j]
                prob += w[u][0][j] >= z[u][j] - x[u]

        cost_total = pulp.lpSum(
            cost_mat[(u, m_idx, j)] * self.demand.get_frequency(u) * w[u][m_idx][j]
            for u in units for m_idx in range(2) for j in range(len(T_DOMAIN))
        )

        # Supply: B_interno disponible
        prob += cost_total <= self.b_interno, "supply_interno"

        # Regularización: rompe empates en favor del bin mínimo válido.
        # λ << costo_unitario_mínimo (~$0.002) — no altera decisiones costo-óptimas.
        # Sin esto, CBC elige arbitrariamente entre bins de costo idéntico.
        _lambda = 1e-5
        t_reg = pulp.lpSum(
            T_DOMAIN[j] * z[u][j]
            for u in units for j in range(len(T_DOMAIN))
        )

        # Objetivo: minimizar costo + regularización de bins
        prob += cost_total + _lambda * t_reg

        status = prob.solve(pulp.PULP_CBC_CMD(msg=0))

        model_by_unit, max_tokens_by_unit = {}, {}
        for u in units:
            model_by_unit[u] = 'sonnet' if round(pulp.value(x[u]) or 0) == 1 else 'haiku'
            for j, t in enumerate(T_DOMAIN):
                if round(pulp.value(z[u][j]) or 0) == 1:
                    max_tokens_by_unit[u] = t
                    break
            else:
                max_tokens_by_unit[u] = T_DOMAIN[-1]

        total_cost = pulp.value(cost_total) or 0.0
        congestion = total_cost > self.b_interno * 0.9

        # Heartbeat recomendado: si congestionado, duplicar intervalo
        hrec = self.heartbeat_hours * (2.0 if congestion else 1.0)

        shadow = {}
        for name, c in prob.constraints.items():
            if not name.startswith('_') and c.pi is not None and abs(c.pi) > 1e-9:
                shadow[name] = round(c.pi, 6)

        forced_by_unit = {u: (qc.get(u) is not None) for u in units}

        return MILPResult(
            status=pulp.LpStatus[status],
            instance_type='paperclip',
            model_by_unit=model_by_unit,
            max_tokens_by_unit=max_tokens_by_unit,
            forced_by_unit=forced_by_unit,
            pricing={},
            total_cost_monthly=round(total_cost, 2),
            b_interno=self.b_interno,
            heartbeat_recommended_hours=hrec,
            congestion_signal=congestion,
            shadow_prices=shadow,
            data_source=self.demand.get_source(),
        )

