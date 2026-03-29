---
name: HF_CORE_V2_DESIGN
description: Diseño HF v2 multiplicativo con angularidad y casas — especificación y diagnóstico
tipo: formula
version: v2 (superado — diagnóstico)
estado: archivado
tags: [harmony-field, v2, angularidad, casas, multiplicativo, diagnóstico]
---

# HF Core v2 — Diseño y especificación

Ver también: [[field_v3]] · [[HF_EXPERIMENT_LOG]] · [[resonance_weights]]

> **Estado**: La formulación multiplicativa de v2 no aumentó la señal respecto a v1 (z_RSI 0.137 vs 0.44). Superado por modelo aditivo v3. Ver [[HF_EXPERIMENT_LOG#Experiment 2 — HF Core v2 Relocation Test|Experimento 2]].

---

## Objetivo

Extender HF Core v1 para que el score responda a relocación incorporando explícitamente:

- Ocupación de casas (house-aware)
- Fuerza de angularidad (distancia a ASC/MC/DESC/IC)
- Ponderación de resonancias por contexto de casas y angularidad

Mantiene HF v1 intacto como núcleo y añade correcciones multiplicativas simples.

---

## Parámetros por defecto

- Pesos planetarios: iguales (todos 1.0)
- Sigma angular: $10°$
- Multiplicadores: $\lambda_{house} = 0.3$, $\lambda_\alpha = 0.5$

---

## Fórmulas clave

### Angularidad

Para cada planeta $p$ y ángulo $a \in \{\text{ASC, MC, DESC, IC}\}$:

$$A_{p,a} = \exp\left(-\frac{\Delta(p,a)^2}{2\sigma_\alpha^2}\right)$$

`mean_strength(p)` es el promedio de sus $A_{p,a}$.

### Peso por casa

$$H_k = \sum_{p \in \text{casa } k} w_p \quad ; \quad \tilde H_k = \frac{H_k}{\sum_j H_j}$$

### Corrección de resonancia por par (multiplicativa)

Sea $R^{(a)}_{ij}$ la resonancia v1 entre puntos $i,j$ para el aspecto $a$.

$$W_{ij}^{\text{house}} = 1 + \lambda_\text{house} \cdot \frac{\tilde H_{h_i} + \tilde H_{h_j}}{2}$$

$$W_{ij}^{\alpha} = 1 + \lambda_\alpha \cdot \frac{A_i + A_j}{2}$$

$$R^{(a)}_{ij, v2} = R^{(a)}_{ij} \cdot W_{ij}^{\text{house}} \cdot W_{ij}^{\alpha}$$

### Total v2

$$HF_{\text{total},v2} = \sum_{i<j} \sum_a R^{(a)}_{ij,v2}$$

---

## Diagnóstico post-experimento

El esquema multiplicativo de v2 **no incrementó la estructura espacial** frente a HF v1.

- v1 mean z_RSI = 0.44
- v2 mean z_RSI = 0.137

Esto no implica que ASC/MC o casas sean irrelevantes — la representación matemática multiplicativa fue insuficiente. La solución fue el modelo **aditivo** de [[field_v3]]: `HF_total_v3 = HF_aspects + β*HF_angles + γ*HF_houses`.

---

## Implementación (módulos)

- `abu_engine/harmony/schema_v2.py` — constantes, defaults
- `abu_engine/harmony/houses.py` — asignación planeta→casa, ocupación, entropía
- `abu_engine/harmony/angularity.py` — fuerza gaussiana a ASC/MC/DESC/IC
- `abu_engine/harmony/field_v2.py` — agrega HF v1 con multiplicadores (superado)
