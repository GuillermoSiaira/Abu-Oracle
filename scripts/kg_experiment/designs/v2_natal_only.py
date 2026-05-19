"""
Diseño v2 — "Natal Only"

Lectura de talentos, temperamento y potencias innatas desde el
cielo natal puro. Sin tránsitos, profección ni firdaria. Marco
doctrinal válido por igual para sujetos vivos e históricos.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Path setup — el módulo puede ser importado desde runner.py o standalone
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ABU = _REPO_ROOT / "abu_engine"
if str(_ABU) not in sys.path:
    sys.path.insert(0, str(_ABU))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.chart_graph import build_chart_graph, get_key_planets, serialize_subgraph  # noqa: E402


DESIGN_ID = "v2_natal_only"
DESIGN_DESCRIPTION = (
    "Lectura de talentos, temperamento y potencias innatas desde el "
    "cielo natal puro. Sin tránsitos, profección ni firdaria. Marco "
    "doctrinal válido por igual para sujetos vivos e históricos."
)

EVAL_PROMPT = """Un astrólogo clásico recibe el siguiente contexto de una carta natal.
Identifica los talentos, potencias innatas y temperamento del nativo usando:
- Dignidades esenciales de los planetas
- Señoríos de Ascendente, Medio Cielo, Parte de Fortuna y Parte del Espíritu
- Recepciones mutuas y aspectos relevantes
- Casas ocupadas

NO menciones tránsitos, profecciones, firdaria ni eventos futuros — solo lo natal.
Máximo 250 palabras."""


# Sujetos importados desde config.py (fuente única de verdad).
from scripts.kg_experiment.config import SUBJECTS  # noqa: E402, F401


_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _lon_to_sign_deg(lon: float) -> tuple[str, float]:
    lon = float(lon) % 360.0
    return _SIGNS[int(lon // 30)], lon % 30


def _dignity_name(planet: dict) -> str:
    d = planet.get("dignity")
    if isinstance(d, dict):
        name = d.get("dignity")
        if isinstance(name, str) and name:
            return name
        # Fallback: revisar flags booleanos
        for flag in ("domicile", "exaltation", "triplicity", "term", "face", "detriment", "fall"):
            if d.get(flag) is True:
                return flag
        return "peregrine"
    if isinstance(d, str) and d:
        return d
    return "peregrine"


def build_context_a(natal: dict, bio: dict) -> str:
    """Condición A — Cielo natal serializado como texto plano (sin temporal)."""
    del bio

    chart = natal.get("chart", {})
    derived = natal.get("derived", {})

    planets = chart.get("planets", []) or []
    houses_obj = chart.get("houses", {}) or {}
    asc = float(houses_obj.get("asc", 0.0))
    mc = float(houses_obj.get("mc", 0.0))
    aspects = chart.get("aspects", []) or []
    lots = derived.get("lots", {}) or {}
    sect = derived.get("sect", "?")

    lines = ["=== CIELO NATAL ===", f"Sect: {sect}", "", "PLANETAS:"]

    for p in planets:
        name = p.get("name", "?")
        # Preferir sign + degree_in_sign que /analyze ya provee; computar desde
        # longitud solo como fallback.
        sign = p.get("sign")
        deg = p.get("degree_in_sign", p.get("degree"))
        if not sign or deg is None:
            lon = p.get("longitude", p.get("lon", 0.0))
            sign_calc, deg_calc = _lon_to_sign_deg(lon)
            sign = sign or sign_calc
            if deg is None:
                deg = deg_calc
        house = p.get("house", "?")
        dignity_name = _dignity_name(p)
        lines.append(f"  {name}: {sign} {float(deg):.1f}° Casa {house} ({dignity_name})")

    lines.append("")
    lines.append("ÁNGULOS:")
    asc_sign, asc_deg = _lon_to_sign_deg(asc)
    mc_sign, mc_deg = _lon_to_sign_deg(mc)
    lines.append(f"  ASC: {asc_sign} {asc_deg:.1f}°")
    lines.append(f"  MC:  {mc_sign} {mc_deg:.1f}°")

    lines.append("")
    lines.append("PARTES ÁRABES:")
    # lots puede venir como list de dicts (formato actual /analyze) o dict
    lots_normalized: list[dict] = []
    if isinstance(lots, list):
        lots_normalized = [l for l in lots if isinstance(l, dict)]
    elif isinstance(lots, dict):
        for key, val in lots.items():
            if isinstance(val, dict):
                lots_normalized.append({"name": key, **val})

    # Mostrar Fortuna y Espíritu (los doctrinales primarios)
    for target_name, label in (("Fortuna", "Fortuna"), ("Spirit", "Espíritu")):
        lot = next(
            (l for l in lots_normalized
             if str(l.get("name", "")).lower() == target_name.lower()),
            None,
        )
        if lot:
            sign = lot.get("sign", "?")
            degree = lot.get("degree", 0.0) or 0.0
            house = lot.get("house", "?")
            lord = lot.get("lord", "?")
            lines.append(f"  {label}: {sign} {float(degree):.1f}° Casa {house} (lord: {lord})")

    # Aspectos: /analyze actualmente no expone chart.aspects (queda como []),
    # así que solo se imprimen si hay datos. Mantiene la sección comparable
    # con la condición B, que tampoco recibe aspects en este setup.
    if aspects:
        lines.append("")
        lines.append("ASPECTOS NATALES:")
        for aspect in aspects:
            p_a = aspect.get("planet_a", aspect.get("a", "?"))
            p_b = aspect.get("planet_b", aspect.get("b", "?"))
            a_type = aspect.get("type", "?")
            orb = aspect.get("orb", 0.0) or 0.0
            lines.append(f"  {p_a} {a_type} {p_b} (orb {float(orb):.1f}°)")

    lines.append("")
    lines.append("===================")

    return "\n".join(lines)


def build_context_b(natal: dict, bio: dict) -> str:
    """Condición B — KG: señoríos y dignidades natales (sin activadores temporales)."""
    del bio
    graph = build_chart_graph(natal)
    # derived={} excluye firdaria/profección del key set; quedan solo
    # señor_ASC, señor_MC, señor_fortuna, señor_spirit
    key_planets = get_key_planets(graph, {})
    text = serialize_subgraph(graph, key_planets)

    # Post-filtrar líneas con edges temporales (por si serialize las incluye)
    filtered_lines = [
        line for line in text.split("\n")
        if "firdaria_mayor" not in line
        and "firdaria_menor" not in line
        and "señor_del_año" not in line
    ]
    filtered = "\n".join(filtered_lines).strip()

    if not filtered:
        filtered = "[sin datos de senorios]"

    return "=== CIELO NATAL (KG) ===\n" + filtered + "\n========================="
