---
name: NOTEBOOK_PROMPT_HF_V5_RESULTS
description: Resultados y diagnóstico del experimento HF_v5 — prompt listo para notebook de análisis
tipo: experimento
version: 2026-03-29
estado: negativo — HF_v5 no mejora HF_v3
tags: [hf_v5, cohens_d, dignidad_esencial, firdaria, correlacion, notebook]
---

# HF_v5 — Resultados del correlador (527 eventos, 26 sujetos)

## Tabla comparativa

| Casa    | n_eventos | cohens_d_v3 | cohens_d_v5 | delta   |
|---------|-----------|-------------|-------------|---------|
| H04     | 0         | n/a         | n/a         | n/a     |
| H05     | 57        | n/a         | n/a         | n/a     |
| H07     | 93        | +0.055      | +0.038      | −0.017  |
| H10     | 250       | +0.056      | −0.379      | −0.435  |
| global  | 529       | +0.441      | −0.064      | −0.505  |

> H04 = 0 eventos en `biographical_events_v2` con `house_domain=4`.
> H05: N−=1, Cohen's d no computable.

## Fórmula HF_v5

```
HF_v5 = Σ_{pares} pair_score(i, j, asp) + 0.6 * angularity_sum

pair_score(i, j) = kernel(δθ, σ=4°) × (dignity_i + dignity_j) × w_firdaria

kernel = exp(−δθ² / 2σ²)
dignity ∈ {domicile:+5, exaltation:+4, peregrine:0, detriment:−4, fall:−5}
w_firdaria = 1.5 si algún planeta del par está en el período firdaria activo, else 1.0
```

- Dignidades: sistema tradicional (7 planetas clásicos)
- Firdaria: `get_current_fardar(birth_dt, is_diurnal, query_date=event_dt)`
- Angularidad: calculada con `calculate_houses(birth_dt, b_lat, b_lon)` en ubicación natal

## Diagnóstico

**Resultado**: HF_v5 es significativamente peor que HF_v3.
El Cohen's d global cae de +0.441 a −0.064 (delta = −0.505). H10 invierte el signo.

**Hipótesis sobre la causa**:

El término `(dignity_i + dignity_j)` oscila entre −10 y +10 con media cercana a cero.
Los planetas peregrinos (dignity=0) anulan el par — correcto doctrinalmente.
Pero los pares con planetas debilitados (detrimento/caída) generan scores **negativos**
que no correlacionan con la valencia del evento (un evento negativo puede tener
significadores en domicilio, y uno positivo en detrimento).

La dignidad esencial describe la *calidad intrínseca* del planeta, no su *activación favorable*.
Mezclar dignidad con resonancia geométrica invierte la señal en lugar de amplificarla.

**Conclusión**: la señal de HF_v3 (resonancia posicional pura, sin dignidades) no mejora
al ponderar por dignidad esencial de los significadores de dominio.

## Hipótesis alternativas para próximos experimentos

1. **Dignidad como filtro binario**: incluir el par solo si `max(dignity_i, dignity_j) > 0`
   (al menos un planeta digno), ignorarlo si ambos están debilitados.
2. **Dignidad como multiplicador en angularidad**: ponderar `angularity_sum` por la
   dignidad del planeta más angular, no los pares.
3. **Firdaria como `planet_subset` puro**: reducir los significadores del dominio
   a solo los planetas activos en firdaria (mayor + sub), sin cambiar el kernel.
4. **Firdaria × dominio solo cuando coinciden**: amplificar solo si el planeta firdaria
   también es significador de la casa del evento (intersección, no unión).

## Archivos del experimento

| Archivo | Descripción |
|---------|-------------|
| `abu_engine/harmony/hf_v5.py` | Implementación completa de HF_v5 |
| `scripts/run_hf_v5_comparison.py` | Runner: 529 eventos, z-score por sujeto, tabla comparativa |
| `analysis/domain_correlation_results.json` | Referencia v3 (fuente de cohens_d_v3) |
| `data/biographical_events_v2/` | Dataset de eventos con `house_domain` pre-asignado |
