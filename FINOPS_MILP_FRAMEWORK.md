# FINOPS_MILP_FRAMEWORK.md
> Creado: 2026-04-06
> Estado: diseño completo — implementación en fases, Fase 1 ejecutable ahora
> Referencias cruzadas: [[COST_OPTIMIZATION]] · [[finops_milp]] · [[FINOPS_MILP_VARIABLES]]

---

## Visión

El módulo FinOps MILP no es una herramienta de pricing para Abu Oracle.
Es un **framework genérico de optimización de recursos para organizaciones
de agentes LLM**, con dos instancias de uso inmediato:

```
MILP Framework (genérico)
├── Instancia A — Abu Oracle Production
│     Optimiza: precio al usuario
│     Variables: {p_genesis, p_monthly, p_annual}
│     Calidad: fija (Sonnet everywhere)
│     Demanda: usuarios reales post-launch
│
└── Instancia B — Paperclip Internal
      Optimiza: modelo y max_tokens por agente
      Variables: {modelo_agente, max_tokens_agente}
      Calidad: variable (Haiku para rutinario, Sonnet para estratégico)
      Demanda: agentes internos corriendo en VPS
```

Ambas instancias comparten el mismo solver (PuLP/CBC) y el mismo
esquema de presupuesto compartido bajo `B_total`.

---

## Arquitectura del presupuesto compartido

```
B_total  (presupuesto mensual Anthropic — conocido, fijo)
│
├── B_produccion  (usuarios reales de Abu Oracle)
│     Prioridad: ABSOLUTA
│     Gestionado por: Instancia A
│     Floor: nunca puede comprimirse por demanda interna
│
└── B_interno  (agentes Paperclip)
      Prioridad: SUBORDINADA
      Gestionado por: Instancia B
      Ceiling: B_total - B_produccion - margen_seguridad
      Comportamiento ante congestión:
        → si B_produccion tiene presión, B_interno se contrae
        → heartbeat de Paperclip puede ralentizarse dinámicamente
        → agentes no críticos degradan a Haiku automáticamente
```

**Regla invariante:** ningún agente interno puede comprometer la calidad
del servicio a usuarios reales de Abu Oracle.

---

## Formulación matemática — Framework genérico

### Variables de decisión (configurables por instancia)

```
x_u  ∈ {Haiku, Sonnet}     modelo asignado a unidad u (ruta o agente)
t_u  ∈ ℤ⁺                  max_tokens autorizado para unidad u
p_k  ∈ ℝ⁺                  precio por plan k (solo Instancia A)
```

### Función de costo por unidad

```
κ(u, x_u, t_u) = c_input(x_u) · tokens_input(u)
               + c_output(x_u) · E[min(output(u), t_u)]
               + P(truncación | t_u) · κ(u, x_u, t_u)  ← costo de reintento
```

El tercer término es el más importante para cadenas de agentes:
la truncación genera reintento, el reintento duplica el costo real.

### Supply constraint (compartida entre instancias)

```
Σ_u∈A κ(u, x_u, t_u) · freq(u) +
Σ_u∈B κ(u, x_u, t_u) · freq(u) ≤ B_total

donde:
  A = conjunto de unidades de Abu Oracle (rutas Lilly)
  B = conjunto de unidades de Paperclip (agentes)
  freq(u) = frecuencia de ejecución de la unidad u por mes
```

### Constraint de no truncación (crítico en cadenas de agentes)

```
P(truncación | t_u) ≤ ε_u    para todo u

donde ε_u se calibra empíricamente:
  ε_u = 0.01  para agentes en posición intermedia de cadena
              (truncación rompe el siguiente agente)
  ε_u = 0.05  para agentes terminales o rutas de bajo riesgo
```

### Constraint de calidad doctrinal (solo Instancia A)

```
x_u = Sonnet    para todo u ∈ rutas_doctrinales_Abu_Oracle

Rutas doctrinales: screen-open, planet, technique, city,
                   transit, domain, solar-return, sky, house, chat
```

### Función objetivo — Instancia A (pricing)

```
Maximizar: Σ_k (p_k - cost_k) · N_k
sujeto a:  p_k ≥ cost_k + μ_k     (floor de margen por plan)
```

### Función objetivo — Instancia B (eficiencia interna)

```
Minimizar: Σ_u∈B κ(u, x_u, t_u) · freq(u)
sujeto a:  calidad(u) ≥ calidad_minima(u)    (tarea completada sin truncación)
           Σ_u∈B κ(u) · freq(u) ≤ B_interno  (presupuesto interno)
```

