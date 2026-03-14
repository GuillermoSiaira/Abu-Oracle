"""Weight Optimizer: find optimal w_h, w_t, w_c that maximize correlation
between HF_weighted and event valence.

Strategy: grid search over weight space. Since we already have per-event
harmony/tension/conjunction components from the correlator, we just
re-compute HF_weighted = w_h*harmony + w_t*tension + w_c*conjunction
for each weight combination and measure correlation with valence.

No ephemeris recomputation needed — pure arithmetic on cached data.
"""
from __future__ import annotations

import json
import logging
import sys
from itertools import product
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

RESULTS_PATH = Path(__file__).resolve().parent.parent / "data" / "biographical_events" / "correlation_results.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "biographical_events" / "optimization_results.json"


def load_events() -> list[dict]:
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]


def compute_metrics(events: list[dict], w_h: float, w_t: float, w_c: float) -> dict:
    """Re-compute HF_weighted for all events with given weights and return correlation."""
    valences = []
    hf_vals = []
    natal_hf_vals = []

    for evt in events:
        h = evt["transit_hf_harmony"]
        t = evt["transit_hf_tension"]
        c = evt["transit_hf_conjunction"]
        hf_w = w_h * h + w_t * t + w_c * c
        hf_vals.append(hf_w)
        valences.append(evt["valence_num"])

        # Also re-weight natal for delta
        # natal components not stored — approximate from natal_hf_weighted
        # Actually we need natal harmony/tension/conjunction too.
        # For now use delta approach: compare within-subject z-scores
        natal_hf_vals.append(evt.get("natal_hf_weighted", 0.0))

    valences = np.array(valences)
    hf_vals = np.array(hf_vals)

    # Correlations
    def safe_corr(a, b):
        if len(a) < 3 or np.std(a) < 1e-10 or np.std(b) < 1e-10:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    # All events
    corr_all = safe_corr(valences, hf_vals)

    # Non-neutral only
    non_neutral = valences != 0
    corr_nn = safe_corr(valences[non_neutral], hf_vals[non_neutral]) if non_neutral.sum() >= 3 else 0.0

    # Group means
    pos_mask = valences > 0
    neg_mask = valences < 0
    mean_pos = float(hf_vals[pos_mask].mean()) if pos_mask.sum() > 0 else 0.0
    mean_neg = float(hf_vals[neg_mask].mean()) if neg_mask.sum() > 0 else 0.0

    # Separation score: how well positive and negative are separated
    # Higher = positive events have higher HF than negative events
    separation = mean_pos - mean_neg

    # Cohen's d (effect size)
    if pos_mask.sum() > 1 and neg_mask.sum() > 1:
        s_pos = float(hf_vals[pos_mask].std())
        s_neg = float(hf_vals[neg_mask].std())
        pooled_std = np.sqrt((s_pos**2 + s_neg**2) / 2)
        cohens_d = separation / pooled_std if pooled_std > 0 else 0.0
    else:
        cohens_d = 0.0

    return {
        "w_h": w_h, "w_t": w_t, "w_c": w_c,
        "corr_all": corr_all,
        "corr_nn": corr_nn,
        "mean_pos": mean_pos,
        "mean_neg": mean_neg,
        "separation": separation,
        "cohens_d": cohens_d,
    }


def grid_search(events: list[dict]) -> list[dict]:
    """Exhaustive grid search over weight space."""
    # Fine grid: w_h in [-2, 3], w_t in [-2, 3], w_c in [-2, 3], step 0.25
    w_range = np.arange(-2.0, 3.25, 0.25)
    
    results = []
    total = len(w_range) ** 3
    logger.info("Grid search: %d combinations (%d^3)", total, len(w_range))

    for i, (wh, wt, wc) in enumerate(product(w_range, w_range, w_range)):
        metrics = compute_metrics(events, float(wh), float(wt), float(wc))
        results.append(metrics)
        if (i + 1) % 5000 == 0:
            logger.info("  %d / %d done …", i + 1, total)

    return results


