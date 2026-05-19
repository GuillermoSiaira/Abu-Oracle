# KG Experiment — Laboratorio

Espacio para experimentos comparando formatos de contexto (JSON plano vs Knowledge Graph)
en la calidad de interpretaciones doctrinales de Lilly.

## Estructura

```
scripts/kg_experiment/
├── INDEX.md                     ← este archivo
├── runner.py                    ← runner genérico, acepta --design
├── judge.py                     ← juez ciego con Sonnet 4.6 (Anthropic)
├── cross_judge.py               ← juez ciego con Gemini 2.5 Pro (Vertex AI)
├── assemble_context.py          ← helper: build_timeline_section_a()
├── config.py                    ← ABU_ENGINE_URL (config técnica, no de diseño)
└── designs/
    ├── __init__.py
    └── vN_<nombre>.py           ← un módulo por diseño experimental
```

## Diseños disponibles

| ID | Pregunta científica | Status | Resultados |
|---|---|---|---|
| **v1_current_life** | ¿KG mejora interpretación de "vida del nativo hoy" vs JSON timeline? | ✅ Corrido 2026-05-18 (2 veces) | `RESULTS_v1_current_life_2026-05-18.md` (1ª corrida); 2ª corrida con `--thinking` en disco pero sin doc |
| **v2_natal_only** | ¿KG (4 señores) mejora vs JSON natal (10 planetas) cuando el frame es natal puro? | ⚠️ Corrido 2026-05-18/19 (2 corridas — 1ª con bug, 2ª limpia). **Refutó la hipótesis naive: A +11%**. El "test" estaba viciado: A tenía 10 planetas y B solo 4 — no era test de formato sino de cantidad. | Sin doc dedicada; resultado en `data/kg_experiment/v2_natal_only/results_*.json` |
| **v3_natal_full_kg** | Con MISMA información en A y B (10 planetas + 4 ángulos + 4 partes + 12 señoríos + aspectos + recepciones), ¿el formato KG en tripletas supera al JSON plano? | 🟡 Corrido 2026-05-19, **pendiente de análisis y cross-judge** | En disco; documentar en `RESULTS_v3_natal_full_kg_2026-05-19.md` |

### Hallazgos cruzados

- **Cross-validation cuenta**: la primera medición de v1 dio B +47% con juez Sonnet. Cross-judge con Gemini sobre los mismos outputs dio B +11%. Lección: siempre cross-validar con modelo distinto antes de declarar finding.
- **Bug del schema vs del lab**: descubrimos que `serialize_subgraph(graph, get_key_planets(graph, {}))` solo emite 4 planetas, contradiciendo lo que el schema doctrinal (`docs/theory/KG_ONTOLOGY_SCHEMA.md`) propone. v3 implementa lo que el schema realmente especifica.
- **Aspectos no en `/analyze`**: `chart.aspects` viene vacío. v3 los computa localmente desde longitudes (orbe 6° menores / 8° mayores per schema).

## Cómo correr un experimento

```bash
# 1. Levantar Abu Engine local
docker-compose up abu_engine -d

# 2. Setear ANTHROPIC_API_KEY en env
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# 3. Correr con un diseño específico
python scripts/kg_experiment/runner.py --design v1_current_life

# 4. Re-evaluar con cross-judge (Gemini, créditos Vertex)
python scripts/kg_experiment/cross_judge.py --design v1_current_life
```

Outputs van a `data/kg_experiment/<design_id>/results_TIMESTAMP.json` (gitignored).

## Cómo crear un diseño nuevo

1. Crear archivo `designs/v<N>_<nombre>.py` con el contrato mínimo:
   - `DESIGN_ID: str` (mismo que el nombre del archivo, sin `.py`)
   - `DESIGN_DESCRIPTION: str`
   - `EVAL_PROMPT: str`
   - `SUBJECTS: list[dict]`
   - `build_context_a(natal, bio) -> str`
   - `build_context_b(natal, bio) -> str`
2. Agregar entrada a la tabla "Diseños disponibles" de arriba.
3. Correr `python runner.py --design v<N>_<nombre> --dry-run` para validar.
4. Correr el experimento real.
5. Documentar resultados en `RESULTS_<diseño>_<fecha>.md`.

## Convención de nombres

- Diseños: `v<N>_<descripción_corta>.py` — ej: `v2_natal_only.py`, `v3_natal_with_ground_truth.py`
- Resultados: `RESULTS_<design_id>_<YYYY-MM-DD>.md` — para preservar el análisis junto al código
