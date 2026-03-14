#!/usr/bin/env python3
"""Three concrete analyses on HF-Valence correlation."""

import json
from pathlib import Path
import numpy as np
from scipy import stats

# Load data
results_file = Path("data/biographical_events/correlation_results.json")
with open(results_file, encoding='utf-8') as f:
    data = json.load(f)

events = data.get('events', [])
print(f"Total events: {len(events)}\n")

# Convert to working format
events_data = []
for e in events:
    events_data.append({
        'subject_id': e.get('subject_id'),
        'subject_name': e.get('subject_name'),
        'event_date': e.get('event_date'),
        'event_type': e.get('event_type'),
        'valence_num': float(e.get('valence_num', 0)),
        'hf_harmony': float(e.get('transit_hf_harmony', 0)),
        'hf_tension': float(e.get('transit_hf_tension', 0)),
        'hf_conjunction': float(e.get('transit_hf_conjunction', 0)),
        'hf_weighted': float(e.get('transit_hf_weighted', 0)),
        'description': e.get('description', ''),
    })

# ============================================================================
# ANALYSIS 1: Distribution of valence by quartile of hf_harmony
# ============================================================================
print("=" * 80)
print("ANALYSIS 1: VALENCE DISTRIBUTION BY HF_HARMONY QUARTILE")
print("=" * 80)

harmonies = [e['hf_harmony'] for e in events_data]
q1, q2, q3 = np.percentile(harmonies, [25, 50, 75])

print(f"\nQuartile cutoffs:")
print(f"  Q1 (<={q1:.2f}): bottom 25%")
print(f"  Q2 ({q1:.2f} to {q2:.2f}): 25-50%")
print(f"  Q3 ({q2:.2f} to {q3:.2f}): 50-75%")
print(f"  Q4 (>{q3:.2f}): top 25%")

quartiles = []
for name, condition in [
    ('Q1', lambda e: e['hf_harmony'] <= q1),
    ('Q2', lambda e: q1 < e['hf_harmony'] <= q2),
    ('Q3', lambda e: q2 < e['hf_harmony'] <= q3),
    ('Q4', lambda e: e['hf_harmony'] > q3),
]:
    subset = [e for e in events_data if condition(e)]
    pos = sum(1 for e in subset if e['valence_num'] > 0)
    neg = sum(1 for e in subset if e['valence_num'] < 0)
    neu = sum(1 for e in subset if e['valence_num'] == 0)
    total = len(subset)
    pos_pct = 100 * pos / total if total > 0 else 0

    print(f"\n{name} (n={total}):")
    print(f"  Positive: {pos} ({pos_pct:.1f}%)")
    print(f"  Negative: {neg} ({100*neg/total if total > 0 else 0:.1f}%)")
    print(f"  Neutral:  {neu} ({100*neu/total if total > 0 else 0:.1f}%)")
    print(f"  Mean valence: {np.mean([e['valence_num'] for e in subset]):.3f}")
    quartiles.append({'name': name, 'pct_positive': pos_pct, 'n': total})

# Statistical test: ANOVA across quartiles
q1_vals = [e['valence_num'] for e in events_data if e['hf_harmony'] <= q1]
q4_vals = [e['valence_num'] for e in events_data if e['hf_harmony'] > q3]
t_stat, p_val = stats.ttest_ind(q4_vals, q1_vals)
print(f"\nT-test Q4 vs Q1: t={t_stat:.3f}, p={p_val:.4f}")
if p_val < 0.05:
    print("  [YES] SIGNIFICANT difference in valence between Q4 and Q1")
else:
    print("  [NO] NO significant difference — hf_harmony does NOT discriminate valence")

# ============================================================================
# ANALYSIS 2: Partial correlation
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 2: PARTIAL CORRELATION (controlling for tension + conjunction)")
print("=" * 80)

# Simple correlation first
harmony = np.array([e['hf_harmony'] for e in events_data])
valence = np.array([e['valence_num'] for e in events_data])
tension = np.array([e['hf_tension'] for e in events_data])
conjunction = np.array([e['hf_conjunction'] for e in events_data])

corr_raw = np.corrcoef(harmony, valence)[0, 1]
print(f"\nSimple correlation (hf_harmony vs valence): r={corr_raw:.4f}")

# Partial correlation: residuals method
# Use linear regression to get residuals
from scipy.stats import linregress

# harmony ~ tension
reg_h_t = linregress(tension, harmony)
resid_h = harmony - (reg_h_t.intercept + reg_h_t.slope * tension)

# valence ~ tension
reg_v_t = linregress(tension, valence)
resid_v = valence - (reg_v_t.intercept + reg_v_t.slope * tension)

# Now correlate residuals (partial correlation)
corr_partial_t = np.corrcoef(resid_h, resid_v)[0, 1]
print(f"Partial correlation (controlling for tension): r={corr_partial_t:.4f}")

