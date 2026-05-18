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
| **v1_current_life** | ¿KG mejora interpretación de "vida del nativo hoy" vs JSON timeline? | ✅ Corrido 2026-05-18 | `RESULTS_2026-05-18.md` |
| _(próximo: v2_natal_only)_ | ¿KG mejora interpretación de talentos innatos natales sin contexto temporal? | 🔵 Pendiente | — |

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
