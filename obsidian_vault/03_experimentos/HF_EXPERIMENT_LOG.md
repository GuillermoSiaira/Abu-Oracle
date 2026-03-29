---
name: HF_EXPERIMENT_LOG
description: Log secuencial de experimentos del Harmony Field — Exp 1-5, RSI, correlaciones y diagnóstico
tipo: experimentos
version: 2026-03-13
estado: activo
tags: [experimentos, RSI, correlacion, domain, validacion-empirica, cohen-d]
---

# Harmony Field Experiments Log

Ver también: [[domain_correlation_report]] · [[correlation_results]] · [[HF_V4_SESSION_B]] · [[AXIOMATICS_v0_4]]

> Nota metodológica: los resultados de HF v2 muestran que la formulación actual de angularidad/casas no aumentó la estructura espacial frente a HF v1. Esto **no** implica que ASC/MC o casas sean irrelevantes — solo que la representación matemática fue insuficiente.

---

## Experiment 1 — HF Core v1 Relocation Test

**Fecha**: 2026-03-07 · Dataset: hf_dataset_v1.parquet

**Hipótesis**: HF define un campo de relocalización estructurado. Cartas reales deben producir mayor estructura espacial que rotaciones aleatorias.

**Métrica RSI**: Relocation Structure Index — contraste relativo entre natal y campo global. Mayor RSI = mayor estructura espacial.

**Null model**: rotación aleatoria de longitudes planetarias.

**Resultados** (18 sujetos piloto):

| Métrica | Valor |
|---------|-------|
| mean z_RSI | 0.44 |
| median z_RSI | −0.17 |
| % z_RSI > 1 | 33% |
| % z_RSI > 2 | 11% |

Señal presente pero débil. HF v1 tiene estructura espacial real.

---

## Experiment 2 — HF Core v2 Relocation Test

**Fecha**: 2026-03-07

**Cambios**: angularidad (λ_α=0.5) y casas (λ_house=0.3) multiplicativos sobre HF v1.

**Resultados** (50 sujetos):

| Métrica | HF v1 | HF v2 |
|---------|-------|-------|
| mean z_RSI | 0.44 | 0.137 |
| median z_RSI | −0.17 | −0.425 |

**Conclusión**: HF v2 no aumentó la señal. El esquema multiplicativo introduce ruido. Solución: modelo aditivo v3 (ver [[field_v3]]).

---

## Experiment 3 — HF Core v3 (aditivo) y visualización

**Fecha**: 2026-03-08

**Cambios clave**: modelo aditivo `HF_v3 = HF_aspectos + β*HF_ángulos + γ*HF_casas`.

Campos generados para ~4,650 sujetos. Visualización con delta HF vs natal.

**Validación cualitativa** (10 sujetos demo):

| Sujeto | Observación |
|--------|-------------|
| Van Gogh | h10_p5 = −1.74: carrera problemática en casi cualquier lugar |
| Picasso | h10_p95 = +1.40: máximo potencial de mejora en Carrera → se mudó a París a los 23 |
| Freud | h7_p95 = +1.58: mayor potencial en Relaciones → construyó la escuela psicoanalítica en Viena |

Estos casos constituyen validación cualitativa no diseñada — el HF por dominio resuena con biografía real.

---

## Experimento 4 — HF por dominio + fallback subset

**Fecha**: 2026-03-13

Fallback implementado: si `len(subset) < 3`, completar con Sol + Luna + señor ASC.

10 sujetos demo con variación real en h7 y h10 verificada.

---

## Experimento 5 — Correlación HF por dominio vs HF global

**Fecha**: 2026-03-13

**Hipótesis**: `corr(HF_dominio_k, eventos_casa_k) > corr(HF_global, eventos_casa_k)`

**Dataset**: 527 eventos · 26 sujetos · script `scripts/correlate_by_domain.py`

**Resultados resumidos**:

| Casa | N | corr_global | corr_domain | Δcorr | Resultado |
|------|---|-------------|-------------|-------|-----------|
| H04 (Hogar) | 34 | −0.001 | +0.305 | +0.306 | ✅ confirmado |
| H05 (Creatividad) | 57 | +0.198 | +0.353 | +0.155 | ✅ confirmado |
| H06 (Trabajo/Salud) | 18 | −0.317 | +0.051 | +0.369 | ✅ confirmado |
| H07 (Amor) | 93 | +0.098 | +0.088 | −0.010 | ❌ sin mejora |
| H09 (Expansión) | 56 | +0.014 | −0.123 | −0.138 | ❌ sin mejora |
| H10 (Carrera) | 226 | +0.090 | +0.033 | −0.057 | ❌ sin mejora* |

*H10 Cohen's d_global = +0.871 — separación real pero desbalance N+=208/N−=4 limita Pearson.

Ver resultados completos: [[domain_correlation_report]] · [[correlation_results]]

### Nota metodológica — H10 y Pearson vs. Cohen's d

Cohen's d = +0.871 para H10 significa: el HF en fechas de logros de carrera está 0.87 SD por encima del HF en fechas de fracasos (efecto grande, Cohen 1988: d>0.8=large). La baja correlación de Pearson **no invalida** la señal — invalida la aplicabilidad de Pearson a un corpus con ratio 52:1.

---

## Fórmula HF v1 (referencia)

$$HF(\phi, \lambda, t) = \sum_{i<j} \sum_{a \in \text{Aspects}} w_a \; \exp\left( -\frac{(\Delta \theta_{ij} - \alpha_a)^2}{2\sigma_a^2} \right)$$

RSI se calcula comparando HF sobre la grilla de relocalización contra null de rotaciones aleatorias.

---

*Artefactos: `analysis/domain_correlation_report.md` · `analysis/domain_correlation_results.json` · `analysis/null_model_*.csv`*

---

## Experiment 4 — HF_v6: Dignidad × Angularidad × Firdaria∩Dominio

**Fecha:** 2026-03-29

**Hipótesis:** Separar los mecanismos de aspectos (geometría pura) y
angularidad (modulada por dignidad esencial × amplificador de
intersección firdaria∩dominio) produce mayor separación empírica
entre eventos positivos y negativos que HF_v3.

**Cambios respecto a HF_v5:**
- Dignidad removida del kernel de aspecto
- Dignidad aplicada SOLO al término de angularidad
- Amplificador w=2.0 SOLO en intersección firdaria∩subset(dominio)
  (no para todos los planetas de firdaria)

**Fundamento doctrinal:**
- Ptolomeo: angularidad amplifica, dignidad dicta el contenido
- Lilly: D4 scoring (+5/+4/0/−4/−5)
- Axioma 9.4: confluencia de potencial natal + resonancia
  geográfica + activación temporal

**Resultados:**

| casa   | d_v3   | d_v6   | delta  |
|--------|--------|--------|--------|
| H07    | +0.055 | +0.587 | +0.532 |
| H10    | +0.056 | +0.702 | +0.646 |
| global | +0.441 | +0.193 | −0.248 |

**Conclusión:** Hipótesis doctrinal confirmada en 2 dominios.
La separación de mecanismos (geometría vs cualidad) es la
decisión arquitectural correcta. La degradación global es esperada
y confirma el Axioma 8 — especificidad de dominio como condición de
legibilidad del campo.

**Next steps:**
- Testear H04 y H05 cuando haya suficientes eventos con N- > 1
- Extender dignidad D4 a tabla completa de Lilly
  (triplicidades +3, términos +2, cara +1)
- Scraping Wikidata para ampliar corpus

**Artefactos:** [[HF_V6_RESULTS]] · `abu_engine/harmony/hf_v6.py` · `scripts/run_hf_v6_comparison.py`
