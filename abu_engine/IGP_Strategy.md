# Inteligencia Geográfica Predictiva (IGP) — Hybrid Strategy

## 1. Objective

The **Predictive Geographic Intelligence (IGP)** system identifies the optimal location on Earth for spending one's birthday, maximizing the astrological quality of the Solar Return (SR) according to Persian astrological principles and user preferences. By relocating the SR chart to different geographic coordinates, we can evaluate variations in house cusps, angular placements, and derived scores to recommend the most favorable locations for the upcoming year.

---

## 2. Design Principles

- **Single SR moment in UTC**: The exact moment of the Solar Return is computed once (when the transiting Sun returns to its natal longitude). This instant is fixed and universal; only the geographic relocation varies.
- **Relocation by lat/lon**: For each candidate location, we recompute house cusps and angular positions using the fixed SR datetime and the candidate's coordinates.
- **Configurable scoring function**: A weighted score incorporates dignities, angularity, sect considerations, aspects, and house emphases. Weights are adjustable via `abu_engine/data/weights.json`.
- **Total determinism**: Given identical input (birth data, target year, preferences), the system produces identical output. No randomness in scoring or evaluation.
- **Practical constraints**: Prioritize habitable, accessible locations. Optionally exclude oceanic areas or restrict to specific regions/continents.

---

## 3. Hybrid Approach

The IGP strategy combines three phases to balance computational efficiency, practical relevance, and optimization depth.

### 3.1 Phase 1 — City-Based Preselection

- **Dataset**: Evaluate ~5,000–10,000 cities from `abu_engine/data/cities.json` (includes name, country, latitude, longitude, population).
- **Rationale**: Cities represent habitable, meaningful locations. Provides global coverage with practical relevance.
- **Caching**: Results cached by `(person_hash, target_year, city_id)` to accelerate re-evaluation and iterative refinement.
- **Output**: Top-N cities (e.g., N=20–50) ranked by score.

**Advantages**:
- Fast initial scan (~5–10s for 10k cities with multiprocessing).
- Maintains real-world context (travel, lodging, timezone).
- Strong baseline for 80/20 value.

### 3.2 Phase 2 — Local Refinement

- **Method**: Apply local optimization (Nelder-Mead simplex or hill-climbing) around each of the top-N cities from Phase 1.
- **Step size**: Adaptive, starting at ~0.05°–0.1° (~5–10 km).
- **Bounds**: Restrict search radius to avoid drifting into ocean or uninhabitable terrain (optional land-mask validation).
- **Termination**: Converge when score improvement < threshold (e.g., 0.001) or max iterations reached.
- **Output**: Refined lat/lon coordinates with improved scores.

**Advantages**:
- Extracts additional value from promising areas.
- Handles edge cases where optimal point lies between cities.
- Still deterministic and reproducible.

### 3.3 Phase 3 — Geographic Diversity

- **Clustering**: Group refined results by proximity using H3 geospatial indexing (resolution 7–8, ~1–5 km hexagons) or DBSCAN with ~30–80 km epsilon.
- **Selection**: From each cluster, pick the highest-scoring location. Return 2–3 geographically distinct options.
- **Rationale**: Users benefit from alternatives in different regions (e.g., Europe, South America, Asia) for practical travel planning.

**Advantages**:
- Avoids redundant recommendations (multiple nearby cities).
- Provides strategic options across continents or regions.
- Enhances user experience with actionable variety.

### 3.4 Advanced Alternative — Deep Grid Search (Optional)

For quality assurance or edge cases:
- **Coarse-to-fine global grid**: Start with 2° resolution (~200 km), refine to 0.5° (~50 km), then 0.1° (~10 km) in high-score areas.
- **Use case**: Research validation, benchmarking, or users requesting exhaustive search.
- **Trade-off**: Higher computational cost (minutes instead of seconds). Suitable for async jobs.

---

## 4. Objective Function

The scoring mechanism reuses the established `Solar_Return_Ranking_Implementation.md` framework and `weights.json` configuration.

### 4.1 Core Components

- **Dignities**: Essential dignity scores (domicile, exaltation, triplicity, term, face) per planet.
- **Angularity**: Distance from Ascendant, Midheaven, Descendant, IC. Bands: ±3° (strong), ±6° (moderate), ±10° (weak).
- **Sect**: Diurnal/nocturnal alignment and sect light emphasis.
- **Aspects**: Major aspects (conjunction, opposition, trine, square, sextile) with applying/separating and orbs.
- **House emphasis**: Aggregated planet strength per house (angular houses weighted higher).
- **Malefic mitigation**: Bonification of Mars/Saturn when well-placed or in favorable houses.

### 4.2 Adjustable Weighting by Intent

