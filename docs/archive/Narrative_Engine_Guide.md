# Narrative Engine Guide

## Overview

El Narrative Engine transforma el JSON Maestro en texto interpretativo clásico usando GPT-4 bajo un contrato estricto que garantiza:

- Fidelidad a los datos (sin invención)
- Estructura determinística (7 secciones fijas)
- Tono apropiado al idioma (español sobrio, inglés clásico-poético, portugués suave)
- Sin conceptos modernos no-persas

## Arquitectura

```
JSON Maestro → generate_narrative() → GPT-4 → Texto estructurado
```

**Módulo:** `lilly_engine/narrative_engine.py`

## Contrato estricto

### Reglas obligatorias

1. **Solo leer del Maestro**
   - NUNCA inferir nuevos cálculos
   - NUNCA inventar posiciones, aspectos, dignidades o timing
   - NUNCA contradecir el Maestro

2. **Estructura determinística**
   - 7 secciones en orden fijo
   - Siempre incluir headers de sección
   - Mismo orden para todos los idiomas

3. **Marco conceptual**
   - SOLO conceptos presentes en el Maestro
   - Evitar frameworks no-persas (psicología moderna, tarot, etc.)
   - Mantener cosmología persa-medieval

4. **Tono y estilo**
   - Sin predicciones de peligro absolutas
   - Sin consejos psicológicos no fundamentados en el Maestro
   - Neutro culturalmente
   - Elegante pero accesible

## Estructura de la narrativa

### 1. Opening Overview (Resumen Inicial)
**Contenido:**
- Interpretar `year_element` del Maestro
- Resumir tono del año desde `year_tone_keywords`
- Referenciar Ascendente RS y Sol RS

**Ejemplo:**
```
El año se presenta bajo el elemento agua, lo que sugiere una 
tonalidad emocional y profunda. Se destacan temas como el enfoque 
en la familia, el trabajo interno y la sanación. El Sol se encuentra 
en Cáncer, específicamente en la sexta casa.
```

### 2. Elemental Dynamics (Dinámicas Elementales)
**Contenido:**
- Interpretar dominancia elemental desde `elemental_analysis.counts_by_element`
- Mencionar planetas angulares relevantes desde `angularity_and_dignities`

**Ejemplo:**
```
El elemento dominante es el agua, con cinco planetas alineados 
en esta categoría. La Luna, ubicada en un ángulo significativo, 
intensifica la conexión emocional y la intuición durante este periodo.
```

### 3. Lord of the Year (Señor del Año)
**Contenido:**
- Describir naturaleza del planeta desde `lord_of_year.lord_keywords`
- Explicar influencia en casas/temas
- Mencionar qué tópicos amplifica

**Ejemplo:**
```
Júpiter se erige como el señor del año, caracterizado por su 
naturaleza caliente y húmeda. Su influencia se siente en la expansión 
de temas relacionados con la familia, la espiritualidad y la búsqueda 
de significado.
```

### 4. Timing Layer (Capa de Tiempo)
**Contenido:**
- Profecciones (año + ventana mensual) desde `monthly_windows`
- Fardars (período mayor + subperíodo) desde `extended.fardars.current`
- Mansión lunar desde `rs_natal_interplay.themes_unlocked`

**Ejemplo:**
```
En términos de profecciones, se sugiere que el cuarto mes (Aries) 
será clave. La mansión lunar del año, Al-Tarf, también aportará 
un enfoque adicional en los temas de transformación.
```

### 5. Solar Return Overlay (Superposición del Retorno Solar)
**Contenido:**
- Temas RS desde `year_overview.sun_rs`
- Interacción RS–Natal desde `rs_natal_interplay`

**Ejemplo:**
```
Los temas del Retorno Solar destacan la importancia de la salud 
y el bienestar diario. La interacción entre el Sol del Retorno 
y su posición natal requiere una integración más profunda.
```

### 6. Critical Days and Transits (Días Críticos y Tránsitos)
**Contenido:**
- Listar timing anchors desde `transits_contextualized.major_transits`
- Mencionar días críticos desde `critical_days`
- Si listas vacías: indicar período de calma para reflexión

