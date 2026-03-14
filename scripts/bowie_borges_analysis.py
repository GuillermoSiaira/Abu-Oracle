#!/usr/bin/env python3
"""Deep dive into David Bowie and Jorge Luis Borges."""

import json
from pathlib import Path
import numpy as np
from scipy import stats

# Load data
results_file = Path("data/biographical_events/correlation_results.json")
with open(results_file, encoding='utf-8') as f:
    data = json.load(f)

events = data.get('events', [])

events_data = []
for e in events:
    events_data.append({
        'subject_id': e.get('subject_id'),
        'subject_name': e.get('subject_name'),
        'event_date': e.get('event_date'),
        'event_type': e.get('event_type'),
        'valence_num': float(e.get('valence_num', 0)),
        'valence': e.get('valence'),
        'hf_harmony': float(e.get('transit_hf_harmony', 0)),
        'hf_tension': float(e.get('transit_hf_tension', 0)),
        'hf_conjunction': float(e.get('transit_hf_conjunction', 0)),
        'hf_weighted': float(e.get('transit_hf_weighted', 0)),
        'description': e.get('description', ''),
    })

# Reference stats
all_harm = [e['hf_harmony'] for e in events_data]
all_mean_harmony = np.mean(all_harm)
all_std_harmony = np.std(all_harm)

print(f"Population stats:")
print(f"  Mean hf_harmony: {all_mean_harmony:.2f}")
print(f"  Std hf_harmony: {all_std_harmony:.2f}\n")

# ============================================================================
# DAVID BOWIE
# ============================================================================
print("=" * 100)
print("DAVID BOWIE")
print("=" * 100)

bowie_events = [e for e in events_data if e['subject_name'] == 'David Bowie']
bowie_events.sort(key=lambda x: x['event_date'])

print(f"\nTotal events: {len(bowie_events)}\n")
print(f"{'Date':<12} {'Type':<25} {'Valence':<10} {'hf_harmony':<12} {'hf_tension':<12} {'hf_conj':<10}")
print("-" * 100)

harmony_by_valence = {'positive': [], 'negative': [], 'neutral': []}
for e in bowie_events:
    valence_label = 'positive' if e['valence_num'] > 0 else ('negative' if e['valence_num'] < 0 else 'neutral')
    harmony_by_valence[valence_label].append(e['hf_harmony'])

    print(f"{e['event_date']:<12} {e['event_type']:<25} {valence_label:<10} "
          f"{e['hf_harmony']:>11.2f} {e['hf_tension']:>11.2f} {e['hf_conjunction']:>9.2f}")

print("\n--- Summary Statistics for David Bowie ---")
bowie_harm = [e['hf_harmony'] for e in bowie_events]
bowie_mean = np.mean(bowie_harm)
print(f"Overall mean hf_harmony: {bowie_mean:.2f} (population mean: {all_mean_harmony:.2f})")
print(f"  Z-score: {(bowie_mean - all_mean_harmony) / all_std_harmony:.2f}")

for valence_label in ['positive', 'negative', 'neutral']:
    values = harmony_by_valence[valence_label]
    if values:
        print(f"{valence_label.upper()}: mean hf_harmony = {np.mean(values):.2f} (n={len(values)}, std={np.std(values):.2f})")

# Statistical test: Is Bowie structurally high/low harmony?
t_stat_bowie, p_val_bowie = stats.ttest_ind(bowie_harm, all_harm)
print(f"\nT-test Bowie vs all subjects: t={t_stat_bowie:.3f}, p={p_val_bowie:.4f}")
if p_val_bowie < 0.05:
    if bowie_mean > all_mean_harmony:
        print("  [YES] Bowie has SIGNIFICANTLY HIGHER hf_harmony overall")
    else:
        print("  [YES] Bowie has SIGNIFICANTLY LOWER hf_harmony overall")
else:
    print("  [NO] Bowie's harmony is NOT significantly different from population")

# Are positive events different from negative?
bowie_pos = [e['hf_harmony'] for e in bowie_events if e['valence_num'] > 0]
bowie_neg = [e['hf_harmony'] for e in bowie_events if e['valence_num'] < 0]
if bowie_neg and bowie_pos:
    t_stat_b_pn, p_val_b_pn = stats.ttest_ind(bowie_pos, bowie_neg)
    print(f"\nWithin Bowie: positive vs negative hf_harmony")
    print(f"  Positive mean: {np.mean(bowie_pos):.2f} (n={len(bowie_pos)})")
    print(f"  Negative mean: {np.mean(bowie_neg):.2f} (n={len(bowie_neg)})")
    print(f"  t-test: t={t_stat_b_pn:.3f}, p={p_val_b_pn:.4f}")
    if p_val_b_pn < 0.05:
        print("  [YES] Bowie's positive events have DIFFERENT harmony than his negative events")
    else:
        print("  [NO] NO significant difference — Bowie's harmony doesn't discriminate valence")

# ============================================================================
# JORGE LUIS BORGES
# ============================================================================
print("\n\n" + "=" * 100)
print("JORGE LUIS BORGES")
print("=" * 100)

borges_events = [e for e in events_data if e['subject_name'] == 'Jorge Luis Borges']
borges_events.sort(key=lambda x: x['event_date'])

print(f"\nTotal events: {len(borges_events)}\n")
print(f"{'Date':<12} {'Type':<25} {'Valence':<10} {'hf_harmony':<12} {'hf_tension':<12} {'hf_conj':<10}")
print("-" * 100)

