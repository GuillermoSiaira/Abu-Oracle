# Developer Guide: Extending Persian Calculations

## Overview

This guide explains how to add new Persian/medieval astrology calculations to AI Oracle and integrate them into the full pipeline (Abu → Maestro → Narrative).

## Architecture recap

```
User Request
    ↓
Abu Engine (FastAPI)
    ├─ Swiss Ephemeris (planets, houses, aspects)
    └─ Persian modules (dignities, lots, fardars, profections, mansions, stars)
    ↓
/api/astro/chart/extended → JSON
    ↓
Lilly Engine (FastAPI)
    ├─ JSON Maestro (deterministic semantic layer)
    └─ Narrative Engine (GPT text generation)
    ↓
/api/ai/interpret → {maestro, narrative}
```

## Step-by-step: Adding a new Persian calculation

### 1. Implement the calculation in Abu Engine

**Location:** `abu_engine/core/<new_module>.py`

**Example:** Add "Temperament" calculation (hot/cold/moist/dry balance).

```python
# abu_engine/core/temperament.py

def compute_temperament(planets: list[dict]) -> dict:
    """
    Compute temperament based on planetary elements and qualities.
    
    Args:
        planets: List of planet dicts with 'name', 'sign', 'longitude'.
    
    Returns:
        {
            "dominant_quality": "hot",
            "qualities_score": {"hot": 5, "cold": 2, "moist": 3, "dry": 4},
            "interpretation": "Hot and dry temperament suggests..."
        }
    """
    # Element/quality mappings (import from dignities.py or define here)
    ELEMENT_QUALITIES = {
        "fire": {"hot": 2, "dry": 1},
        "earth": {"cold": 1, "dry": 2},
        "air": {"hot": 1, "moist": 2},
        "water": {"cold": 2, "moist": 1}
    }
    
    qualities_score = {"hot": 0, "cold": 0, "moist": 0, "dry": 0}
    
    for planet in planets:
        sign = planet.get("sign", "")
        element = _sign_to_element(sign)
        for quality, score in ELEMENT_QUALITIES.get(element, {}).items():
            qualities_score[quality] += score
    
    dominant = max(qualities_score, key=qualities_score.get)
    
    return {
        "dominant_quality": dominant,
        "qualities_score": qualities_score,
        "interpretation": f"{dominant.capitalize()} temperament predominates."
    }

def _sign_to_element(sign: str) -> str:
    ELEMENT_BY_SIGN = {
        "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
        "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
        "Gemini": "air", "Libra": "air", "Aquarius": "air",
        "Cancer": "water", "Scorpio": "water", "Pisces": "water"
    }
    return ELEMENT_BY_SIGN.get(sign, "fire")
```

**Best practices:**
- Return dict with clear keys (`dominant_quality`, `qualities_score`, `interpretation`)
- Handle missing data gracefully (empty lists, None values)
- Document expected input/output formats
- Keep calculations pure (no side effects, no external API calls)

---

### 2. Add to Abu Extended endpoint

**File:** `abu_engine/main.py`

**Modify:** `/api/astro/chart/extended` endpoint

```python
from abu_engine.core.temperament import compute_temperament

@app.get("/api/astro/chart/extended")
def get_chart_extended(date: str, lat: float, lon: float):
    # ... existing base_chart calculation ...
    
    extended = {}
    
    # Existing calculations
    try:
        extended["dignities"] = compute_dignities(base_chart["planets"])
    except Exception as e:
        extended["dignities"] = {"error": str(e)}
    
    # ... lots, fardars, profections, mansions, stars ...
    
    # NEW: Temperament
    try:
        extended["temperament"] = compute_temperament(base_chart["planets"])
    except Exception as e:
        extended["temperament"] = {"error": str(e)}
    
    return {
        "base_chart": base_chart,
        "extended": extended
    }
```

**Error handling pattern:**
- Wrap each subcalc in try/except
- Return `{"error": "..."}` instead of failing entire request
- This allows partial failures without breaking Maestro

---

### 3. Test Abu calculation

**Create:** `abu_engine/tests/test_temperament.py`