Users can specify an **intent** to bias the scoring:

| Intent       | Emphasis                                   |
|--------------|---------------------------------------------|
| `health`     | Ascendant, 1st house, sect light           |
| `career`     | Midheaven, 10th house, angular planets     |
| `relationships` | 7th house, Venus, Moon, Descendant       |
| `creative`   | 5th house, Sun, Jupiter                    |
| `general`    | Balanced (default weights)                 |

### 4.3 Example Input and Output

**Input** (simplified):
```json
{
  "birth": {"date": "1990-01-15T10:30:00Z", "lat": 40.7128, "lon": -74.0060},
  "target_year": 2026,
  "intent": "career",
  "preferences": {
    "min_score": 0.65,
    "exclude_regions": ["ocean"],
    "max_candidates": 50
  },
  "refine": true,
  "diversity": true,
  "language": "en"
}
```

**Output** (fragment):
```json
{
  "best_locations": [
    {
      "city": "Barcelona",
      "country": "Spain",
      "lat": 41.3874,
      "lon": 2.1686,
      "score": 0.87,
      "rank": 1
    },
    {
      "city": "Sydney",
      "country": "Australia",
      "lat": -33.8688,
      "lon": 151.2093,
      "score": 0.84,
      "rank": 2
    }
  ],
  "alternatives": [...],
  "clusters": [
    {"region": "Western Europe", "top_score": 0.87, "count": 8},
    {"region": "Oceania", "top_score": 0.84, "count": 3}
  ],
  "score_summary": {
    "angularity": 0.92,
    "dignities": 0.78,
    "aspects": 0.81,
    "house_emphasis": {"1": 0.9, "10": 0.88}
  },
  "astro_metadata": {
    "source": "igp",
    "sr_datetime": "2026-01-15T10:27:43Z",
    "refinement_applied": true,
    "cities_evaluated": 5342,
    "refinement_iterations": 18
  },
  "reasoning": "Barcelona offers strong Midheaven angularity with Jupiter..."
}
```

---

## 5. API Contract

### Endpoint: `POST /api/rs/optimize`

**Request Body**:
```json
{
  "birth": {
    "date": "ISO8601 datetime (UTC preferred)",
    "lat": "decimal degrees",
    "lon": "decimal degrees"
  },
  "target_year": "integer (e.g., 2026)",
  "intent": "string (health|career|relationships|creative|general)",
  "preferences": {
    "min_score": "float (0.0–1.0, optional filter)",
    "exclude_regions": ["ocean", "antarctica"],
    "max_candidates": "integer (default 50)",
    "continents": ["europe", "south_america"] // optional allowlist
  },
  "refine": "boolean (default true)",
  "diversity": "boolean (default true)",
  "language": "string (es|en|pt|fr)"
}
```

**Response**:
```json
{
  "best_locations": [
    {
      "city": "string",
      "country": "string",
      "lat": "float",
      "lon": "float",
      "score": "float",
      "rank": "integer"
    }
  ],
  "alternatives": ["array of similar structure, 3–5 additional options"],
  "clusters": [
    {
      "region": "string",
      "top_score": "float",
      "count": "integer"
    }
  ],
  "score_summary": {
    "angularity": "float",
    "dignities": "float",
    "aspects": "float",
    "house_emphasis": {"1": "float", "10": "float", ...}
  },
  "astro_metadata": {
    "source": "igp",
    "sr_datetime": "ISO8601",
    "refinement_applied": "boolean",
    "cities_evaluated": "integer",
    "refinement_iterations": "integer",
    "duration_ms": "float"
  },
  "reasoning": "string (narrative from Lilly Engine)"
}
```

---

## 6. Technical Pipeline

### 6.1 High-Level Flow

```
User Request (birth, target_year, intent, preferences)
    ↓
[1] Compute SR datetime (UTC) → fixed instant
    ↓
[2] Batch evaluate cities.json → scores per city
    ↓
[3] Select top-N (e.g., 50)
    ↓
[4] If refine=true → local optimization (Nelder-Mead) per top city
    ↓
[5] If diversity=true → cluster by proximity (H3/DBSCAN) → pick 2–3 distinct
    ↓
[6] Format results → call Lilly Engine for reasoning narrative
    ↓
Response (best_locations, alternatives, clusters, reasoning)
```

### 6.2 Parallelization and Caching

- **Multiprocessing**: Use `ProcessPoolExecutor` to evaluate cities in parallel (bypasses GIL). Batch size ~100–500 cities per worker.
- **Cache key**: `(birth_date_hash, target_year, city_id)` → stores score and chart summary.
- **Cache backend**: In-memory LRU (MVP), extend to Redis or disk-backed for persistence.
- **Invalidation**: Clear cache on weight configuration changes or astrological library updates.

