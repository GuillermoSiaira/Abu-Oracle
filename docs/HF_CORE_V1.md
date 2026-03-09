# HF Core v1 – Modelo Matemático y Flujo de Datos

## 1. Modelo matemático

### Espacio del sistema

- Puntos considerados (12): Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, ASC, MC.
- Cada punto es un ángulo eclíptico: $\theta_i \in [0, 360)$. El espacio total es $(S^1)^{12}$.

### Vector circular (24D)

Cada punto se proyecta al círculo unitario:

$$
(\cos \theta_i, \sin \theta_i)
$$

El vector final concatena los 12 pares en orden fijo (Sun→MC), resultando en 24 dimensiones.

### Firma armónica (8D)

Para cada armónico $k$:

$$
H_k = \left| \sum_i w_i\, e^{\, i k \theta_i} \right|
$$

Con $k \in \{1,2,3,4,5,6,8,12\}$ y pesos $w_i$ opcionales (por defecto 1). Esto produce 8 componentes.

### Distancia angular

$$
\Delta \theta_{ij} = \min\big(|\theta_i - \theta_j|,\, 360 - |\theta_i - \theta_j|\big) \in [0, 180]
$$

### Resonancia de aspecto (kernel gaussiano)

Aspectos mayores: 0° (conjunction), 60° (sextile), 90° (square), 120° (trine), 180° (opposition).

Para cada aspecto $a$:

$$
R_{ij}^{(a)} = \exp\left( -\frac{(\Delta \theta_{ij} - a)^2}{2\, \sigma_{a}^2} \right)
$$

En HF Core v1, $\sigma_a$ es configurable por aspecto (constante). El diseño contempla un orb adaptativo (p.ej. $\sigma_{ij} = \tfrac{\sqrt{\sigma_i^2 + \sigma_j^2}}{2}$), pero la versión actual usa $\sigma$ fijo por aspecto.

### Harmony Field

Resonancias por par sobre 66 combinaciones de los 12 puntos. Con pesos por aspecto $w_a$:

$$
HF_{total} = \sum_{i<j} \sum_{a \in \text{aspectos}} w_a\, R_{ij}^{(a)}
$$

Subcomponentes (suma restringida a los aspectos indicados):

- $HF_{harmony}$: sextile + trine
- $HF_{tension}$: square + opposition
- $HF_{conjunction}$: conjunction

### Firma final del chart (36D)

- 24 dimensiones: vector circular.
- 8 dimensiones: firma armónica $H_k$.
- 4 métricas: $HF_{total}$, $HF_{harmony}$, $HF_{tension}$, $HF_{conjunction}$.

## 2. Implementación técnica (HF Core v1)

Ubicación: `abu_engine/harmony/`

- `chart_vector.py`: orden fijo de 12 puntos; conversión ángulo→(cos, sin); vector de 24D.
- `harmonics.py`: cálculo de $H_k$ y lote para $k \in \{1,2,3,4,5,6,8,12\}$ con pesos opcionales.
- `resonance.py`: distancia angular y kernel gaussiano; constantes configurables `ASPECTS`, `SIGMAS`, `ASPECT_WEIGHTS`.
- `field.py`: resonancias para los 66 pares; agregados $HF_{total}$, $HF_{harmony}$, $HF_{tension}$, $HF_{conjunction}$.

## 3. Pipeline de datos (bridge previsto)

1) **Fuente**: `carta-natal.es` → `raw_birthdata.jsonl` (5359 charts actuales).
2) **Ephemeris**: Abu Engine calcula posiciones planetarias/angulares para cada registro.
3) **HF Core**:
   - Vector circular (24D)
   - Firma armónica (8D)
   - Métricas HF (4D)
4) **Salida**: Dataset HF (recomendado Parquet) con campos base (id, nombre, fecha/lat/lon) + posiciones + 24+8+4 características.
5) **Sanity checks**: Distribuciones de $HF_{total}$, $HF_{harmony}$, $HF_{tension}$ (p.ej., media esperada ≈ 10–25, std ≈ 4–8) antes de cualquier ML.

> Nota: El “bridge” masivo (`scripts/generate_hf_dataset.py`) aún no se implementa en repo; este documento congela HF Core v1 para trazabilidad experimental.