```python
import pytest
from abu_engine.core.temperament import compute_temperament

def test_compute_temperament_basic():
    planets = [
        {"name": "Sun", "sign": "Aries"},  # fire: hot+dry
        {"name": "Moon", "sign": "Cancer"},  # water: cold+moist
        {"name": "Mars", "sign": "Leo"}  # fire: hot+dry
    ]
    
    result = compute_temperament(planets)
    
    assert "dominant_quality" in result
    assert "qualities_score" in result
    assert result["dominant_quality"] in ["hot", "cold", "moist", "dry"]
    assert result["qualities_score"]["hot"] > 0

def test_compute_temperament_empty():
    result = compute_temperament([])
    assert result["qualities_score"]["hot"] == 0
```

**Run:**
```bash
cd abu_engine
pytest tests/test_temperament.py
```

---

### 4. Integrate into JSON Maestro

**File:** `lilly_engine/json_maestro.py`

**Add new helper function:**

```python
def _build_temperament_analysis(extended: dict) -> dict:
    """
    Extract temperament data from extended and format for Maestro.
    
    Args:
        extended: Abu extended response dict.
    
    Returns:
        {
            "dominant_quality": "hot",
            "balance": {"hot": 5, "cold": 2, "moist": 3, "dry": 4},
            "note": "Hot temperament predominates, suggesting active energy."
        }
    """
    temperament = extended.get("temperament", {})
    
    if "error" in temperament:
        return {
            "dominant_quality": None,
            "balance": {},
            "note": f"Temperament calculation unavailable: {temperament['error']}"
        }
    
    return {
        "dominant_quality": temperament.get("dominant_quality"),
        "balance": temperament.get("qualities_score", {}),
        "note": temperament.get("interpretation", "")
    }
```

**Update `build_json_maestro()`:**

```python
def build_json_maestro(chart_extended: dict, metadata_context: dict) -> dict:
    # ... existing sections ...
    
    maestro["temperament_analysis"] = _build_temperament_analysis(extended)
    
    return maestro
```

**JSON Maestro structure now includes:**

```json
{
  "maestro": {
    "temperament_analysis": {
      "dominant_quality": "hot",
      "balance": {"hot": 5, "cold": 2, "moist": 3, "dry": 4},
      "note": "Hot temperament predominates, suggesting active energy."
    }
  }
}
```

---

### 5. Update Narrative Engine (optional)

If the new calculation should appear in narrative, update `SYSTEM_PROMPT`.

**File:** `lilly_engine/narrative_engine.py`

**Modify `SYSTEM_PROMPT`:**

```python
SYSTEM_PROMPT = (
    "...\n"
    "STRUCTURE (fixed order, always include headers):\n"
    "1) Opening Overview – ...\n"
    "2) Elemental Dynamics – interpret elemental dominance and temperament balance.\n"
    "3) Temperament Analysis – describe dominant quality (hot/cold/moist/dry) and its implications.\n"
    "4) Lord of the Year – ...\n"
    "...\n"
)
```

**If NOT updating narrative:**
- Leave SYSTEM_PROMPT unchanged
- Temperament will be available in Maestro for future use
- Frontend can display it separately

---

### 6. Test Maestro integration

**Create:** `lilly_engine/tests/test_temperament_maestro.py`

```python
from lilly_engine.json_maestro import build_json_maestro

def test_maestro_includes_temperament():
    chart_extended = {
        "base_chart": {"planets": [], "houses": [], "aspects": []},
        "extended": {
            "temperament": {
                "dominant_quality": "hot",
                "qualities_score": {"hot": 5, "cold": 2, "moist": 3, "dry": 4},
                "interpretation": "Hot temperament predominates."
            }
        }
    }
    
    maestro = build_json_maestro(chart_extended, {})
    
    assert "temperament_analysis" in maestro
    assert maestro["temperament_analysis"]["dominant_quality"] == "hot"
    assert maestro["temperament_analysis"]["balance"]["hot"] == 5

def test_maestro_temperament_error_handling():
    chart_extended = {
        "base_chart": {"planets": [], "houses": [], "aspects": []},
        "extended": {
            "temperament": {"error": "Calculation failed"}
        }
    }
    
    maestro = build_json_maestro(chart_extended, {})
    
    assert maestro["temperament_analysis"]["dominant_quality"] is None
    assert "unavailable" in maestro["temperament_analysis"]["note"].lower()
```