### 6.3 Time Budget and Async Mode

- **Sync mode**: Target <30s for 10k cities + refinement. Return results immediately.
- **Async mode** (future): For deep grid search or >20k cities, return job ID and poll status endpoint.
- **Timeout**: If computation exceeds budget, return Phase 1 results only (top cities without refinement).

### 6.4 Structured Logging

Emit event logs for observability:
- `igp.eval_location` per city/coordinate evaluated (lat, lon, score, duration_ms).
- `igp.refinement` per local optimization run (iterations, score_delta).
- `igp.clustering` when applying diversity (clusters_found, selected_count).
- `igp.request` overall job summary (cities_evaluated, refinement_applied, total_duration_ms).

JSON format (if `ABU_VERBOSE=1`):
```json
{
  "ts": "ISO8601",
  "level": "INFO",
  "event": "igp.eval_location",
  "meta": {
    "lat": 41.3874,
    "lon": 2.1686,
    "city": "Barcelona",
    "score": 0.87,
    "dur_ms": 12.3
  }
}
```

---

## 7. Implementation Roadmap

### Sprint 1: Foundation (2–3 weeks)
**Goal**: Batch evaluation by cities + cache + basic endpoint.

**Deliverables**:
- Module `abu_engine/core/igp_optimizer.py`:
  - `compute_sr_instant(birth_date, birth_lat, birth_lon, target_year) -> datetime`
  - `score_location(sr_datetime, lat, lon, weights, intent) -> float`
  - `batch_evaluate_cities(sr_datetime, cities, weights, intent, cache) -> [city_results]`
- Cache wrapper: `abu_engine/core/igp_cache.py` (LRU or Redis adapter).
- Endpoint `POST /api/rs/optimize` (Phase 1 only: cities, no refinement yet).
- Unit tests: determinism, cache hit/miss, scoring consistency.
- Benchmark: 1k / 5k / 10k cities with timings.

**Success Criteria**:
- 10k cities evaluated in <15s (parallel).
- Cache reduces redundant computation by >80%.
- Tests pass with deterministic scores.

---

### Sprint 2: Refinement + Diversity + Narrative (2–3 weeks)
**Goal**: Add local optimization, clustering, and Lilly integration.

**Deliverables**:
- `refine_location(sr_datetime, initial_lat, initial_lon, weights, intent) -> (refined_lat, refined_lon, score)`
- `apply_diversity_clustering(results, min_distance_km) -> [cluster_representatives]`
- Extend endpoint: `refine` and `diversity` flags.
- Lilly prompt extension: interpret `best_locations` and `score_summary` into actionable narrative.
- Preferences parsing: `intent`, `exclude_regions`, `continents`.
- Integration tests: full flow from request to narrative response.
- Benchmark: refinement overhead per top-N.

**Success Criteria**:
- Refinement improves top-N scores by avg 2–5%.
- Diversity returns 2–3 distinct regions.
- Lilly narrative mentions key astrological factors and practical advice.

---

### Sprint 3: Advanced Features + Optimization (2 weeks)
**Goal**: Deep grid mode, persistent cache, weight tuning UI (optional).

**Deliverables**:
- `deep_grid_search(sr_datetime, weights, intent, resolution_steps) -> [grid_results]`
- Persistent cache (Redis or SQLite).
- Admin endpoint (internal): adjust weights dynamically.
- Async job mode: POST returns job ID, GET `/api/rs/optimize/{job_id}` polls status.
- Performance tuning: vectorization, land-mask filtering.
- User validation: A/B test with 5–10 real users.

**Success Criteria**:
- Deep mode completes 50k+ points in <5 min (async).
- Cache persists across restarts.
- Users report 90%+ satisfaction with top recommendations.

---

## 8. Validation and Benchmarks

### 8.1 Determinism Tests

- **Snapshot tests**: For fixed input (birth, year, weights), store expected output. Verify on each run.
- **Cross-platform**: Ensure identical results on Linux, macOS, Windows (ephemeris consistency).

### 8.2 Performance Benchmarks

| Dataset Size | Phase 1 (Cities) | Phase 2 (Refine) | Total (P1+P2) |
|--------------|-------------------|-------------------|---------------|
| 1k cities    | ~1.5s             | ~2s (top 20)      | ~3.5s         |
| 5k cities    | ~7s               | ~2s (top 20)      | ~9s           |
| 10k cities   | ~14s              | ~2s (top 20)      | ~16s          |

*Target hardware: 8-core CPU, 16 GB RAM.*

### 8.3 Comparative Analysis

