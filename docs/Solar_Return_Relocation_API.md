# Solar Return Relocation API

## Overview

This document now covers two complementary paths:

1) Lilly (AI narrative, heuristic elements) → POST /api/ai/solar-return
2) Abu (cálculo astronómico + ranking persa) → GET /api/astro/solar-return/ranking

The Abu ranking computes a complete Solar Return per city (topocentric), assigns houses with Placidus, evaluates essential dignities, angularity, solar conditions (cazimi/combust), reception in aspects, and sect. It returns a scored, ordered list of cities.

## Endpoint

```
POST /api/ai/solar-return
```

**Service**: Lilly Engine (port 8001)

## Request Body

```json
{
  "natal_chart": {
    "planets": [
      {
        "name": "Sun",
        "sign": "Cancer",
        "longitude": 120.5
      }
    ]
  },
  "solar_chart": {
    "planets": [
      {
        "name": "Sun", 
        "sign": "Cancer",
        "longitude": 120.1
      }
    ]
  },
  "language": "es"
}
```

### Parameters

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `natal_chart` | object | Yes | - | Natal chart data with planets array |
| `solar_chart` | object | Yes | - | Solar return chart data with planets array |
| `language` | string | No | `"es"` | Response language: `es`, `en`, `pt`, `fr` |

### Chart Format

Both `natal_chart` and `solar_chart` must include a `planets` array with at least the Sun:

```json
{
  "planets": [
    {
      "name": "Sun",
      "sign": "Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces",
      "longitude": 0-360
    }
  ]
}
```

## Response

```json
{
  "best_locations": [
    "Lisbon",
    "Rio de Janeiro", 
    "Venice"
  ],
  "location_details": [
    {
      "city": "Lisbon",
      "coordinates": {
        "lat": 38.7223,
        "lon": -9.1393
      },
      "element": "water",
      "region": "Europe",
      "compatibility": "high"
    }
  ],
  "reasoning": "El Ascendente natal en Cancer (water) se combina con el Ascendente del Retorno Solar en Cancer (water)...",
  "natal_ascendant": {
    "sign": "Cancer",
    "element": "water"
  },
  "solar_ascendant": {
    "sign": "Cancer", 
    "element": "water"
  },
  "astro_metadata": {
    "source": "heuristic",
    "model": null,
    "language": "es",
    "cities_analyzed": 16
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `best_locations` | string[] | Top 2-3 recommended cities for favorable solar return |
| `location_details` | object[] | Detailed info about each recommended location |
| `reasoning` | string | Multilingual explanation of recommendations |
| `natal_ascendant` | object | Natal Ascendant sign and element |
| `solar_ascendant` | object | Solar Return Ascendant sign and element |
| `astro_metadata` | object | Analysis metadata including source and language |

### Location Details Object

```json
{
  "city": "Lisbon",
  "coordinates": {
    "lat": 38.7223,
    "lon": -9.1393
  },
  "element": "water",
  "region": "Europe",
  "compatibility": "high|moderate"
}
```

## Astrological Logic

### Element Analysis

The API analyzes Ascendant elements based on zodiac sign classification:

**Fire Signs**: Aries, Leo, Sagittarius
- Traits: Energy, initiative, action
- Compatible with: Air, Fire

**Earth Signs**: Taurus, Virgo, Capricorn
- Traits: Stability, practicality, structure
- Compatible with: Water, Earth

**Air Signs**: Gemini, Libra, Aquarius
- Traits: Communication, intellect, ideas
- Compatible with: Fire, Air

**Water Signs**: Cancer, Scorpio, Pisces
- Traits: Emotion, intuition, depth
- Compatible with: Earth, Water

### City Database

The API includes 16 curated cities across 4 elements and regions:

**Fire Cities** (energetic, entrepreneurial):
- Dubai, Los Angeles, Barcelona, Sydney

**Earth Cities** (stable, practical):
- Zurich, Singapore, Toronto, Copenhagen

**Air Cities** (intellectual, communicative):
- London, Amsterdam, San Francisco, Berlin

**Water Cities** (emotional, creative):
- Venice, Rio de Janeiro, Lisbon, Buenos Aires

### Relocation Strategy

1. **Element Compatibility**: Finds cities where the relocated Ascendant would be in a compatible element
2. **Mode Analysis**: Considers Cardinal/Fixed/Mutable qualities for timing
3. **Geographic Diversity**: Suggests cities across different regions
4. **Compatibility Ranking**: Prioritizes "high" compatibility matches

## Usage Examples

### Example 1: Water Ascendant (Cancer)

**Request:**
```bash
curl -X POST http://localhost:8001/api/ai/solar-return \
  -H "Content-Type: application/json" \
  -d '{
    "natal_chart": {
      "planets": [{"name": "Sun", "sign": "Cancer", "longitude": 120.5}]
    },
    "solar_chart": {
      "planets": [{"name": "Sun", "sign": "Cancer", "longitude": 120.1}]
    },
    "language": "es"
  }'
