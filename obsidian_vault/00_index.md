---
name: 00_index
description: Mapa central del vault — índice navegable de todos los documentos
tipo: index
version: 2026-03-28
estado: activo
tags: [index, mapa, navegacion]
---

# Abu Oracle — Knowledge Vault

Motor astrológico computacional con campo escalar geográfico (Harmony Field) e interpretación por agentes LLM (Lilly).

**Proyecto**: `D:\projects\ai-oracle` · **Producción**: `app.abu-oracle.com`

---

## 01 — Fórmula

| Documento | Descripción |
|-----------|-------------|
| [[resonance_weights]] | Constantes de aspectos, sigmas y GROUP_WEIGHTS en producción (w_h=−1.0, w_t=−1.0, w_c=+2.5) |
| [[field_v3]] | Fórmula completa `HF_total_v3 = HF_aspects + β*HF_angles + γ*HF_houses` (β=0.6, γ=0.3) |
| [[HF_CORE_V2_DESIGN]] | Diseño v2 multiplicativo (archivado) — diagnóstico de por qué no funcionó |
| [[HF_V4_SESSION_B]] | Spec HF v4 pesos diferenciados + correlador de eventos biográficos |

---

## 02 — Doctrina

| Documento | Descripción |
|-----------|-------------|
| [[AXIOMATICS_v0_4]] | **Activo** — Axiomática v0.4 con Especificidad de Dominio (Ax. 8) y Activación Condicionada (Ax. 9) |
| [[AXIOMATICS_v0_3]] | Archivado — v0.3 con axiomas de campo de relocalización y Abu Mashar |

---

## 03 — Experimentos

| Documento | Descripción |
|-----------|-------------|
| [[HF_EXPERIMENT_LOG]] | Log secuencial Exp 1-7: RSI, v1/v2/v3, correlación por dominio, validación cualitativa, diagnósticos D1-D3 |
| [[EXP_003_HF_v3_global]] | EXP_003 — Correlación global HF_v3 (r=0.121, d=0.441, n=527) |
| [[EXP_004_HF_v6_domain]] | EXP_004 — Correlación por dominio + diagnósticos D1/D2/D3 — H05 ✅, H10 corpus insuficiente |
| [[NOTE_SESSION_B]] | Referencia y resumen de Session B (ver [[HF_V4_SESSION_B]]) |

---

## 04 — Hipótesis

| Documento | Descripción |
|-----------|-------------|
| [[HIPOTESIS_REGISTRO]] | H01–H07: estructura espacial, signos de pesos, especificidad de dominio, validación directa, firdaria temporal, convergencia |
| [[H01_domain_specificity]] | H01 — Especificidad de dominio: confirmada H05 ✅, no testeable H10 (N−=5) |
| [[H01b_significator_speed]] | H01b — Eficacia del filtro en función de velocidad orbital: parcial en velocidad, refutada en varianza |

---

## 05 — Resultados

| Documento | Descripción |
|-----------|-------------|
| [[domain_correlation_report]] | Reporte final — 527 eventos, 26 sujetos. H05 ✅ H07 ✅ H10 señal en rb |
| [[domain_correlation_baseline]] | Baseline pre-dominio — referencia para cuantificar mejoras |
| [[correlation_results]] | Datos crudos JSON — todos los valores exactos de corr/d/rb por casa |

---

## Fórmula de producción (resumen)

```
HF_total_v3 = HF_aspects + 0.6 * HF_angles + 0.3 * HF_houses

HF_aspects = −1.0 * (sextile + trine)
           + −1.0 * (square + opposition)
           + +2.5 * conjunction

# Filtrado por dominio:
planet_subset = house_significators(natal, house=k)
```

Fuente: [[resonance_weights]] · [[field_v3]]

---

## Hallazgos clave

1. **H05 Creatividad**: Δcorr=+0.150 — confirmado con Pearson
2. **H10 Carrera**: Cohen's d_global=+0.871 (efecto grande) · delta_rb=+0.249 · Pearson limitado por N−=4
3. **H07 Relaciones**: delta_rb=+0.214 — señal real en rank-biserial
4. **Pesos óptimos contraintuitivos**: w_harmony=−1.0, w_tension=−1.0, w_conjunction=+2.5. Explicación: campo global mezcla dominios → inversión de señal. El filtrado por dominio es la solución correcta, no ajustar más los pesos.

---

## Hipótesis pendientes de prueba

- [[HIPOTESIS_REGISTRO#H04 — Hipótesis de Validación Espacial Directa|H04]] — Corpus georeferenciado (lat/lon por evento)
- [[HIPOTESIS_REGISTRO#H05 — Firdaria como Filtro Temporal del HF|H05]] — Firdaria como planet_subset temporal
- [[HIPOTESIS_REGISTRO#H06 — Convergencia Temporal como Amplificador|H06]] — Profección + firdaria + tránsito lento convergentes
- [[HIPOTESIS_REGISTRO#H07 — HF × Tránsito × Fecha|H07]] — Interacción lugar × tiempo × dominio

---

## 06 — Engineering

| Documento | Descripción |
|-----------|-------------|
| [[finops_milp]] | FinOps MILP — entry point, links a research/finops/ |
| [[FINOPS_MILP_VARIABLES]] | Variables de decisión técnicas — max_tokens por ruta, modelos |

---

## 07 — Sonic Field

| Documento | Descripción |
|-----------|-------------|
| [[sonic_field/SONIC_FIELD_SPEC\|SONIC_FIELD_SPEC]] | Spec fundacional — doctrina Cousto, arquitectura 3 capas, mapeo astrológico→síntesis |
| [[sonic_field/sonic_capa1_natal\|sonic_capa1_natal]] | ✅ Capa 1 implementada y validada — Firma Sonora Natal con Tone.js |
| [[sonic_capa2_transitos]] | ✅ Capa 2 implementada — Tránsitos activos como capa aditiva sobre la firma natal |

---

## Convenciones del motor

| Parámetro | Valor |
|-----------|-------|
| Sistema de casas | Placidus |
| Referencial | Topocéntrico |
| Efemérides | Swiss Ephemeris DE440s |
| Grilla relocalización | 2.5°×2.5°, lat∈[−70,70], lon∈[−180,175] (~9,425 pts) |
| Planetas activos | Sol, Luna, Merc, Venus, Marte, Júpiter, Saturno, Urano, Neptuno, Plutón + ASC + MC |
| Aspectos | 0° / 60° / 90° / 120° / 180° |
