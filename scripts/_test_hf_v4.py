"""Quick comparison: old HF_total vs new HF_weighted."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "abu_engine"))

from harmony.field import aggregate_field

mock = {
    "Sun": 10, "Moon": 40, "Mercury": 70, "Venus": 120, "Mars": 190,
    "Jupiter": 220, "Saturn": 250, "Uranus": 300, "Neptune": 310, "Pluto": 330,
    "ASC": 15, "MC": 285,
}
agg = aggregate_field(mock)
print(f"HF_harmony:     {agg['HF_harmony']:.4f}")
print(f"HF_tension:     {agg['HF_tension']:.4f}")
print(f"HF_conjunction: {agg['HF_conjunction']:.4f}")
print(f"HF_total(old):  {agg['HF_total']:.4f}")
print(f"HF_weighted(v4):{agg['HF_weighted']:.4f}")
print(f"Delta:          {agg['HF_weighted'] - agg['HF_total']:.4f}")
print(f"Weights:        {agg['group_weights']}")