```

**Response:**
```json
{
  "best_locations": ["Venice", "Rio de Janeiro", "Lisbon"],
  "reasoning": "El Ascendente natal en Cancer (water) se combina con el Ascendente del Retorno Solar en Cancer (water). Las siguientes ubicaciones ofrecen Ascendentes más favorables para este año: Venice, Rio de Janeiro, Lisbon.",
  "natal_ascendant": {"sign": "Cancer", "element": "water"},
  "solar_ascendant": {"sign": "Cancer", "element": "water"}
}
```

### Example 2: Fire Ascendant with English Response

**Request:**
```json
{
  "natal_chart": {
    "planets": [{"name": "Sun", "sign": "Aries", "longitude": 15.0}]
  },
  "solar_chart": {
    "planets": [{"name": "Sun", "sign": "Aries", "longitude": 15.2}]
  },
  "language": "en"
}
```

**Response:**
```json
{
  "best_locations": ["Dubai", "Los Angeles", "Barcelona"],
  "reasoning": "The natal Ascendant in Aries (fire) combines with the Solar Return Ascendant in Aries (fire). The following locations offer more favorable Ascendants for this year: Dubai, Los Angeles, Barcelona.",
  "astro_metadata": {
    "language": "en"
  }
}
```

### Example 3: Mixed Elements

**Request:**
```json
{
  "natal_chart": {
    "planets": [{"name": "Sun", "sign": "Gemini", "longitude": 75.0}]
  },
  "solar_chart": {
    "planets": [{"name": "Sun", "sign": "Gemini", "longitude": 75.1}]
  },
  "language": "pt"
}
```

**Response (Air element → Fire/Air cities):**
```json
{
  "best_locations": ["London", "Amsterdam", "San Francisco"],
  "reasoning": "O Ascendente natal em Gemini (air) combina-se com o Ascendente do Retorno Solar em Gemini (air)...",
  "astro_metadata": {
    "language": "pt"
  }
}
```

## Error Handling

### 400 Bad Request - Insufficient Data

```json
{
  "detail": "Error interpreting solar return: Insufficient chart data to analyze"
}
```

**Response:**
```json
{
  "best_locations": [],
  "reasoning": "Insufficient chart data to analyze",
  "astro_metadata": {
    "source": "heuristic",
    "model": null,
    "language": "es"
  }
}
```

### 400 Bad Request - Invalid Input

```json
{
  "detail": "Error interpreting solar return: 'NoneType' object is not iterable"
}
```

**Cause**: Missing required fields in request body

## Integration with Abu Engine

The Solar Return Relocation API is designed to work with Abu Engine's `/api/astro/solar-return` endpoint:

```javascript
// Step 1: Get Solar Return chart from Abu
const solarReturn = await fetch(
  `http://abu_engine:8000/api/astro/solar-return?birthDate=1990-01-01T12:00:00Z&lat=40.7128&lon=-74.0060`
);
const { solar_return_datetime, planets, aspects } = await solarReturn.json();

// Step 2: Get natal chart
const natalChart = await fetch(
  `http://abu_engine:8000/api/astro/chart?date=1990-01-01T12:00:00Z&lat=40.7128&lon=-74.0060`
);
const { positions } = await natalChart.json();

// Step 3: Get relocation recommendations from Lilly
const relocation = await fetch(
  'http://lilly_engine:8001/api/ai/solar-return',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      natal_chart: { planets: positions },
      solar_chart: { planets },
      language: 'es'
    })
  }
);
const { best_locations, reasoning } = await relocation.json();
```

## Technical Notes

### Current Limitations

1. **Ascendant Approximation**: Uses Sun sign as proxy for Ascendant (actual ASC calculation requires birth time)
2. **Simplified Element Logic**: Uses basic element compatibility rules
3. **Fixed City Database**: 16 pre-defined cities (extensible in `RELOCATION_CITIES`)
4. **Heuristic-Only**: No OpenAI integration yet (future enhancement)

### Future Enhancements

- [ ] OpenAI integration for narrative interpretations
- [ ] Actual Ascendant calculation from birth time
- [ ] Dynamic city database with API integration
- [ ] House cusp analysis for each location
- [ ] Expanded to include MC (Midheaven) relocation
- [ ] Historical event correlation per city

### Performance

- **Response time**: < 50ms (heuristic only)
- **Memory**: ~2KB per request
- **Concurrency**: Thread-safe, supports multiple simultaneous requests

## Multilingual Support

The API supports 4 languages with culturally adapted reasoning:

| Language | Code | Tone |
|----------|------|------|
| Spanish | `es` | Introspective, poetic |
| English | `en` | Practical, action-oriented |
| Portuguese | `pt` | Emotional, relationship-focused |
| French | `fr` | Poetic, philosophical |

Template example (Spanish):
```
El Ascendente natal en {sign} ({element}) se combina con el Ascendente del Retorno Solar en {sign} ({element}).