**Run:**
```bash
cd lilly_engine
pytest tests/test_temperament_maestro.py
```

---

### 7. Document the new calculation

**Update:** `docs/JSON_Maestro_Schema.md`

Add new section:

```markdown
### 11. temperament_analysis

**Purpose:** Describe planetary temperament balance (hot/cold/moist/dry).

**Structure:**
```json
{
  "temperament_analysis": {
    "dominant_quality": "hot",
    "balance": {
      "hot": 5,
      "cold": 2,
      "moist": 3,
      "dry": 4
    },
    "note": "Hot temperament predominates, suggesting active energy."
  }
}
```

**Fields:**
- `dominant_quality`: Most prominent quality (hot/cold/moist/dry)
- `balance`: Score breakdown for all four qualities
- `note`: Interpretation text from Abu

**Rules:**
- If Abu calculation fails, `dominant_quality` is `null` and `note` explains error
- Balance scores are cumulative from all planets
```

**Update:** `docs/OpenAPI_Specification.md`

Add to Extended endpoint response:

```json
"extended": {
  "temperament": {
    "dominant_quality": "hot",
    "qualities_score": {"hot": 5, "cold": 2, "moist": 3, "dry": 4},
    "interpretation": "Hot temperament predominates."
  }
}
```

---

### 8. Update CLI (optional)

If you want CLI to display new calculation:

**File:** `scripts/abu_cli.py`

**Modify `--extended` output:**

```python
if args.extended:
    print("\n--- EXTENDED ---")
    
    # ... existing dignities, lots, fardars, profections ...
    
    # NEW: Temperament
    if "temperament" in ext:
        print("\n[Temperament]")
        temp = ext["temperament"]
        if "error" in temp:
            print(f"  Error: {temp['error']}")
        else:
            print(f"  Dominant Quality: {temp.get('dominant_quality', 'N/A')}")
            print(f"  Balance: {temp.get('qualities_score', {})}")
```

---

## E2E verification

### Test full pipeline

1. **Start services:**
```bash
# Abu Engine
uvicorn abu_engine.main:app --reload --port 8000

# Lilly Engine (load .env first)
Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.+)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') } }
uvicorn lilly_engine.main:app --reload --port 8001
```

2. **Test Abu Extended:**
```bash
curl "http://localhost:8000/api/astro/chart/extended?date=1990-01-01T12:00:00Z&lat=40.7128&lon=-74.0060" | jq .extended.temperament
```

3. **Test Maestro:**
```bash
curl -X POST http://localhost:8001/api/ai/interpret \
  -H "Content-Type: application/json" \
  -d '{
    "birthDate": "1990-01-01T12:00:00Z",
    "lat": 40.7128,
    "lon": -74.0060,
    "language": "es",
    "include_narrative": false
  }' | jq .maestro.temperament_analysis
```

4. **Test Narrative (if updated SYSTEM_PROMPT):**
```bash
curl -X POST http://localhost:8001/api/ai/interpret \
  -H "Content-Type: application/json" \
  -d '{
    "birthDate": "1990-01-01T12:00:00Z",
    "lat": 40.7128,
    "lon": -74.0060,
    "language": "es",
    "include_narrative": true
  }' | jq .narrative
```

Check that narrative includes temperament section if you updated SYSTEM_PROMPT.

---

## Deployment

### Update Cloud Run

After implementing and testing locally:

1. **Rebuild Abu Engine:**
```bash
cd abu_engine
gcloud builds submit --tag gcr.io/[PROJECT_ID]/abu-engine
gcloud run deploy abu-engine --image gcr.io/[PROJECT_ID]/abu-engine
```

2. **Rebuild Lilly Engine:**
```bash
cd lilly_engine
gcloud builds submit --tag gcr.io/[PROJECT_ID]/lilly-engine
gcloud run deploy lilly-engine --image gcr.io/[PROJECT_ID]/lilly-engine
```

