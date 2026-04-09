# Prompt para CC — MILP Framework Fase 1

> Leer FINOPS_MILP_FRAMEWORK.md completo antes de empezar.
> Este es trabajo standalone en research/finops/milp_framework/.
> NO tocar selectModel.ts ni ningún archivo de producción.
> Workflow: diagnóstico → estructura → implementar capa por capa
> → test → reporte. Una capa a la vez, confirmación entre capas.

---

## Contexto

Estamos implementando la Fase 1 del framework MILP genérico para
optimización de recursos en organizaciones de agentes LLM.

El framework tiene dos instancias:
- Instancia A: Abu Oracle (pricing por plan, Sonnet everywhere)
- Instancia B: Paperclip (modelo por agente, presupuesto interno)

En Fase 1 todo corre sobre datos sintéticos. No hay integración
con producción. El objetivo es tener el solver funcionando y
produciendo output legible para ambas instancias.

---

## Prerequisitos

Verificar que PuLP esté instalado:
```bash
cd research/finops/milp_framework  # crear si no existe
pip show pulp
# si no está: pip install pulp
```

---

## Estructura de archivos a crear

```
research/finops/milp_framework/
├── demand_model.py       # Capa 1 — modelos de demanda
├── milp_solver.py        # Capa 2 — solver MILP
├── adapters/
│   ├── __init__.py
│   ├── abu_oracle_adapter.py
│   └── paperclip_adapter.py
├── config/
│   ├── abu_oracle_config.py
│   └── paperclip_config.py
├── run_milp.py           # CLI principal
└── tests/
    └── test_solver.py
```

Mostrar la estructura antes de crear cualquier archivo.
Esperar confirmación.

---

## CAPA 1 — demand_model.py

Implementar tres clases con interfaz común:

```python
class DemandModel(ABC):
    @abstractmethod
    def get_units(self) -> list[str]:
        """Retorna lista de unidades (rutas o agentes)"""

    @abstractmethod
    def get_frequency(self, unit: str) -> float:
        """Frecuencia mensual de ejecución de la unidad"""

    @abstractmethod
    def get_tokens_input_dist(self, unit: str) -> dict:
        """{'mean': float, 'p99': float}"""

    @abstractmethod
    def get_tokens_output_dist(self, unit: str) -> dict:
        """{'mean': float, 'std': float, 'p99': float}"""

    @abstractmethod
    def get_source(self) -> str:
        """'synthetic' | 'logs' | 'paperclip_logs'"""
```

### SyntheticDemandModel (instancia Abu Oracle)

Usar exactamente estos valores del FINOPS_MILP_FRAMEWORK.md:

```python
ROUTE_FREQ = {
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

TOKENS_INPUT = {
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

OUTPUT_DIST = {
    'screen-open': {'mean': 960,  'std': 39,  'p99': 1536},
    'transit':     {'mean': 800,  'std': 150, 'p99': 1200},
    'chat':        {'mean': 1200, 'std': 300, 'p99': 2000},
    # resto: estimar como mean=700, std=150, p99=1100
}

SESSIONS_PER_MONTH = {
    'genesis': 40,
    'annual':  20,
    'monthly': 8,
}

N_USERS = {
    'genesis': 100,   # 100 slots Genesis
    'annual':  50,    # estimado
    'monthly': 200,   # estimado
}
```

### SyntheticPaperclipDemandModel

```python
AGENTS = ['ceo', 'investigador', 'redactor', 'revisor', 'rutinario']

HEARTBEAT_HOURS = 1.0  # configurable

AGENTS_PER_CYCLE = {
    'ceo':          1,
    'investigador': 2,
    'redactor':     1,
    'revisor':      2,
    'rutinario':    3,
}

TOKENS_PER_TASK = {
    'ceo':          {'input': 6000, 'output_mean': 2000, 'output_std': 500},
    'investigador': {'input': 8000, 'output_mean': 3000, 'output_std': 800},
    'redactor':     {'input': 5000, 'output_mean': 4000, 'output_std': 1000},
    'revisor':      {'input': 4000, 'output_mean': 500,  'output_std': 100},
    'rutinario':    {'input': 2000, 'output_mean': 300,  'output_std': 50},
}

# frecuencia = ciclos/mes × agentes_por_ciclo
# ciclos/mes = (24/heartbeat_hours) × 30
```

Mostrar implementación completa de demand_model.py.
Esperar confirmación antes de continuar con Capa 2.

---

## CAPA 2 — milp_solver.py

### Precios de modelos (Anthropic, abril 2026)

```python
MODEL_COSTS = {
    'sonnet': {
        'input':       3.00 / 1_000_000,
        'cache_write': 3.75 / 1_000_000,
        'cache_read':  0.30 / 1_000_000,
        'output':     15.00 / 1_000_000,
    },
    'haiku': {
        'input':       0.80 / 1_000_000,
        'cache_write': 1.00 / 1_000_000,
        'cache_read':  0.08 / 1_000_000,
        'output':       4.00 / 1_000_000,
    },
}
```

### Clase MILPInstance

