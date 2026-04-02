# Solar Return Ranking Implementation

## Overview
Persian/Hellenistic astrology-based ranking system for Solar Return relocation analysis. This module replaces the previous heuristic-based approach with proper astronomical calculations per city.

## Endpoint

```
GET /api/astro/solar-return/ranking
```

### Parameters
- `birthDate` (required): ISO datetime of natal birth (e.g., `1990-07-05T12:00:00Z`)
- `year` (optional): Target Solar Return year (default: current year)
- `cities` (optional): Comma-separated list of city names (default: all 16 predefined cities)
- `top_n` (optional): Number of top recommendations to show (default: 3)

### Response Structure

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
        "dignities": {
          "asc_ruler_dignity": {"planet": "Mars", "dignity": "peregrine", "score": 0},
          "mc_ruler_dignity": {"planet": "Saturn", "dignity": "peregrine", "score": 0.0},
          "all_planets_score": 0.0,
          "total": 0.0
        },
        "angularity": {
          "angular_planets": [],
          "note": "House data not yet implemented",
          "total": 6
        },
        "solar_conditions": {
          "conditions": [
            {"planet": "Jupiter", "state": "combust", "score": -10}
          ],
          "total": -10
        },
        "aspects_reception": {
          "aspects": [
            {"planets": "Sun trine Moon", "reception": false, "score": 3},
            {"planets": "Venus sextile Saturn", "reception": false, "score": 3}
          ],
          "total": 15
        },
        "sect": {
          "sect": "diurnal",
          "note": "House-based sect not yet implemented, using simplified logic",
          "total": 0
        }
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

## Scoring Criteria (Persian/Hellenistic Astrology)

### 1. Essential Dignities (35 points max)
Evaluates planetary strength based on zodiac sign placement:
- **Domicile** (+5): Planet in its home sign (e.g., Mars in Aries)
- **Exaltation** (+4): Planet in exaltation sign (e.g., Sun in Aries at 19°)
- **Detriment** (-5): Planet in exile (opposite of domicile)
- **Fall** (-4): Planet in fall (opposite of exaltation)
- **Peregrine** (0): No essential dignity

**Weighting:**
- ASC ruler: 2× multiplier
- MC ruler: 1.5× multiplier
- All other planets: 0.5× multiplier each

### 2. Angularity (25 points max) [SIMPLIFIED - MVP]
Evaluates planets in angular houses (1, 4, 7, 10):
- **Benefics** (Jupiter, Venus): +8 points each
- **Luminaries** (Sun, Moon): +5-6 points
- **Malefics** (Saturn, Mars): +3 if dignified, -2 if poorly placed

**Current Status:** Simplified for MVP. House calculation not yet integrated. Uses dignity-based proxy:
- Benefics: +3 points
- Well-dignified malefics: +1 point

### 3. Solar Conditions (15 points max)
Evaluates planetary relationship to the Sun:
- **Cazimi** (+10): Within 17 arcminutes of exact conjunction ("in the heart of the Sun")
- **Combust** (-10): Within 8° of Sun (but not cazimi)
- **Under the Beams** (-5): Within 17° of Sun (but not combust)

**Calculation:**
```python
def check_cazimi(planet_lon, sun_lon):
    distance = abs(planet_lon - sun_lon)
    if distance > 180:
        distance = 360 - distance
    return distance < 0.283  # 17 arcminutes

def check_combust(planet_lon, sun_lon):
    distance = abs(planet_lon - sun_lon)
    if distance > 180:
        distance = 360 - distance
    return 0.283 < distance < 8

def check_under_beams(planet_lon, sun_lon):
    distance = abs(planet_lon - sun_lon)
    if distance > 180:
        distance = 360 - distance
    return distance < 17
```

### 4. Aspects with Reception (15 points max)
Evaluates harmonious and tense aspects between planets:
- **Trine/Sextile with reception:** +5 points
- **Trine/Sextile without reception:** +3 points
- **Square/Opposition with reception:** +1 point (mitigated by reception)
- **Square/Opposition without reception:** -3 points
- **Conjunction:** 0 points (neutral, depends on planets involved)

**Mutual Reception:** Two planets each in a sign ruled by the other (e.g., Mars in Libra, Venus in Aries).

### 5. Sect (10 points max) [SIMPLIFIED - MVP]
Evaluates alignment with diurnal/nocturnal chart quality:
- **Diurnal charts** (Sun above horizon): Favor Jupiter, avoid Saturn in angular houses
- **Nocturnal charts** (Sun below horizon): Favor Venus, avoid Mars in angular houses

**Current Status:** Simplified for MVP. Uses dignities of sect benefics (Jupiter for diurnal, Venus for nocturnal):
- Well-dignified sect benefic: +5 points

**Simplified Sect Determination:**
```python
def is_diurnal_chart(chart):
    sun = next((p for p in chart['planets'] if p['name'] == 'Sun'), None)
    # Simplified: Sun in upper half of zodiac (0-180°) = diurnal
    return (sun['lon'] % 360) < 180
```

## Predefined Cities (16 total)