**Ejemplo:**
```
Actualmente, no se identifican tránsitos mayores ni días críticos 
señalados, lo que podría indicar un periodo de calma que permite 
la reflexión y el trabajo interno.
```

### 7. Closing Summary (Resumen Final)
**Contenido:**
- Sintetizar temas centrales
- Evitar predicciones de peligro
- Evitar consejos psicológicos no presentes en el Maestro

**Ejemplo:**
```
Este año, marcado por la influencia de Júpiter y el elemento agua, 
se enfoca en la profundidad emocional y la sanación familiar. 
La combinación de energía acuática y la posición de Júpiter sugiere 
un periodo propicio para la introspección.
```

## System Prompt

El prompt usado internamente en `narrative_engine.py`:

```python
SYSTEM_PROMPT = (
    "You are a Narrative Engine for Persian-medieval astrology.\n"
    "STRICT CONTRACT:\n"
    "- Read ONLY the provided JSON Maestro.\n"
    "- NEVER infer new calculations, positions, aspects, dignities, or timings.\n"
    "- NEVER contradict the Maestro.\n"
    "- Use ONLY concepts present in the Maestro; avoid non-Persian frameworks unless explicitly present.\n"
    "- Deterministic structure and section order. Return a single plain text block.\n"
    "LANGUAGE MODE: Use the language code provided (es|en|pt).\n"
    "STRUCTURE (fixed order, always include headers):\n"
    "1) Opening Overview – interpret year_element, tone, reference Ascendant RS and Sun RS.\n"
    "2) Elemental Dynamics – interpret elemental dominance and mention angular planets.\n"
    "3) Lord of the Year – nature, house influence, amplified topics.\n"
    "4) Timing Layer – profections (year + monthly), Fardars (major+sub), lunar mansion.\n"
    "5) Solar Return Overlay – RS themes and any RS–Natal interplay present.\n"
    "6) Critical Days and Transits – timing anchors with context (list what exists).\n"
    "7) Closing Summary – highlight core themes; avoid danger predictions or non-sourced advice.\n"
    "STYLE:\n"
    "- es: sobrio, elegante, neutro-cultural.\n"
    "- en: concise, classical-poetic.\n"
    "- pt: suave, fluido.\n"
)
```

## Uso en código

### Generación básica

```python
from lilly_engine.narrative_engine import generate_narrative

narrative = generate_narrative(maestro, language="es")
print(narrative)
```

### Integración en endpoint

```python
@app.post("/api/ai/interpret")
def interpret_astro_data(data: MaestroRequest):
    # 1. Llamar a Abu Extended
    chart_extended = abu_client.get("/api/astro/chart/extended", ...)
    
    # 2. Construir Maestro
    maestro = build_json_maestro(chart_extended, metadata_context)
    
    # 3. Generar narrativa si se solicita
    narrative_text = None
    if data.include_narrative:
        try:
            narrative_text = generate_narrative(maestro, data.language or "es")
        except Exception:
            narrative_text = None  # Fail gracefully
    
    return {"maestro": maestro, "narrative": narrative_text}
```

## Configuración

### Variables de entorno

```bash
OPENAI_API_KEY=sk-proj-...              # Obligatoria
OPENAI_NARRATIVE_MODEL=gpt-4o-mini      # Opcional (default: gpt-4o-mini)
```

### Modelos recomendados

- `gpt-4o-mini` (default): Balance latencia/calidad, ideal para narrativa estructurada
- `gpt-4o`: Mayor calidad en lenguaje complejo, ~2x latencia
- `gpt-4-turbo`: Legacy, no recomendado para nueva integración

## Ejemplos de output

### Español (sobrio, elegante)

```
### Resumen Inicial
El año se presenta bajo el elemento agua, lo que sugiere una 
tonalidad emocional y profunda. Se destacan temas como el enfoque 
en la familia, el trabajo interno y la sanación.

### Dinámicas Elementales
El elemento dominante es el agua, con cinco planetas alineados 
en esta categoría. La Luna, ubicada en un ángulo significativo...
```

