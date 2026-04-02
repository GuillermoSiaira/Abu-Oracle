# OpenAI Assistant Integration Plan

**Date**: November 10, 2025  
**Status**: 🔄 Planning  
**Next Sprint**: OpenAI Assistant API Integration

## Overview

Integrate OpenAI Assistants API with our FastAPI backend to enable conversational astrological interpretations with function calling capabilities.

## Current State

### Existing OpenAI Integration
- **Location**: `lilly_engine/core/llm.py`
- **Mode**: Chat Completions API
- **Model**: GPT-4 (fallback to GPT-3.5-turbo)
- **Features**:
  - Structured JSON responses
  - Multilingual support (ES/EN/PT/FR)
  - Conversation memory (`data/memory.json`)
  - Fallback to `archetypes.json` when API unavailable

### Current Flow
```
Frontend → Abu Engine → Lilly Engine → OpenAI Chat Completions → Response
```

## Goals

### Primary Objectives
1. ✅ Enable function calling for dynamic astrological queries
2. ✅ Reduce latency with streaming responses
3. ✅ Maintain conversation context across sessions
4. ✅ Preserve fallback behavior for resilience

### Non-Goals
- ❌ Replace existing Chat Completions entirely (keep both modes)
- ❌ Add new astrological calculations (use existing Abu endpoints)
- ❌ Change frontend contracts (maintain response schema)

## Architecture

### Proposed Flow
```
Frontend → Abu/Lilly → OpenAI Assistant
                 ↓
            Function Calls
                 ↓
         Abu Endpoints (tools)
                 ↓
       Assistant Response → Frontend
```

### Assistant Configuration

**Assistant Capabilities**:
- Function calling to Abu endpoints
- File retrieval (optional: archetypes.json as knowledge base)
- Code interpreter (optional: for calculations)

**Functions to Expose**:
1. `get_birth_chart` → `/api/astro/chart`
2. `get_forecast` → `/api/astro/forecast`
3. `get_life_cycles` → `/api/astro/life-cycles`
4. `get_solar_return` → `/api/astro/solar-return`
5. `optimize_sr_location` → `/api/rs/optimize` (NEW)

## Implementation Plan

### Phase 1: Assistant Setup ✅
**Tasks**:
- [ ] Create OpenAI Assistant via API or Playground
- [ ] Define system prompt with astrological expertise
- [ ] Configure function schemas matching Abu endpoints
- [ ] Upload `archetypes.json` as knowledge file (optional)
- [ ] Test assistant in Playground with sample queries

**Deliverables**:
- Assistant ID (stored in env: `OPENAI_ASSISTANT_ID`)
- Function schemas JSON
- System prompt template

### Phase 2: Backend Integration 🔧
**Tasks**:
- [ ] Create `lilly_engine/core/assistant.py` module
- [ ] Implement thread management (create/retrieve threads)
- [ ] Add function call handler for Abu endpoints
- [ ] Implement streaming response handling
- [ ] Add fallback logic (Assistant → Chat Completions → Archetypes)
- [ ] Update `main.py` to route `/api/ai/interpret` to Assistant mode

**Deliverables**:
- `assistant.py` with `AssistantClient` class
- Function call dispatcher
- Streaming endpoint (optional: `/api/ai/interpret/stream`)
- Environment flag: `USE_ASSISTANT_API=true`

### Phase 3: Testing & Validation ✅
**Tasks**:
- [ ] Unit tests for function call dispatcher
- [ ] Integration tests for Assistant endpoint
- [ ] Test streaming responses
- [ ] Validate fallback behavior (API key invalid, Assistant unavailable)
- [ ] Performance benchmarking (latency vs Chat Completions)

**Deliverables**:
- `tests/test_assistant.py` (unit tests)
- `tests/test_assistant_integration.py` (integration tests)
- Performance report (avg latency, tokens/sec)

### Phase 4: Documentation & Deployment 📚
**Tasks**:
- [ ] Update API Examples with Assistant mode
- [ ] Document function schemas
- [ ] Add deployment guide (setting ASSISTANT_ID in production)
- [ ] Update README with Assistant mode instructions
- [ ] Create migration guide (Chat Completions → Assistant)

**Deliverables**:
- `docs/OpenAI_Assistant_Integration.md`
- Updated `docs/API_Examples.md`
- Environment variable documentation

## Technical Specifications

### Environment Variables
```bash
# Existing
OPENAI_API_KEY=sk-...
DEFAULT_LANGUAGE=ES

# New
OPENAI_ASSISTANT_ID=asst_...
USE_ASSISTANT_API=true  # Toggle between modes
ASSISTANT_MODEL=gpt-4o  # Override assistant model
```

### Function Schemas

