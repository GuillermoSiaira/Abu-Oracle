# HF Core v2 — Diseño y especificación

## Objetivo
Extender HF Core v1 para que el score responda a relocación incorporando explícitamente:

- Ocupación de casas (house-aware)
- Fuerza de angularidad (distancia a ASC/MC/DESC/IC)
- Ponderación de resonancias por contexto de casas y angularidad

Mantiene HF v1 intacto como núcleo y añade correcciones multiplicativas simples.

## Bloques de features

- **Geometría base (v1):** vector circular 24D + armónicos 8D + resonancias v1.
- **Ocupación de casas:** `house_count_1..12`, `house_weighted_1..12`, entropía `house_entropy`.
- **Angularity:** fuerza gaussiana planeta→{ASC,MC,DESC,IC}; agregados `angularity_sum`, `angularity_mean`.
- **Métricas v2:** `hf_total_v2`, `hf_harmony_v2`, `hf_tension_v2`, `hf_conjunction_v2`, `hf_angularity`, `hf_house_balance`.

## Parámetros por defecto

- Pesos planetarios: iguales (todos 1.0).
- Sigma angular: $10^\circ$.
- Sigma cúspides: $10^\circ$ (reservado).
- Multiplicadores: $\lambda_\text{house} = 0.3$, $\lambda_\alpha = 0.5$.

## Fórmulas clave

### Angularidad
Para cada planeta $p$ y ángulo $a \in \{\text{ASC, MC, DESC, IC}\}$:

$$A_{p,a} = \exp\left(-\frac{\Delta(p,a)^2}{2\sigma_\alpha^2}\right)$$

`mean_strength(p)` es el promedio de sus $A_{p,a}$.

### Peso por casa

Distribución ponderada por pesos planetarios $w_p$:

$$H_k = \sum_{p \in \text{casa } k} w_p \quad ; \quad \tilde H_k = \frac{H_k}{\sum_j H_j}$$

### Corrección de resonancia por par

Sea $R^{(a)}_{ij}$ la resonancia v1 entre puntos $i,j$ para el aspecto $a$.

$$W_{ij}^{\text{house}} = 1 + \lambda_\text{house} \cdot \frac{\tilde H_{h_i} + \tilde H_{h_j}}{2}$$
$$W_{ij}^{\alpha} = 1 + \lambda_\alpha \cdot \frac{A_i + A_j}{2}$$

$$R^{(a)}_{ij, v2} = R^{(a)}_{ij} \cdot W_{ij}^{\text{house}} \cdot W_{ij}^{\alpha}$$

### Totales v2

$$HF_{\text{total},v2} = \sum_{i<j} \sum_a R^{(a)}_{ij,v2}$$

Agrupaciones:

- $HF_{\text{harmony},v2}$: sextil + trígono
- $HF_{\text{tension},v2}$: cuadratura + oposición
- $HF_{\text{conjunction},v2}$: conjunción
- $HF_{\text{angularity}}$: suma de `mean_strength` planetaria
- $HF_{\text{house\_balance}}$: entropía de distribución de casas

## Implementación

- Nuevos módulos en `abu_engine/harmony/`:
  - `schema_v2.py`: constantes, defaults.
  - `houses.py`: asignación planeta→casa, ocupación, entropía.
  - `angularity.py`: fuerza gaussiana a ASC/MC/DESC/IC.
  - `field_v2.py`: agrega HF v1 con multiplicadores de casas y angularidad.

- Scripts:
  - `scripts/generate_hf_dataset_v2.py`: dataset Parquet con features v2 (+ v1).
  - `scripts/generate_relocation_field_v2.py`: grids de relocación usando HF v2.

## Migración y compatibilidad

- HF v1 no se modifica; v2 se calcula en paralelo (métricas v1 siguen disponibles en datasets v2).
- Defaults elegidos para trazabilidad; todos los parámetros son configurables en código.
- Requiere `pyswisseph` (igual que v1) para cúspides y ángulos.

## Próximos pasos sugeridos

1) Generar `hf_dataset_v2.parquet` con el script nuevo.
2) Producir `relocation_fields_v2` para el mismo set de sujetos piloto.
3) Repetir los tests de RSI/z-score vs null model y comparar v1 vs v2.
4) Afinar $(\lambda_\text{house}, \lambda_\alpha)$ y $\sigma_\alpha$ si la señal relocacional aún es débil.
