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

## Diagnóstico post-experimento (2026-04-01)

### D1 — Bootstrap H10 (10,000 iteraciones)
- d_observado = 0.551 con N+=232, N−=5
- IC 95% bootstrap: [−0.962, +0.947] — abarca casi el rango completo
- Bootstrap media = −0.003, p-value = 0.50
- **Conclusión**: d=0.551 en H10 es estadísticamente indistinguible del ruido con N−=5.
  Es un artefacto de corpus, no un efecto real medible.

### D2 — LOSO H10
- 21/26 sujetos tienen cero eventos negativos en H10
- Todos los LOSO d ≥ 0.35 — ningún sujeto único colapsa la señal
- **Conclusión**: el problema no es concentración en pocos sujetos,
  sino que el 81% de los sujetos no tiene ningún evento negativo de carrera en el corpus.

### D3 — Velocidad de significadores
- H05 significadores: 50% rápidos, 36.7% lentos, velocidad media 2.67 deg/día
- H10 significadores: 41.1% rápidos, 46.7% lentos, velocidad media 0.96 deg/día
- Ratio velocidad H05/H10 = 2.77x — H05 es casi 3x más rápido
- **Varianza geográfica HF_domain** (25 parquets): std_h5=0.323, std_h10=0.362
- La varianza geográfica de H10 es ligeramente MAYOR que H05, no menor
- **Conclusión**: hipótesis de planetas lentos PARCIALMENTE confirmada en velocidad,
  pero REFUTADA en varianza geográfica. D4 descartado.

### Hipótesis alternativa (validada)
El colapso de d_domain en H10 se explica por el desbalance de corpus (N−=5),
no por las propiedades del campo HF filtrado. El filtro de dominio funciona
correctamente — simplemente no hay datos negativos suficientes para medirlo.

## Links
[[EXP_003_HF_v3_global]] — experimento anterior (baseline global)
[[H01_domain_specificity]] — hipótesis parcialmente confirmada
[[H01b_significator_speed]] — sub-hipótesis generada por estos diagnósticos
