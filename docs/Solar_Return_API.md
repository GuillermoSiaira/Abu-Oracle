# Solar Return Endpoint - Abu Engine

## Overview

The Solar Return (Revolución Solar) endpoint calculates the exact moment when the transiting Sun returns to its natal longitude. This is a key astrological technique for annual forecasting.

## Endpoint

```
GET /api/astro/solar-return
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `birthDate` | string (ISO) | Yes | Natal birth date and time (e.g., `1990-07-05T12:00:00Z`) |
| `lat` | float | Yes | Latitude for the solar return location |
| `lon` | float | Yes | Longitude for the solar return location |
| `year` | integer | No | Target year (defaults to current year) |

## Response Structure

```json
{
  "solar_return_datetime": "2025-07-05T14:23:45+00:00",
  "birth_date": "1990-07-05T12:00:00+00:00",
  "location": {"lat": 40.7128, "lon": -74.0060},
  "year": 2025,
  "planets": [
    {"name": "Sun", "lon": 103.12, "sign": "Cancer", "house": null},
    {"name": "Moon", "lon": 245.8, "sign": "Sagittarius", "house": null},
    ...
  ],
  "aspects": [
    {"a": "Sun", "b": "Mars", "type": "trine", "orb": 2.1, "angle": 120},
    ...
  ],
  "score_summary": {
    "total_score": 4.5,
    "num_aspects": 3,
    "interpretation": "favorable"
  }
}
```

## Example Requests

### Basic Solar Return (current year)

```bash
GET /api/astro/solar-return?birthDate=1990-07-05T12:00:00Z&lat=40.7128&lon=-74.0060
```

### Solar Return for specific year

```bash
GET /api/astro/solar-return?birthDate=1990-07-05T12:00:00Z&lat=40.7128&lon=-74.0060&year=2025
```

### Solar Return for different location (relocation)

```bash
GET /api/astro/solar-return?birthDate=1985-03-15T08:30:00Z&lat=51.5074&lon=-0.1278&year=2024
```

## How It Works

1. **Natal Sun Position**: Calculates the exact ecliptic longitude of the Sun at birth
2. **Binary Search**: Uses iterative refinement to find when the transiting Sun returns to that exact position
3. **Chart Generation**: Calculates a full birth chart for that precise moment
4. **Scoring**: Applies aspect weights to generate a favorability score

## Precision

- The solar return time is calculated with **~1 minute precision**
- The Sun's position at the return matches the natal position within **0.001°** (approximately 3.6 seconds of arc)

## Interpretation

The `score_summary` includes:

- **total_score**: Weighted sum of all aspects (positive = favorable, negative = challenging)
- **num_aspects**: Count of major aspects formed
- **interpretation**: Quick assessment (`"favorable"`, `"challenging"`, or `"neutral"`)

## Use Cases

1. **Annual Forecasting**: Predict themes and challenges for the upcoming year
2. **Relocation Analysis**: Compare solar returns for different locations
3. **Timing Events**: Identify favorable periods for major decisions
4. **Multi-Year Planning**: Generate solar returns for multiple consecutive years

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Missing required parameters (`birthDate`, `lat`, or `lon`) |
| 422 | Invalid date format (must be ISO 8601) |
| 500 | Calculation error (e.g., ephemeris data unavailable) |

## Technical Details

- **Ephemeris**: Uses JPL DE440s via Skyfield
- **Algorithm**: Binary search with 20 iterations for convergence
- **Aspects**: Conjunction (0°), Sextile (60°), Square (90°), Trine (120°), Opposition (180°)
- **Orb**: 6° maximum orb for aspect detection
- **Scoring**: Based on `weights.json` configuration

## Testing

Run validation tests:

```bash
python abu_engine/tests/test_solar_return_quick.py
```

For full accuracy tests (requires ephemeris download):

```bash
python abu_engine/tests/test_solar_return.py
```

## Limitations

- Year must be within ephemeris range (typically 1950-2050)
- Requires `de440s.bsp` ephemeris file in `abu_engine/data/`
- Solar return is calculated for tropical zodiac only
- House cusps not yet implemented (all planets show `house: null`)

## Future Enhancements

- [ ] Add house cusp calculations
- [ ] Support for progressed charts
- [ ] Harmonic charts (Solar Arc, Secondary Progressions)
- [ ] Composite chart calculations
- [ ] Synastry (relationship) charts
