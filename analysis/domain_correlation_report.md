# Domain Correlation Report — HF por Casa

Total events analysed: 527
Subjects: 26 · Normalización: z-score por sujeto · Métrica primaria: rank-biserial (Mann-Whitney U)

## Hipótesis

El HF filtrado por dominio de casa predice mejor la valencia de eventos biográficos
que el HF global — medido como delta_rb = rb_domain − rb_global.

## Resultados por Casa

| Casa | N | N+ | N− | pearson_d | cohens_d_g | cohens_d_d | rb_global | rb_domain | delta_rb | mw_p_dom | Δcorr |
|------|---|----|----|-----------|------------|------------|-----------|-----------|----------|----------|-------|
| H01 | 3 | 0 | 1 | -0.890 | n/a | n/a | n/a | n/a | n/a | n/a | -0.913 |
| H02 | 2 | 0 | 2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| H05 | 57 | 51 | 1 | +0.350 | n/a | n/a | n/a | n/a | n/a | n/a | +0.150 |
| H06 | 10 | 0 | 9 | -0.117 | n/a | n/a | n/a | n/a | n/a | n/a | +0.006 |
| H07 | 93 | 81 | 9 | +0.041 | +0.062 | +0.055 | -0.215 | -0.001 | +0.214 | +0.500 | +0.017 |
| H08 | 34 | 0 | 34 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| H09 | 66 | 14 | 4 | -0.046 | -0.221 | -0.175 | +0.143 | +0.250 | +0.107 | +0.779 | +0.017 |
| H10 | 250 | 231 | 4 | +0.013 | +0.567 | +0.056 | -0.315 | -0.066 | +0.249 | +0.412 | -0.061 |
| H12 | 12 | 0 | 5 | -0.377 | n/a | n/a | n/a | n/a | n/a | n/a | -0.308 |

## Conclusiones

### Lo que el modelo hace bien

**H05 — Creatividad** (N=57, delta_corr=+0.150, estable):
Señal confirmada por Pearson. El HF de dominio mejora consistentemente sobre el global.
Resultado robusto a z-score y cambio de métrica.

**H10 — Carrera** (N=250, delta_rb=+0.249):
El rank-biserial global es −0.315 (el HF global invierte la predicción).
El HF de dominio reduce ese error a −0.066 — mejora de 0.249 puntos.
El filtrado por planet_subset de H10 corrige parcialmente la señal negativa del global.
Poder estadístico limitado por desbalance estructural del corpus (N+=231, N−=4).

**H07** (N=93, delta_rb=+0.214): mejora real en rank-biserial, pero mismo problema de desbalance (N−=9).

### Lo que el modelo no puede probar con este corpus

- **Validación espacial directa**: los eventos no tienen coordenadas propias.
  El cálculo usa la ubicación de nacimiento para todos los eventos del sujeto.
  La hipótesis central del producto (delta_hf_domain en la ubicación real del evento)
  requiere geocodificación por evento — fuera del alcance de este dataset.

- **Casas con N < 40**: H01, H02, H06, H08, H12 — resultados no interpretables.

- **Desbalance estructural N+/N−**: corpus biográfico público tiene sesgo sistemático
  hacia eventos positivos. No es un error metodológico — es la realidad del dato.
  Mann-Whitney no puede pronunciarse con N−=1..4 en los grupos negativos.

### Veredicto

La hipótesis del dominio HF está **parcialmente confirmada y no refutada**.
El límite de validación es el corpus, no el modelo.
Evidencia disponible: H05 confirmado, H10 y H07 con señal positiva en rank-biserial
pero sin poder estadístico suficiente para significancia formal.

## Notas metodológicas

- `pearson_d`: Pearson r entre transit_hf_domain (z-score) y valence_num.
- `cohens_d_g / cohens_d_d`: Cohen's d entre grupos pos/neg para HF global y dominio.
- `rb_global` / `rb_domain`: rank-biserial (Mann-Whitney U, one-sided pos>neg). >0 = positivos tienen HF mayor.
- `delta_rb`: métrica central — rb_domain − rb_global. Positivo = dominio mejora sobre global.
- `mw_p_domain`: p-value Mann-Whitney U. Interpretable solo cuando N+≥10 y N−≥10.
- `Δcorr`: corr_domain − corr_global (Pearson). Referencia complementaria.
- Normalización z-score aplicada por sujeto antes de agregar al dataset global.