harmony_by_valence_b = {'positive': [], 'negative': [], 'neutral': []}
for e in borges_events:
    valence_label = 'positive' if e['valence_num'] > 0 else ('negative' if e['valence_num'] < 0 else 'neutral')
    harmony_by_valence_b[valence_label].append(e['hf_harmony'])

    print(f"{e['event_date']:<12} {e['event_type']:<25} {valence_label:<10} "
          f"{e['hf_harmony']:>11.2f} {e['hf_tension']:>11.2f} {e['hf_conjunction']:>9.2f}")

print("\n--- Summary Statistics for Jorge Luis Borges ---")
borges_harm = [e['hf_harmony'] for e in borges_events]
borges_mean = np.mean(borges_harm)
print(f"Overall mean hf_harmony: {borges_mean:.2f} (population mean: {all_mean_harmony:.2f})")
print(f"  Z-score: {(borges_mean - all_mean_harmony) / all_std_harmony:.2f}")

for valence_label in ['positive', 'negative', 'neutral']:
    values = harmony_by_valence_b[valence_label]
    if values:
        print(f"{valence_label.upper()}: mean hf_harmony = {np.mean(values):.2f} (n={len(values)}, std={np.std(values):.2f})")

# Statistical test
t_stat_borges, p_val_borges = stats.ttest_ind(borges_harm, all_harm)
print(f"\nT-test Borges vs all subjects: t={t_stat_borges:.3f}, p={p_val_borges:.4f}")
if p_val_borges < 0.05:
    if borges_mean > all_mean_harmony:
        print("  [YES] Borges has SIGNIFICANTLY HIGHER hf_harmony overall")
    else:
        print("  [YES] Borges has SIGNIFICANTLY LOWER hf_harmony overall")
else:
    print("  [NO] Borges's harmony is NOT significantly different from population")

# Are positive events different from negative?
borges_pos = [e['hf_harmony'] for e in borges_events if e['valence_num'] > 0]
borges_neg = [e['hf_harmony'] for e in borges_events if e['valence_num'] < 0]
if borges_neg and borges_pos:
    t_stat_bo_pn, p_val_bo_pn = stats.ttest_ind(borges_pos, borges_neg)
    print(f"\nWithin Borges: positive vs negative hf_harmony")
    print(f"  Positive mean: {np.mean(borges_pos):.2f} (n={len(borges_pos)})")
    print(f"  Negative mean: {np.mean(borges_neg):.2f} (n={len(borges_neg)})")
    print(f"  t-test: t={t_stat_bo_pn:.3f}, p={p_val_bo_pn:.4f}")
    if p_val_bo_pn < 0.05:
        print("  [YES] Borges's positive events have DIFFERENT harmony than his negative events")
    else:
        print("  [NO] NO significant difference — Borges's harmony doesn't discriminate valence")

# ============================================================================
# COMPARATIVE SUMMARY
# ============================================================================
print("\n\n" + "=" * 100)
print("COMPARATIVE SUMMARY")
print("=" * 100)

summary = {
    'Marilyn Monroe': {
        'n': 26,
        'mean_harm': 9.77,
        'z_score': (9.77 - all_mean_harmony) / all_std_harmony,
        'pos_mean': 9.77,
        'neg_mean': 6.61,
        'discriminates': True,
    },
    'David Bowie': {
        'n': len(bowie_events),
        'mean_harm': bowie_mean,
        'z_score': (bowie_mean - all_mean_harmony) / all_std_harmony,
        'pos_mean': np.mean(bowie_pos) if bowie_pos else None,
        'neg_mean': np.mean(bowie_neg) if bowie_neg else None,
        'discriminates': p_val_b_pn < 0.05 if (bowie_neg and bowie_pos) else False,
    },
    'Jorge Luis Borges': {
        'n': len(borges_events),
        'mean_harm': borges_mean,
        'z_score': (borges_mean - all_mean_harmony) / all_std_harmony,
        'pos_mean': np.mean(borges_pos) if borges_pos else None,
        'neg_mean': np.mean(borges_neg) if borges_neg else None,
        'discriminates': p_val_bo_pn < 0.05 if (borges_neg and borges_pos) else False,
    },
}

print(f"\n{'Subject':<20} {'n':<5} {'Mean HF':<10} {'Z-score':<10} {'Pos mean':<10} {'Neg mean':<10} {'Discriminates?':<15}")
print("-" * 100)
for subject, stats_dict in summary.items():
    print(f"{subject:<20} {stats_dict['n']:<5} "
          f"{stats_dict['mean_harm']:<10.2f} {stats_dict['z_score']:<10.2f} "
          f"{stats_dict['pos_mean']:<10.2f}" if stats_dict['pos_mean'] else f"{'':<10} "
          f"{stats_dict['neg_mean']:<10.2f}" if stats_dict['neg_mean'] else f"{'':<10} "
          f"{'YES' if stats_dict['discriminates'] else 'NO':<15}")

print("\n" + "=" * 100)
print("INTERPRETATION:")
print("=" * 100)
print("""
If a subject appears in top "hf_harmony > 8 + valence positive" events,
there are two possibilities:

1. STRUCTURAL: The subject has high harmony in their natal chart overall.
   - Their positive AND negative events both have high harmony.
   - The pattern doesn't show that harmony predicts valence.

2. DISCRIMINATIVE: The subject has high harmony specifically during positive events.
   - Their positive events have high harmony, negative events have lower harmony.
   - This would suggest harmony is actually capturing something about valence.

This analysis shows which pattern fits each subject.
""")
