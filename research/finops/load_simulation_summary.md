# Load Simulation — Resultados

**Generado:** 2026-04-03T03:05:22.978966+00:00  
**Usuarios:** 800 · **Duracion:** 60 min · **Req/usuario/hr:** 10 · **Seed:** 42

---

## Comparacion de politicas

| Metrica | static_baseline | greedy_approximation | Delta |
|---------|----------------|----------------------|-------|
| Requests servidos | 7,786 | 7,863 | +1.0% |
| Requests dropped | 230 | 153 | +33.5% |
| Drop rate | 2.9% | 1.9% | — |
| Costo total (USD) | $120.4897 | $92.6613 | +23.1% |
| Revenue total (USD) | $109.6905 | $110.7854 | +1.0% |
| Margen total (USD) | $-10.7992 | $18.1242 | +267.8% |
| Revenue lost (dropped) | $3.2143 | $2.1195 | — |
| Avg cost/req | $0.015475 | $0.011784 | +23.9% |
| Avg margin/req | $-0.001387 | $0.002305 | +266.2% |
| Cache hit rate | 62.2% | 63.0% | — |
| Continuation rate | 15.2% | 14.8% | — |
| Max TPM utilization | 100.0% | 100.0% | — |
| Max RPM utilization | 19.2% | 18.6% | — |
| Max shadow price TPM | $0.000000 | $0.018288 | — |
| R5 applications | 0 | 2,354 | — |

---

## Margen por plan

| Plan | Politica | Requests | Costo | Revenue | Margen | Avg margin/req |
|------|----------|----------|-------|---------|--------|----------------|
| genesis | static | 761 | $11.9393 | $2.5367 | $-9.4026 | $-0.012356 |
| genesis | greedy | 767 | $11.3588 | $2.5567 | $-8.8021 | $-0.011476 |
| annual | static | 2,289 | $34.9155 | $28.2205 | $-6.6949 | $-0.002925 |
| annual | greedy | 2,314 | $19.5166 | $28.5288 | $9.0122 | $0.003895 |
| monthly | static | 4,736 | $73.6350 | $78.9333 | $5.2983 | $0.001119 |
| monthly | greedy | 4,782 | $61.7859 | $79.7000 | $17.9141 | $0.003746 |

---

## Shadow prices — interpretacion

**static_baseline** max shadow price TPM: $0.000000  
**greedy_approximation** max shadow price TPM: $0.018288

El shadow price de TPM cuantifica el valor economico de 1 token adicional de capacidad cuando el sistema supera el 95% de saturacion.
Un shadow price > 0 indica que subir de tier tiene valor economico medible.

---

## Costo de la limitacion de rate limit

**static_baseline** revenue lost por 429: $3.2143  
**greedy_approximation** revenue lost por 429: $2.1195

Revenue perdido = revenue que hubiera generado cada request dropped.
Esto cuantifica el costo de no subir de tier en escenarios de alta carga.

---

_Nota: greedy_approximation es un heuristico derivado de la estructura del MILP,_
_no una solucion LP exacta. Ver MILP_INITIATIVE.md para la formulacion completa._