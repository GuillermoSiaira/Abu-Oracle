# Protocolo de Experimento: JSON plano vs. KG Architecture
**Fecha:** 2026-05-05
**Estado:** Draft — pendiente implementación
**Objetivo:** Validar que la arquitectura KG mejora calidad de interpretación
y reduce costo por interpretación simultáneamente.

---

## Hipótesis central

La arquitectura KG (subgrafo instanciado) vs. JSON plano produce:

| Dimensión | Hipótesis | Fundamento |
|---|---|---|
| Precisión doctrinal | Sube | Relaciones afirmadas vs. inferidas — menos error en cadenas largas |
| Tokens de input | Baja | Subgrafo relevante < JSON completo de carta |
| Tokens de output | Baja | Lilly no gasta tokens reconstruyendo Capa 3 |
| Costo total | Baja | Suma de ambas reducciones |
| Consistencia | Sube | Relaciones estructurales son determinísticas — varianza inter-sesión baja |

**Análogo empírico ya existente en Abu Oracle:**
HF_global (0.155) vs. HF_dominio (0.615) — misma arquitectura de filtrado, misma lógica.
Pasar el subgrafo relevante es exactamente `planet_subset = house_significators(natal, house=k)`.

---

## Diseño del experimento

### Condición A — Baseline (arquitectura actual)
```
Input:  system_prompt_lilly + JSON completo de carta + pregunta del usuario
Output: respuesta de Lilly
Medir:  input_tokens, output_tokens, costo, calidad doctrinal
```

### Condición B — KG Architecture
```
Input:  system_prompt_lilly + subgrafo instanciado (serializado) + pregunta del usuario
Output: respuesta de Lilly
Medir:  input_tokens, output_tokens, costo, calidad doctrinal
        + tiempo de build del grafo NetworkX
```

**Control:** misma pregunta, misma carta, mismo modelo (`claude-sonnet-4-6`),
misma temperatura, mismo momento (batch simultáneo para evitar variación de modelo).

---

## Corpus de prueba

### Dataset primario
Los **527 eventos biográficos** ya catalogados en `HF_EXPERIMENT_LOG.md`.
Cada evento tiene:
- Carta natal asociada
- Fecha del evento
- Dominio de vida (salud, carrera, relaciones, etc.)
- Valencia (+/-/neutral)

Esto permite evaluar no solo calidad de interpretación sino también
si la interpretación KG predice mejor la valencia del evento real.

### Muestra mínima para validez estadística
- N = 60 pares (A/B) — poder estadístico 0.8 para detectar d = 0.5
- Estratificado por dominio de vida (10 por dominio: carrera, salud, relaciones,
  finanzas, viajes, creación, familia, spiritualidad, social, crisis)
- Estratificado por complejidad de pregunta (simple 1-hop / compleja 3+ hops)

---

## Métricas

### 1. Tokens y costo

```python
# Ya disponible en @anthropic-ai/sdk — response.usage
{
  "input_tokens":  int,   # tokens del prompt completo
  "output_tokens": int,   # tokens de la respuesta de Lilly
  "total_tokens":  int,
  "costo_usd":     float  # input * precio_input + output * precio_output
}

# claude-sonnet-4-6 pricing (verificar vigente):
# Input:  $3.00 / 1M tokens
# Output: $15.00 / 1M tokens
```

**Métricas derivadas:**
- `delta_input_tokens` = A.input - B.input (esperado: positivo — KG usa menos)
- `delta_output_tokens` = A.output - B.output (esperado: positivo)
- `delta_costo_usd` = A.costo - B.costo
- `ahorro_pct` = delta_costo / A.costo × 100

### 2. Precisión doctrinal

Evaluar si las **relaciones de Capa 3** están correctas en la respuesta.

```
Para cada respuesta, identificar afirmaciones de Capa 3:
  - "X es señor del año" → verificable contra profección
  - "Y es señor de la firdaria" → verificable contra tabla de firdarías
  - "Z recibe a W" → verificable contra dignidades
  - "la Parte de Fortuna está bajo señorío de..." → computable

Score: n_afirmaciones_correctas / n_afirmaciones_Capa3_totales
```

**Evaluador:** automático para relaciones computables (Abu Engine puede verificar),
manual para relaciones interpretativas complejas.

### 3. Longitud de cadena sin error

Contar la cadena de razonamiento más larga que Lilly completa sin error doctrinal.

```
Ejemplo cadena correcta (4 hops):
  "Saturno señor del año [✓] → en detrimento en Leo [✓] → ocupa Casa 7 [✓]
   → señor de la Casa 7 es Sol [✓] → Sol en Casa X [✓]"

Score: longitud de la cadena correcta más larga en la respuesta
```

Hipótesis: cadena media sube de ~2.5 hops (JSON) a ~4+ hops (KG).

### 4. Consistencia inter-sesión

Misma carta, misma pregunta, 5 llamadas independientes en cada condición.

```python
# Métrica: similitud semántica entre respuestas
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

embeddings = model.encode(responses)  # 5 respuestas
variance = np.var(cosine_similarity(embeddings))
# Hipótesis: variance_B < variance_A (KG produce respuestas más consistentes)
```

### 5. Costo por interpretación correcta (métrica compuesta)

```python
# La métrica más importante para el paper:
eficiencia = precision_doctrinal / costo_usd

# Hipótesis: eficiencia_B >> eficiencia_A
# (KG es más barato Y más preciso → eficiencia compuesta mucho mayor)
```

---

## Implementación técnica

### Paso 1 — Logging de tokens (sin cambiar arquitectura)

Agregar a los handlers de Lilly en `app/api/lilly/`:

```typescript
// En el handler actual, después de la llamada a Claude:
const response = await anthropic.messages.create({...});

// Agregar logging:
await logInterpretationMetrics({
  requestId: crypto.randomUUID(),
  condition: 'A',  // baseline
  chartId: chartId,
  question: userMessage,
  inputTokens: response.usage.input_tokens,
  outputTokens: response.usage.output_tokens,
  costUsd: calculateCost(response.usage),
  timestamp: new Date().toISOString(),
  tradition: 'persian' | 'hellenistic' | etc,
  domain: detectedDomain,
});
```

**Output:** tabla `interpretation_metrics` en Firestore.
Esto arranca la recolección de baseline (Condición A) sin cambiar nada del producto.

### Paso 2 — Build del grafo NetworkX (Fase 1 del KG)

```python
# En abu_engine, nuevo módulo: chart_graph.py
import networkx as nx

def build_chart_graph(abu_json: dict, tradition: str) -> nx.DiGraph:
    """Construye grafo del chart desde el JSON de Abu Engine."""
    G = nx.DiGraph()
    # ... (ver KG_ONTOLOGY_SCHEMA.md para tipos de nodo)
    return G

def serialize_subgraph(G: nx.DiGraph, question_domain: str) -> str:
    """Serializa el subgrafo relevante para pasar a Lilly."""
    subgraph = extract_domain_subgraph(G, question_domain)
    return format_as_structured_context(subgraph)
```

### Paso 3 — Endpoint paralelo para experimento

```typescript
// Nueva ruta: app/api/lilly/experiment/
// Llama A y B en paralelo para el mismo input
// Guarda ambas respuestas con sus métricas
// No expuesto al usuario — solo para el experimento
```

### Paso 4 — Evaluador automático de precisión doctrinal

```python
# evaluator.py
# Usa Abu Engine para verificar afirmaciones de Capa 3

def evaluate_capa3_claims(response: str, chart: dict) -> dict:
    """
    Extrae y verifica afirmaciones de Capa 3 en la respuesta de Lilly.
    Abu Engine ya puede computar: profección, firdaria, partes arábicas.
    """
    claims = extract_doctrinal_claims(response)  # NLP simple
    verified = [verify_claim(c, chart) for c in claims]
    return {
        "total_claims": len(claims),
        "correct": sum(verified),
        "precision": sum(verified) / len(claims) if claims else None
    }
```

---

## Estructura de datos del experimento

```
Firestore: collection "kg_experiment"
  document: {
    id: uuid,
    timestamp: datetime,
    chart_id: str,
    question: str,
    question_domain: str,        # carrera | salud | relaciones | etc.
    question_complexity: int,    # 1-3 hops esperados
    tradition: str,

    condition_A: {
      input_tokens: int,
      output_tokens: int,
      cost_usd: float,
      response: str,
      doctrinal_precision: float,
      chain_length: int,
    },

    condition_B: {
      input_tokens: int,
      output_tokens: int,
      cost_usd: float,
      response: str,
      doctrinal_precision: float,
      chain_length: int,
      graph_build_ms: int,       # overhead de construir el grafo
    },

    delta: {
      input_tokens: int,         # A - B (positivo = KG usa menos)
      output_tokens: int,
      cost_usd: float,
      precision: float,          # B - A (positivo = KG más preciso)
      efficiency: float,         # (B.precision/B.cost) / (A.precision/A.cost)
    }
  }
```

---

## Análisis estadístico

```python
import scipy.stats as stats

# Para cada métrica, t-test pareado (misma carta/pregunta, condición distinta):
t_stat, p_value = stats.ttest_rel(metrics_A, metrics_B)

# Tamaño del efecto (Cohen's d):
d = (mean_A - mean_B) / pooled_std

# Reporte mínimo para paper:
# - delta tokens: mean ± SD, p-value, Cohen's d
# - delta costo: mean ± SD, p-value
# - delta precisión: mean ± SD, p-value, Cohen's d
# - eficiencia compuesta: ratio B/A con IC 95%
```

---

## Criterio de éxito para publicación

| Métrica | Threshold mínimo | Threshold fuerte |
|---|---|---|
| Reducción de tokens | > 15% | > 30% |
| Mejora de precisión doctrinal | > 0.10 (absoluto) | > 0.25 |
| p-value | < 0.05 | < 0.01 |
| Cohen's d | > 0.3 (pequeño) | > 0.5 (mediano) |
| Eficiencia compuesta | > 1.5× | > 2.0× |

---

## Timeline sugerido

| Paso | Duración estimada | Entregable |
|---|---|---|
| Logging de tokens en producción (baseline) | 1 día | Datos Condición A empiezan a acumularse |
| `chart_graph.py` — NetworkX Fase 1 | 2-3 días | Grafo instanciable desde abu_json |
| Endpoint paralelo de experimento | 1 día | Condición A y B corriendo en paralelo |
| Evaluador automático de Capa 3 | 2-3 días | Precisión doctrinal automática |
| Recolección N=60 pares | 1-2 semanas | Dataset completo |
| Análisis estadístico + paper | 1 semana | Borrador publicable |

---

## Referencias

- `docs/theory/GRAPHRAG_KG_VISION.md` — visión arquitectónica
- `docs/theory/KG_ONTOLOGY_SCHEMA.md` — schema de capas 1-3
- `docs/HF_EXPERIMENT_LOG.md` — precedente metodológico (HF_global vs HF_dominio)
- `app/api/lilly/` — handlers actuales de Lilly
- `abu_engine/` — motor de cómputo

---

*Abu Oracle Project — 2026-05-05*
