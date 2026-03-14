# Session B — HF v4 Weighted + Event Correlator

## Objetivo
Implementar la fórmula HF v4 con pesos diferenciados para harmony/tension/conjunction, y construir el correlador que mide la calidad de esos pesos contra eventos biográficos reales.

## Prerequisito
Sesión A completada: debe existir `data/biographical_events/*.json` con eventos fechados (mínimo 13 sujetos).

## Contexto mínimo
- Proyecto: AI Oracle — motor astrológico HF (Harmony Field).
- Fórmula actual (v3): `hf_total = harmony + tension + conjunction` → TODO se SUMA. Pesos todos = 1.0.
- Problema: Un lugar con muchas squares/oppositions puntúa igual que uno con trines/sextiles.
- Decisión: v4 con pesos diferenciados y signo negativo para tensión.

## Fórmula HF v4

### Core (aspectos)
```python
hf_weighted = w_h * hf_harmony + w_t * hf_tension + w_c * hf_conjunction
```
Donde:
- `hf_harmony = sextile + trine` (como antes)
- `hf_tension = square + opposition` (como antes)
- `hf_conjunction = conjunction` (como antes)
- Pesos iniciales: `w_h = +1.5`, `w_t = -0.8`, `w_c = +1.0`

### Relocation (v4 completa)
```python
hf_v4(φ,λ) = hf_weighted(φ,λ) + β * hf_angles(φ,λ) + γ * hf_houses(φ,λ)
```
- `β = 0.6`, `γ = 0.3` (heredar de v3, no cambiar en esta sesión)

## Archivos a modificar

### 1. `abu_engine/harmony/resonance.py`
- Agregar constantes de peso por grupo:
```python
# HF v4 signed aspect-group weights
GROUP_WEIGHTS: Dict[str, float] = {
    "harmony": 1.5,
    "tension": -0.8,    # RESTA
    "conjunction": 1.0,
}
```
- NO cambiar ASPECT_WEIGHTS (esos son por aspecto individual, quedan en 1.0).

### 2. `abu_engine/harmony/field.py` → `aggregate_field()`
- Cambiar la línea `hf_total = sum(totals.values())` por:
```python
from .resonance import GROUP_WEIGHTS
hf_total = (
    GROUP_WEIGHTS["harmony"] * hf_harmony +
    GROUP_WEIGHTS["tension"] * hf_tension +
    GROUP_WEIGHTS["conjunction"] * hf_conjunction
)
```
- Mantener `HF_harmony`, `HF_tension`, `HF_conjunction` en el return dict (son componentes Raw, útiles para auditoría).
- Agregar `HF_total_raw` = antigua suma total (para comparación).

### 3. `abu_engine/harmony/field_v3.py` → `compute_hf_aspects()`
- Ya usa `aggregate_field()` internamente → hereda la corrección automáticamente.
- Verificar que el return `agg["HF_total"]` ahora es el weighted.

### 4. Regenerar datos demo
```powershell
# Tras la modificación, regenerar los 10 demo packs
python scripts/batch_compute_demo.py   # o el script equivalente
```

## Correlador de eventos (nuevo)

### Input
- Eventos biográficos: `data/biographical_events/{id}_{slug}.json`
- Para cada evento con fecha + ubicación: calcular HF(fecha, lat, lon) usando tránsitos.

### Lógica
```python
# Para cada sujeto:
for event in biographical_events:
    # 1. Calcular carta de tránsitos a la fecha del evento
    transit_chart = compute_chart(event.date, event.lat, event.lon)
    # 2. Calcular HF entre carta natal y tránsitos
    hf_at_event = compute_hf_v4(natal_angles, transit_angles)
    # 3. Almacenar (hf_value, valence)
    correlations.append((hf_at_event, event.valence))

# Métrica: correlación entre hf_value y valence_numeric
# positive → +1, neutral → 0, negative → -1
```

### Archivo a crear
```
scripts/
  hf_correlator/
    __init__.py
    compute.py       # Calcula HF en cada evento
    correlate.py     # Mide correlación hf ↔ valence
    optimize.py      # Grid search sobre (w_h, w_t, w_c, β, γ)
    report.py        # Genera CSV + plots
```

### Optimización de pesos
```python
# Grid search simple
import itertools
best_corr = -1
for w_h in [1.0, 1.2, 1.5, 2.0]:
    for w_t in [-0.5, -0.8, -1.0, -1.2]:
        for w_c in [0.5, 0.8, 1.0, 1.2]:
            # Recalcular HF para todos los eventos con estos pesos
            corr = compute_correlation(events, w_h, w_t, w_c)
            if corr > best_corr:
                best_corr = corr
                best_weights = (w_h, w_t, w_c)
```

### Output del correlador
```
analysis/
  hf_v4_correlation.csv          # event_id, subject, date, hf_weighted, valence, valence_num
  hf_v4_weight_optimization.csv  # w_h, w_t, w_c, correlation, n_events
  plots/
    hf_vs_valence_scatter.png
    weight_heatmap.png
```

## Código de referencia existente

### `abu_engine/harmony/resonance.py` (actual)
```python
ASPECT_WEIGHTS: Dict[str, float] = {
    "conjunction": 1.0, "sextile": 1.0, "square": 1.0, "trine": 1.0, "opposition": 1.0,
}
```

### `abu_engine/harmony/field.py` → `aggregate_field()` (actual)
```python
hf_harmony = totals.get("sextile", 0.0) + totals.get("trine", 0.0)
hf_tension = totals.get("square", 0.0) + totals.get("opposition", 0.0)
hf_conjunction = totals.get("conjunction", 0.0)
hf_total = sum(totals.values())  # ← ESTO CAMBIA
```

### `abu_engine/harmony/field_v3.py` → `compute_hf_v3()`
```python
def compute_hf_v3(angles_deg, asc, mc, cusps, ...):
    hf_aspects = compute_hf_aspects(angles_deg)  # ← hereda de aggregate_field
    hf_angles = compute_hf_angles(...)
    hf_houses = compute_hf_houses(...)
    return hf_aspects + beta * hf_angles + gamma * hf_houses
```

## Tests
- `pytest abu_engine/tests/` — asegurar que los tests existentes pasan (ajustar expected values).
- Agregar test: `test_hf_weighted_tension_subtracts` — verificar que square/opposition reducen HF_total.
- Agregar test: `test_hf_v4_vs_v3_comparison` — verificar que v4 produce valores distintos a v3.

## NO hacer en esta sesión
- No tocar el frontend.
- No tocar lilly_engine.
- No cambiar endpoints (la API devuelve el mismo shape, solo cambian los valores numéricos).
- No cambiar β (0.6) ni γ (0.3) — solo optimizar w_h, w_t, w_c.
- No implementar el scraper bio (es Sesión A).
