# Analyze Endpoint Contract (Abu Engine)

Path: POST /analyze

Purpose: Unified backend response for UI and Abu Agent. Computes natal chart + derived metrics in a strict, JSON-only schema.

## Request

Body JSON:
{
  "person": { "name": string | null, "question": string },
  "birth": { "date": ISO8601 string, "lat": number, "lon": number },
  "current": { "lat": number, "lon": number, "date"?: ISO8601 string }
}

Notes:
- current.date is optional; defaults to now (UTC).
- Coordinates are decimal degrees.

## Response (contract)

{
  "person": { "name": string | null, "question": string },
  "chart": {
    "planets": [
      {
        "name": string,
        "longitude": number,
        "sign": string,
        "degree_in_sign": number,
        "formatted": string,
        "dignity": { "domicile": bool, "exaltation": bool, "detriment": bool, "fall": bool, "peregrine": bool, "score": number },
        "house": number | null
      }
    ],
    "houses": {
      "houses": [ { "house": 1..12, "start": number, "end": number } ],
      "asc": number | null,
      "mc": number | null
    }
  },
  "derived": {
    "sect": "diurnal" | "nocturnal" | null,
    "firdaria": { "current": { "major": string, "sub": string, "start": ISO8601 string, "end": ISO8601 string } | null },
    "profection": { "house": 1..12 | null },
    "lunar_transit": { "moon_position": number | null, "aspects": [ { "planet": string, "type": string, "orb": number } ] }
  },
  "question": string
}

## Implementation mapping
- chart.planets → core.extended_calc.calculate_detailed_positions() over chart_json() results
- chart.houses → core.houses_swiss.calculate_houses() + normalize_lon(); ASC/MC numeric
- derived.sect → core.fardars.is_diurnal_chart(sun_lon, asc_lon)
- derived.firdaria.current → core.fardars.get_current_fardar(birth_dt, is_diurnal, current_dt)
- derived.profection.house → core.profections.calculate_annual_profection().sign_offset → (offset % 12) + 1
- derived.lunar_transit → chart_json() at current + core.transits.calculate_transits(); filter transit_planet == "Moon" and project {planet, type, orb}

## Example (minimal)
{
  "person": { "name": "Ada", "question": "" },
  "birth": { "date": "1990-01-01T12:00:00Z", "lat": -34.6037, "lon": -58.3816 },
  "current": { "lat": -34.6037, "lon": -58.3816 }
}

Tip: Use Content-Type: application/json.

## Guarantees
- JSON-only output; no narrative/prose outside the JSON
- Stable keys present even when data is unavailable (e.g., firdaria.current may be null)
- Houses always numeric with start/end (normalized 0..360)

## Troubleshooting
- Seeing old schema (e.g., houses with strings)? Rebuild the abu_engine container to pick up code changes:
  - docker compose up -d --build abu_engine
- If Swiss Ephemeris is unavailable, houses.houses may be empty and asc/mc null; planets still include dignities.
