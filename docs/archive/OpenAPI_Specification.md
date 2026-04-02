# AI Oracle API – OpenAPI Specification

## Overview

API specification for AI Oracle services (Abu Engine + Lilly Engine).

**Base URLs:**
- Abu Engine: `https://abu-engine-503488473965.us-central1.run.app` (Cloud Run)
- Lilly Engine: `http://localhost:8001` (local dev) / TBD (Cloud Run)

---

## Abu Engine Endpoints

### GET /api/astro/chart

Compute natal chart (planets, houses, aspects).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `date` | string (ISO 8601) | Yes | Birth datetime (UTC) |
| `lat` | number | Yes | Birth latitude |
| `lon` | number | Yes | Birth longitude |

**Response:** `200 OK`
```json
{
  "planets": [
    {
      "name": "Sun",
      "longitude": 100.5,
      "latitude": 0.0,
      "speed": 0.9833,
      "sign": "Cancer",
      "house": 6,
      "retrograde": false
    }
  ],
  "houses": [
    {"house": 1, "longitude": 25.3, "sign": "Cancer"}
  ],
  "aspects": [
    {
      "planet1": "Sun",
      "planet2": "Moon",
      "aspect": "trine",
      "angle": 120.0,
      "orb": 2.5,
      "applying": true
    }
  ]
}
```

---

### GET /api/astro/chart/extended
Compute natal chart + Persian calculations (dignities, lots, fardars, profections, mansions, fixed stars).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `date` | string (ISO 8601) | Yes | Birth datetime (UTC) |
| `lat` | number | Yes | Birth latitude |
| `lon` | number | Yes | Birth longitude |

