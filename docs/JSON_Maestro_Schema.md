# JSON Maestro Schema

## Overview

El JSON Maestro es la estructura semántica central de AI Oracle. Transforma los datos astronómicos crudos del Abu Engine en un formato interpretable que preserva la cosmología persa-medieval.

**Principios de diseño:**
- Determinístico: mismos inputs → mismo Maestro
- Sin invención de datos
- Organizado por temas astrológicos (no por planetas)
- Preparado para consumo por LLM o UI

## Estructura completa

```json
{
  "metadata": {
    "mode": "persian_cosmology",
    "calculated_by": "abu_engine",
    "interpreted_by": "lilly_engine",
    "version": "1.0",
    "generated_at": "2025-11-14T01:54:26.747048Z",
    "request_context": {
      "language": "es",
      "birthDate": "1978-07-05T21:15:00Z",
      "lat": -34.6037,
      "lon": -58.3816
    }
  },
  
  "cosmology_context": {
    "system": "persian_medieval",
    "key_principles": [
      "Four Qualities Framework (heat, cold, moisture, dryness)",
      "Four Elements (fire, air, water, earth)",
      "Planetary natures (Saturn cold+dry, Jupiter hot+moist, etc.)",
      "Essential and accidental dignities",
      "Lord of the Year methodology (Ṣāḥib al-Sana)",
      "Annual revolution as renewal of cosmic decree",
      "Use of profections, Fardars and lunar mansions for timing"
    ]
  },
  
  "year_overview": {
    "rs_location": null | "Buenos Aires",
    "ascendant_rs": {
      "sign": "Cancer" | null,
      "degree": 12.3 | null,
      "element": "water" | null
    },
    "sun_rs": {
      "sign": "Cancer",
      "house_rs": 6
    },
    "year_element": "water" | "fire" | "earth" | "air",
    "year_tone_keywords": [
      "emotional depth",
      "family focus",
      "inner work",
      "intuition",
      "healing",
      "memory"
    ]
  },
  
  "elemental_analysis": {
    "counts_by_element": {
      "fire": 4,
      "earth": 2,
      "air": 1,
      "water": 5
    },
    "dominant_element_reasoning": {
      "ascendant_element": "water" | null,
      "sun_element": "water",
      "angular_water_planets": ["Moon"],
      "additional_notes": "Derived from chart.planets and house positions (angularity)."
    },
    "interpretation": {
      "core_drivers": []
    }
  },
  
  "lord_of_year": {
    "candidates": {
      "time_lord": "Jupiter",
      "ascendant_ruler": "Moon"
    },
    "evaluation": {
      "angularity_scores": {
        "Jupiter": 1,
        "Moon": 4
      },
      "essential_dignity_scores": {
        "Jupiter": 5,
        "Moon": -4
      },
      "accidental_dignity_scores": {
        "Jupiter": 1,
        "Moon": 4
      }
    },
    "final_lord": "Jupiter",
    "lord_keywords": [
      "planet_nature: hot, moist"
    ]
  },
  
  "angularity_and_dignities": {
    "strong_planets": [
      {
        "planet": "Moon",
        "reason": "angular, essential_debility"
      }
    ],
    "weak_planets": [
      {
        "planet": "Sun",
        "reason": "essential_debility"
      }
    ],
    "combustion_flags": []
  },
  
  "rs_natal_interplay": {
    "rs_asc_falls_in_natal_house": null | 10,
    "rs_sun_falls_in_natal_house": null | 6,
    "themes_unlocked": [
      "Will be refined when RS–Natal overlay is fully integrated.",
      "Lunar mansion of the year: Al-Tarf"
    ]
  },
  
  "transits_contextualized": {
    "major_transits": [
      {
        "transit": "Saturn square natal Sun",
        "timing": "2025-11-15",
        "interpretation_depends_on_rs": "To be filled by rule-based engine or LLM layer."
      }
    ]
  },
  
  "monthly_windows": {
    "primary_by_sign": [
      {
        "month": 4,
        "sign": "Aries",
        "theme": "Derived from profection lord and house; to be refined."
      }
    ],
    "secondary_by_house": []
  },
  
  "critical_days": []
}
```

## Secciones explicadas

### 1. metadata
Contexto de generación y versión del Maestro.

### 2. cosmology_context
Marco conceptual del sistema persa usado (no cambia entre cartas).

### 3. year_overview
Vista general del año: elemento dominante, tono, posición del Sol/Asc en RS.

**Regla de year_element:**
- Conteo de planetas por elemento
- Peso extra (+2) para Asc y Sol
- Elemento mayoritario = elemento del año

**year_tone_keywords:**
- water: emotional depth, family focus, inner work, intuition, healing, memory
- fire: initiative, courage, visibility, risk-taking, leadership
- earth: stability, work, material consolidation, discipline
- air: ideas, communication, networks, mobility, learning

### 4. elemental_analysis
Conteos detallados y razonamiento para la dominancia elemental.

### 5. lord_of_year (Ṣāḥib al-Sana)
Planeta que gobierna el año según:
- Candidatos: time_lord (profecciones), ascendant_ruler, almuten de casa 1
- Evaluación: angularidad (1-4 pts), dignidad esencial (+5/-4), dignidad accidental
- final_lord: candidato con mayor suma

### 6. angularity_and_dignities
Clasificación de planetas fuertes/débiles según:
- Angularidad (casas 1, 4, 7, 10)
- Dignidades esenciales (domicilio, exaltación, detrimento, caída)
- Combustión

### 7. rs_natal_interplay
Temas desbloqueados por superposición RS–Natal (en desarrollo).

### 8. transits_contextualized
Tránsitos mayores con timing y contexto RS.

### 9. monthly_windows
Ventanas mensuales derivadas de profecciones.

### 10. critical_days
Días críticos calculados desde:
- Fronteras de mansiones lunares
- Tránsitos exactos
- Ángulos RS
- Almutens de tiempo

## Uso en código

```python
from lilly_engine.json_maestro import build_json_maestro

# Llamar a Abu Extended
chart_extended = abu_client.get("/api/astro/chart/extended", params={...})

# Construir Maestro
maestro = build_json_maestro(
    chart_extended,
    metadata_context={
        "language": "es",
        "birthDate": "1978-07-05T21:15:00Z",
        "lat": -34.6037,
        "lon": -58.3816
    }
)

# Usar Maestro para narrativa o UI
narrative = generate_narrative(maestro, language="es")
```

## Extensión

Para agregar nuevas secciones al Maestro:

1. Agregar función `_build_nueva_seccion(chart, extended)` en `json_maestro.py`
2. Llamar función en `build_json_maestro()`
3. Agregar clave al dict de retorno
4. Actualizar este schema
5. Actualizar `SYSTEM_PROMPT` en `narrative_engine.py` si la narrativa debe incluirla

**Principio clave:** El Maestro solo organiza datos de Abu; nunca inventa ni calcula.
