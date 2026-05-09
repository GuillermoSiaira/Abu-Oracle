---
name: 00_index
description: Mapa central del vault — índice navegable de todos los documentos
tipo: index
version: 2026-04-25
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
| [[hf_v6]] | HF v6 — scoring con pesos diferenciados por grupo, usado en validación H10/H07 |
| [[HF_CORE_V2_DESIGN]] | Diseño v2 multiplicativo (archivado) — diagnóstico de por qué no funcionó |
| [[HF_V4_SESSION_B]] | Spec HF v4 pesos diferenciados + correlador de eventos biográficos |
| [[hf_embedding_36d]] | Embedding 36D — vector circular 24D + armónicos 8D + métricas HF 4D (usado en hf_dataset_v2.parquet) |

---

## 02 — Doctrina

| Documento | Descripción |
|-----------|-------------|
| [[AXIOMATICS_OF_HEAVENS_v0_4]] | **Redirect** — Tabla resumen axiomas + links a versión vault y repo |
| [[AXIOMATICS_v0_4]] | **Activo** — Axiomática v0.4 con Especificidad de Dominio (Ax. 8) y Activación Condicionada (Ax. 9) |
| [[AXIOMATICS_v0_3]] | Archivado — v0.3 con axiomas de campo de relocalización y Abu Mashar |
| [[persian_techniques]] | Técnicas persas+helenísticas: Sect, Profección, Firdaria, Lotes, Tránsitos Lunares, Ciclos |

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
| [[HIPOTESIS_REGISTRO]] | H01–H09: estructura espacial, signos de pesos, especificidad, convergencia, ontología del campo, código dual |
| [[H01_domain_specificity]] | H01 — Especificidad de dominio: confirmada H05 ✅, no testeable H10 (N−=5) |
| [[H01b_significator_speed]] | H01b — Eficacia del filtro en función de velocidad orbital |
| [[AXIOM_0_MECANISMO]] | **H08+H09** — Axioma 0: ontología del campo continuo, invariante natal, código dual $\{\pi_{natal}, \mathcal{N}\}$, transformación hermética |

---

## 05 — Resultados

| Documento | Descripción |
|-----------|-------------|
| [[HF_V6_RESULTS]] | Resultados HF v6 — Cohen's d_global H10=+0.702, H07=+0.587; disclaimer v3≠v6 |
| [[MUNDANA_H_A_RESULTADOS]] | H_mundana_A ✅ — conj. J-S p=5×10⁻⁶ density=4.3×; Fase 12 pipeline completo |
| [[REVISION_2026_04_01]] | Revisión numérica 2026-04-01 — 5 inconsistencias H10/H07 diagnosticadas y resueltas |
| [[domain_correlation_report]] | Reporte final — 527 eventos, 26 sujetos. H05 ✅ H07 ✅ H10 señal en rb |
| [[domain_correlation_baseline]] | Baseline pre-dominio — referencia para cuantificar mejoras |
| [[correlation_results]] | Datos crudos JSON — todos los valores exactos de corr/d/rb por casa |
| [[wikidata_candidates]] | Candidatos Wikidata para ampliar corpus biográfico — criterios y sujetos propuestos |

---

## 05b — Validación Lilly (Blind Validation)

| Documento | Descripción |
|-----------|-------------|
| [[BLIND_VALIDATION_EXPERIMENT]] | Protocolo carta ciega — H08 (inferencia doctrinal sin nombre) |
| [[BV_001_trump]] | BV_001 — Mr. X (Trump) · 4/5 dims ✅ · 2026-04-03 |

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

## 06b — Estrategia y Publicación

| Documento | Descripción |
|-----------|-------------|
| [[ANTHROPIC_STRATEGY]] | Estrategia Anthropic — 3 ejes publicables + Anthology Fund (⚡ ejecutable con 30d logs) |
| [[grant_proposal_ResearchHub]] | 4 papers candidatos ResearchHub — FinOps, Blind Validation, HF estadístico, Axioma 0 |

---

## 06 — Engineering

| Documento | Descripción |
|-----------|-------------|
| [[ARCHITECTURE]] | **Hub central** — contrato Abu↔Lilly, AbuContext, rutas Lilly, Event System, capas del sistema |
| [[COST_OPTIMIZATION]] | Estrategia costos API — modelos por ruta, fases A-E, pricing Genesis, rate limiting |
| [[finops_milp]] | FinOps MILP — entry point, links a research/finops/ |
| [[FINOPS_MILP_VARIABLES]] | Variables de decisión técnicas — max_tokens por ruta, modelos |
| [[MUNDANA_PHASE12]] | Fase 12 — módulo mundana + publisher autónomo Cloud Run |
| [[CONTEXT_QUALITY_FIXES]] | 4 fixes de calidad de contexto Lilly (2026-04-16) |

---

## 07 — Knowledge Graph & GraphRAG

> Schema completo de 3 capas — formalizado con Lilly (tradición helenística/persa) — 2026-05-05

| Documento | Descripción |
|-----------|-------------|
| [[07_knowledge_graph/GRAPHRAG_KG_VISION\|GRAPHRAG_KG_VISION]] | Visión estratégica — por qué KG, capacidades vs. arquitectura actual, ruta de implementación |
| [[07_knowledge_graph/KG_ONTOLOGY_SCHEMA\|KG_ONTOLOGY_SCHEMA]] | **Schema 3 capas completo** — entidades, relaciones estáticas, derivadas + caso de prueba + formato tripletas |
| [[07_knowledge_graph/KG_EXPERIMENT_PROTOCOL\|KG_EXPERIMENT_PROTOCOL]] | Protocolo experimento A/B — tokens, costo, precisión doctrinal, criterios publicación |

**Estado:** Capas 1, 2 y 3 formalizadas ✅ · Pendiente: `chart_graph.py` en Abu Engine

---

## 07b — Sonic Field

| Documento | Descripción |
|-----------|-------------|
| [[sonic_field/SONIC_FIELD_SPEC\|SONIC_FIELD_SPEC]] | Spec fundacional — doctrina Cousto, arquitectura 3 capas, mapeo astrológico→síntesis |
| [[sonic_field/sonic_capa1_natal\|sonic_capa1_natal]] | ✅ Capa 1 implementada y validada — Firma Sonora Natal con Tone.js |
| [[sonic_capa2_transitos]] | ✅ Capa 2 implementada — Tránsitos activos como capa aditiva sobre la firma natal |

---

## 08 — BABEL *(Appendix VII — Research)*

> Intérprete universal de lenguajes animales — grafo semántico cross-especie. El R2-D2 que falta.

| Documento | Descripción |
|-----------|-------------|
| [[08_babel/BABEL_overview\|BABEL_overview]] | **Hub central** — hipótesis, arquitectura, 9 primitivas semánticas, conexión QUEST + Abu Oracle |
| [[08_babel/BABEL_literature\|BABEL_literature]] | Mapa de literatura — ESP, CETI, NatureLM, Copenhague, NeurIPS 2025, Total Turing Test |
| [[08_babel/BABEL_phase0\|BABEL_phase0]] | Phase 0 — demo sintético: sil=0.750 ✅ · MFCC real: sil=-0.185 ❌ (esperado) → valida necesidad NatureLM |

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
