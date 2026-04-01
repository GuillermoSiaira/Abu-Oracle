# EXP_003 — HF_v3 Global Correlation

## Resultado
- Pearson r = 0.121 (todos los eventos, n=527)
- Pearson r = 0.133 (no-neutral, n=446)
- Cohen's d = 0.441 (positivo vs negativo)
- Media HF positivo: −12.010
- Media HF negativo: −13.098
- Separación media: +1.088 unidades HF

## Dataset
- 527 eventos biográficos · 26 sujetos
- Rango: 1855–2021
- Fuentes: 425 birth certificate / 49 biography / 53 curados GS
- 25 tipos de evento · 377 positivos / 69 negativos / 81 neutrales

## Interpretación
Señal estadística presente pero atenuada por mezcla de dominios.
El HF global suma resonancias de todas las casas — la señal de casa específica
queda diluida. Ver [[H01_domain_specificity]] — Axioma 8.

El valor absoluto de HF es negativo para todos los grupos (escala relativa a
posición natal). La diferencia clave es el delta entre grupos, no el absoluto.

## Fórmula usada
```python
HF_weighted = w_h * hf_harmony + w_t * hf_tension + w_c * hf_conjunction
# pesos: w_h = -1.0, w_t = -1.0, w_c = +2.5
```

## Limitaciones
- Desbalance valence: 377 positivos vs 69 negativos (ratio 5.5:1)
- No normalizado por sujeto (z-score por sujeto mejoraría la señal)
- Mezcla de dominios suprime la señal de casas específicas

## Artefactos
- `abu-oracle-research/data/results/correlation_v3_global.json`
- `abu-oracle-research/figures/hf_valence_distribution.png`
- `data/biographical_events/events_detailed.csv`

## Links
[[EXP_004_HF_v6_domain]] — experimento siguiente con filtrado por dominio
[[AXIOMATICS_OF_HEAVENS_v0_4]] — Axioma 8: Especificidad de Dominio
