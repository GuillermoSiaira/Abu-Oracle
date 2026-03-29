---
name: resonance_weights
description: Constantes de pesos de aspectos y grupos — núcleo de la fórmula HF
tipo: formula
version: v4 (producción)
estado: activo
tags: [harmony-field, aspectos, pesos, resonancia, produccion]
---

# Resonance Weights — HF Core

Archivo fuente: `abu_engine/harmony/resonance.py`

Ver también: [[field_v3]] · [[HF_V4_SESSION_B]] · [[AXIOMATICS_v0_4]]

---

## Aspectos y sigmas

| Aspecto     | Ángulo | Sigma (σ) | Peso individual |
|-------------|--------|-----------|-----------------|
| conjunction | 0°     | 4.0°      | 1.0             |
| sextile     | 60°    | 4.0°      | 1.0             |
| square      | 90°    | 4.0°      | 1.0             |
| trine       | 120°   | 4.0°      | 1.0             |
| opposition  | 180°   | 4.0°      | 1.0             |

---

## GROUP_WEIGHTS — pesos en producción (v2 optimizados)

```python
GROUP_WEIGHTS: Dict[str, float] = {
    "w_harmony": -1.0,
    "w_tension": -1.0,
    "w_conjunction": 2.5,
}
```

**Patrón de signos**: harmony y tension RESTAN; conjunction SUMA.
Optimización v2: 527 eventos biográficos · 26 sujetos · corr_nn=+0.156 · Cohen's d=+0.447.

### Fórmula HF weighted

```
HF_weighted = w_harmony * (sextile + trine)
            + w_tension * (square + opposition)
            + w_conjunction * conjunction
```

---

## Función de resonancia gaussiana

```python
def gaussian_resonance(delta_deg, aspect_deg, sigma):
    diff = delta_deg - aspect_deg
    return math.exp(-(diff * diff) / (2 * sigma * sigma))
```

El kernel gaussiano evalúa qué tan cerca está la separación angular real del ángulo del aspecto.

---

## Código fuente completo

```python
"""Resonance kernel utilities for Harmony Field (HF Core v1)."""

from typing import Dict
import math

ASPECTS: Dict[str, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

SIGMAS: Dict[str, float] = {
    "conjunction": 4.0,
    "sextile": 4.0,
    "square": 4.0,
    "trine": 4.0,
    "opposition": 4.0,
}

ASPECT_WEIGHTS: Dict[str, float] = {
    "conjunction": 1.0,
    "sextile": 1.0,
    "square": 1.0,
    "trine": 1.0,
    "opposition": 1.0,
}

# Group-level weights — optimized v2 (527 bio events, 26 subjects)
# Sign pattern confirmed: harmony and tension both SUBTRACT; conjunction ADDS.
GROUP_WEIGHTS: Dict[str, float] = {
    "w_harmony": -1.0,
    "w_tension": -1.0,
    "w_conjunction": 2.5,
}


def angular_distance_deg(a_deg: float, b_deg: float) -> float:
    """Smallest angular distance on the circle in degrees (0–180]."""
    return abs((a_deg - b_deg + 180) % 360 - 180)


def gaussian_resonance(delta_deg: float, aspect_deg: float, sigma: float) -> float:
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    diff = delta_deg - aspect_deg
    return math.exp(-(diff * diff) / (2 * sigma * sigma))
```