---

## Mapeo de unidades — Instancia B (Paperclip)

Equivalencia ruta Abu Oracle → agente Paperclip:

| Tipo de agente Paperclip | Equivalente Abu Oracle | Modelo sugerido | ε (truncación) |
|--------------------------|----------------------|-----------------|-----------------|
| CEO (planificación estratégica) | `chat` / `domain` | Sonnet | 0.01 |
| Investigador (análisis profundo) | `transit` / `sky` | Sonnet | 0.02 |
| Redactor (contenido largo) | `screen-open` | Sonnet | 0.01 |
| Revisor (verificación) | `technique` | Haiku | 0.05 |
| Newsletter / summary | `lilly_summary` | Haiku | 0.05 |
| Tareas rutinarias / filing | — | Haiku | 0.10 |

**Nota:** el CEO de Paperclip es estratégico — usa Sonnet.
Los agentes de revisión y tareas repetitivas usan Haiku.
Esta es la distinción que en Abu Oracle no podíamos hacer porque
toda ruta es doctrinal. En Paperclip sí aplica.

---

## Heartbeat como variable de control

El heartbeat de Paperclip (intervalo entre ciclos del CEO) es una
palanca de control natural del MILP de Instancia B:

```
heartbeat_interval = f(B_interno_disponible, demanda_proyectada)

Si B_interno < 20% del ceiling:
  → heartbeat_interval × 2   (ralentizar ciclos)
  → agentes no críticos → Haiku
  → tareas no urgentes → diferir al próximo ciclo

Si B_produccion tiene presión (usuarios reales):
  → pausar heartbeat completamente hasta que B_produccion normalice
```

Esto da al MILP control sobre el ritmo de la "empresa interna"
sin intervención manual.

---

## Modelo de demanda sintética (para desarrollo pre-launch)

Mientras no hay datos reales, el framework se calibra con distribuciones
sintéticas razonables:

### Instancia A — Abu Oracle (sintético)

```python
# Frecuencia de rutas por sesión (distribución empírica estimada)
ROUTE_FREQ_SYNTHETIC = {
    'screen-open':  0.10,   # 1 por sesión típica
    'planet':       0.15,
    'technique':    0.10,
    'transit':      0.20,
    'domain':       0.15,
    'house':        0.10,
    'city':         0.05,
    'sky':          0.05,
    'chat':         0.10,
}

# Tokens de input por ruta (estimados de logs actuales)
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

# Output: distribución Normal(μ, σ) por ruta
OUTPUT_DIST = {
    'screen-open': (960, 39),    # empírico de Fase F
    'transit':     (800, 150),
    'chat':        (1200, 300),
    # resto: estimados
}

# Sesiones por usuario por mes por plan
SESSIONS_PER_MONTH = {
    'genesis':  40,   # usuarios genesis: acceso amplio
    'annual':   20,
    'monthly':  8,
}
```

### Instancia B — Paperclip (sintético)

```python
# Ciclos del CEO por día
CEO_CYCLES_PER_DAY = 24 / (heartbeat_hours)  # heartbeat_hours configurable

# Agentes activos por ciclo (estimado inicial)
AGENTS_PER_CYCLE = {
    'ceo':          1,
    'investigador': 2,
    'redactor':     1,
    'revisor':      2,
    'rutinario':    3,
}

# Tokens por tarea por tipo de agente
TOKENS_PER_TASK = {
    'ceo':          {'input': 6000, 'output': 2000},
    'investigador': {'input': 8000, 'output': 3000},
    'redactor':     {'input': 5000, 'output': 4000},
    'revisor':      {'input': 4000, 'output': 500},
    'rutinario':    {'input': 2000, 'output': 300},
}
```

**Principio:** los datos sintéticos son placeholders honestos.
El framework documenta explícitamente qué es sintético y qué es observado.
Cuando lleguen datos reales, se reemplaza el input — el solver no cambia.

---

## Arquitectura de software — tres capas desacopladas

