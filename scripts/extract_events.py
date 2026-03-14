#!/usr/bin/env python3
"""Extract event data from correlation_results.json to CSV."""

import json
from pathlib import Path

# Paths
results_file = Path("data/biographical_events/correlation_results.json")
output_file = Path("data/biographical_events/events_detailed.csv")

# Load JSON
with open(results_file, encoding='utf-8') as f:
    data = json.load(f)

events = data.get('events', [])
print(f"Total events: {len(events)}")

# Write CSV header
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("subject_id,subject_name,event_date,event_type,valence,valence_num,"
            "hf_harmony,hf_tension,hf_conjunction,hf_weighted,hf_total_v3,"
            "delta_hf_weighted,delta_hf_total_v3,description\n")

    # Write events
    for evt in events:
        desc = evt.get('description', '').replace('"', '""').replace('\n', ' ')
        row = (
            f"{evt.get('subject_id')},"
            f"{evt.get('subject_name')},"
            f"{evt.get('event_date')},"
            f"{evt.get('event_type')},"
            f"{evt.get('valence')},"
            f"{evt.get('valence_num')},"
            f"{evt.get('transit_hf_harmony')},"
            f"{evt.get('transit_hf_tension')},"
            f"{evt.get('transit_hf_conjunction')},"
            f"{evt.get('transit_hf_weighted')},"
            f"{evt.get('transit_hf_total_v3')},"
            f"{evt.get('delta_hf_weighted')},"
            f"{evt.get('delta_hf_total_v3')},"
            f'"{desc}"\n'
        )
        f.write(row)

print(f"CSV exported to: {output_file}")

# Analysis: hf_harmony > 8 + valence POSITIVE
filtered = [e for e in events
            if e.get('transit_hf_harmony', 0) > 8 and e.get('valence_num') == 1.0]

print(f"\nFilter: hf_harmony > 8 + valence POSITIVE = {len(filtered)} events")
print("\n--- TOP 10 EVENTS ---")
for i, e in enumerate(sorted(filtered, key=lambda x: x.get('transit_hf_harmony', 0), reverse=True)[:10], 1):
    print(f"\n{i}. {e['subject_name']} ({e['event_date']})")
    print(f"   Type: {e['event_type']}")
    print(f"   hf_harmony={e['transit_hf_harmony']:.2f}, hf_tension={e['transit_hf_tension']:.2f}, hf_conj={e['transit_hf_conjunction']:.2f}")
    print(f"   HF_weighted={e['transit_hf_weighted']:.2f} | Delta={e['delta_hf_weighted']:.2f}")
    print(f"   {e['description'][:100]}...")