3. **Verify deployment:**
```bash
curl "https://abu-engine-503488473965.us-central1.run.app/api/astro/chart/extended?date=1990-01-01T12:00:00Z&lat=40.7128&lon=-74.0060" | jq .extended.temperament
```

---

## Best practices checklist

When adding new Persian calculations:

- [ ] Calculation is deterministic (same input → same output)
- [ ] Handles edge cases (empty planets, None values, invalid signs)
- [ ] Returns structured dict (not plain string or number)
- [ ] Includes `error` key in response if calculation fails
- [ ] Has unit tests in `tests/test_<module>.py`
- [ ] Integrated into `/api/astro/chart/extended` with try/except
- [ ] Added to JSON Maestro with helper function
- [ ] Maestro helper handles Abu errors gracefully
- [ ] Documented in `JSON_Maestro_Schema.md`
- [ ] Documented in `OpenAPI_Specification.md`
- [ ] (Optional) Added to CLI output
- [ ] (Optional) Added to Narrative SYSTEM_PROMPT
- [ ] E2E tested with real data
- [ ] Deployed to Cloud Run

---

## Common Persian calculations to add

### Priority 1 (high value, moderate complexity)
- **Temperament:** Hot/cold/moist/dry balance (described above)
- **Almuten Figuris:** Most powerful planet in chart
- **Hayz:** Sect-based dignity (day/night chart alignment)

### Priority 2 (medium value, higher complexity)
- **Zodiacal Releasing:** Time-lord periods from Hellenistic astrology
- **Annual Profections by House:** More detailed profection system
- **Planetary Hours:** Traditional hour rulers for precise timing

### Priority 3 (specialized, research-heavy)
- **Persian Parts beyond Fortuna:** Additional Arabic lots
- **Decans and Bounds:** Subdivision dignities
- **Antiscia:** Mirror points across solstice axis

---

## Troubleshooting

### Issue: Abu calculation returns error in extended response

**Symptom:** `extended.new_calc = {"error": "..."}`

**Debug:**
1. Check Abu logs for traceback
2. Test calculation in isolation (unit test)
3. Verify input data format (planets list structure)
4. Add defensive checks for None/empty values

### Issue: Maestro doesn't include new calculation

**Symptom:** Key missing from Maestro JSON

**Debug:**
1. Verify `_build_<new_calc>()` is called in `build_json_maestro()`
2. Check that extended response contains new_calc key
3. Test Maestro builder with sample data (unit test)
4. Print maestro dict to console for inspection

### Issue: Narrative doesn't mention new calculation

**Symptom:** Narrative ignores new data

**Debug:**
1. Verify SYSTEM_PROMPT includes instructions for new section
2. Check that Maestro contains new_calc data (narrative reads from Maestro)
3. Test with `include_narrative: true` explicitly
4. Review GPT output for section presence

### Issue: Frontend doesn't display new calculation

**Symptom:** UI shows old data format

**Debug:**
1. Verify `/api/ai/interpret` response includes new Maestro field
2. Update frontend types/interfaces to include new field
3. Add UI component to render new calculation
4. Test with browser DevTools Network tab

---

## Further reading

- **Persian Astrology Sources:**
  - Masha'allah: "On Reception" (dignities)
  - Abu Ma'shar: "The Great Introduction" (Fardars, profections)
  - Al-Biruni: "The Book of Instruction" (lots, mansions)

- **Technical References:**
  - Swiss Ephemeris documentation: https://www.astro.com/swisseph/
  - FastAPI docs: https://fastapi.tiangolo.com
  - OpenAI API: https://platform.openai.com/docs

- **AI Oracle Docs:**
  - `docs/AI_Oracle_Technical_Documentation.md` (system architecture)
  - `docs/persian_calculations.md` (calculation details)
  - `docs/JSON_Maestro_Schema.md` (Maestro structure)
  - `docs/Narrative_Engine_Guide.md` (narrative generation)

---

**Last Updated:** 2024-01-15
