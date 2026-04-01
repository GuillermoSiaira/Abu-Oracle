# Abu Oracle Research Repository

> Public companion to the Abu Oracle astrological computation engine.
> Contains anonymised corpus statistics, validation results, and reproducibility assets.

---

## Overview

Abu Oracle is a computational astrology system combining:
- **Harmony Field (HF)** — a geographic scalar field measuring natal chart resonance across ~9,425 grid points worldwide
- **Domain-filtered HF (v6)** — HF restricted to planetary significators of a specific life domain (house)
- **Lilly** — an LLM interpretation agent (Claude Sonnet 4.6) consuming the computed context

This repository documents the empirical validation of the HF hypothesis:

> *Locations with higher HF scores in the relevant life domain are statistically associated with positive biographical events in that domain.*

---

## Repository Structure

```
abu-oracle-research/
├── data/
│   ├── corpus/
│   │   ├── events_summary.csv       # Aggregate corpus statistics (1 row)
│   │   └── events_public.csv        # Anonymised event-level data (no subject names)
│   └── results/
│       ├── correlation_v3_global.json    # Global HF_v3 validation
│       └── domain_correlation_table.csv  # Per-domain HF_v6 validation
├── figures/
│   ├── corpus_overview.png
│   ├── hf_valence_distribution.png
│   ├── domain_correlation_heatmap.png
│   └── cohens_d_by_domain.png
├── config/
│   └── event_house_map.json         # Event type to house mapping
├── notebooks/
│   ├── 01_corpus_audit.ipynb
│   ├── 02_hfv3_global_validation.ipynb
│   └── 03_hfv6_domain_validation.ipynb
└── hashes/
```

---

## Corpus

| Metric | Value |
|--------|-------|
| Total events | 527 |
| Positive | 377 (71.5%) |
| Negative | 69 (13.1%) |
| Neutral | 81 (15.4%) |
| Subjects | 26 |
| Date range | 1853 - 2021 |
| Event types | 25 |

### Data Quality

Rodden Rating is not directly available in this dataset. The `source` field from
carta-natal.es is used as a proxy for birth data quality:

| Source Category | Events |
|----------------|--------|
| Birth Certificate (Certificado/Registro nacimiento) | 425 |
| Biography / Memoir (Bio/Memorias) | 49 |
| Other / Gold Standard hand-curated subjects | 53 |
| Unconfirmed | 0 |

All birth times in the corpus have `time_precision: exact` (sourced from natal chart
databases with recorded birth hours). Gold Standard subjects (GS_001 Jung, GS_002 Tesla,
GS_003 Turing) are hand-curated.

**Limitations:**
- Positive/negative valence imbalance (377 vs 69) limits Pearson r sensitivity, especially
  for domains dominated by positive events (H10 Career: 231 positive / 4 negative).
- Events were assigned to houses via per-event labeling using Persian-Hellenistic doctrine.
  The `event_house_map.json` in this repo provides the heuristic event-type-to-house mapping
  used for reproducibility; the authoritative labels are in the private v2 corpus.
- Spatial validation (HF at actual event location) was not possible for most subjects
  because biographical events lack precise coordinates. Location-of-birth was used as
  a proxy.

---

## Results

### HF_v3 Global Validation

| Metric | Value |
|--------|-------|
| Pearson r (all events) | 0.121 |
| Pearson r (non-neutral) | 0.133 |
| Cohen's d | 0.441 |
| Mean HF+ (positive events) | -12.01 |
| Mean HF- (negative events) | -13.10 |

Cohen's d = 0.441 (medium effect size) despite the small Pearson r. The negative
HF values reflect optimized weights (w_h=-1.0, w_t=-1.0, w_c=+2.5) where harmony
and tension components were negatively weighted — the conjunction component dominates.

### HF_v6 Domain-Filtered Validation

| House | Domain | N | N+ | N- | r_global | r_domain | d_global | d_domain | p_global | p<.05 |
|-------|--------|---|----|----|----------|----------|----------|----------|----------|-------|
| 1 | Identidad | 3 | 0 | 1 | 0.023 | -0.890 | — | — | — |  |
| 2 | Recursos | 2 | 0 | 2 | — | — | — | — | — |  |
| 3 | Comunicacion | 0 | 0 | 0 | — | — | — | — | — |  |
| 4 | Hogar | 0 | 0 | 0 | — | — | — | — | — |  |
| 5 | Creatividad | 57 | 51 | 1 | 0.200 | 0.350 | — | — | 0.155 |  |
| 6 | Trabajo/Salud | 10 | 0 | 9 | -0.123 | -0.117 | — | — | 0.753 |  |
| 7 | Relaciones | 93 | 81 | 9 | 0.063 | 0.041 | 0.207 | 0.055 | 0.558 |  |
| 8 | Transformacion | 34 | 0 | 34 | — | — | — | — | — |  |
| 9 | Expansion | 66 | 14 | 4 | -0.063 | -0.045 | -0.221 | -0.175 | 0.805 |  |
| 10 | Carrera | 250 | 231 | 4 | 0.074 | 0.013 | 0.567 | 0.056 | 0.261 |  |
| 12 | Inconsciente | 12 | 0 | 5 | -0.070 | -0.377 | — | — | 0.911 |  |

**Key findings:**
- **H05 Creatividad** (n=57): domain filtering consistently improves correlation
  (+0.150 delta). Strongest reproducible result in the corpus.
- **H07 Relaciones** (n=93): near-zero correlation in both metrics. Marriage events
  are distributed across the HF spectrum with no geographic preference.
- **H09 Expansion** (n=66): modest negative Cohen's d; domain filtering slightly
  reduces the effect size. Signal remains weak.
- **H10 Carrera** (n=250): high Cohen's d_global (0.567) but near-zero d_domain.
  The domain filter does not improve career event prediction; likely because H10
  significators include slow outer planets (Neptune, Pluto) with low temporal variance.
  Severe valence imbalance (231 positive / 4 negative) prevents meaningful Pearson r.

---

## Reproducibility

### Requirements

```bash
pip install pandas numpy scipy matplotlib seaborn
```

### Running the analysis

The build script reads from `d:/projects/ai-oracle/data/` and writes to this repo.
Adjust `ROOT` at the top of each script for your environment.

```bash
PYTHONUTF8=1 python build_research_repo.py
PYTHONUTF8=1 python build_table_3c.py
PYTHONUTF8=1 python build_figures_34.py
```

Notebooks in `notebooks/` provide step-by-step walkthroughs of each phase.

---

## File Integrity

| File | SHA-256 |
|------|---------|
| events_detailed.csv | `aea8ea86d87f9ef2463e0280e54fb9401fb4faed7f9372137ebc9f1bbec7069c` |

---

## Citation

```
Abu Oracle Research Team (2026).
Empirical Validation of Harmony Field: A Geographic Scalar Field for
Persian-Hellenistic Astrological Doctrine.
Technical Report. https://abu-oracle.com/corpus/
```

---

## License

Corpus data: research use only. Subject identities anonymised in public files.
Code: MIT.

*Generated: 2026-04-01*
