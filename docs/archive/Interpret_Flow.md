# Interpretation Flow: Abu → Lilly

This document explains how astrological interpretation is orchestrated end-to-end using Abu Engine (calculation) and Lilly Engine (LLM).

## Architecture

```
User/Frontend
      ↓
POST /api/astro/interpret (Abu)
      ↓
POST /analyze (Abu internal)
      ↓ (consolidated payload)
core.interpreter_llm.interpret_analysis
      ↓ (HTTP POST)
POST /api/ai/interpret (Lilly)
      ↓ (JSON: headline, narrative, actions, astro_metadata)
Response → User/Frontend
```

## Endpoints

### 1) POST /api/astro/interpret (Abu Engine)

**Purpose**: Single endpoint to obtain direct interpretation from natal data.

**Input**:
```json
{
  "birthDate": "1990-01-01T12:00:00Z",
  "lat": -34.6037,
  "lon": -58.3816,
  "language": "es"  // optional (default: "es")
}
```

**Internal flow**:
1. Validates parameters (400 if missing, 422 if invalid date).
2. Builds payload via internal POST /analyze (chart + derived + life_cycles + forecast).
3. Calls `core.interpreter_llm.interpret_analysis(payload, language)`.
4. Returns Lilly's JSON as-is.

**Response (200)**:
```json
{
  "headline": "Ciclo de aprendizaje y transformación",
  "narrative": "La configuración actual sugiere un periodo de crecimiento personal...",
  "actions": [
    "Mantén un diario de reflexión personal",
    "Explora nuevas áreas de conocimiento",
    "Cultiva relaciones significativas"
  ],
  "astro_metadata": {
    "source": "openai",  // or "fallback" if no LLM
    "language": "es",
    "events": 3
  }
}
```

**Errors**:
- 400: Missing birthDate/lat/lon
- 422: Invalid date format
- 502: Lilly unreachable (timeout/connection) or Lilly internal error

**Logging**: Records total flow duration in ms.

---

### 2) POST /analyze (Abu Engine, internal)

**Purpose**: Compose all astrological calculations into a single payload.

**Input**:
```json
{
  "person": { "name": null, "question": "" },
  "birth": { "date": "1990-01-01T12:00:00Z", "lat": -34.6037, "lon": -58.3816 },
  "current": { "lat": -34.6037, "lon": -58.3816, "date": null }
}
```

**Output** (extended with life_cycles and forecast):
```json
{
  "person": { "name": null, "question": "" },
  "chart": {
    "planets": [ { "name": "Sun", "longitude": 280.95, "sign": "Capricorn", ... } ],
    "houses": { "houses": [...], "asc": 320.49, "mc": 224.96 }
  },
  "derived": {
    "sect": "nocturnal",
    "firdaria": { "current": { "major": "Mars", "sub": "South Node", ... } },
    "profection": { "house": 12 },
    "lunar_transit": { "moon_position": 65.74, "aspects": [...] }
  },
  "life_cycles": {
    "events": [
      { "cycle": "Saturn Return", "planet": "Saturn", "angle": 0, "approx": "2019-03-22" }
    ]
  },
  "forecast": {
    "timeseries": [ { "t": "2025-11-07", "F": 0.23 }, ... ],
    "peaks": [ { "t": "2026-08-12", "F": 0.89, "kind": "peak" }, ... ]
  },
  "question": ""
}
```

**Error handling per block**:
- If a block fails (e.g., pyswisseph unavailable), returns `{"error": "module not available"}` for that block and continues with others.

---

### 3) POST /api/ai/interpret (Lilly Engine)

**Purpose**: Generate narrative interpretation in JSON from Abu's payload.

**Input**:
```json
{
  "chart": {...},
  "derived": {...},
  "life_cycles": {...},
  "forecast": {...},
  "language": "es"
}
```

**Output**:
```json
{
  "headline": "...",
  "narrative": "...",
  "actions": ["...", "...", "..."],
  "astro_metadata": { "source": "openai" | "fallback", "language": "es", ... }
}
```

**Configuration**:
- Environment variable `OPENAI_API_KEY` in Lilly to use GPT-4.
- Without key or with `USE_ASSISTANTS=false`, Lilly returns fallback from `archetypes.json`.

---

## Internal Client: `core.interpreter_llm.interpret_analysis`

**Location**: `abu_engine/core/interpreter_llm.py`

**Function**:
```python
def interpret_analysis(payload: Dict[str, Any], language: str = "es") -> Dict[str, Any]:
    """
    Sends Abu's aggregated payload to Lilly and returns the JSON interpretation.
    
    Args:
        payload: Output from /analyze (chart, derived, life_cycles, forecast).
        language: Interpretation language ("es", "en", "pt", "fr").
    
    Returns:
        dict with keys: headline, narrative, actions, astro_metadata.
        
    Raises:
        RuntimeError: if Lilly's response doesn't meet the contract.
        
    Returns {"error": "Lilly unreachable"} if timeout/connection error.
    """
```

