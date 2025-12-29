# Technical Debt & Improvement Backlog

**Status:** Living document  
**Last Updated:** 2025-11-10  
**Owner:** AI Oracle Backend Team

This document tracks technical debt, deprecation warnings, and improvement opportunities across the AI Oracle codebase. Items are prioritized by impact and effort.

---

## 🔴 High Priority (Blocking / Production Impact)

### 1. Pydantic v2 Migration
**Issue:** Using deprecated `.dict()` method; Pydantic v2 recommends `.model_dump()`  
**Impact:** 800+ warnings in test suite; future compatibility risk  
**Files Affected:**
- `abu_engine/core/chart.py:261-262` (2 calls)
- Propagates through all tests using chart DTOs

**Action Required:**
```python
# Current (deprecated):
"planets": [p.dict() for p in chart.planets]

# Target (Pydantic v2):
"planets": [p.model_dump() for p in chart.planets]
```

**Estimated Effort:** 2 hours (search-replace + verify tests)  
**Risk:** Low (backward compatible in Pydantic 2.x)

---

### 2. FastAPI Lifecycle Event Migration
**Issue:** `@app.on_event("startup")` deprecated; use lifespan handlers  
**Impact:** 4 deprecation warnings per test run; future FastAPI incompatibility  
**Files Affected:**
- `abu_engine/main.py:290` (`on_event("startup")`)

**Action Required:**
```python
# Current (deprecated):
@app.on_event("startup")
async def warmup():
    ...

# Target (FastAPI 0.109+):
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await warmup()
    yield
    # Shutdown (if needed)

app = FastAPI(lifespan=lifespan)
```

**Estimated Effort:** 1 hour (refactor + test startup sequence)  
**Risk:** Medium (changes app initialization order; test carefully)

**Reference:** [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)

---

## 🟡 Medium Priority (Technical Debt / Maintainability)

### 3. IGP Cache Integration
**Issue:** Cache module created but not wired into batch evaluation pipeline  
**Impact:** Repeated evaluations for same SR/city pairs waste CPU  
**Files Affected:**
- `abu_engine/core/igp_optimizer.py:156` (batch_evaluate_cities)
- `abu_engine/main.py:1976` (endpoint passes cache but unused)

**Action Required:**
- Modify `_evaluate_city_worker` to check cache before scoring
- Add cache key generation using SR datetime + city lat/lon
- Ensure thread-safe access in multiprocessing context

**Estimated Effort:** 4 hours (implement + unit tests + benchmark validation)  
**Risk:** Medium (multiprocessing cache access requires careful design)

---

### 4. SR Natal/Solar Datetime Confusion
**Issue:** Hack in `score_location`: passes SR datetime as `birth_date` parameter  
**Impact:** Confusing API contract; risks misinterpretation by future maintainers  
**Files Affected:**
- `abu_engine/core/igp_optimizer.py:106` (hack comment)
- `abu_engine/core/solar_return_ranking.py:428` (score_solar_return_location signature)

**Action Required:**
- Refactor `score_solar_return_location` to accept SR datetime directly
- Add explicit `natal_birth_date` parameter if natal data needed
- Update tests for new signature

**Estimated Effort:** 3 hours (refactor + update all call sites + tests)  
**Risk:** Low (internal API; no external consumers)

---

### 5. Missing Planet Speed Calculation
**Issue:** Speed always returns 0 in transit/forecast endpoints  
**Impact:** No retrograde detection; incomplete astrology data  
**Files Affected:**
- `abu_engine/main.py:1193` (TODO comment)

**Action Required:**
- Compute velocity using Swiss Ephemeris `SEFLG_SPEED` flag
- Add retrograde indicator (`is_retrograde: bool`) to planet DTOs
- Update tests to verify speed calculation

