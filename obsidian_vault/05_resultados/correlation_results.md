---
name: correlation_results
description: Tabla de resultados JSON — correlación HF por dominio, 527 eventos, valores exactos
tipo: resultados
version: 2026-03-13
estado: final
tags: [resultados, json, correlacion, pearson, cohen-d, rank-biserial, datos-crudos]
---

# Correlation Results — Datos Crudos

Archivo fuente: `analysis/domain_correlation_results.json`

Ver también: [[domain_correlation_report]] · [[HF_EXPERIMENT_LOG]]

---

## Datos completos (JSON)

```json
{
  "n_events": 527,
  "table": [
    {
      "house": 1, "n_events": 3, "n_positive": 0, "n_negative": 1,
      "corr_global": 0.0228, "corr_domain": -0.8898,
      "cohens_d_global": null, "cohens_d_domain": null,
      "improvement_corr": -0.9126,
      "mw_p_domain": null, "mw_p_global": null,
      "rb_domain": null, "rb_global": null, "delta_rb": null
    },
    {
      "house": 2, "n_events": 2, "n_positive": 0, "n_negative": 2,
      "corr_global": null, "corr_domain": null,
      "improvement_corr": null
    },
    {
      "house": 5, "n_events": 57, "n_positive": 51, "n_negative": 1,
      "corr_global": 0.2002, "corr_domain": 0.3497,
      "cohens_d_global": null, "cohens_d_domain": null,
      "improvement_corr": 0.1495,
      "mw_p_domain": null, "rb_domain": null, "rb_global": null, "delta_rb": null
    },
    {
      "house": 6, "n_events": 10, "n_positive": 0, "n_negative": 9,
      "corr_global": -0.1230, "corr_domain": -0.1173,
      "improvement_corr": 0.0056
    },
    {
      "house": 7, "n_events": 93, "n_positive": 81, "n_negative": 9,
      "corr_global": 0.0239, "corr_domain": 0.0406,
      "cohens_d_global": 0.0624, "cohens_d_domain": 0.0547,
      "improvement_corr": 0.0167,
      "mw_p_domain": 0.500, "mw_p_global": 0.147,
      "rb_domain": -0.00137, "rb_global": -0.21536, "delta_rb": 0.21399
    },
    {
      "house": 8, "n_events": 34, "n_positive": 0, "n_negative": 34,
      "corr_global": null, "corr_domain": null, "improvement_corr": null
    },
    {
      "house": 9, "n_events": 66, "n_positive": 14, "n_negative": 4,
      "corr_global": -0.0626, "corr_domain": -0.0455,
      "cohens_d_global": -0.2210, "cohens_d_domain": -0.1748,
      "improvement_corr": 0.0171,
      "mw_p_domain": 0.779, "mw_p_global": 0.677,
      "rb_domain": 0.2500, "rb_global": 0.1429, "delta_rb": 0.1071
    },
    {
      "house": 10, "n_events": 250, "n_positive": 231, "n_negative": 4,
      "corr_global": 0.0737, "corr_domain": 0.0131,
      "cohens_d_global": 0.5668, "cohens_d_domain": 0.0559,
      "improvement_corr": -0.0606,
      "mw_p_domain": 0.412, "mw_p_global": 0.141,
      "rb_domain": -0.0660, "rb_global": -0.3149, "delta_rb": 0.2489
    },
    {
      "house": 12, "n_events": 12, "n_positive": 0, "n_negative": 5,
      "corr_global": -0.0697, "corr_domain": -0.3774,
      "improvement_corr": -0.3077
    }
  ]
}
```

---

## Lectura rápida — señales más fuertes

| Señal | Casa | Valor | Interpretación |
|-------|------|-------|----------------|
| Mejor Δcorr | H05 | +0.150 | Creatividad: dominio mejora sobre global |
| Mejor delta_rb | H07 | +0.214 | Relaciones: filtrado corrige sesgo del global |
| Mejor delta_rb | H10 | +0.249 | Carrera: filtrado reduce error global −0.315 → −0.066 |
| Mayor efecto | H10 | d=+0.567 | Carrera: separación pos/neg significativa |
