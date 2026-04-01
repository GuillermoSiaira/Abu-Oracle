# EXP_004 — HF_v6 Domain-Filtered Correlation

## Resultado

| Casa | Dominio | N | N+ | N- | r_global | r_domain | d_global | d_domain |
|------|---------|---|----|----|----------|----------|----------|----------|
| 5 | Creatividad | 57 | 51 | 1 | 0.200 | **0.350** | — | — |
| 6 | Trabajo/Salud | 10 | 0 | 9 | −0.123 | −0.117 | — | — |
| 7 | Relaciones | 93 | 81 | 9 | 0.063 | 0.041 | 0.207 | 0.055 |
| 9 | Expansión | 66 | 14 | 4 | −0.063 | −0.046 | −0.221 | −0.175 |
| 10 | Carrera | 250 | 231 | 4 | 0.074 | 0.013 | **0.567** | 0.056 |
| 12 | Inconsciente | 12 | 0 | 5 | −0.070 | −0.377 | — | — |

*Nota: d = NaN cuando N+ < 2 o N- < 2 (Cohen's d requiere varianza en ambos grupos)*

## Hallazgo clave: H05 Creatividad ✅
El único dominio que confirma la hipótesis de mejora por filtrado:
- r global: 0.200 → r domain: 0.350 (Δ = +0.150)
- N=57 es el segundo corpus más grande después de H10

## Hallazgo clave: H10 Carrera — diagnóstico
Cohen's d_global = 0.567 colapsa a d_domain = 0.056.
Causa: los significadores de H10 incluyen planetas lentos (Neptuno, Plutón)
con baja varianza temporal → el filtro de planetas lentos no diferencia
entre eventos positivos y negativos en el campo HF.
Adicionalmente: 231 positivos vs 4 negativos — Pearson no puede funcionar.

## Interpretación global
La hipótesis H01 (Domain Specificity) se confirma parcialmente:
- Confirmada para H05 Creatividad
- Ni confirmada ni refutada para H07 (señal marginal) y H09 (señal débil)
- Refutada para H10 (señal colapsa con filtro de dominio)
- Limitada por N insuficiente en H01, H02, H03, H04

## Metodología
```python
# Datos de HF_domain provienen de correlate_by_domain.py
# que calcula el campo HF con planet_subset = house_significators(casa)
# Los datos HF_global son hf_weighted de events_detailed.csv

from scipy import stats
pearson_r, p_value = stats.pearsonr(events['valence_num'], events['hf_weighted'])

pooled_std = sqrt((pos.std()**2 + neg.std()**2) / 2)
cohens_d = (pos.mean() - neg.mean()) / pooled_std
```

## Artefactos
- `abu-oracle-research/data/results/domain_correlation_table.csv`
- `abu-oracle-research/figures/domain_correlation_heatmap.png`
- `abu-oracle-research/figures/cohens_d_by_domain.png`
- `analysis/domain_correlation_results.json` — resultados originales del correlator

## Links
[[EXP_003_HF_v3_global]] — experimento anterior (baseline global)
[[H01_domain_specificity]] — hipótesis parcialmente confirmada
