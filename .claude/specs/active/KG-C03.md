# KG-C03 — Experiment Runner: Condición B (KG vs JSON baseline)

**Fecha:** 2026-05-08  
**Track:** Knowledge Graph / Investigación  
**Prioridad:** Media — después de QA-C01 y FI-C01  
**Depende de:** KG-C02 completado (`abu_engine/core/chart_graph.py` existente y con tests pasando)  
**Independiente de:** FI-C01 (no comparte código)

---

## Objetivo

Comparar la calidad del contexto que recibe Lilly en dos condiciones:

- **Condición A (baseline)**: sección `LÍNEA DE TIEMPO` del `assembleContextBlock()` actual —
  texto serializado desde JSON plano (profecciones + firdaria + tránsitos como lista lineal)

- **Condición B (KG)**: misma sección reemplazada por `serialize_subgraph()` —
  el subgrafo NetworkX con relaciones Capa 3 instanciadas (señoríos, aspectos top-3, fardarios)

**Hipótesis**: Condición B produce interpretaciones con mayor coherencia doctrinal
porque Lilly recibe hechos relacionales en lugar de lista de atributos.

**Medición**: juez LLM (Claude Opus o Sonnet) evalúa pares A/B ciegamente en una escala
de 5 criterios doctrinales.

---

## Diseño del experimento

### Sujetos de prueba

Usar los 3 sujetos del Gold Standard + Guillermo (GS_004):

| Sujeto | birthDate | lat | lon | Notas |
|---|---|---|---|---|
| Einstein | 1879-03-14T11:30:00 | 48.4 | 10.0 | AA Rodden |
| Jung | 1875-07-26T19:32:00 | 47.5 | 7.5 | A Rodden |
| Tesla | 1856-07-10T00:00:00 | 44.3 | 19.8 | B Rodden |
| GS_004 | 1983-10-10T05:20:00 | -34.6 | -58.4 | Corpus propio |

### Prompt de evaluación (fijo para A y B)

```
Lilly recibe el siguiente contexto sobre una carta natal y debe dar una orientación inicial.
Responde como lo haría un astrólogo clásico: mencioná el señor del año, la firdaria activa,
y cómo se relacionan con la vida del nativo ahora mismo. Máximo 200 palabras.
```

### Criterios de evaluación (juez LLM)

El juez recibe ambas respuestas (A y B, sin saber cuál es cuál) y evalúa 1-5 en:

1. **Coherencia doctrinal**: ¿usa correctamente señoríos y firdaria?
2. **Especificidad**: ¿menciona planetas, casas y fechas concretas?
3. **Multi-hop reasoning**: ¿conecta señor del año → su casa natal → su dignidad → implicancia?
4. **Ausencia de genérico**: ¿evita frases vacías como "este es un período de transformación"?
5. **Síntesis**: ¿produce una lectura integrada o una lista de datos?

---

## Archivo a crear: `scripts/kg_experiment/runner.py`

### Estructura de carpeta

```
scripts/kg_experiment/
  runner.py          ← entry point
  assemble_context.py ← replica Python de la sección LÍNEA DE TIEMPO de context-builder.ts
  judge.py           ← juez LLM que evalúa pares A/B
  config.py          ← sujetos, prompt, criterios
```

### `config.py`

```python
ABU_ENGINE_URL = "http://localhost:8000"

SUBJECTS = [
    { "id": "einstein", "birthDate": "1879-03-14T11:30:00", "lat": 48.4,  "lon": 10.0,  "name": "Einstein" },
    { "id": "jung",     "birthDate": "1875-07-26T19:32:00", "lat": 47.5,  "lon": 7.5,   "name": "Jung" },
    { "id": "tesla",    "birthDate": "1856-07-10T00:00:00", "lat": 44.3,  "lon": 19.8,  "name": "Tesla" },
    { "id": "gs004",    "birthDate": "1983-10-10T05:20:00", "lat": -34.6, "lon": -58.4, "name": "GS_004" },
]

EVAL_PROMPT = """Un astrólogo clásico recibe el siguiente contexto sobre una carta natal.
Responde como lo haría: mencioná el señor del año, la firdaria activa,
y cómo se relacionan con la vida del nativo ahora mismo. Máximo 200 palabras."""

JUDGE_CRITERIA = [
    "coherencia_doctrinal",
    "especificidad",
    "multi_hop_reasoning",
    "ausencia_de_generico",
    "sintesis",
]
```

### `assemble_context.py`

Replica Python de la sección **LÍNEA DE TIEMPO** de `assembleContextBlock()` (TypeScript).
Solo esta sección — no todo el contextBlock.