def analyze_results(results: list[dict]) -> dict:
    """Find best weights by different criteria."""

    # 1. Best by correlation (all events) — want POSITIVE correlation
    best_corr_all = max(results, key=lambda r: r["corr_all"])

    # 2. Best by correlation (non-neutral)
    best_corr_nn = max(results, key=lambda r: r["corr_nn"])

    # 3. Best by separation (positive - negative)
    best_sep = max(results, key=lambda r: r["separation"])

    # 4. Best by Cohen's d effect size
    best_d = max(results, key=lambda r: r["cohens_d"])

    # 5. Composite score: normalize and combine
    # composite = 0.4*corr_nn + 0.3*separation + 0.3*cohens_d
    corr_vals = np.array([r["corr_nn"] for r in results])
    sep_vals = np.array([r["separation"] for r in results])
    d_vals = np.array([r["cohens_d"] for r in results])

    def norm(arr):
        mn, mx = arr.min(), arr.max()
        return (arr - mn) / (mx - mn) if mx > mn else np.zeros_like(arr)

    composite = 0.4 * norm(corr_vals) + 0.3 * norm(sep_vals) + 0.3 * norm(d_vals)
    best_composite_idx = int(np.argmax(composite))
    best_composite = results[best_composite_idx]

    return {
        "best_by_corr_all": best_corr_all,
        "best_by_corr_nn": best_corr_nn,
        "best_by_separation": best_sep,
        "best_by_cohens_d": best_d,
        "best_composite": best_composite,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s",
                        stream=sys.stdout)

    events = load_events()
    logger.info("Loaded %d events", len(events))

    results = grid_search(events)
    analysis = analyze_results(results)

    print("\n" + "=" * 75)
    print("WEIGHT OPTIMIZATION RESULTS")
    print("=" * 75)

    for label, best in analysis.items():
        print(f"\n{label}:")
        print(f"  Weights: w_h={best['w_h']:.2f}  w_t={best['w_t']:.2f}  w_c={best['w_c']:.2f}")
        print(f"  Corr(all)={best['corr_all']:.4f}  Corr(nn)={best['corr_nn']:.4f}")
        print(f"  Mean+ = {best['mean_pos']:.4f}  Mean- = {best['mean_neg']:.4f}  Sep = {best['separation']:.4f}")
        print(f"  Cohen's d = {best['cohens_d']:.4f}")

    # Print the initial weights for comparison
    initial = compute_metrics(events, 1.5, -0.8, 1.0)
    print(f"\nInitial weights (1.5, -0.8, 1.0) for comparison:")
    print(f"  Corr(all)={initial['corr_all']:.4f}  Corr(nn)={initial['corr_nn']:.4f}")
    print(f"  Mean+ = {initial['mean_pos']:.4f}  Mean- = {initial['mean_neg']:.4f}  Sep = {initial['separation']:.4f}")
    print(f"  Cohen's d = {initial['cohens_d']:.4f}")

    # Also test: what if ALL weights equal (legacy)?
    legacy = compute_metrics(events, 1.0, 1.0, 1.0)
    print(f"\nLegacy weights (1.0, 1.0, 1.0):")
    print(f"  Corr(all)={legacy['corr_all']:.4f}  Corr(nn)={legacy['corr_nn']:.4f}")
    print(f"  Mean+ = {legacy['mean_pos']:.4f}  Mean- = {legacy['mean_neg']:.4f}  Sep = {legacy['separation']:.4f}")
    print(f"  Cohen's d = {legacy['cohens_d']:.4f}")

    print("=" * 75)

    # Save
    save_data = {
        "analysis": {k: v for k, v in analysis.items()},
        "initial_weights": initial,
        "legacy_weights": legacy,
        "grid_config": {"range": [-2.0, 3.0], "step": 0.25, "n_combinations": len(results)},
        "n_events": len(events),
        # Top 20 by composite
        "top_20_composite": sorted(results, key=lambda r: 
            0.4 * r["corr_nn"] + 0.3 * r["separation"] + 0.3 * r["cohens_d"], 
            reverse=True)[:20],
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {OUTPUT_PATH}")