Las siguientes ubicaciones ofrecen Ascendentes más favorables para este año: {cities}.

Estas ciudades enfatizan elementos compatibles que apoyan el crecimiento y la evolución personal.
```

## Testing

Run the test suite:

```bash
python lilly_engine/test_solar_return_interpret.py
```

**Expected output:**
```
=== Solar Return Interpretation Tests ===

✓ All imports successful
✓ Sign attributes working correctly
✓ City database loaded (16 cities)
✓ Location finder working (3 recommendations)
✓ interpret_solar_return function working
✓ Solar Return endpoint registered
✓ Multilingual support working (4 languages)

=== Results: 7/7 tests passed ===
```

## See Also

- [Solar Return Chart API](./Solar_Return_API.md) - Abu Engine solar return calculations
- [Multilingual Support](../lilly_engine/MULTILINGUAL.md) - Language detection and prompts
- [AI Interpretation API](../README.md#lilly-engine) - Main interpretation endpoint

---

# Abu Solar Return Ranking API (Persian/Hellenistic)

## Endpoint

```
GET /api/astro/solar-return/ranking
```

**Service**: Abu Engine (port 8000)

### Query Parameters

| Name | Required | Example | Description |
|------|----------|---------|-------------|
| `birthDate` | Yes | `1990-07-05T12:00:00Z` | Natal birth datetime (ISO 8601) |
| `year` | No | `2025` | Solar Return year (defaults to current) |
| `cities` | No | `London,Zurich,Singapore` | Comma-separated list; if omitted, analyzes all 16 predefined cities |
| `top_n` | No | `3` | Number of top cities to return |

### Response

```json
{
  "top_recommendations": ["London", "Zurich", "Singapore"],
  "rankings": [
    {
      "city": "London",
      "coordinates": {"lat": 51.5074, "lon": -0.1278},
      "region": "Europe",
      "total_score": 15.0,
      "breakdown": {
        "dignities": { "total": 0.0, "asc_ruler_dignity": {"planet": "Mars", "dignity": "peregrine", "score": 0}},
        "angularity": { "total": 6, "angular_planets": [] },
        "solar_conditions": { "total": -10, "conditions": [{"planet": "Jupiter", "state": "combust", "score": -10}] },
        "aspects_reception": { "total": 15, "aspects": [{"planets": "Sun trine Moon", "reception": false, "score": 3}] },
        "sect": { "sect": "diurnal", "total": 0 }
      },
      "chart_summary": {
        "asc_sign": "Aries",
        "mc_sign": "Capricorn",
        "solar_return_datetime": "2025-07-05T11:17:48.750000+00:00"
      }
    }
  ],
  "criteria": "Persian/Hellenistic (dignities, angularity, sect, reception, solar conditions)",
  "cities_analyzed": 3,
  "year": 2025
}
```

### Scoring Criteria

- Essential dignities (35): domicilio, exaltación, destierro, caída (ASC/MC rulers prioritized)
- Angularity (25): benéficos angulares bonificados; maléficos angulares ponderados por dignidad
- Solar conditions (15): cazimi (+10), combust (-10), bajo rayos (-5)
- Aspects + reception (15): trino/sextil (+3/+5 con recepción), cuadratura/oposición (-3/+1 con recepción)
- Sect (10): diurna favorece Júpiter angular/sucedente; nocturna favorece Venus; evita maléficos angulares

### Notes

- Topocéntrico por ciudad: calcula la carta de RS exacta por lugar y hora, y las casas (Placidus).
- Fallbacks: si el cálculo de casas falla en un edge-case, el endpoint sigue respondiendo con un modo simplificado para Angularidad/Secta.
- Ciudades predefinidas: 16 (Dubai, Los Angeles, Barcelona, Sydney, Zurich, Singapore, Toronto, Copenhagen, London, Amsterdam, San Francisco, Berlin, Venice, Rio de Janeiro, Lisbon, Buenos Aires).

### Example (curl)

```bash
curl "http://localhost:8000/api/astro/solar-return/ranking?birthDate=1990-07-05T12:00:00Z&year=2025&cities=London,Zurich,Singapore&top_n=3"
```