```python
class MILPInstance:
    def __init__(
        self,
        instance_type: str,          # 'abu_oracle' | 'paperclip'
        demand_model: DemandModel,
        config: dict,
    ):
        ...

    def solve(self) -> MILPResult:
        """
        Retorna:
          - modelo asignado por unidad
          - max_tokens por unidad
          - precios por plan (solo abu_oracle)
          - costo total mensual estimado
          - shadow_prices de constraints activas
          - status: 'optimal' | 'infeasible' | 'unbounded'
        """

    def shadow_prices(self) -> dict:
        """
        Shadow prices de constraints binding:
          - supply_constraint: costo marginal de un token adicional
          - margin_constraints: por plan
          - quality_constraints: por unidad
        """
```

### Constraints a implementar

**Todas las instancias:**
```
Supply: Σ_u κ(u) · freq(u) ≤ B_disponible
No truncación: P(trunc | t_u) ≤ ε_u
  donde P(trunc) = 1 - CDF_Normal(t_u, mean_output, std_output)
```

**Solo Abu Oracle:**
```
Calidad doctrinal: x_u = Sonnet para todas las rutas
Floor de precio: p_k ≥ cost_k + margin_minimo_k
```

**Solo Paperclip:**
```
B_interno ≤ B_total - B_produccion - margen_seguridad
Heartbeat: cycles_per_month ≤ B_interno / cost_per_cycle
```

### Función de costo por unidad (con reintento)

```python
def unit_cost(unit, model, max_tokens, demand):
    p_trunc = 1 - norm.cdf(max_tokens,
                            demand.output_mean(unit),
                            demand.output_std(unit))
    base_cost = (MODEL_COSTS[model]['input'] * demand.tokens_input(unit) +
                 MODEL_COSTS[model]['output'] * min(demand.output_mean(unit), max_tokens))
    # costo de reintento: p_trunc × 2 × base_cost
    return base_cost * (1 + p_trunc)
```

Mostrar milp_solver.py completo.
Esperar confirmación antes de continuar.

---

## CAPA 3 — Adaptadores

### abu_oracle_adapter.py

Output: tabla de recomendaciones por ruta + precios óptimos por plan.

```python
def get_recommendations() -> dict:
    return {
        'routes': {
            'transit': {'model': 'sonnet', 'max_tokens': 1024},
            ...
        },
        'pricing': {
            'monthly': {'current': 5.00, 'optimal': X.XX, 'gap': Y.YY},
            'annual':  {...},
            'genesis': {...},
        },
        'total_cost_monthly': float,
        'shadow_prices': {...},
        'data_source': 'synthetic',
        'generated_at': timestamp,
    }
```

### paperclip_adapter.py

Output: tabla de modelo/max_tokens por agente + señal de heartbeat.

```python
def get_agent_config() -> dict:
    return {
        'agents': {
            'ceo':          {'model': 'sonnet', 'max_tokens': 2000},
            'investigador': {'model': 'sonnet', 'max_tokens': 3000},
            'redactor':     {'model': 'sonnet', 'max_tokens': 4000},
            'revisor':      {'model': 'haiku',  'max_tokens': 1024},
            'rutinario':    {'model': 'haiku',  'max_tokens': 512},
        },
        'heartbeat_recommended_hours': float,
        'b_interno_monthly': float,
        'congestion_signal': bool,
        'data_source': 'synthetic',
        'generated_at': timestamp,
    }
```

---

## CLI — run_milp.py

```bash
# Instancia Abu Oracle
python run_milp.py --instance abu_oracle --n-users 100 --b-total 3000

# Instancia Paperclip
python run_milp.py --instance paperclip --heartbeat 1.0 --b-interno 200

# Ambas con presupuesto compartido
python run_milp.py --instance both --b-total 3000 --b-produccion 2800

# Output en JSON
python run_milp.py --instance abu_oracle --output json > milp_output.json
```

El output en consola debe ser legible como el ejemplo en
FINOPS_MILP_FRAMEWORK.md § "Output esperado de Fase 1".

---

## Tests mínimos

En `tests/test_solver.py`:

1. `test_synthetic_demand_loads` — SyntheticDemandModel instancia sin error
2. `test_abu_oracle_solves` — solve() retorna status 'optimal'
3. `test_paperclip_solves` — ídem
4. `test_sonnet_constraint` — todas las rutas Abu Oracle tienen model='sonnet'
5. `test_no_truncation` — max_tokens ≥ p99 output para ε=0.01
6. `test_shadow_prices_exist` — shadow_prices() retorna dict no vacío

```bash
python -m pytest tests/ -v
```

Todos deben pasar antes del commit.

---

## Commit

```bash
git add research/finops/milp_framework/
git commit -m "feat(finops): MILP framework Fase 1 — solver genérico con datos sintéticos

Implementación standalone en research/finops/milp_framework/.
Dos instancias: abu_oracle (pricing) y paperclip (eficiencia interna).
Tres capas desacopladas: DemandModel → MILPSolver → Adapters.
Datos sintéticos como placeholder — reemplazables con logs reales.
No toca producción.

Ver FINOPS_MILP_FRAMEWORK.md para arquitectura completa."
```

---

## Al terminar

Reportar:
1. Hash del commit
2. Output de `python run_milp.py --instance both --b-total 3000`
3. Output de `python -m pytest tests/ -v`
4. Cualquier decisión de diseño que hayas tomado distinta a la spec
   (no asumir — reportar y esperar instrucción)