```
┌─────────────────────────────────────────────────┐
│  CAPA 1 — Modelo de Demanda (intercambiable)    │
│                                                  │
│  demand_model.py                                 │
│  ├── SyntheticDemandModel   ← usa ahora          │
│  ├── LogsDemandModel        ← post-launch Abu    │
│  └── PaperclipDemandModel   ← post-Paperclip     │
└──────────────────┬──────────────────────────────┘
                   │ freq(u), tokens_dist(u)
┌──────────────────▼──────────────────────────────┐
│  CAPA 2 — Optimizador MILP (estable)            │
│                                                  │
│  milp_solver.py                                  │
│  ├── MILPInstance(config)                        │
│  ├── solve() → {modelo_u, max_tokens_u, precio_k}│
│  └── shadow_prices() → señales de congestión     │
└──────────────────┬──────────────────────────────┘
                   │ decisiones óptimas
┌──────────────────▼──────────────────────────────┐
│  CAPA 3 — Adaptadores (uno por contexto)        │
│                                                  │
│  adapters/                                       │
│  ├── abu_oracle_adapter.py  → selectModel.ts     │
│  └── paperclip_adapter.py   → heartbeat control  │
└─────────────────────────────────────────────────┘
```

**Por qué este diseño:** si mañana aparece un tercer contexto
(otro producto, otra organización de agentes), se agrega un
`DemandModel` y un `Adapter` sin tocar el solver.

---

## Plan de implementación en fases

### Fase 1 — Framework base con datos sintéticos ← EJECUTAR AHORA

**Entregable:** `research/finops/milp_framework/` con las tres capas
funcionando sobre datos sintéticos. El solver resuelve y produce
decisiones óptimas para ambas instancias.

Tareas para CC:
1. `demand_model.py` — `SyntheticDemandModel` con las distribuciones definidas arriba
2. `milp_solver.py` — formulación completa con PuLP/CBC, ambas funciones objetivo,
   todas las constraints
3. `adapters/abu_oracle_adapter.py` — produce tabla de modelo/max_tokens por ruta
4. `adapters/paperclip_adapter.py` — produce tabla de modelo/max_tokens por agente
   + señal de heartbeat
5. `run_milp.py` — CLI: `python run_milp.py --instance abu_oracle|paperclip`
6. Output: JSON con decisiones + shadow prices + reporte de margen

**No tocar:** `selectModel.ts` ni ningún archivo de producción en esta fase.
El framework corre standalone en `research/finops/`.

### Fase 2 — Calibración con datos reales Abu Oracle (post-launch)

- `LogsDemandModel` lee logs de Cloud Run de `selectModel.ts`
- MILP recalibra decisiones con demanda real
- `abu_oracle_adapter` actualiza recomendaciones de pricing

### Fase 3 — Integración Paperclip (cuando Paperclip esté corriendo en VPS)

- `PaperclipDemandModel` lee logs de Paperclip
- `paperclip_adapter` intercepta cada tarea antes de llamar a la API
- Heartbeat controlado dinámicamente por señal de congestión

### Fase 4 — Presupuesto compartido B_total

- Las dos instancias se comunican vía shared state (Firestore o Redis)
- Constraint de supply compartida activa
- Panel de monitoreo unificado

---

## Output esperado de Fase 1

```
=== MILP Abu Oracle — Instancia A ===
Demanda: SINTÉTICA (N=100 usuarios estimados)

Decisiones de modelo:
  screen-open → Sonnet · max_tokens: 1536
  transit     → Sonnet · max_tokens: 1024
  technique   → Sonnet · max_tokens: 1536  ← revertido desde Haiku
  city        → Sonnet · max_tokens: 1024  ← revertido desde Haiku
  [...]

Precios óptimos por plan:
  monthly  → $5.80/mes  (actual: $5.00 — margen negativo con Sonnet everywhere)
  annual   → $52.00/año (actual: $45.00)
  genesis  → $100.00 lifetime ✓ (sostenible)

Shadow prices:
  supply_constraint: $0.0023/token  ← no binding todavía
  margin_monthly: $0.80/usuario     ← binding — precio actual insuficiente

=== MILP Paperclip — Instancia B ===
Demanda: SINTÉTICA (heartbeat: 1h, 9 agentes)

Decisiones por agente:
  ceo          → Sonnet · max_tokens: 2000
  investigador → Sonnet · max_tokens: 3000
  redactor     → Sonnet · max_tokens: 4000
  revisor      → Haiku  · max_tokens: 1024
  rutinario    → Haiku  · max_tokens: 512

Costo estimado/mes (B_interno): $45.20
Heartbeat recomendado: 60 min (sin congestión)
```

---

## Nota sobre publicabilidad

El framework en Fase 1 ya es publicable como contribución metodológica:
un MILP genérico para organizaciones de agentes LLM con instancias
configurables por contexto. La comparación Abu Oracle vs Paperclip
como dos instancias del mismo solver es el caso de estudio del paper.

Con datos reales en Fase 2, el paper tiene contribución empírica.

Ver [[ANTHROPIC_STRATEGY]] — Eje 1 (eficiencia económica).
