"""Leave-One-Subject-Out (LOSO) Cross-Validation for HF weight optimization.

For each of the 26 subjects:
  1. Hold out that subject's events (test set)
  2. Run grid search on the remaining 25 subjects (train set)
  3. Record the optimal weights found on train set
  4. Evaluate those weights on the held-out subject
  5. Collect per-fold metrics

This validates whether the optimized weights generalize across subjects
or are artifacts of fitting to specific individuals.

Output: data/biographical_events/cross_validation_results.json
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
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "biographical_events" / "cross_validation_results.json"


def load_events() -> list[dict]:
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]


def compute_metrics(events: list[dict], w_h: float, w_t: float, w_c: float) -> dict:
    """Compute correlation metrics for a set of events with given weights."""
    if not events:
        return {"corr_nn": 0.0, "cohens_d": 0.0, "separation": 0.0, "n": 0}

    valences = np.array([e["valence_num"] for e in events])
    hf_vals = np.array([w_h * e["transit_hf_harmony"] + w_t * e["transit_hf_tension"] + w_c * e["transit_hf_conjunction"]
                        for e in events])

    def safe_corr(a, b):
        if len(a) < 3 or np.std(a) < 1e-10 or np.std(b) < 1e-10:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    non_neutral = valences != 0
    corr_nn = safe_corr(valences[non_neutral], hf_vals[non_neutral]) if non_neutral.sum() >= 3 else 0.0

    pos_mask = valences > 0
    neg_mask = valences < 0
    mean_pos = float(hf_vals[pos_mask].mean()) if pos_mask.sum() > 0 else 0.0
    mean_neg = float(hf_vals[neg_mask].mean()) if neg_mask.sum() > 0 else 0.0
    separation = mean_pos - mean_neg

    if pos_mask.sum() > 1 and neg_mask.sum() > 1:
        s_pos = float(hf_vals[pos_mask].std())
        s_neg = float(hf_vals[neg_mask].std())
        pooled_std = np.sqrt((s_pos**2 + s_neg**2) / 2)
        cohens_d = separation / pooled_std if pooled_std > 0 else 0.0
    else:
        cohens_d = 0.0

    return {
        "corr_nn": corr_nn,
        "cohens_d": cohens_d,
        "separation": separation,
        "n": len(events),
        "n_pos": int(pos_mask.sum()),
        "n_neg": int(neg_mask.sum()),
    }


def grid_search_best(events: list[dict]) -> dict:
    """Find best weights by Cohen's d on the given events."""
    w_range = np.arange(-2.0, 3.25, 0.25)
    best = None
    best_d = -999.0

    for wh, wt, wc in product(w_range, w_range, w_range):
        m = compute_metrics(events, float(wh), float(wt), float(wc))
        if m["cohens_d"] > best_d:
            best_d = m["cohens_d"]
            best = {"w_h": float(wh), "w_t": float(wt), "w_c": float(wc), **m}

    return best