**Estimated Effort:** 3 hours (implement + test + validate against ephemeris)  
**Risk:** Low (additive feature; doesn't break existing logic)

---

### 6. Test Return Value Warnings
**Issue:** Tests return boolean instead of using assertions  
**Impact:** 3 pytest warnings; non-idiomatic test style  
**Files Affected:**
- `abu_engine/tests/test_solar_return_quick.py:test_imports`
- `abu_engine/tests/test_solar_return_quick.py:test_endpoint_exists`
- `abu_engine/tests/test_solar_return_quick.py:test_function_signature`

**Action Required:**
```python
# Current (returns bool):
def test_imports():
    try:
        from core.solar_return import calculate_solar_return
        return True
    except ImportError:
        return False

# Target (use assertions):
def test_imports():
    from core.solar_return import calculate_solar_return
    assert calculate_solar_return is not None
```

**Estimated Effort:** 30 minutes (fix 3 tests)  
**Risk:** None (cosmetic fix)

---

## 🟢 Low Priority (Nice-to-Have / Future Enhancements)

### 7. External Cities Dataset
**Issue:** Hardcoded RELOCATION_CITIES in code; should load from JSON  
**Impact:** Limited scalability; requires code change to add cities  
**Files Affected:**
- `abu_engine/main.py:1949` (TODO comment)
- `abu_engine/core/solar_return_ranking.py:49` (RELOCATION_CITIES dict)

**Action Required:**
- Create `abu_engine/data/cities.json` with extended dataset
- Implement loader in `igp_optimizer.load_cities_dataset` (already stubbed)
- Update endpoint to use external file

**Estimated Effort:** 2 hours (create dataset + loader + validation)  
**Risk:** Low (fallback to hardcoded cities if file missing)

---

### 8. Natal-to-Solar Comparison
**Issue:** Placeholder function with no implementation  
**Impact:** Missing feature for SR analysis depth  
**Files Affected:**
- `abu_engine/core/solar_return.py:193` (TODO comment in `compare_natal_to_solar_return`)

**Action Required:**
- Calculate ASC/MC longitude differences
- Identify angular planets in SR vs natal
- Return structured comparison dict

**Estimated Effort:** 4 hours (research + implement + test)  
**Risk:** Low (additive feature; doesn't affect existing flows)

---

### 9. IGP Intent-Based Weighting
**Issue:** Sprint 2 deferred feature; intent parameter accepted but ignored  
**Impact:** All city evaluations use same criteria regardless of user goals  
**Files Affected:**
- `abu_engine/core/igp_optimizer.py:104` (TODO Sprint 2 comment)

**Action Required:**
- Design weights.json schema (dignities, angularity, aspects per intent)
- Implement intent loader in `score_location`
- Add integration tests for health/career/relationships intents

**Estimated Effort:** 8 hours (design + implement + test)  
**Risk:** Medium (requires astrology domain validation)

**Roadmap:** Scheduled for IGP Sprint 2

---

### 10. Integration Tests for IGP Endpoint
**Issue:** Only unit tests exist; no end-to-end API validation  
**Impact:** Risk of endpoint contract drift from implementation  
**Files Affected:**
- Missing: `abu_engine/tests/test_igp_endpoint.py`

**Action Required:**
- Create FastAPI TestClient integration tests
- Validate request/response schemas
- Test error cases (invalid birth dates, missing params)

**Estimated Effort:** 3 hours (write + run tests)  
**Risk:** Low (testing only)

---

## 📊 Metrics Summary

| Priority | Count | Estimated Effort |
|----------|-------|------------------|
| 🔴 High  | 2     | 3 hours          |
| 🟡 Medium| 4     | 14 hours         |
| 🟢 Low   | 4     | 17 hours         |
| **Total**| **10**| **34 hours**     |

---

## 🎯 Recommended Sprint Plan

### Sprint A: Deprecation Cleanup (3 hours)
- Pydantic v2 migration
- FastAPI lifespan refactor
- Test return value fixes

**Benefit:** Eliminates 800+ warnings; future-proofs dependencies

---

### Sprint B: IGP Completion (7 hours)
- Cache integration
- SR datetime hack removal
- Integration tests

**Benefit:** Completes IGP Sprint 1 acceptance criteria

---

### Sprint C: Feature Parity (7 hours)
- Planet speed calculation
- External cities dataset
- Natal-to-Solar comparison

**Benefit:** Closes feature gaps for production readiness

---

## 📝 Notes

- **Pydantic Warnings:** Can be suppressed short-term via pytest config if migration deferred:
  ```ini
  # pytest.ini
  [pytest]
  filterwarnings =
      ignore::pydantic.warnings.PydanticDeprecatedSince20
  ```

- **FastAPI Lifespan:** Breaking change in FastAPI 1.0; current code works but will fail in future versions.

- **IGP Cache:** Multiprocessing requires shared memory cache (e.g., `multiprocessing.Manager.dict()`) or pre-fork cache population.

---

## 🔗 Related Documents
- [IGP Strategy](./IGP_Strategy.md)
- [Agent Builder Brief](./Agent_Builder_Brief.md)
- [Performance Optimizations](./AI_Oracle_Performance_Optimizations.md)