**Response:** `200 OK`
```json
{
  "base_chart": {
    "planets": [...],
    "houses": [...],
    "aspects": [...]
  },
  "extended": {
    "dignities": {
      "by_planet": [
        {
          "planet": "Sun",
          "sign": "Cancer",
          "essential": ["exaltation"],
          "accidental": ["angular"],
          "note": "Sun in Cancer (exaltation), angular (house 10)"
        }
      ]
    },
    "lots": {
      "fortuna": 150.2,
      "spirit": 200.5,
      "eros": 75.0,
      "necessity": 320.0
    },
    "fardars": {
      "current": {
        "major_lord": "Saturn",
        "major_start": "2020-01-01T00:00:00Z",
        "major_end": "2031-01-01T00:00:00Z",
        "sub_lord": "Mars",
        "sub_start": "2023-06-01T00:00:00Z",
        "sub_end": "2024-09-01T00:00:00Z"
      },
      "upcoming": [...]
    },
    "profections": {
      "year": {
        "age": 33,
        "house": 10,
        "sign": "Aries",
        "lord": "Mars"
      },
      "month": {
        "month_index": 4,
        "house": 2,
        "sign": "Gemini",
        "lord": "Mercury"
      }
    },
    "lunar_mansions": {
      "moon_mansion": {
        "number": 9,
        "name": "Al-Tarf",
        "longitude_range": [102.857, 115.714]
      }
    },
    "fixed_stars": {
      "conjunctions": [
        {
          "planet": "Sun",
          "star": "Regulus",
          "orb": 1.2,
          "star_longitude": 149.8
        }
      ]
    }
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing or invalid parameters
- `500 Internal Server Error`: Calculation failure

---

### GET /api/astro/forecast

Compute astrological forecast (transit intensity timeseries + peaks).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `birthDate` | string (ISO 8601) | Yes | Birth datetime |
| `lat` | number | Yes | Birth latitude |
| `lon` | number | Yes | Birth longitude |
| `start` | string (ISO 8601) | Yes | Forecast start date |
| `end` | string (ISO 8601) | Yes | Forecast end date |
| `step` | number | No | Days between data points (default: 1) |
| `horizon` | number | No | Peak detection window in days (default: 7) |

**Response:** `200 OK`
```json
{
  "timeseries": [
    {
      "date": "2024-01-01T00:00:00Z",
      "score": 65.3,
      "harmony_field": {
        "H_scalar": 65.3,
        "components": {},
        "model": {"paksa": "astro-geodetic", "baseline": "QAOA"},
        "geodesy": {"model": "WGS84"}
      }
    }
  ],
  "peaks": [
    {
      "date": "2024-03-15T00:00:00Z",
      "score": 92.1,
      "harmony_field": {
        "H_scalar": 92.1,
        "components": {},
        "model": {"paksa": "astro-geodetic", "baseline": "QAOA"},
        "geodesy": {"model": "WGS84"}
      },
      "is_peak": true
    }
  ]
}
```

---

### GET /api/astro/life-cycles

Compute major life cycles (Saturn Return, Uranus Opposition, etc.) and forward to Lilly for interpretation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `birthDate` | string (ISO 8601) | Yes | Birth datetime |
| `lat` | number | No | Birth latitude (optional) |
| `lon` | number | No | Birth longitude (optional) |

**Response:** `200 OK`
```json
{
  "astro_data": {
    "events": [
      {
        "cycle": "Saturn Return",
        "planet": "Saturn",
        "angle": 0,
        "approx": "2025-06-01T00:00:00Z"
      }
    ]
  },
  "interpretation": {
    "headline": "Ciclo de Retorno de Saturno",
    "narrative": "El Retorno de Saturno marca un periodo...",
    "actions": ["Revisar estructuras de vida", "Consolidar metas"],
    "astro_metadata": {"source": "openai"}
  }
}
```

---

### GET /api/astro/solar-return

Compute Solar Return chart for a given year.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `birthDate` | string (ISO 8601) | Yes | Birth datetime |
| `lat` | number | Yes | Solar Return latitude |
| `lon` | number | Yes | Solar Return longitude |
| `year` | number | No | Solar Return year (default: current year) |

**Response:** `200 OK`
```json
{
  "solar_return_datetime": "2024-06-21T12:30:00Z",
  "planets": [...],
  "aspects": [...],
  "score_summary": {
    "total_score": 75.5,
    "component_scores": {
      "angular_planets": 20.0,
      "benefic_aspects": 15.0
    }
  },
  "harmony_field": {
    // Ver definición canónica en whitepaper, sección 2.X
    "H_scalar": 75.5,
    "components": {
      "angular_planets": 20.0,
      "benefic_aspects": 15.0
    },
    "model": {"paksa": "astro-geodetic", "baseline": "modern_control_v1", "optimizer": "QAOA"},
    "geodesy": {"model": "WGS84"}
  }
}
```

---

### POST /api/ai/solar-return

Analyze Solar Return and suggest favorable relocation cities based on Ascendant elements.

**Request Body:**
```json
{
  "natal_chart": {
    "planets": [...],
    "houses": [...]
  },
  "solar_chart": {
    "planets": [...],
    "houses": [...]
  },
  "language": "es"
}
```

**Response:** `200 OK`
```json
{
  "best_locations": [
    {"city": "Buenos Aires", "country": "Argentina"},
    {"city": "Barcelona", "country": "Spain"}
  ],
  "location_details": [
    {
      "city": "Buenos Aires",
      "country": "Argentina",
      "latitude": -34.6,
      "longitude": -58.4,
      "reasoning": "Ascendente en Sagitario (elemento fuego), propicio para expansión."
    }
  ],
  "reasoning": "El Ascendente del Retorno Solar en tu ubicación actual es Virgo (tierra)...",
  "natal_ascendant": {
    "sign": "Cancer",
    "element": "water"
  },
  "solar_ascendant": {
    "sign": "Virgo",
    "element": "earth"
  },
  "astro_metadata": {
    "source": "openai"
  }
}
```

---

## Lilly Engine Endpoints

### POST /api/ai/interpret

Generate JSON Maestro (deterministic semantic layer) + optional narrative from birth data.

**Request Body:**
```json
{
  "birthDate": "1990-01-01T12:00:00Z",
  "lat": 40.7128,
  "lon": -74.0060,
  "language": "es",
  "include_narrative": true
}
```

**Response:** `200 OK`
```json
{
  "maestro": {
    "metadata": {
      "mode": "persian_cosmology",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "cosmology_context": {
      "elements": ["fire", "earth", "air", "water"],
      "qualities": ["hot", "cold", "moist", "dry"]
    },
    "year_overview": {
      "sun_rs": {
        "sign": "Cancer",
        "house": 6,
        "element": "water",
        "ruler": "Moon"
      },
      "asc_rs": {
        "sign": "Aquarius",
        "element": "air"
      },
      "year_element": "water",
      "year_tone_keywords": ["emotional", "introspective", "healing"]
    },
    "elemental_analysis": {
      "counts_by_element": {
        "fire": 2,
        "earth": 1,
        "air": 2,
        "water": 5
      },
      "dominant_element": "water",
      "dominant_keywords": ["intuitive", "empathetic", "deep"]
    },
    "lord_of_year": {
      "planet": "Jupiter",
      "element_by_sign": "water",
      "lord_keywords": ["expansion", "wisdom", "optimism"],
      "amplified_topics": ["family", "spirituality", "knowledge"]
    },
    "angularity_and_dignities": {
      "angular_planets": [
        {
          "planet": "Moon",
          "house": 10,
          "dignity": "angular",
          "essential": ["domicile"]
        }
      ],
      "succedent": [],
      "cadent": []
    },
    "rs_natal_interplay": {
      "themes_unlocked": ["emotional depth", "family focus"],
      "lunar_mansion": {
        "number": 9,
        "name": "Al-Tarf"
      }
    },
    "transits_contextualized": {
      "major_transits": [
        {
          "planet": "Saturn",
          "aspect": "square",
          "to_natal": "Moon",
          "approx": "2024-06-15T00:00:00Z"
        }
      ]
    },
    "monthly_windows": [
      {
        "month_index": 4,
        "house": 2,
        "sign": "Gemini",
        "lord": "Mercury",
        "note": "Profected house of the 4th month"
      }
    ],
    "critical_days": []
  },
  "narrative": "### Resumen Inicial\nEl año se presenta bajo el elemento agua..."
}
```

**Error Responses:**
- `400 Bad Request`: Abu Extended returned empty response
- `502 Bad Gateway`: Abu Engine failed (returned 500)
- `500 Internal Server Error`: Maestro construction failed

**Notes:**
- If `include_narrative: false` or OpenAI fails, `narrative` will be `null`
- Maestro generation is resilient; partial Abu failures result in empty subcalc sections
- Narrative failure does NOT fail the endpoint; Maestro always returned

---

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Codes:**
- `400 Bad Request`: Missing/invalid parameters or empty upstream response
- `500 Internal Server Error`: Calculation or internal processing failure
- `502 Bad Gateway`: Upstream service (Abu/Lilly) returned error

---

## Authentication

Currently: **None** (public endpoints for MVP).

Future: Bearer token authentication via `Authorization: Bearer <token>` header.

---

## Rate Limiting

Currently: **None**.

Future: 100 requests/hour per IP.

---

## Examples

### cURL: Get extended chart

```bash
curl -X GET "https://abu-engine-503488473965.us-central1.run.app/api/astro/chart/extended?date=1990-01-01T12:00:00Z&lat=40.7128&lon=-74.0060"
```

### Python: Generate Maestro + narrative

```python
import requests

response = requests.post(
    "http://localhost:8001/api/ai/interpret",
    json={
        "birthDate": "1990-01-01T12:00:00Z",
        "lat": 40.7128,
        "lon": -74.0060,
        "language": "es",
        "include_narrative": True
    }
)

data = response.json()
print(data["maestro"]["year_overview"])
print(data["narrative"])
```

### JavaScript (fetch): Life cycles

```javascript
const response = await fetch(
  'https://abu-engine-503488473965.us-central1.run.app/api/astro/life-cycles?birthDate=1990-01-01T12:00:00Z'
);
const data = await response.json();
console.log(data.interpretation.headline);
```

---

## Schemas

### Planet Object

```json
{
  "name": "Sun",
  "longitude": 100.5,
  "latitude": 0.0,
  "speed": 0.9833,
  "sign": "Cancer",
  "house": 6,
  "retrograde": false
}
```

### Aspect Object

```json
{
  "planet1": "Sun",
  "planet2": "Moon",
  "aspect": "trine",
  "angle": 120.0,
  "orb": 2.5,
  "applying": true
}
```

### House Object

```json
{
  "house": 1,
  "longitude": 25.3,
  "sign": "Cancer"
}
```

### Dignity Object

```json
{
  "planet": "Sun",
  "sign": "Cancer",
  "essential": ["exaltation"],
  "accidental": ["angular"],
  "note": "Sun in Cancer (exaltation), angular (house 10)"
}
```

### Fardar Object

```json
{
  "major_lord": "Saturn",
  "major_start": "2020-01-01T00:00:00Z",
  "major_end": "2031-01-01T00:00:00Z",
  "sub_lord": "Mars",
  "sub_start": "2023-06-01T00:00:00Z",
  "sub_end": "2024-09-01T00:00:00Z"
}
```

### Profection Object (Year)

```json
{
  "age": 33,
  "house": 10,
  "sign": "Aries",
  "lord": "Mars"
}
```

### Lunar Mansion Object

```json
{
  "number": 9,
  "name": "Al-Tarf",
  "longitude_range": [102.857, 115.714]
}
```

### Fixed Star Conjunction

```json
{
  "planet": "Sun",
  "star": "Regulus",
  "orb": 1.2,
  "star_longitude": 149.8
}
```

---

## Components

### HarmonyField (Reusable Schema)

> El objeto HarmonyField sigue la definición canónica establecida en el whitepaper, sección 2.X (“Astro-Geodetic Harmony Field”).

```json
{
  "H_scalar": 75.5,
  "components": {
    "angular_planets": 20.0,
    "benefic_aspects": 15.0
  },
  "model": {
    "paksa": "astro-geodetic",
    "baseline": "modern_control_v1",
    "optimizer": "QAOA"
  },
  "geodesy": {
    "model": "WGS84"
  }
}
```

---

## Versioning

Current API version: **v1** (implicit, no version prefix in URLs).

Future: `/v2/api/...` for breaking changes.

---

## Support

For API issues or questions:
- Check `docs/` folder for detailed guides
- Review error responses for diagnostic info
- Test with cURL examples above

---

**Last Updated:** 2024-01-15