### Fire Element
- Dubai (25.2048, 55.2708) - Middle East
- Los Angeles (34.0522, -118.2437) - North America
- Barcelona (41.3851, 2.1734) - Europe
- Sydney (-33.8688, 151.2093) - Oceania

### Earth Element
- Zurich (47.3769, 8.5417) - Europe
- Singapore (1.3521, 103.8198) - Asia
- Toronto (43.6532, -79.3832) - North America
- Copenhagen (55.6761, 12.5683) - Europe

### Air Element
- London (51.5074, -0.1278) - Europe
- Amsterdam (52.3676, 4.9041) - Europe
- San Francisco (37.7749, -122.4194) - North America
- Berlin (52.5200, 13.4050) - Europe

### Water Element
- Venice (45.4408, 12.3155) - Europe
- Rio de Janeiro (-22.9068, -43.1729) - South America
- Lisbon (38.7223, -9.1393) - Europe
- Buenos Aires (-34.6037, -58.3816) - South America

## Example Request

```bash
curl "http://localhost:8000/api/astro/solar-return/ranking?\
birthDate=1990-07-05T12:00:00Z&\
year=2025&\
cities=London,Zurich,Singapore&\
top_n=3"
```

## Implementation Files

### Core Module
- **`abu_engine/core/solar_return_ranking.py`**: Main ranking logic
  - `score_solar_return_location()`: Calculates SR chart and scores for a single city
  - `rank_solar_return_locations()`: Ranks multiple cities, returns top N
  - `score_dignities()`: Essential dignities scoring (35 pts)
  - `score_angularity()`: Angular house scoring (25 pts, simplified)
  - `score_solar_conditions()`: Cazimi/combust/under beams scoring (15 pts)
  - `score_aspects_reception()`: Aspect scoring with reception (15 pts)
  - `score_sect()`: Sect affinity scoring (10 pts, simplified)

### Dependencies
- **`core.chart.solar_return_chart()`**: Calculates Solar Return moment and chart
- **`core.dignities.get_planet_dignity()`**: Returns dignity kind and score
- **`core.dignities.get_ruler()`**: Returns planetary ruler of a sign

### API Endpoint
- **`abu_engine/main.py`**: FastAPI route `/api/astro/solar-return/ranking`

## Future Enhancements (Post-MVP)

### 1. House System Integration
Currently, angularity and sect scoring are simplified because `chart_json()` does not populate `house` fields for planets. **Next steps:**
- Integrate `houses_swiss.py` to calculate topocentric houses for SR location
- Add `asc_sign`, `mc_sign`, and `house` fields to `PlanetDTO`
- Update `score_angularity()` to use real angular house data
- Update `score_sect()` to use Sun's actual house position

### 2. Advanced Reception Checks
Current implementation only checks basic mutual reception (ruler swap). **Enhancements:**
- Exaltation-based reception (planet A in exaltation sign of planet B)
- Triplicity/term/face-based reception
- Mixed reception (one planet by domicile, other by exaltation)

### 3. Specialized Weights for SR Goals
Different weights per use case:
- **Career-focused SR**: Emphasize MC ruler dignity, 10th house angularity
- **Relationship-focused SR**: Emphasize Venus/7th house, reception aspects
- **Health-focused SR**: Emphasize ASC ruler, 6th house, malefic placements

### 4. Historical Validation
Test algorithm against known favorable/unfavorable SR years for historical figures to validate scoring accuracy.

### 5. Expand City Database
- Add user-defined custom cities
- Integrate `cities.json` database (20,000+ cities) for full global coverage
- Add timezone-aware calculations

## Testing

### Unit Tests
```bash
# Run from abu_engine directory
pytest tests/test_solar_return_ranking.py
```

### Manual Testing
```bash
# Test with default cities (all 16)
curl "http://localhost:8000/api/astro/solar-return/ranking?\
birthDate=1990-07-05T12:00:00Z&year=2025"

# Test with specific cities
curl "http://localhost:8000/api/astro/solar-return/ranking?\
birthDate=1990-07-05T12:00:00Z&\
year=2025&\
cities=London,Dubai,Buenos Aires&\
top_n=2"

# Test invalid city handling
curl "http://localhost:8000/api/astro/solar-return/ranking?\
birthDate=1990-07-05T12:00:00Z&\
cities=Paris"
# Expected: 400 error with available cities list
```

## Performance Considerations

- **Calculation Time:** ~2-3 seconds per city (includes SR moment calculation + chart generation)
- **Optimization:** SR calculations run sequentially; could parallelize with `asyncio` for 16+ cities
- **Caching:** Consider caching SR moments for common birth dates/years

## References

- **Persian Astrology Dignities:** `docs/persian_calculations.md`
- **Solar Return API:** `docs/Solar_Return_API.md`
- **Dignity Tables:** `abu_engine/core/dignities.py`
- **OpenAI Assistant Integration:** Can use this endpoint via `abu_get_solar_return_ranking` tool

---

**Version:** 1.0.0  
**Date:** 2025-11-05  
**Author:** AI Oracle Team