```python
def build_timeline_section_a(bio_json: dict, natal_json: dict) -> str:
    """
    Construye la sección LÍNEA DE TIEMPO desde el JSON de /api/astro/biography.
    
    Replica el formato de context-builder.ts → buildActiveContext() → sección "LÍNEA DE TIEMPO".
    
    Args:
        bio_json:  respuesta de GET /api/astro/biography
        natal_json: respuesta de POST /analyze (para señor del año derivado)
    
    Returns:
        String con el bloque LÍNEA DE TIEMPO en el mismo formato que el TS.
    """
    lines = ["╔══ LÍNEA DE TIEMPO ══╗"]
    
    profections = bio_json.get("profections", [])
    firdaria    = bio_json.get("firdaria",    [])
    transits    = bio_json.get("transits_window", [])
    
    # Profección activa
    active_prof = next((p for p in profections if p.get("is_active")), None)
    if active_prof:
        lines.append(f"Profección activa: Casa {active_prof['house']} · {active_prof['sign']} · "
                     f"Señor: {active_prof.get('lord', '?')} · hasta {active_prof.get('date_end', '?')[:10]}")
    
    # Profección siguiente
    next_prof = next((p for p in profections if not p.get("is_active")), None)
    if next_prof:
        lines.append(f"Próxima profección: Casa {next_prof['house']} · {next_prof['sign']} · "
                     f"desde {next_prof.get('date_start', '?')[:10]}")
    
    # Firdaria activa
    active_fird = next((f for f in firdaria if f.get("is_active")), None)
    if active_fird:
        lines.append(f"Firdaria mayor: {active_fird['major_planet']} · "
                     f"Menor: {active_fird.get('minor_planet', '?')} · "
                     f"hasta {active_fird.get('date_end', '?')[:10]}")
    
    # Tránsitos lentos activos (solo conjunciones y oposiciones)
    slow_active = [t for t in transits 
                   if t.get("is_active") 
                   and t.get("speed_class") == "slow"
                   and t.get("aspect") in ("conjunction", "opposition")]
    
    if slow_active:
        lines.append("Tránsitos lentos activos:")
        for tr in slow_active[:5]:  # cap a 5
            exact = tr.get("exact_date", "")[:10] if tr.get("exact_date") else "?"
            lines.append(f"  {tr['transit_planet']} {tr['aspect']} natal {tr['natal_planet']} · exacto: {exact}")
    
    lines.append("╚════════════════════╝")
    return "\n".join(lines)
```

### `runner.py`