**Configuration**:
- Environment variable `LILLY_API_URL` (default: `http://lilly_engine:8001` for Docker Compose).
- Timeout: 15 seconds.

**Validation**:
- Verifies response contains required keys: `headline`, `narrative`, `actions`, `astro_metadata`.
- Raises `RuntimeError` if any key is missing or JSON is invalid.

---

## Configuration and Environment Variables

### Abu Engine

| Variable | Default | Description |
|----------|---------|-------------|
| `LILLY_API_URL` | `http://lilly_engine:8001` | Lilly Engine base URL (no trailing slash) |

### Lilly Engine

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key for GPT-4 (optional; uses fallback if missing) |
| `USE_ASSISTANTS` | `true` | Use OpenAI Assistants API (if `false`, uses archetypes) |
| `ABU_URL` | `http://abu_engine:8000` | Abu Engine URL (for reverse calls if needed) |

---

## Detailed Data Flow

1. **User sends POST to /api/astro/interpret**
   - Body: `{ birthDate, lat, lon, language? }`

2. **Abu validates input**
   - 400 if missing parameters
   - 422 if birthDate is invalid

3. **Abu builds consolidated payload**
   - Internally calls `analyze()` to obtain:
     - chart (planets + houses)
     - derived (sect, firdaria, profection, lunar_transit)
     - life_cycles (major events)
     - forecast (timeseries + peaks)

4. **Abu invokes internal client**
   - `interpret_analysis(payload, language)` POST to `{LILLY_API_URL}/api/ai/interpret`

5. **Lilly processes and responds**
   - With OPENAI_API_KEY: uses GPT-4 to generate personalized interpretation
   - Without OPENAI_API_KEY: uses fallback from `archetypes.json`
   - Returns JSON with headline/narrative/actions/astro_metadata

6. **Abu returns response to user**
   - 200 with Lilly's JSON
   - 502 if Lilly doesn't respond or returns error

---

## Tests

### `abu_engine/tests/test_interpret_contract.py`

- `test_interpret_contract_shape()`: Verifies response has required keys (headline, narrative, actions, astro_metadata) when Lilly responds 200.
- `test_interpret_missing_params()`: Verifies returns 400 if birthDate/lat/lon missing.
- `test_interpret_invalid_date()`: Verifies returns 422 if birthDate is invalid.

**Execution**:
```powershell
D:/projects/AI_Oracle/venv/Scripts/python.exe -m pytest -q d:/projects/AI_Oracle/abu_engine/tests/test_interpret_contract.py
```

### `abu_engine/tests/test_analyze_contract.py`

- Verifies POST /analyze returns expected shape (extended with life_cycles and forecast).

---

## Usage Example

### With PowerShell

```powershell
$body = @{
  birthDate = "1990-01-01T12:00:00Z"
  lat = -34.6037
  lon = -58.3816
  language = "es"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:8000/api/astro/interpret `
  -Method POST `
  -ContentType 'application/json' `
  -Body $body | ConvertTo-Json -Depth 8
```

### With curl

```bash
curl -X POST http://127.0.0.1:8000/api/astro/interpret \
  -H "Content-Type: application/json" \
  -d '{
    "birthDate": "1990-01-01T12:00:00Z",
    "lat": -34.6037,
    "lon": -58.3816,
    "language": "es"
  }'
```

---

## Troubleshooting

### Error 502: Lilly unreachable

**Cause**: Lilly is not running or `LILLY_API_URL` points to incorrect URL.

**Solution**:
1. Verify Lilly is running:
   ```powershell
   docker compose ps
   ```
2. Check Lilly logs:
   ```powershell
   docker compose logs lilly_engine
   ```
3. Verify connectivity from Abu:
   ```powershell
   docker exec abu_engine curl -I http://lilly_engine:8001/
   ```

### Response with `"source": "fallback"`

**Cause**: Lilly doesn't have `OPENAI_API_KEY` configured or `USE_ASSISTANTS=false`.

**Solution**:
1. Add `OPENAI_API_KEY` in `.env` or `docker-compose.yml`:
   ```yaml
   environment:
     - OPENAI_API_KEY=sk-...
   ```
2. Restart Lilly:
   ```powershell
   docker compose restart lilly_engine
   ```

### Tests fail with "module not available"

**Cause**: Missing dependencies (pyswisseph, skyfield) or ephemeris not loaded.

**Solution**:
1. Verify `de440s.bsp` is in `abu_engine/data/`.
2. Rebuild Abu:
   ```powershell
   docker compose up -d --build abu_engine
   ```

---

## Next Steps

- **Payload caching**: Avoid recalculating same payload if birthDate/lat/lon unchanged.
- **Streaming**: Implement SSE for progressive Lilly responses (if OpenAI supports streaming).
- **Multi-language**: Expand pt/fr/en support with specific prompts in Lilly.
- **Validation with Zod/Pydantic**: Add strict schemas for input/output payloads.
