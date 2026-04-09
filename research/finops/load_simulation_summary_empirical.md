# Load Simulation — Resultados

**Generado:** 2026-04-04T06:17:09.172370+00:00  
**Usuarios:** 50 · **Duracion:** 5 min · **Req/usuario/hr:** 10 · **Seed:** 42

---

## Comparacion de politicas

| Metrica | static_baseline | greedy_approximation | Delta |
|---------|----------------|----------------------|-------|
| Requests servidos | 39 | 39 | +0.0% |
| Requests dropped | 0 | 0 | N/A |
| Drop rate | 0.0% | 0.0% | — |
| Costo total (USD) | $0.4799 | $0.4913 | -2.4% |
| Revenue total (USD) | $0.5356 | $0.5356 | +0.0% |
| Margen total (USD) | $0.0557 | $0.0443 | -20.5% |
| Revenue lost (dropped) | $0.0000 | $0.0000 | — |
| Avg cost/req | $0.012305 | $0.012598 | -2.4% |
| Avg margin/req | $0.001429 | $0.001135 | -20.6% |
| Cache hit rate | 23.1% | 17.9% | — |
| Continuation rate | 10.3% | 2.6% | — |
| Max TPM utilization | 8.2% | 8.0% | — |
| Max RPM utilization | 1.0% | 1.0% | — |
| Max shadow price TPM | $0.000000 | $0.000000 | — |
| R5 applications | 0 | 10 | — |

---

## Margen por plan

| Plan | Politica | Requests | Costo | Revenue | Margen | Avg margin/req |
|------|----------|----------|-------|---------|--------|----------------|
| genesis | static | 5 | $0.0708 | $0.0167 | $-0.0541 | $-0.010821 |
| genesis | greedy | 5 | $0.0739 | $0.0167 | $-0.0572 | $-0.011449 |
| annual | static | 11 | $0.1292 | $0.1356 | $0.0064 | $0.000584 |
| annual | greedy | 11 | $0.0628 | $0.1356 | $0.0729 | $0.006623 |
| monthly | static | 23 | $0.2799 | $0.3833 | $0.1034 | $0.004496 |
| monthly | greedy | 23 | $0.3547 | $0.3833 | $0.0287 | $0.001246 |

---

## Shadow prices — interpretacion

**static_baseline** max shadow price TPM: $0.000000  
**greedy_approximation** max shadow price TPM: $0.000000

El shadow price de TPM cuantifica el valor economico de 1 token adicional de capacidad cuando el sistema supera el 95% de saturacion.
Un shadow price > 0 indica que subir de tier tiene valor economico medible.

---

## Costo de la limitacion de rate limit

**static_baseline** revenue lost por 429: $0.0000  
**greedy_approximation** revenue lost por 429: $0.0000

Revenue perdido = revenue que hubiera generado cada request dropped.
Esto cuantifica el costo de no subir de tier en escenarios de alta carga.

---

_Nota: greedy_approximation es un heuristico derivado de la estructura del MILP,_
_no una solucion LP exacta. Ver MILP_INITIATIVE.md para la formulacion completa._