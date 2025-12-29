# -*- coding: utf-8 -*-
import json, math
from pathlib import Path

# Cargar pesos desde ruta absoluta
BASE_DIR = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = BASE_DIR / "data" / "weights.json"

with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
    weights = json.load(f)

def compute_score(aspects):
    """
    Calcula el puntaje total de favorabilidad según pesos configurados.
    """
    total = 0
    for asp in aspects:
        w_asp = weights["aspects"].get(asp["type"], 0)
        w_planet = weights["planets"].get(asp["planet"], 1)
        orb_factor = math.exp(-abs(asp["orb_deg"]) / 3)
        total += w_asp * w_planet * orb_factor
    return round(total, 3)