```python
#!/usr/bin/env python3
"""
KG Experiment Runner — Condition A vs B
Compara LÍNEA DE TIEMPO JSON plano vs subgrafo NetworkX serializado.
"""
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Abu Engine auth headers (si AUTH_ENABLED=true en local, pasar token)
ABU_HEADERS = {}  # si AUTH_ENABLED=false en Docker local, vacío es suficiente

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "abu_engine"))
from core.chart_graph import build_chart_graph, get_key_planets, serialize_subgraph
from scripts.kg_experiment.assemble_context import build_timeline_section_a
from scripts.kg_experiment.judge import evaluate_pair
from scripts.kg_experiment.config import SUBJECTS, EVAL_PROMPT, ABU_ENGINE_URL


def fetch_natal(subject: dict) -> dict:
    """Llama POST /analyze — retorna abu_json completo."""
    url = f"{ABU_ENGINE_URL}/analyze"
    payload = {
        "birthDate": subject["birthDate"],
        "lat":       subject["lat"],
        "lon":       subject["lon"],
        "name":      subject["name"],
    }
    res = requests.post(url, json=payload, headers=ABU_HEADERS, timeout=30)
    res.raise_for_status()
    return res.json()


def fetch_biography(subject: dict) -> dict:
    """Llama GET /api/astro/biography — retorna profecciones + firdaria + transits_window."""
    url = f"{ABU_ENGINE_URL}/api/astro/biography"
    params = {
        "birthDate":      subject["birthDate"].split("T")[0],
        "birthLat":       subject["lat"],
        "birthLon":       subject["lon"],
        "window_months":  "18",
    }
    res = requests.get(url, params=params, headers=ABU_HEADERS, timeout=30)
    res.raise_for_status()
    return res.json()


def build_context_a(natal: dict, bio: dict) -> str:
    """Condición A: LÍNEA DE TIEMPO desde JSON plano."""
    return build_timeline_section_a(bio, natal)


def build_context_b(natal: dict) -> str:
    """Condición B: LÍNEA DE TIEMPO reemplazada por subgrafo KG serializado."""
    G         = build_chart_graph(natal)
    derived   = natal.get("derived", {})
    key       = get_key_planets(G, derived)
    subgraph  = serialize_subgraph(G, key)
    
    if not subgraph:
        return "╔══ SEÑORÍOS ACTIVOS (KG) ══╗\n[sin datos de señoríos]\n╚═══════════════════════════╝"
    
    return f"╔══ SEÑORÍOS ACTIVOS (KG) ══╗\n{subgraph}\n╚═══════════════════════════╝"


def call_lilly(context: str, subject: dict) -> str:
    """
    Llama Claude Sonnet directamente (sin Next.js) para obtener la interpretación.
    Usa el EVAL_PROMPT fijo para condición A y B por igual.
    """
    import anthropic
    
    api_key = __import__('os').environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    system = (
        "Eres Lilly, astrólogo clásico formado en la tradición helenística y persa. "
        "Interpretas cartas natales siguiendo la doctrina de Ptolomeo, Al-Biruni y William Lilly."
    )
    
    user_msg = f"{EVAL_PROMPT}\n\nContexto de la carta:\n{context}"
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=system,
        messages=[{ "role": "user", "content": user_msg }],
    )
    
    return response.content[0].text if response.content else ""


def run_experiment():
    results = []
    
    for subject in SUBJECTS:
        print(f"\n{'='*60}")
        print(f"Sujeto: {subject['name']} ({subject['id']})")
        print('='*60)
        
        try:
            print("  Fetching natal + biography...")
            natal = fetch_natal(subject)
            bio   = fetch_biography(subject)
            time.sleep(1)  # rate limit precaution
            
            print("  Building contexts A and B...")
            ctx_a = build_context_a(natal, bio)
            ctx_b = build_context_b(natal)
            
            print("  Calling Lilly with context A...")
            resp_a = call_lilly(ctx_a, subject)
            time.sleep(2)
            
            print("  Calling Lilly with context B...")
            resp_b = call_lilly(ctx_b, subject)
            time.sleep(2)
            
            print("  Evaluating pair...")
            scores = evaluate_pair(ctx_a, ctx_b, resp_a, resp_b)
            
            result = {
                "subject_id":   subject["id"],
                "subject_name": subject["name"],
                "timestamp":    datetime.utcnow().isoformat(),
                "context_a":    ctx_a,
                "context_b":    ctx_b,
                "response_a":   resp_a,
                "response_b":   resp_b,
                "scores":       scores,
            }
            results.append(result)
            
            print(f"  Scores A: {scores.get('total_a', '?')} | B: {scores.get('total_b', '?')}")
        
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({ "subject_id": subject["id"], "error": str(e) })
    
    # Guardar resultados
    output_path = Path("data/kg_experiment") / f"results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Resultados guardados en {output_path}")
    
    # Resumen
    valid = [r for r in results if "scores" in r]
    if valid:
        avg_a = sum(r["scores"].get("total_a", 0) for r in valid) / len(valid)
        avg_b = sum(r["scores"].get("total_b", 0) for r in valid) / len(valid)
        print(f"\nResumen: {len(valid)}/{len(SUBJECTS)} sujetos evaluados")
        print(f"  Promedio Condición A (JSON): {avg_a:.2f}/5")
        print(f"  Promedio Condición B (KG):   {avg_b:.2f}/5")
        print(f"  Δ (B - A): {avg_b - avg_a:+.2f}")


if __name__ == "__main__":
    run_experiment()
```

### `judge.py`

