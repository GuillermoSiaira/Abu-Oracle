---
name: domain_correlation_baseline
description: Baseline pre-Fase 3 — correlación HF global vs valencia de eventos, segmentada por casa
tipo: resultados
version: 2026-03-13 (pre-Fase 3)
estado: archivado
tags: [baseline, correlacion, pearson, cohen-d, pre-dominio]
---

# Domain Correlation Baseline — Fase 2.3

Archivo fuente: `analysis/domain_correlation_baseline.md`

Ver también: [[domain_correlation_report]] · [[HF_EXPERIMENT_LOG]] · [[HIPOTESIS_REGISTRO]]

> **Contexto**: Baseline calculado antes de implementar el filtrado por dominio. Mide la correlación del HF **global** contra valence de eventos, segmentado por house_domain. Sirve como referencia para cuantificar la mejora del campo por dominio.

---

## Resultados baseline (HF global, por casa)

| Casa | N | N+ | N− | corr_all | corr_nn | Cohen's d |
|------|---|----|----|----------|---------|-----------|
| H05 | 57 | 51 | 1 | +0.049 | +0.105 | n/a |
| H07 | 93 | 81 | 9 | +0.078 | +0.063 | +0.207 |
| H08 | 34 | 0 | 34 | n/a | n/a | n/a |
| H09 | 66 | 14 | 4 | +0.066 | +0.181 | +0.417 |
| H10 | 250 | 231 | 4 | +0.050 | +0.051 | +0.391 |

### Casas sin cálculo (N insuficiente)

- H06: 10 eventos — no calculado
- H12: 12 eventos — no calculado

### Referencia global (sin segmentar)

N=527 · corr_all=+0.121 · corr_nn=+0.133 · Cohen's d=+0.371

---

## Comparación con resultados de dominio

La mejora de cambiar de HF global a HF dominio se mide como `Δcorr = corr_domain − corr_baseline`:

| Casa | corr_baseline | corr_domain | Δcorr final |
|------|---------------|-------------|-------------|
| H05 | +0.049 | +0.350 | +0.301 |
| H07 | +0.078 | +0.041 | −0.037 |
| H09 | +0.066 | −0.046 | −0.112 |
| H10 | +0.050 | +0.013 | −0.037 |

*Nota*: los resultados del reporte final usan una normalización z-score adicional que modifica ligeramente los valores. Ver [[domain_correlation_report]] para los números definitivos.

---

## Métricas de referencia

- `corr_all`: Pearson sobre todos los eventos del segmento (incluye neutros)
- `corr_nn`: Pearson excluyendo eventos de valencia neutra
- `Cohen's d`: separación mean_pos − mean_neg / SD pooled
