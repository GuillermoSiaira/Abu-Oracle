#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

# Ensure lilly_engine is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lilly_engine'))
sys.path.insert(0, os.path.dirname(__file__))

from lilly_engine.narrative_engine import generate_narrative

maestro = {
    "metadata": {"mode": "persian_cosmology"},
    "year_overview": {"year_element": "water", "year_tone_keywords": ["emotional depth", "family focus"]},
    "lord_of_year": {"final_lord": "Jupiter", "lord_keywords": ["planet_nature: hot, moist"]},
}

try:
    result = generate_narrative(maestro, 'es')
    print(f"SUCCESS: {len(result)} chars")
    print("="*80)
    print(result)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