```python
"""
Juez LLM: evalúa pares de respuestas A/B en 5 criterios doctrinales.
Ciega: el juez no sabe cuál es A y cuál es B.
"""
import json
import anthropic
import os

JUDGE_PROMPT_TEMPLATE = """
Eres un evaluador experto en astrología helenística clásica.
Evalúa estas dos interpretaciones de carta natal en una escala del 1 al 5 para cada criterio.
NO sabes cuál interpretación fue generada con qué método — evalúa solo el contenido.

INTERPRETACIÓN X:
{resp_x}

INTERPRETACIÓN Y:
{resp_y}

Criterios (1=malo, 5=excelente):
1. coherencia_doctrinal: ¿usa correctamente señoríos y firdaria según la doctrina clásica?
2. especificidad: ¿menciona planetas, casas y fechas concretas (no genérico)?
3. multi_hop_reasoning: ¿conecta señor del año → su posición natal → dignidad → implicancia para el nativo?
4. ausencia_de_generico: ¿evita frases vacías ("período de transformación", "momento de cambio")?
5. sintesis: ¿produce una lectura integrada o es solo una lista de datos desconectados?

Responde SOLO con JSON, sin texto extra:
{{
  "x": {{"coherencia_doctrinal":N,"especificidad":N,"multi_hop_reasoning":N,"ausencia_de_generico":N,"sintesis":N,"total":N}},
  "y": {{"coherencia_doctrinal":N,"especificidad":N,"multi_hop_reasoning":N,"ausencia_de_generico":N,"sintesis":N,"total":N}}
}}
"""


def evaluate_pair(ctx_a: str, ctx_b: str, resp_a: str, resp_b: str) -> dict:
    """
    Envía el par A/B al juez LLM y retorna los scores.
    La asignación X/Y es aleatoria para control de orden.
    """
    import random
    
    if random.random() < 0.5:
        x_is_a = True
        resp_x, resp_y = resp_a, resp_b
    else:
        x_is_a = False
        resp_x, resp_y = resp_b, resp_a
    
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="Eres un evaluador experto en astrología helenística clásica. Responde siempre con JSON válido.",
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT_TEMPLATE.format(resp_x=resp_x, resp_y=resp_y)
        }],
    )
    
    raw = response.content[0].text if response.content else "{}"
    
    try:
        scores = json.loads(raw)
        # Reasignar X/Y → A/B según el orden que usamos
        if x_is_a:
            return { "scores_a": scores.get("x", {}), "scores_b": scores.get("y", {}),
                     "total_a": scores.get("x", {}).get("total", 0),
                     "total_b": scores.get("y", {}).get("total", 0) }
        else:
            return { "scores_a": scores.get("y", {}), "scores_b": scores.get("x", {}),
                     "total_a": scores.get("y", {}).get("total", 0),
                     "total_b": scores.get("x", {}).get("total", 0) }
    except json.JSONDecodeError:
        return { "raw_judge_output": raw, "total_a": 0, "total_b": 0 }
```

---

## Cómo correr el experimento

```bash
# 1. Activar entorno virtual
cd d:/projects/ai-oracle
source .venv311/Scripts/activate   # Git Bash

# 2. Abu Engine debe estar corriendo en localhost:8000 con AUTH_ENABLED=false
#    (docker-compose up abu_engine — ya tiene AUTH_ENABLED=false en el compose)

# 3. ANTHROPIC_API_KEY debe estar configurada
export ANTHROPIC_API_KEY="sk-ant-..."

# 4. Correr
python scripts/kg_experiment/runner.py
```

Costo estimado: ~4 sujetos × 3 llamadas × ~800 tokens = ~10k tokens ≈ $0.15

---

## Estructura de output

```
data/kg_experiment/
  results_20260508_143022.json    ← resultados completos
```

Cada entrada del JSON:

```json
{
  "subject_id":   "einstein",
  "subject_name": "Einstein",
  "timestamp":    "2026-05-08T14:30:22.000Z",
  "context_a":    "╔══ LÍNEA DE TIEMPO ══╗\n...",
  "context_b":    "╔══ SEÑORÍOS ACTIVOS (KG) ══╗\n...",
  "response_a":   "Lilly responde con contexto A...",
  "response_b":   "Lilly responde con contexto B...",
  "scores": {
    "scores_a": { "coherencia_doctrinal": 3, "especificidad": 4, ... "total": 17 },
    "scores_b": { "coherencia_doctrinal": 4, "especificidad": 5, ... "total": 21 },
    "total_a": 17,
    "total_b": 21
  }
}
```

---

## Criterios de aceptación

- [ ] El runner corre sin errores para los 4 sujetos de prueba
- [ ] `data/kg_experiment/results_*.json` se genera con todos los campos
- [ ] Las respuestas A y B son distintas (el contexto diferente produce texto diferente)
- [ ] El juez LLM devuelve JSON parseable con scores numéricos
- [ ] El resumen imprime promedios A/B y el delta

---

## Lo que NO hace este spec

- **NO** persiste resultados en Firestore (archivo local es suficiente para el experimento)
- **NO** modifica las rutas Lilly de producción — es un runner externo de investigación
- **NO** usa Condición C (persistencia de grafo en Firestore) — eso es Fase 3 del KG
- **NO** evalúa la calidad del HF — eso es la validación empírica cuantitativa (ya completada)

---

## Commit sugerido

```
feat(kg): experiment runner — condition B vs baseline (KG-C03)

- scripts/kg_experiment/runner.py: fetches natal+bio, builds A/B contexts, calls Lilly, evaluates
- scripts/kg_experiment/assemble_context.py: Python replica of LÍNEA DE TIEMPO section
- scripts/kg_experiment/judge.py: blind LLM evaluation of A/B pairs
- scripts/kg_experiment/config.py: 4 test subjects (Einstein, Jung, Tesla, GS_004)
- data/kg_experiment/: output directory for results
```
