# FinOps — Scaling Analysis Empírica (Fase A-2b)

**Generado:** 2026-04-04T06:19:09.253760+00:00  
**Calibración:** empírica — distribución real de output tokens por ruta  
**Continuación:** estocástica por ruta (ROUTE_CONTINUATION_RATE empírico)  
**P_CONTINUATION:** 0.036 (medido) vs 0.150 (supuesto anterior)

---

## Tabla comparativa — Margen (empírico vs sintético)

| N_USERS | Margen static | Margen greedy | Δ greedy-static | vs synthetic static | vs synthetic greedy |
|---------|--------------|--------------|-----------------|---------------------|---------------------|
| 500 | $12.74 | $19.54 | **$6.80** | +19.58 | +8.31 |
| 700 | $17.96 | $27.38 | **$9.42** | +27.94 | +11.54 | ← θ
| 800 | $20.07 | $31.31 | **$11.24** | +30.78 | +13.24 |
| 1,000 | $26.16 | $39.13 | **$12.97** | +37.17 | +15.33 |
| 5,000 | $6.48 | $20.79 | **$14.31** | +29.48 | +14.60 |
| 50,000 | $-6.53 | $3.28 | **$9.81** | -1.55 | +4.23 |

---

## Continuation rate (empírico vs sintético)

| N_USERS | Cont. rate static (empírico) | Cont. rate static (sintético) | Delta |
|---------|------------------------------|-------------------------------|-------|
| 500 | 0.069 | 0.152 | -0.083 |
| 700 | 0.068 | 0.152 | -0.084 |
| 800 | 0.068 | 0.152 | -0.084 |
| 1,000 | 0.065 | 0.152 | -0.087 |
| 5,000 | 0.065 | 0.152 | -0.087 |
| 50,000 | 0.066 | 0.152 | -0.086 |

---

## Shadow price TPM (empírico)

| N_USERS | Shadow TPM static | Shadow TPM greedy | θ activo |
|---------|------------------|------------------|----------|
| 500 | $0.000000 | $0.000000 | no |
| 700 | $0.001678 | $0.006651 | **YES** |
| 800 | $0.012379 | $0.018142 | **YES** |
| 1,000 | $0.031925 | $0.034075 | **YES** |
| 5,000 | $0.020845 | $0.035115 | **YES** |
| 50,000 | $0.005383 | $0.011780 | **YES** |

---

## Drop rate y revenue perdido

| N_USERS | Drop% static | Drop% greedy | Rev. lost static | Rev. lost greedy |
|---------|-------------|-------------|-----------------|-----------------|
| 500 | 0.0% | 0.0% | $0.00 | $0.00 |
| 700 | 0.2% | 0.2% | $0.22 | $0.17 |
| 800 | 1.1% | 1.2% | $1.14 | $1.28 |
| 1,000 | 4.8% | 4.7% | $6.98 | $6.79 |
| 5,000 | 84.3% | 84.3% | $588.58 | $588.30 |
| 50,000 | 98.8% | 98.8% | $6930.32 | $6930.14 |

---

## El número del abstract (calibrado empíricamente)

**A 1,000 usuarios simultáneos (60 minutos de carga sostenida):**

> La greedy_approximation genera **+$12.97 USD de margen adicional** respecto a la política estática. Extrapolado a operación mensual (720h, 70% uptime): **+$6,535 USD/mes de margen adicional a N=1,000 usuarios.**

*Comparación: con supuestos sintéticos el número era +$34.81 USD/60min (+$17,524/mes).*


---

## Cambios respecto a calibración sintética

| Parámetro | Sintético | Empírico (A-2b) | Impacto |
|-----------|-----------|----------------|---------|
| P_CONTINUATION | 0.150 | **0.036** | Costo sobreestimado ~12% en sintético |
| Continuación | estocástica (P_CONT=0.15 global) | **estocástica por ruta (empírico)** | screen-open: 71.1%; técnicas: 0-2.2% |
| screen-open output | Normal(665,154) | **Normal(960,39)** | Costo real 2× mayor para esta ruta |
| technique_* output | Normal(1331,307) | **Normal(415-437,40-44)** | Costo sintético 3× sobreestimado |
| domain output | Normal(665,154) | **Normal(660,147)** | Bien calibrado originalmente |

---

## Bug conocido — screen-open max_tokens

Con mean=960 y max_tokens=1024, `screen-open` produce **71.1% de continuación** (32/45 records).
En producción, `completeLilly()` detecta esto y hace una segunda llamada API,
duplicando el costo de esa ruta. Solución: subir max_tokens a 1536 o 2048.
**Estado: bug activo en producción. Pendiente fix.**

## Oportunidad — technique_lot y technique_firdaria

p95 real ≈ 497 tokens vs max_tokens=2048 actual. Reducir a 512 ahorra:
- `(2048-512)/1e6 × $4.00/1M × n_requests ≈ $0.006/request` en Haiku
- A N=1,000 con ~9% de requests en estas rutas: ahorro ~$0.5/hr o ~$250/mes

---

_Generado por `scripts/finops/_run_scaling_empirical.py`_  
_Datos A-2: `research/finops/token_distribution_output.json`_  
_Calibración: Fase A-2b, 2026-04-04_