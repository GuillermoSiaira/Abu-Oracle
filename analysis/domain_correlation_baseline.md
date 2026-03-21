# Domain Correlation Baseline — Fase 2.3

Correlación de `transit_hf_weighted` (campo global) contra `valence_num`,
segmentada por `house_domain`. Baseline pre-Fase 3.

| Casa | N | N+ | N− | corr_all | corr_nn | Cohen's d | corr_domain | cohens_d_domain |
|------|---|----|----|----------|---------|-----------|-------------|-----------------|
| H05 | 57 | 51 | 1 | +0.049 | +0.105 | +nan | pendiente | pendiente |
| H07 | 93 | 81 | 9 | +0.078 | +0.063 | +0.207 | pendiente | pendiente |
| H08 | 34 | 0 | 34 | +nan | +nan | +nan | pendiente | pendiente |
| H09 | 66 | 14 | 4 | +0.066 | +0.181 | +0.417 | pendiente | pendiente |
| H10 | 250 | 231 | 4 | +0.050 | +0.051 | +0.391 | pendiente | pendiente |

## Casas con señal débil (sin cálculo — n insuficiente)

- **H06**: 10 eventos — no se calcula correlación
- **H12**: 12 eventos — no se calcula correlación

## Referencia global (sin segmentar)

N=527 | corr_all=+0.121 | corr_nn=+0.133 | Cohen's d=+0.371

## Notas

- `corr_all`: Pearson sobre todos los eventos del segmento (incluye neutros)
- `corr_nn`: Pearson excluyendo eventos de valencia neutra
- `Cohen's d`: separación mean_pos − mean_neg / SD pooled
- `corr_domain` / `cohens_d_domain`: pendiente Fase 3 (requiere grillas por dominio)
