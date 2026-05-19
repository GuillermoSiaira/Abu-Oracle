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
| **v2_natal_only** | ¿KG (4 señores) mejora vs JSON natal (10 planetas) cuando el frame es natal puro? | ⚠️ Corrido 2026-05-18/19. **Refutó la hipótesis naive: A +11%**. El "test" estaba viciado: A tenía 10 planetas y B solo 4 — no era test de formato sino de cantidad. | Sin doc dedicada; resultado en `data/kg_experiment/v2_natal_only/results_*.json` |
| **v3_natal_full_kg** | Con MISMA información en A y B (10 planetas + 4 ángulos + 4 partes + 12 señoríos + aspectos + recepciones), ¿el formato KG en tripletas supera al JSON plano? | ✅ Corrido 2 veces (n=4 luego n=5). **Con n=5 y sujeto corregido: TIE (Claude 0%, Gemini +1.3%). Tesis refutada.** | `RESULTS_v3v4v5_n5_2026-05-19.md` |
| **v4_natal_finops** | ¿KG con downgrade Sonnet→Haiku mantiene calidad? Test FinOps puro. | ✅ Corrido n=5 (2026-05-19). **REFUTADA: −24% calidad en ambos jueces, acuerdo 5/5.** | `RESULTS_v3v4v5_n5_2026-05-19.md` |
| **v5_natal_kg_haiku** | ¿KG ayuda a Haiku (JSON+Haiku vs KG+Haiku)? Test del scaffolding sobre modelo barato. | ✅ Corrido n=5 (2026-05-19). **CONFIRMADA: +15.8% Claude, +18.1% Gemini, acuerdo 4/5.** | `RESULTS_v3v4v5_n5_2026-05-19.md` |

### Hallazgos cruzados

- **Tesis revisada con datos (2026-05-19):** "El formato KG es scaffolding para modelos menores: agrega +16-18% de calidad a Haiku. NO mejora cuando el modelo es Sonnet, NO compensa downgrade." Ver `RESULTS_v3v4v5_n5_2026-05-19.md` para el análisis completo.
- **GS_004 (carta del autor) es outlier en ambas direcciones:** maximiza el efecto KG con Sonnet (v3 B+8/+9) y lo invierte con Haiku (v5 A+4/+1). Carta doctrinalmente densa que satura a Haiku con el KG.
- **Cross-validation cuenta**: la primera medición de v1 dio B +47% con juez Sonnet. Cross-judge con Gemini sobre los mismos outputs dio B +11%. Lección: siempre cross-validar con modelo distinto antes de declarar finding.
- **n=4 → n=5 cambia el resultado de v3 dramáticamente** (+6.8% → 0%). Lección: con n pequeño un solo sujeto outlier mueve la aguja. n≥10-12 es necesario para publicación.
- **Bug del schema vs del lab**: descubrimos que `serialize_subgraph(graph, get_key_planets(graph, {}))` solo emite 4 planetas, contradiciendo lo que el schema doctrinal (`docs/theory/KG_ONTOLOGY_SCHEMA.md`) propone. v3 implementa lo que el schema realmente especifica.
- **Aspectos no en `/analyze`**: `chart.aspects` viene vacío. v3 los computa localmente desde longitudes (orbe 6° menores / 8° mayores per schema).
- **Bug de atribución de sujeto resuelto (2026-05-19):** `gs004` en config.py era una carta sintética (1983-10-10 BA), no la del autor. Renombrada a `synth001`; carta real agregada como nueva entrada `gs004` (1978-07-06 Balcarce). Ver `.claude/specs/active/DOC_C01_kg_subject_misattribution.md`.

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