Example: `get_birth_chart`
```json
{
  "name": "get_birth_chart",
  "description": "Calculate natal birth chart with planets, houses, and aspects",
  "parameters": {
    "type": "object",
    "properties": {
      "birth_date": {
        "type": "string",
        "description": "Birth datetime in ISO8601 format (e.g., 1990-01-15T10:30:00Z)"
      },
      "latitude": {
        "type": "number",
        "description": "Birth location latitude in decimal degrees"
      },
      "longitude": {
        "type": "number",
        "description": "Birth location longitude in decimal degrees"
      }
    },
    "required": ["birth_date", "latitude", "longitude"]
  }
}
```

### System Prompt Template
```
You are Lilly, an expert astrologer with deep knowledge of traditional and modern astrology.

Your role:
- Interpret astrological data using symbolic language
- Provide insights for personal growth and timing
- Use function calls to retrieve astrological calculations
- Respond in {language} (Spanish by default)
- Format responses as structured JSON with keys: headline, narrative, actions

Guidelines:
- Be empowering and solution-oriented
- Avoid fatalistic language
- Ground interpretations in provided data
- Use archetypes knowledge when relevant
- Keep responses concise (300-500 words)

Available functions:
- get_birth_chart: Calculate natal positions
- get_forecast: Get upcoming transits and timing
- get_life_cycles: Identify major life cycles (Saturn Return, etc.)
- get_solar_return: Calculate Solar Return chart
- optimize_sr_location: Find optimal relocation cities for Solar Return

When a user asks about their chart or forecast, use the appropriate function.
```

### Response Format

**Chat Completions (Current)**:
```json
{
  "headline": "Saturno en Casa 10: Consolidación Profesional",
  "narrative": "Este tránsito marca un período...",
  "actions": ["Revisar metas profesionales", "Estructurar proyectos"],
  "astro_metadata": {
    "source": "lilly",
    "model": "gpt-4",
    "tokens": 234
  }
}
```

**Assistant Mode (Proposed)** - Same structure:
```json
{
  "headline": "Saturno en Casa 10: Consolidación Profesional",
  "narrative": "Este tránsito marca un período...",
  "actions": ["Revisar metas profesionales", "Estructurar proyectos"],
  "astro_metadata": {
    "source": "lilly_assistant",
    "assistant_id": "asst_abc123",
    "thread_id": "thread_xyz789",
    "model": "gpt-4o",
    "tokens": 234,
    "function_calls": 2
  }
}
```

## Function Call Flow

### Example: User asks "What's my forecast for next month?"

1. **User Input** → Frontend sends to `/api/ai/interpret`:
   ```json
   {
     "question": "What's my forecast for next month?",
     "profile": {
       "birth_date": "1990-01-15T10:30:00Z",
       "lat": 40.7128,
       "lon": -74.0060
     },
     "language": "es"
   }
   ```

2. **Lilly creates Assistant thread** with user message

3. **Assistant determines** it needs forecast data → calls `get_forecast`:
   ```json
   {
     "birth_date": "1990-01-15T10:30:00Z",
     "latitude": 40.7128,
     "longitude": -74.0060,
     "start": "2025-11-01",
     "end": "2025-12-01"
   }
   ```

4. **Lilly intercepts function call** → makes HTTP request to Abu:
   ```http
   GET http://abu_engine:8000/api/astro/forecast?birthDate=1990-01-15T10:30:00Z&lat=40.7128&lon=-74.0060&start=2025-11-01&end=2025-12-01
   ```

5. **Abu responds** with forecast data (peaks, timeseries)

6. **Lilly submits function result** back to Assistant

7. **Assistant generates interpretation** using forecast data

8. **Lilly formats response** into standardized JSON

9. **Frontend receives** final interpretation

## Error Handling

### Fallback Cascade
```
Assistant API (primary)
    ↓ (if unavailable/error)
Chat Completions API (secondary)
    ↓ (if unavailable/error)
Archetypes.json (tertiary)
```

### Error Scenarios

| Error | Handling |
|-------|----------|
| Assistant API down | Fall back to Chat Completions |
| Chat Completions down | Fall back to Archetypes |
| Function call fails | Return error in function result; let Assistant handle |
| Abu endpoint timeout | Return error; Assistant suggests retry |
| Invalid function args | Assistant retries with corrected args |
| Rate limit hit | Exponential backoff; fall back if persistent |

## Performance Considerations

### Expected Latency
- **Chat Completions**: 2-4s (current)
- **Assistant API**: 3-5s (with function calls)
- **Streaming**: First token ~500ms, completion ~3s

### Optimization Strategies
1. ✅ Use streaming for faster perceived latency
2. ✅ Cache Abu responses (already implemented in IGP)
3. ✅ Parallel function calls when possible (Assistant handles)
4. ✅ Use `gpt-4o-mini` for faster responses (lower cost)

### Cost Comparison
- **Chat Completions (GPT-4)**: ~$0.03/request (500 tokens)
- **Assistant API (GPT-4o)**: ~$0.04/request (+ function calls)
- **Assistant API (GPT-4o-mini)**: ~$0.01/request ✅ Recommended

## Testing Strategy

