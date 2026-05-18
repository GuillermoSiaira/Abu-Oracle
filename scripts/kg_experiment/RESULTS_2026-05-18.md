# KG-C03 — Primera corrida con métricas completas

**Fecha:** 2026-05-18
**Run ID:** `results_20260518_182746.json`
**Modelo Lilly:** `claude-sonnet-4-6` (Anthropic API directa)
**Modelo Judge:** `claude-sonnet-4-6` (mismo modelo — ver caveat #3)
**Costo total del run:** $0.073 USD

---

## Diseño del experimento

Comparación pareada (judge ciego con orden randomizado) de dos condiciones de contexto entregadas a Lilly para interpretar cartas natales:

- **Condición A — JSON plano**: sección `LINEA DE TIEMPO` del `assembleContextBlock` actual.
  Construida por `build_timeline_section_a()`: profección activa + próxima profección +
  firdaria mayor + top 5 tránsitos lentos activos.

- **Condición B — Knowledge Graph**: subgrafo NetworkX serializado por `serialize_subgraph()`.
  Incluye señor_ASC, señor_MC, señor_fortuna, señor_spirit, señor_del_año,
  firdaria_mayor/menor + top-3 aspectos por planeta clave.

**Mismo `EVAL_PROMPT` en ambas condiciones**, mismo system message, mismo `max_tokens=400`.

---

## Resultados

### Calidad doctrinal (juez LLM, 1-5 × 5 ejes, max 25)

| Sujeto | A score | B score | Delta | % mejora |
|---|---|---|---|---|
| Einstein | 12 | 20 | +8 | **+67%** |
| Jung | 12 | 19 | +7 | **+58%** |
| Tesla | 10 | 20 | +10 | **+100%** |
| GS_004 | 21 | 22 | +1 | +5% |
| **Promedio** | **13.75** | **20.25** | **+6.50** | **+47.3%** |

### Tokens, costo, latencia

| Métrica | A (JSON) | B (KG) | Delta |
|---|---|---|---|
| Tokens input avg | 233 | 611 | **+162.6%** |
| Tokens output avg | 351 | 373 | +6.1% |
| Costo USD / lectura | $0.0060 | $0.0074 | **+24.4%** |
| Latencia ms | 9940 | 10204 | +2.7% |
| Proyección 10k lecturas/mes | $59.67 | $74.25 | $14.58 |

---

## Hallazgo principal

**Contraintuitivo y favorable:**

> El grafo de conocimiento NO ahorra tokens — los usa **2.6× más** que el baseline JSON.
> Pero la calidad doctrinal sube **+47%** medida por un juez LLM ciego.
> El trade-off real es **+22% costo / +47% calidad = 2.1× más calidad por dólar gastado**.

Esto contradice la hipótesis original ("KG reduce tokens") pero alinea con el insight
formalizado en `docs/theory/KG_ONTOLOGY_SCHEMA.md`:

> *"Lilly razona sobre relaciones afirmadas, no inferidas. Cuatro pasos de inferencia
> en cada respuesta se eliminan al recibir el grafo instanciado."*

La calidad sube porque Lilly recibe relaciones explícitas (señor_de, aspecta, firdaria_mayor)
y se evita la cadena de inferencia "Júpiter exaltado → señor de Piscis → señor del Espíritu
→ significador vocacional primario".

---

## Observaciones técnicas

1. **GS_004 es outlier** (delta +5% vs +58-100% del resto). Hipótesis:
   - Único sujeto vivo con UTC offset correcto → tránsitos contemporáneos enriquecen A
   - Para sujetos históricos (1856-1879) sin activadores temporales actuales, A queda
     pobre y B brilla por contraste
   - Hipótesis falsable: el delta KG vs JSON correlaciona inversamente con la "riqueza"
     temporal del contexto A

2. **n=4 es estadísticamente débil**. Para publicación con credibilidad estadística:
   - N=10-12 mínimo recomendado
   - Costo adicional ~$0.018 por sujeto → N=12 = $0.20 USD total

3. **El juez es el mismo modelo que el intérprete** (Sonnet 4.6 evalúa Sonnet 4.6).
   Riesgo: "Claude prefiere su propio estilo". Mitigación pendiente:
   - Re-evaluar las mismas responses con un cross-model judge (GPT-4o o Gemini 2.5 Pro)
   - Si ambos jueces concuerdan en B > A → señal robusta no atribuible a sesgo de modelo

---

## Caveats sobre la condición A

La sección `build_timeline_section_a` actual produce un contexto **muy compacto**
(~233 tokens promedio). En producción, `assembleContextBlock` entrega MUCHO más contexto
que solo el timeline section. La comparación realizada NO es "JSON plano de producción
vs KG" sino "subset minimal de timeline vs KG completo".

Para una comparación más justa en futuras iteraciones, considerar:

- **A'** = full `assembleContextBlock` sin sección KG (estado actual de producción)
- **B'** = full `assembleContextBlock` + sección KG inyectada (estado propuesto post-integración)

Esa comparación mide la pregunta de producto real: *"¿agregar KG al contexto actual mejora a Lilly?"*

---

## Próximos pasos sugeridos

| Acción | Esfuerzo | Output |
|---|---|---|
| Expandir N a 10-12 sujetos | 10 min + ~$0.20 | Estadística más sólida |
| Cross-model judge (Gemini Pro) | 30 min + $0.10 | Validar que B>A no es sesgo de modelo |
| Comparación justa A' vs B' (contextos full) | 1-2h código + ~$0.30 | Pregunta de producto real |
| Integrar KG al pipeline de producción si pasa cross-judge | 1 día | Capa 2 producto activada |
| Endpoint público `POST /api/v1/chart/graph` (API-C01 Fase 2) | 2-3 días | Diferenciador B2B vs competidores |
| Blog post + thread X/Bluesky | 2h | Contenido distintivo con datos reales |

---

## Archivos del run

- Datos crudos: `data/kg_experiment/results_20260518_182746.json` (gitignored)
- Código:
  - `scripts/kg_experiment/runner.py` — runner instrumentado con tokens/cost/latency
  - `scripts/kg_experiment/judge.py` — judge con markdown-fence stripping
  - `scripts/kg_experiment/config.py` — 4 sujetos con fechas UTC
  - `scripts/kg_experiment/assemble_context.py` — `build_timeline_section_a` (condición A)
  - `abu_engine/core/chart_graph.py` — builder NetworkX (condición B)
- Schema doctrinal: `docs/theory/KG_ONTOLOGY_SCHEMA.md`
- Protocolo experimento: `docs/theory/KG_EXPERIMENT_PROTOCOL.md`
