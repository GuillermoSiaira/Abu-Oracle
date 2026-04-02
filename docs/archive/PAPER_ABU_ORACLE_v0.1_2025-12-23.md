# Abu Oracle: A Deterministic Astro-Social Optimization System with a Quantum Relocation Layer

**Versión:** 0.1 (Draft)  
**Fecha:** 2025-12-23

**Generado por:** ChatGPT 5.2

---

## Abstract

We present Abu Oracle, a hybrid system that converts classical astrological judgment into deterministic, continuous optimization variables, enabling reproducible astro-social experiments. The system computes a natal chart, derived traditional techniques (sect, firdaria, profections, lots), and a relocation objective for Solar Return location selection. A classical engine preselects candidate cities globally, then a quantum layer (QAOA) optimizes a QUBO objective (an “astrological tension Hamiltonian”) using a continuous influence function. We propose an experimental protocol where participants relocate (physically or virtually) to predicted optimal coordinates, provide structured outcome feedback, and allow falsifiable evaluation of the model’s predictions under controlled conditions. The result is a first-of-its-kind bridge between traditional astrological reasoning and modern optimization / quantum heuristics, grounded in deterministic computation and auditable contracts.

---

## 1. Motivation

Astrology historically operated as a judgment art grounded on astronomical computation and rule-based reasoning (Ptolemy; later medieval elaborations). Yet it lacked: (i) formal continuous objective functions, (ii) reproducible optimization workflows, and (iii) empirical protocols for structured validation at scale. Abu Oracle targets exactly these gaps by turning qualitative doctrines into explicit variables, enabling algorithmic optimization and experimental evaluation.

---

## 2. System Overview

- **Abu Engine (FastAPI):** deterministic calculations, Solar Return relocation scoring, and API contracts.
- **Lilly Engine (FastAPI):** interpretation layer returning a structured “Maestro JSON” output and narrative.
- **IGP (Inteligencia Geográfica Predictiva):** hybrid strategy: city scan → local refinement → quantum optimization.

---

## 3. Deterministic Astro Variables (from chart to scores)

### 3.1 Chart primitives
Planet longitudes, houses (ASC/MC/cusps), retrograde, aspects, orbs, applying/separating (all deterministic).

### 3.2 Derived traditional techniques (deterministic)
Sect, firdaria, profections, lots, and other Persian/classical computations.

### 3.3 Continuous influence: the key modern bridge
Classical “aspect exists/does not exist” becomes a continuous scalar via gaussian_influence(Δθ), allowing gradient-like behavior and stable optimization.

---

## 4. Relocation Optimization (IGP)

### 4.1 Classical phase
Evaluate ~5k–10k cities, rank by relocation score, keep top-N candidates. Deterministic caching + integration tests ensure stable contracts.

### 4.2 Local refinement
Optimize around each top city with bounded coordinate search (e.g., hill-climb / Nelder-Mead) to capture “between-cities” maxima.

### 4.3 Quantum phase
Formulate the candidate set as a QUBO and solve via QAOA; interpret the minimum-energy solution as the “optimal” relocation choice under the tension Hamiltonian.

---

## 5. The Astro-Social Experiment Protocol (falsifiable)

**Hypothesis:** relocating the Solar Return chart per Abu Oracle improves pre-registered outcomes (domain-specific) vs. controls.

**Protocol:**
- Pre-register outcomes per participant (e.g., health/energy, finances, relationships).
- Assign: A) Abu-optimal relocation, B) random relocation from top-N, C) no relocation (baseline).
- Collect structured feedback weekly, plus objective proxies (sleep, productivity metrics, finances logs—user-controlled).
- Evaluate effect sizes, robustness, and sensitivity to confounders.

**Why this is historically new:** it makes a traditionally interpretive system auditable, parameterized, and experimentally testable through deterministic APIs and explicit objective functions.

---

## 6. Ethics & Safety

- Avoid deterministic “medical/legal” claims; limit to advisory experimentation with user consent.
- Default privacy: local logging + opt-in data donation.
- Domain-risk gating: some topics require stronger disclaimers.

---

## 7. Roadmap (paper → system)

- Add benefic/malefic percentage (Jyotish weighting).
- Add significators-by-domain (Lilly-style domain mapping).
- Publish benchmark datasets: SR relocation cases with pre-registered outcomes.

---

## 8. Código (Etapa 1–2): módulos + integración en Abu Engine

### Objetivo
Que `/analyze` devuelva dos nuevos bloques en derived:
- benefic_malefic: porcentajes por planeta + por casa/dominio
- significators: mapa “dominio → (planetas/houses) + explicación”

### B1) Nuevo módulo: abu_engine/core/benefic_malefic.py
```python
# abu_engine/core/benefic_malefic.py
# ...ver contenido original del prompt para el código completo...
```

### B2) Nuevo módulo: abu_engine/core/significators.py
```python
# abu_engine/core/significators.py
# ...ver contenido original del prompt para el código completo...
```

### B3) Integración mínima en main.py (endpoint /analyze)
Agregá dos líneas justo antes del response = {...} final:
```python
from core.benefic_malefic import compute_benefic_malefic_table
from core.significators import compute_significators

benefic_malefic = compute_benefic_malefic_table(detailed_planets, sect_label)
significators = compute_significators(detailed_planets)
```
Y luego, dentro de "derived": { ... } sumá:
```python
"benefic_malefic": benefic_malefic,
"significators": significators,
```

### B4) (Opcional) endpoint auditable dedicado
GET /api/astro/scorecard?date=...&lat=...&lon=...
Devuelve solo:
- chart.planets (detailed)
- benefic_malefic
- significators

### B5) Qué sigue inmediatamente
Upgrade v0 → v1 de benefic/malefic:
- meter aspect intensity (usando tu lógica de aspectos + orbes)
- meter solar conditions (combust/cazimi)
- meter receptions y sect-benefic rules (más clásico)

Todo eso está en tu inventario persa ya documentado (dignidades, aspectos, solar conditions, lots, etc.).

---

**Este documento fue redactado el 2025-12-23 y debe ser consumido por agentes de IA y humanos para establecer contexto, fundamentos y roadmap técnico de Abu Oracle.**
