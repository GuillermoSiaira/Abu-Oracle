---
name: field_v3
description: Implementación HF v3 aditivo con aspectos ponderados v4 — fórmula completa de relocalización
tipo: formula
version: v3 (estructura) + v4 (pesos aspectos)
estado: activo
tags: [harmony-field, relocation, formula, produccion, angularity, houses]
---

# Field v3 — HF Core: fórmula de relocalización

Archivo fuente: `abu_engine/harmony/field_v3.py`

Ver también: [[resonance_weights]] · [[HF_CORE_V2_DESIGN]] · [[HF_V4_SESSION_B]] · [[AXIOMATICS_v0_4]]

---

## Fórmula principal

```
HF_total_v3 = HF_aspects + β * HF_angles + γ * HF_houses
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| β (beta)  | 0.6   | Peso del término de angularidad |
| γ (gamma) | 0.3   | Peso del término de casas |
| σ_angle   | 10°   | Sigma gaussiana para proximidad a ASC/MC |

### Componentes

- **HF_aspects**: usa [[resonance_weights#GROUP_WEIGHTS|pesos v4]] — ver fórmula HF_weighted
- **HF_angles**: fuerza gaussiana de cada planeta hacia ASC y MC
- **HF_houses**: score aditivo por ocupación de casas (pesos fijos por casa)

---

## Pesos de casas por defecto

| Casa | Peso | Casa | Peso |
|------|------|------|------|
| 1    | 1.2  | 7    | 1.1  |
| 2    | 1.0  | 8    | 0.95 |
| 3    | 1.0  | 9    | 1.05 |
| 4    | 1.1  | 10   | 1.2  |
| 5    | 1.05 | 11   | 1.0  |
| 6    | 0.9  | 12   | 0.85 |

Casas angulares (1, 4, 7, 10) reciben mayor peso.

---

## Soporte `planet_subset`

Todas las funciones aceptan `planet_subset: List[str] | None`:
- `None` → todos los 12 puntos (global)
- Lista de planetas → solo esos participan en aspectos, angularidad y casas

Fundamento axiomático: [[AXIOMATICS_v0_4#Axioma 8.3 — El subset planetario es la pregunta|Axioma 8.3]]

---

## Código fuente completo

```python
"""HF Core v3: additive, minimal model for relocation.

HF_total_v3 = HF_aspects(weighted) + beta * HF_angles + gamma * HF_houses
"""

DEFAULT_BETA: float = 0.6
DEFAULT_GAMMA: float = 0.3
DEFAULT_SIGMA_ANGLE: float = 10.0

DEFAULT_HOUSE_WEIGHTS: Dict[int, float] = {
    1: 1.2, 2: 1.0, 3: 1.0, 4: 1.1, 5: 1.05, 6: 0.9,
    7: 1.1, 8: 0.95, 9: 1.05, 10: 1.2, 11: 1.0, 12: 0.85,
}


def compute_hf_v3(
    angles_deg, cusps=None, beta=DEFAULT_BETA, gamma=DEFAULT_GAMMA,
    sigma_angle=DEFAULT_SIGMA_ANGLE, aspects=ASPECTS, sigmas=SIGMAS,
    aspect_weights=ASPECT_WEIGHTS, group_weights=GROUP_WEIGHTS,
    house_weights=DEFAULT_HOUSE_WEIGHTS, planet_weights=DEFAULT_PLANET_WEIGHTS,
    planet_subset=None,
) -> Dict[str, float]:
    hf_aspects = compute_hf_aspects(angles_deg, aspects=aspects, sigmas=sigmas,
                                    aspect_weights=aspect_weights, group_weights=group_weights,
                                    planet_subset=planet_subset)
    hf_angles = compute_hf_angles(angles_deg, sigma_angle=sigma_angle,
                                  planet_weights=planet_weights, planet_subset=planet_subset)
    hf_houses = compute_hf_houses(angles_deg, cusps=cusps, house_weights=house_weights,
                                  planet_weights=planet_weights, planet_subset=planet_subset)

    hf_total_v3 = hf_aspects + beta * hf_angles + gamma * hf_houses

    return {
        "hf_total_v3": float(hf_total_v3),
        "hf_aspects": float(hf_aspects),
        "hf_angles": float(hf_angles),
        "hf_houses": float(hf_houses),
        "beta": float(beta),
        "gamma": float(gamma),
        "planet_subset": planet_subset,
    }
```