def loso_cross_validation(events: list[dict]) -> dict:
    """Leave-One-Subject-Out cross-validation."""
    subjects = sorted(set(e["subject_id"] for e in events))
    n_subjects = len(subjects)
    logger.info("LOSO CV: %d subjects, %d events", n_subjects, len(events))

    folds = []

    for i, held_out in enumerate(subjects):
        train_events = [e for e in events if e["subject_id"] != held_out]
        test_events = [e for e in events if e["subject_id"] == held_out]

        held_out_name = test_events[0]["subject_name"] if test_events else held_out

        logger.info("  Fold %2d/%d: hold out %-20s (%3d test, %3d train)",
                     i + 1, n_subjects, held_out_name, len(test_events), len(train_events))

        # Train: find best weights on remaining subjects
        train_best = grid_search_best(train_events)

        # Test: evaluate those weights on held-out subject
        test_metrics = compute_metrics(
            test_events,
            train_best["w_h"], train_best["w_t"], train_best["w_c"]
        )

        # Also evaluate v2 production weights on test
        v2_test = compute_metrics(test_events, -1.0, -1.0, 2.5)

        folds.append({
            "fold": i + 1,
            "held_out_subject": held_out,
            "held_out_name": held_out_name,
            "n_train": len(train_events),
            "n_test": len(test_events),
            "train_best_weights": {
                "w_h": train_best["w_h"],
                "w_t": train_best["w_t"],
                "w_c": train_best["w_c"],
            },
            "train_cohens_d": train_best["cohens_d"],
            "train_corr_nn": train_best["corr_nn"],
            "test_cohens_d": test_metrics["cohens_d"],
            "test_corr_nn": test_metrics["corr_nn"],
            "test_separation": test_metrics["separation"],
            "v2_test_cohens_d": v2_test["cohens_d"],
            "v2_test_corr_nn": v2_test["corr_nn"],
        })

    # Summary statistics
    train_weights = [(f["train_best_weights"]["w_h"],
                      f["train_best_weights"]["w_t"],
                      f["train_best_weights"]["w_c"]) for f in folds]
    w_h_vals = [w[0] for w in train_weights]
    w_t_vals = [w[1] for w in train_weights]
    w_c_vals = [w[2] for w in train_weights]

    # How often is the sign pattern preserved?
    sign_preserved = sum(1 for wh, wt, wc in train_weights
                         if wh < 0 and wt < 0 and wc > 0)

    # Test-set Cohen's d distribution (only folds with enough test neg events)
    test_ds = [f["test_cohens_d"] for f in folds
               if f["n_test"] >= 5]
    v2_test_ds = [f["v2_test_cohens_d"] for f in folds
                  if f["n_test"] >= 5]

    summary = {
        "n_folds": n_subjects,
        "n_events": len(events),
        "sign_pattern_preserved": f"{sign_preserved}/{n_subjects}",
        "sign_pattern_ratio": round(sign_preserved / n_subjects, 3),
        "weight_stability": {
            "w_h": {"mean": round(np.mean(w_h_vals), 3), "std": round(np.std(w_h_vals), 3),
                    "min": round(min(w_h_vals), 2), "max": round(max(w_h_vals), 2)},
            "w_t": {"mean": round(np.mean(w_t_vals), 3), "std": round(np.std(w_t_vals), 3),
                    "min": round(min(w_t_vals), 2), "max": round(max(w_t_vals), 2)},
            "w_c": {"mean": round(np.mean(w_c_vals), 3), "std": round(np.std(w_c_vals), 3),
                    "min": round(min(w_c_vals), 2), "max": round(max(w_c_vals), 2)},
        },
        "test_cohens_d": {
            "n_folds_with_enough_data": len(test_ds),
            "mean": round(float(np.mean(test_ds)), 4) if test_ds else None,
            "std": round(float(np.std(test_ds)), 4) if test_ds else None,
            "median": round(float(np.median(test_ds)), 4) if test_ds else None,
            "min": round(float(np.min(test_ds)), 4) if test_ds else None,
            "max": round(float(np.max(test_ds)), 4) if test_ds else None,
        },
        "v2_fixed_weights_test_d": {
            "mean": round(float(np.mean(v2_test_ds)), 4) if v2_test_ds else None,
            "std": round(float(np.std(v2_test_ds)), 4) if v2_test_ds else None,
            "median": round(float(np.median(v2_test_ds)), 4) if v2_test_ds else None,
        },
        "v2_production_weights": {"w_h": -1.0, "w_t": -1.0, "w_c": 2.5},
    }

    return {"summary": summary, "folds": folds}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s",
                        stream=sys.stdout)

    events = load_events()
    logger.info("Loaded %d events", len(events))

    results = loso_cross_validation(events)

    print("\n" + "=" * 75)
    print("LEAVE-ONE-SUBJECT-OUT CROSS-VALIDATION RESULTS")
    print("=" * 75)

    s = results["summary"]
    print(f"\nFolds: {s['n_folds']}  |  Events: {s['n_events']}")
    print(f"Sign pattern (w_h<0, w_t<0, w_c>0) preserved: {s['sign_pattern_preserved']} folds")

    ws = s["weight_stability"]
    print(f"\nWeight stability across folds:")
    print(f"  w_h: mean={ws['w_h']['mean']:+.3f}  std={ws['w_h']['std']:.3f}  range=[{ws['w_h']['min']:.2f}, {ws['w_h']['max']:.2f}]")
    print(f"  w_t: mean={ws['w_t']['mean']:+.3f}  std={ws['w_t']['std']:.3f}  range=[{ws['w_t']['min']:.2f}, {ws['w_t']['max']:.2f}]")
    print(f"  w_c: mean={ws['w_c']['mean']:+.3f}  std={ws['w_c']['std']:.3f}  range=[{ws['w_c']['min']:.2f}, {ws['w_c']['max']:.2f}]")

    td = s["test_cohens_d"]
    print(f"\nTest-set Cohen's d (per-fold trained weights, {td['n_folds_with_enough_data']} eligible folds):")
    print(f"  mean={td['mean']:.4f}  std={td['std']:.4f}  median={td['median']:.4f}  range=[{td['min']:.4f}, {td['max']:.4f}]")

    v2d = s["v2_fixed_weights_test_d"]
    print(f"\nv2 production weights (-1, -1, 2.5) on test sets:")
    print(f"  mean={v2d['mean']:.4f}  std={v2d['std']:.4f}  median={v2d['median']:.4f}")

    print(f"\n{'='*75}")
    print("Per-fold details:")
    print(f"{'Fold':>4} {'Subject':<22} {'Train d':>8} {'Test d':>8} {'v2 Test d':>9} {'Train wh':>8} {'Train wt':>8} {'Train wc':>8}")
    print("-" * 90)
    for f in results["folds"]:
        w = f["train_best_weights"]
        print(f"{f['fold']:4d} {f['held_out_name']:<22} {f['train_cohens_d']:+8.3f} {f['test_cohens_d']:+8.3f} {f['v2_test_cohens_d']:+9.3f} {w['w_h']:+8.2f} {w['w_t']:+8.2f} {w['w_c']:+8.2f}")

    print("=" * 75)

    # Save results
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {OUTPUT_PATH}")
