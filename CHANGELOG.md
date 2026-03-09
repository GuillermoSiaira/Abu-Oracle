# CHANGELOG – Abu Oracle

**2026-01-09**

## Persian Determinism Refactor (lilly_swarm/core/llm.py)
- **Objective:** Shift LLM personality from "Modern/Psychological" to "Medieval/Deterministic" and fix critical data hallucination (ignoring planets in houses).
- **Key Changes:**
    - **PROMPT_TEMPLATES Refactor:** ES/EN templates rewritten to forbid psychological terms and enforce concrete predictive language ("enemies", "restrictions", "wealth").
    - **build_prompt System Override:** Injected `### SYSTEM OVERRIDE: AXIOMATIC MODE` block at the top of the prompt, forcing the model to scan the JSON data and strictly interpret planets in their listed houses.
    - **Strict System Message:** Updated `generate_interpretation` to define the system role as a "deterministic astrological engine".
- **Validation:** Confirmed with Alan Turing Test Case (1912): Saturn in House 12 now yields deterministic interpretation (imprisonment/enemies).

---

## Roadmap Status
- **Phase 3 UI/UX & Logic Fixes:** Completed (Gold/Black theme, Context Memory Injection, Semantic Determinism).
- **Next Priority (per ARCHITECTURE.md):**
    1. Real Streaming / Server-Sent Events (SSE) for frontend-backend transport layer.
    2. Pending: Harmony Field implementation and Agents Expansion (Firdarias/Profections) may require attention before full SSE optimization, depending on architectural dependencies.
- **Recommendation:**
    - Review Harmony Field and Agents Expansion tasks for technical blockers.
    - If no blockers, proceed with SSE/streaming implementation as next milestone.

---

**References:**
- ARCHITECTURE.md
- ABU_MEDICION_EFICIENCIA_COMPUTACIONAL_2026-01-03.md
- Phase 3 UI/UX & Logic Fixes documentation
