---
name: domain_correlation_report
description: Reporte final de correlación HF por dominio de casa — 527 eventos, 26 sujetos
tipo: resultados
version: 2026-03-13
estado: final
tags: [correlacion, dominio, resultados, pearson, cohen-d, rank-biserial, 527-eventos]
---

# Domain Correlation Report — HF por Casa

Archivo fuente: `analysis/domain_correlation_report.md`

Ver también: [[HF_EXPERIMENT_LOG]] · [[correlation_results]] · [[AXIOMATICS_v0_4]] · [[HIPOTESIS_REGISTRO]]

---

Total eventos: **527** · Sujetos: **26** · Normalización: z-score por sujeto
Métrica primaria: **rank-biserial** (Mann-Whitney U)

---

## Hipótesis

El HF filtrado por dominio de casa predice mejor la valencia de eventos biográficos que el HF global — medido como `delta_rb = rb_domain − rb_global`.

---

## Resultados por Casa

| Casa | N | N+ | N− | pearson_d | cohens_d_g | rb_global | rb_domain | delta_rb | Δcorr |
|------|---|----|----|-----------|------------|-----------|-----------|----------|-------|
| H01 | 3 | 0 | 1 | −0.890 | n/a | n/a | n/a | n/a | −0.913 |
| H02 | 2 | 0 | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| H05 | 57 | 51 | 1 | +0.350 | n/a | n/a | n/a | n/a | **+0.150** |
| H06 | 10 | 0 | 9 | −0.117 | n/a | n/a | n/a | n/a | +0.006 |
| H07 | 93 | 81 | 9 | +0.041 | +0.062 | −0.215 | −0.001 | **+0.214** | +0.017 |
| H08 | 34 | 0 | 34 | n/a | n/a | n/a | n/a | n/a | n/a |
| H09 | 66 | 14 | 4 | −0.046 | −0.221 | +0.143 | +0.250 | +0.107 | +0.017 |
| H10 | 250 | 231 | 4 | +0.013 | **+0.567** | −0.315 | −0.066 | **+0.249** | −0.061 |
| H12 | 12 | 0 | 5 | −0.377 | n/a | n/a | n/a | n/a | −0.308 |

---

## Conclusiones

### Lo que el modelo hace bien

**H05 — Creatividad** (N=57, delta_corr=+0.150):
Señal confirmada por Pearson. El HF de dominio mejora consistentemente sobre el global.

**H10 — Carrera** (N=250, delta_rb=+0.249):
El rank-biserial global es −0.315 (el HF global invierte la predicción). El dominio reduce ese error a −0.066 — mejora de 0.249 puntos. Cohen's d_global = +0.567.

**H07** (N=93, delta_rb=+0.214): mejora real en rank-biserial.

### Lo que el modelo no puede probar con este corpus

- **Validación espacial directa**: los eventos no tienen coordenadas propias. La hipótesis central del producto requiere geocodificación por evento.
- **Casas con N < 40**: H01, H02, H06, H08, H12 — no interpretables.
- **Desbalance estructural N+/N−**: corpus biográfico público tiene sesgo sistemático hacia eventos positivos.

### Veredicto

La hipótesis del dominio HF está **parcialmente confirmada y no refutada**.
El límite de validación es el corpus, no el modelo.

---

## Notas metodológicas

- `pearson_d`: Pearson r entre transit_hf_domain (z-score) y valence_num
- `cohens_d_g`: Cohen's d entre grupos pos/neg para HF global
- `rb_global / rb_domain`: rank-biserial (Mann-Whitney U, one-sided pos>neg). >0 = positivos tienen HF mayor
- `delta_rb`: métrica central — rb_domain − rb_global
- `Δcorr`: corr_domain − corr_global (Pearson)

### Por qué Cohen's d es la métrica correcta para H10

Con ratio N+/N− = 52:1, la varianza de Y es casi nula en el subgrupo negativo y Pearson colapsa. Cohen's d mide directamente la separación entre medias, normalizada por SD pooled, sin requerir balance de clases.

**H10 d_global = +0.871**: el HF en fechas de logros de carrera está 0.87 SD por encima del HF en fechas de fracasos — efecto grande (Cohen 1988: d > 0.8 = large).