### English (concise, classical-poetic)

```
### Opening Overview
This year unfolds under the element of water, suggesting emotional 
depth and introspective focus. Themes of family, inner work, and 
healing emerge prominently.

### Elemental Dynamics
Water dominates with five planets aligned in this element. The Moon, 
positioned at a significant angle...
```

### Português (suave, fluido)

```
### Visão Inicial
O ano se apresenta sob o elemento água, sugerindo uma tonalidade 
emocional e profunda. Destacam-se temas como o foco na família, 
o trabalho interno e a cura.

### Dinâmicas Elementais
O elemento dominante é a água, com cinco planetas alinhados 
nesta categoria. A Lua, localizada em um ângulo significativo...
```

## Testing

### Test con mock de OpenAI

```python
# lilly_engine/tests/test_narrative_engine.py
def test_generate_narrative_basic_monkeypatch(monkeypatch):
    monkeypatch.setattr(ne, 'OpenAI', DummyOpenAI())
    
    maestro = {
        "metadata": {"mode": "persian_cosmology"},
        "year_overview": {"year_element": "water"}
    }
    out = ne.generate_narrative(maestro, language="es")
    
    assert isinstance(out, str)
    assert out.strip() != ""
```

### Test E2E con API real

```bash
# Cargar .env
Get-Content .env | ForEach-Object { 
    if ($_ -match '^([^=]+)=(.+)$') { 
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') 
    } 
}

# Ejecutar test
python test_narrative_live.py
```

## Troubleshooting

### Problema: narrative retorna null

**Causa:** `OPENAI_API_KEY` no está configurada o es inválida.

**Solución:**
```bash
# Verificar key
echo $env:OPENAI_API_KEY

# Cargar desde .env
Get-Content .env | ForEach-Object { ... }
```

### Problema: Narrativa demasiado corta

**Causa:** `max_tokens` muy bajo en `narrative_engine.py`.

**Solución:** Incrementar `max_tokens` en la llamada a GPT (default: 2000).

### Problema: Narrativa inventa datos

**Causa:** Prompt no está siendo respetado por el modelo.

**Solución:** 
1. Verificar que `SYSTEM_PROMPT` está siendo incluido
2. Considerar usar `temperature=0` para mayor determinismo
3. Agregar ejemplos few-shot al prompt si es necesario

### Problema: Secciones fuera de orden

**Causa:** GPT no está siguiendo la estructura.

**Solución:** Reforzar numeración en el prompt y agregar ejemplos.

## Extensión

### Agregar nueva sección a la narrativa

1. Actualizar `SYSTEM_PROMPT` en `narrative_engine.py`:
```python
"8) New Section – description of what to include.\n"
```

2. Asegurar que el Maestro contiene los datos necesarios para esa sección

3. Actualizar tests para verificar presencia de la nueva sección

4. Actualizar este documento con ejemplo de la sección

### Cambiar estilo por idioma

Modificar reglas de estilo en `SYSTEM_PROMPT`:

```python
"STYLE:\n"
"- es: [nuevo estilo español].\n"
"- en: [nuevo estilo inglés].\n"
```

### Agregar nuevo idioma

1. Agregar código de idioma a `_language_tag()`:
```python
def _language_tag(language: str) -> str:
    lang = (language or "es").lower()
    if lang not in {"es", "en", "pt", "fr"}:  # Agregar "fr"
        lang = "es"
    return lang
```

2. Agregar reglas de estilo al `SYSTEM_PROMPT`

3. Actualizar tests

## Performance

Latencia típica (gpt-4o-mini):
- Maestro pequeño (~2KB): ~1-2s
- Maestro completo (~10KB): ~2-4s
- Con transits/fardars detallados: ~3-5s

Optimizaciones:
- Usar `gpt-4o-mini` en lugar de `gpt-4o` (-50% latencia)
- Cachear narrativas idénticas por hash de Maestro
- Generar narrativa async si la UI no la necesita inmediatamente