- **Cities-only vs. Cities+Refinement**: Measure score delta and practical location shift.
- **Expected**: Refinement adds 2–5% score improvement, shifts location by 5–30 km on average.
- **Trade-off**: +2s latency for marginal gain; justify via user preference or "premium" mode.

### 8.4 User Acceptance Testing

- Select 3–5 diverse user profiles (different birth charts, intents).
- Manual review of top-3 recommendations: astrological rationale, practical feasibility, narrative quality.
- Feedback loop: adjust weights or clustering radius based on qualitative input.

---

## 9. Technical Notes

### 9.1 House System

- **MVP**: Whole Sign Houses (simple, traditional, fast).
- **Future**: Support Placidus, Porphyry, or user-selected system via `preferences.house_system`.

### 9.2 Angularity Bands

Define proximity thresholds for angular strength:
- **Strong**: ±3° from exact angle (ASC, MC, DSC, IC).
- **Moderate**: ±6°.
- **Weak**: ±10°.
- Planets outside ±10° receive minimal angularity score.

### 9.3 Sect and Dignities

- **Sect**: Determine chart sect (diurnal/nocturnal) based on Sun above/below horizon.
- **Sect Light**: Sun (diurnal) or Moon (nocturnal) receives bonus weight.
- **Dignities**: Use traditional rulership (e.g., Mars rules Aries/Scorpio). Reference `abu_engine/core/dignities.py` and TRADITIONAL_RULERS table.

### 9.4 Clustering Parameters

- **H3 Resolution**: 7 (~5 km hexagons) for urban areas, 8 (~1 km) for dense cities.
- **DBSCAN**: `eps=30–80 km`, `min_samples=1` (every point forms potential cluster).
- **Selection**: From each cluster, pick highest score. If cluster size >5, consider user's travel preferences (e.g., larger city vs. smaller town).

### 9.5 Land Mask (Optional)

- Use geographic dataset or bounding box checks to exclude oceanic coordinates.
- Trade-off: Adds I/O overhead. Start without; enable if users report ocean results.

### 9.6 Logging Best Practices

- Use structured JSON events (`igp.*` namespace).
- Avoid logging every coordinate in deep grid mode (log every 100th or summary only).
- Include `job_id` in async mode for traceability.

---

## 10. Summary Table — Sprint 1 Deliverables

| Input                          | Process                                  | Output                              | Sprint 1 Status |
|--------------------------------|------------------------------------------|-------------------------------------|-----------------|
| Birth data (date, lat, lon)    | Compute SR instant (UTC)                 | Fixed SR datetime                   | ✅ Planned       |
| Target year                    | Load cities.json                         | ~5–10k city records                 | ✅ Planned       |
| Intent (career/health/etc.)    | Apply weight adjustments                 | Intent-specific scoring function    | ✅ Planned       |
| Cities + SR datetime + weights | Batch evaluate (multiprocess + cache)    | Scored list of cities               | ✅ Planned       |
| Top-N cities                   | Sort and filter by `min_score`           | Ranked top-N (e.g., 50)             | ✅ Planned       |
| Ranked results                 | Format JSON response                     | `best_locations`, `score_summary`   | ✅ Planned       |
| (Refinement deferred)          | —                                        | —                                   | 🔄 Sprint 2      |
| (Diversity deferred)           | —                                        | —                                   | 🔄 Sprint 2      |
| (Lilly narrative deferred)     | —                                        | —                                   | 🔄 Sprint 2      |

**Sprint 1 Success Metrics**:
- Endpoint `/api/rs/optimize` functional with Phase 1 (cities only).
- 10k cities evaluated in <15s.
- Cache achieves >80% hit rate on repeated queries.
- Unit tests validate deterministic scoring.
- Benchmark report documents performance baseline.

---

## 11. Future Enhancements

- **Multi-year planning**: Extend to evaluate optimal locations for next 3–5 years.
- **Cost and logistics integration**: API to fetch flight prices, visa requirements, lodging.
- **Interactive UI**: Map visualization with score heatmap and clickable city markers.
- **Machine learning**: Train a surrogate model (XGBoost, neural net) on scored samples to accelerate deep grid search.
- **Collaborative filtering**: Aggregate anonymized user data to recommend popular or successful relocation choices.

---

## References

- `abu_engine/core/solar_return.py` — SR datetime calculation.
- `abu_engine/core/solar_return_ranking.py` — Scoring logic.
- `abu_engine/data/weights.json` — Configurable weights.
- `abu_engine/data/cities.json` — Global city dataset.
- `docs/Solar_Return_Ranking_Implementation.md` — Detailed scoring methodology.
- `docs/Solar_Return_Relocation_API.md` — Existing relocation endpoint (inspiration).

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-09  
**Maintainer**: AI Oracle Development Team