# Also do it with conjunction
reg_h_c = linregress(conjunction, harmony)
resid_h2 = harmony - (reg_h_c.intercept + reg_h_c.slope * conjunction)

reg_v_c = linregress(conjunction, valence)
resid_v2 = valence - (reg_v_c.intercept + reg_v_c.slope * conjunction)

corr_partial_c = np.corrcoef(resid_h2, resid_v2)[0, 1]
print(f"Partial correlation (controlling for conjunction): r={corr_partial_c:.4f}")

# Even better: use all three
try:
    import statsmodels.api as sm
    X_full = sm.add_constant(np.column_stack([tension, conjunction]))
    model = sm.OLS(valence, X_full).fit()
    print(f"\n--- OLS Regression: valence ~ tension + conjunction ---")
    print(f"Tension coef: {model.params[1]:.4f} (p={model.pvalues[1]:.4f})")
    print(f"Conjunction coef: {model.params[2]:.4f} (p={model.pvalues[2]:.4f})")

    # Now add harmony
    X_with_harmony = sm.add_constant(np.column_stack([harmony, tension, conjunction]))
    model2 = sm.OLS(valence, X_with_harmony).fit()
    print(f"\n--- OLS Regression: valence ~ harmony + tension + conjunction ---")
    print(f"Harmony coef: {model2.params[1]:.4f} (p={model2.pvalues[1]:.4f})")
    print(f"Tension coef: {model2.params[2]:.4f} (p={model2.pvalues[2]:.4f})")
    print(f"Conjunction coef: {model2.params[3]:.4f} (p={model2.pvalues[3]:.4f})")
    print(f"R-squared: {model2.rsquared:.4f}")
except ImportError:
    print("(statsmodels not available, skipping OLS)")

# ============================================================================
# ANALYSIS 3: Marilyn Monroe deep dive
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 3: MARILYN MONROE — ALL EVENTS BY DATE")
print("=" * 80)

monroe_events = [e for e in events_data if e['subject_name'] == 'Marilyn Monroe']
monroe_events.sort(key=lambda x: x['event_date'])

print(f"\nTotal events for Marilyn Monroe: {len(monroe_events)}\n")
print(f"{'Date':<12} {'Type':<20} {'Valence':<10} {'hf_harmony':<12} {'hf_tension':<12} {'hf_conj':<10}")
print("-" * 90)

harmony_by_valence = {'positive': [], 'negative': [], 'neutral': []}
for e in monroe_events:
    valence_label = 'positive' if e['valence_num'] > 0 else ('negative' if e['valence_num'] < 0 else 'neutral')
    harmony_by_valence[valence_label].append(e['hf_harmony'])

    print(f"{e['event_date']:<12} {e['event_type']:<20} {valence_label:<10} "
          f"{e['hf_harmony']:>11.2f} {e['hf_tension']:>11.2f} {e['hf_conjunction']:>9.2f}")

print("\n--- Summary Statistics for Marilyn Monroe ---")
for valence_label in ['positive', 'negative', 'neutral']:
    values = harmony_by_valence[valence_label]
    if values:
        print(f"{valence_label.upper()}: mean hf_harmony = {np.mean(values):.2f} (n={len(values)})")

# Test: does Monroe have structurally high harmony?
monroe_harm = [e['hf_harmony'] for e in monroe_events]
all_harm = [e['hf_harmony'] for e in events_data]
t_stat_monroe, p_val_monroe = stats.ttest_ind(monroe_harm, all_harm)
print(f"\nT-test Monroe vs all subjects: t={t_stat_monroe:.3f}, p={p_val_monroe:.4f}")
if p_val_monroe < 0.05:
    print("  [YES] Monroe has SIGNIFICANTLY different (likely higher) hf_harmony overall")
else:
    print("  [NO] Monroe's harmony is NOT significantly different from population mean")

# Are her positive events higher than her negative?
monroe_pos = [e['hf_harmony'] for e in monroe_events if e['valence_num'] > 0]
monroe_neg = [e['hf_harmony'] for e in monroe_events if e['valence_num'] < 0]
if monroe_neg:
    t_stat_m_pn, p_val_m_pn = stats.ttest_ind(monroe_pos, monroe_neg)
    print(f"\nWithin Monroe: positive vs negative hf_harmony")
    print(f"  Positive mean: {np.mean(monroe_pos):.2f} (n={len(monroe_pos)})")
    print(f"  Negative mean: {np.mean(monroe_neg):.2f} (n={len(monroe_neg)})")
    print(f"  t-test: t={t_stat_m_pn:.3f}, p={p_val_m_pn:.4f}")
    if p_val_m_pn < 0.05:
        print("  [YES] Monroe's positive events have higher harmony than her negative events")
    else:
        print("  [NO] NO difference — Monroe's harmony is high regardless of valence")

print("\n" + "=" * 80)