### Unit Tests
```python
# tests/test_assistant.py
def test_function_call_dispatcher():
    """Test that function calls route to correct Abu endpoints"""
    pass

def test_thread_management():
    """Test thread creation and retrieval"""
    pass

def test_fallback_logic():
    """Test cascade from Assistant → Chat → Archetypes"""
    pass
```

### Integration Tests
```python
# tests/test_assistant_integration.py
def test_assistant_with_forecast_function():
    """Test full flow: question → function call → interpretation"""
    pass

def test_assistant_streaming():
    """Test streaming response handling"""
    pass

def test_assistant_with_invalid_function_args():
    """Test Assistant retries with corrected args"""
    pass
```

### Manual Testing Checklist
- [ ] Create assistant in Playground
- [ ] Test function calling with real Abu endpoints
- [ ] Verify multilingual responses (ES/EN)
- [ ] Test fallback when Assistant unavailable
- [ ] Validate streaming responses in browser
- [ ] Test with various user queries (chart, forecast, cycles)

## Security Considerations

### API Key Management
- ✅ Store `OPENAI_API_KEY` in environment (never commit)
- ✅ Rotate keys quarterly
- ✅ Use separate keys for dev/staging/prod

### Function Call Validation
- ✅ Validate function arguments before calling Abu
- ✅ Sanitize user input (no injection attacks)
- ✅ Rate limit function calls (max 10/request)
- ✅ Whitelist allowed functions (don't expose internal endpoints)

### Data Privacy
- ✅ Don't log user birth data in Assistant threads
- ✅ Implement thread cleanup (delete after 30 days)
- ✅ GDPR compliance: user can request thread deletion
- ✅ Don't upload user data to Assistant files

## Deployment

### Development
```bash
# Set environment variables
export OPENAI_API_KEY=sk-...
export OPENAI_ASSISTANT_ID=asst-...
export USE_ASSISTANT_API=true

# Run Lilly Engine
cd lilly_engine
uvicorn main:app --reload --port 8001
```

### Docker Compose
```yaml
# docker-compose.yml
services:
  lilly_engine:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_ASSISTANT_ID=${OPENAI_ASSISTANT_ID}
      - USE_ASSISTANT_API=true
      - ABU_URL=http://abu_engine:8000
```

### Production (Cloud Run)
```bash
# Set secrets in Cloud Console or CLI
gcloud run services update lilly-engine \
  --update-secrets OPENAI_API_KEY=openai-key:latest \
  --update-env-vars OPENAI_ASSISTANT_ID=asst-... \
  --update-env-vars USE_ASSISTANT_API=true
```

## Migration Plan

### Phase 1: Parallel Mode (Week 1)
- ✅ Deploy Assistant integration alongside Chat Completions
- ✅ Use feature flag: `USE_ASSISTANT_API=false` in production
- ✅ Test in staging with real users

### Phase 2: Gradual Rollout (Week 2-3)
- ✅ Enable Assistant for 10% of requests (A/B test)
- ✅ Monitor latency, error rates, user satisfaction
- ✅ Increase to 50% if metrics acceptable

### Phase 3: Full Cutover (Week 4)
- ✅ Enable Assistant for 100% of requests
- ✅ Keep Chat Completions as fallback
- ✅ Remove feature flag after 2 weeks of stability

## Success Metrics

### Performance
- ✅ P50 latency < 3s
- ✅ P95 latency < 5s
- ✅ Streaming first token < 500ms

### Reliability
- ✅ Error rate < 1%
- ✅ Fallback success rate > 99%
- ✅ Function call success rate > 95%

### User Experience
- ✅ Response quality (user ratings) > 4.0/5
- ✅ Function call accuracy > 90%
- ✅ Multilingual response accuracy > 95%

## Open Questions

1. **Thread Persistence**: Store thread IDs in user sessions or create new threads per request?
   - **Recommendation**: New threads per request for MVP; add persistence later

2. **Streaming Implementation**: WebSocket or Server-Sent Events?
   - **Recommendation**: SSE (simpler, FastAPI native support)

3. **Assistant Updates**: How to handle Assistant prompt/function schema changes?
   - **Recommendation**: Version Assistants (asst-v1, asst-v2); blue-green deployment

4. **Cost Optimization**: Use GPT-4o-mini for all requests or selective routing?
   - **Recommendation**: GPT-4o-mini by default; upgrade to GPT-4o for complex queries

## Next Steps

1. ✅ Create Assistant in OpenAI Playground
2. ✅ Implement `assistant.py` module with basic thread management
3. ✅ Add function call dispatcher for Abu endpoints
4. ✅ Test end-to-end flow in development
5. ✅ Write integration tests
6. ✅ Deploy to staging with feature flag
7. ✅ Monitor metrics and iterate
8. ✅ Document final implementation

## References

- OpenAI Assistants API: https://platform.openai.com/docs/assistants/overview
- Function Calling: https://platform.openai.com/docs/guides/function-calling
- FastAPI Streaming: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- Current Lilly implementation: `lilly_engine/core/llm.py`
- IGP endpoint: `abu_engine/main.py` (line 1890+)
