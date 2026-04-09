# Load Simulation — Resultados

**Generado:** 2026-04-05T12:21:17.765725+00:00  
**Usuarios:** 1000 · **Duracion:** 60 min · **Req/usuario/hr:** 10 · **Seed:** 42

---

## Comparacion de politicas

| Metrica | static_baseline | greedy_approximation | Delta |
|---------|----------------|----------------------|-------|
| Requests servidos | 9,494 | 9,507 | +0.1% |
| Requests dropped | 483 | 470 | +2.7% |
| Drop rate | 4.8% | 4.7% | — |
| Costo total (USD) | $109.1388 | $96.3191 | +11.7% |
| Revenue total (USD) | $135.2990 | $135.4853 | +0.1% |
| Margen total (USD) | $26.1602 | $39.1662 | +49.7% |
| Revenue lost (dropped) | $6.9794 | $6.7931 | — |
| Avg cost/req | $0.011496 | $0.010131 | +11.9% |
| Avg margin/req | $0.002755 | $0.004120 | +49.5% |
| Cache hit rate | 62.2% | 62.7% | — |
| Continuation rate | 6.5% | 6.3% | — |
| Max TPM utilization | 99.8% | 100.0% | — |
| Max RPM utilization | 20.3% | 20.3% | — |
| Max shadow price TPM | $0.031828 | $0.033814 | — |
| R5 applications | 0 | 2,783 | — |

---

## Margen por plan

| Plan | Politica | Requests | Costo | Revenue | Margen | Avg margin/req |
|------|----------|----------|-------|---------|--------|----------------|
| genesis | static | 841 | $9.7147 | $2.8033 | $-6.9113 | $-0.008218 |
| genesis | greedy | 841 | $9.5119 | $2.8033 | $-6.7085 | $-0.007977 |
| annual | static | 2,702 | $31.5600 | $33.3123 | $1.7524 | $0.000649 |
| annual | greedy | 2,709 | $20.6709 | $33.3986 | $12.7278 | $0.004698 |
| monthly | static | 5,951 | $67.8642 | $99.1833 | $31.3192 | $0.005263 |
| monthly | greedy | 5,957 | $66.1364 | $99.2833 | $33.1469 | $0.005564 |

---

## Shadow prices — interpretacion

**static_baseline** max shadow price TPM: $0.031828  
**greedy_approximation** max shadow price TPM: $0.033814

El shadow price de TPM cuantifica el valor economico de 1 token adicional de capacidad cuando el sistema supera el 95% de saturacion.
Un shadow price > 0 indica que subir de tier tiene valor economico medible.

---

## Costo de la limitacion de rate limit

**static_baseline** revenue lost por 429: $6.9794  
**greedy_approximation** revenue lost por 429: $6.7931

Revenue perdido = revenue que hubiera generado cada request dropped.
Esto cuantifica el costo de no subir de tier en escenarios de alta carga.

---

_Nota: greedy_approximation es un heuristico derivado de la estructura del MILP,_
_no una solucion LP exacta. Ver MILP_INITIATIVE.md para la formulacion completa._