"""
Diseño v3 — "Natal Full KG"

Pregunta científica:
    ¿El formato KG (tripletas estructuradas + relaciones tipadas) supera
    al JSON natal plano cuando AMBOS contextos tienen IGUAL información?

v2 medía "10 planetas plano vs 4 planetas estructurado" — confound de cantidad.
v3 corrige: ambos contextos incluyen los 10 planetas, 4 ángulos, 4 partes,
12 señoríos de casa, aspectos computados localmente y recepciones mutuas.
El único factor que varía es el FORMATO.

Implementa la Capa 3 del schema (`docs/theory/KG_ONTOLOGY_SCHEMA.md`) en
versión natal (sin tránsitos, profección ni firdaria).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Path setup
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ABU = _REPO_ROOT / "abu_engine"
if str(_ABU) not in sys.path:
    sys.path.insert(0, str(_ABU))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ── Constantes doctrinales (Capa 2 del schema) ────────────────────

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Aliases ES → EN para normalización
SIGN_ALIASES = {
    "Aries": "Aries", "Tauro": "Taurus", "Géminis": "Gemini", "Geminis": "Gemini",
    "Cáncer": "Cancer", "Cancer": "Cancer",
    "Leo": "Leo", "Virgo": "Virgo", "Libra": "Libra",
    "Escorpio": "Scorpio", "Scorpio": "Scorpio",
    "Sagitario": "Sagittarius", "Sagittarius": "Sagittarius",
    "Capricornio": "Capricorn", "Capricorn": "Capricorn",
    "Acuario": "Aquarius", "Aquarius": "Aquarius",
    "Piscis": "Pisces", "Pisces": "Pisces",
    # Inglés directo:
    "Taurus": "Taurus", "Gemini": "Gemini",
}

# Domicilios tradicionales (planeta → signos que rige)
DOMICILIOS = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mercury": ["Gemini", "Virgo"],
    "Venus": ["Taurus", "Libra"],
    "Mars": ["Aries", "Scorpio"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn": ["Capricorn", "Aquarius"],
}

# Reverse map: signo → planeta regente
SIGN_LORDS = {sign: planet for planet, signs in DOMICILIOS.items() for sign in signs}

# Planetas transpersonales (sin dignidades esenciales según doctrina clásica)
TRANSPERSONAL = {"Uranus", "Neptune", "Pluto", "North Node", "South Node"}

# Aspectos doctrinales (ángulo, orbe máximo)
ASPECT_DEFS = [
    ("conjuncion", 0, 8),
    ("sextil", 60, 6),
    ("cuadratura", 90, 6),
    ("trigono", 120, 8),
    ("oposicion", 180, 8),
]


# ── Design metadata ─────────────────────────────────────────────────

DESIGN_ID = "v3_natal_full_kg"
DESIGN_DESCRIPTION = (
    "KG natal completo (10 planetas + 4 ángulos + 4 partes + 12 señoríos "
    "de casa + aspectos computados + recepciones mutuas) vs JSON plano con "
    "MISMA información. Test puro del formato, sin confound de cantidad."
)

EVAL_PROMPT = """Un astrólogo clásico recibe el siguiente contexto de una carta natal.
Identifica los talentos, potencias innatas y temperamento del nativo usando:
- Dignidades esenciales de los planetas
- Señoríos de Ascendente, Medio Cielo, Parte de Fortuna y Parte del Espíritu
- Recepciones mutuas y aspectos relevantes
- Casas ocupadas

NO menciones tránsitos, profecciones, firdaria ni eventos futuros — solo lo natal.
Máximo 250 palabras."""

# Sujetos del experimento — importados desde config.py (fuente única de verdad).
# Con n=12 desde 2026-05-19: 3 históricos + 7 celebridades demo + SYNTH_001 + GS_004.
from scripts.kg_experiment.config import SUBJECTS  # noqa: E402, F401


# ── Helpers de normalización ───────────────────────────────────────

def _norm_sign(s: str | None) -> str:
    if not s:
        return "?"
    return SIGN_ALIASES.get(str(s), str(s))


def _lon_to_sign_deg(lon: float) -> tuple[str, float]:
    lon = float(lon) % 360.0
    return SIGNS[int(lon // 30)], lon % 30


def _opposite_sign(sign: str) -> str:
    """Devuelve el signo opuesto (a 180°)."""
    sign = _norm_sign(sign)
    if sign not in SIGNS:
        return "?"
    return SIGNS[(SIGNS.index(sign) + 6) % 12]


def _opposite_lon(lon: float) -> float:
    return (float(lon) + 180.0) % 360.0


def _dignity_name(planet: dict) -> str:
    """Extrae dignity name desde el dict del planeta /analyze."""
    d = planet.get("dignity")
    if isinstance(d, str) and d:
        return d
    if isinstance(d, dict):
        name = d.get("dignity")
        if isinstance(name, str) and name:
            return name
        for flag in ("domicile", "exaltation", "triplicity", "term", "face", "detriment", "fall"):
            if d.get(flag) is True:
                return flag
        return "peregrine"
    return "peregrine"


def _planet_name_en(name: str) -> str:
    """Normaliza nombres de planetas ES → EN."""
    es_to_en = {
        "Sol": "Sun", "Luna": "Moon", "Mercurio": "Mercury", "Venus": "Venus",
        "Marte": "Mars", "Júpiter": "Jupiter", "Jupiter": "Jupiter",
        "Saturno": "Saturn", "Urano": "Uranus", "Neptuno": "Neptune",
        "Plutón": "Pluto", "Pluton": "Pluto",
    }
    return es_to_en.get(name, name)


# ── Extractores desde /analyze ─────────────────────────────────────

def _planets_list(natal: dict) -> list[dict]:
    """Devuelve lista normalizada de planetas con campos consistentes."""
    chart = natal.get("chart", {})
    raw = chart.get("planets", []) or []
    if isinstance(raw, dict):
        raw = [{"name": k, **v} for k, v in raw.items() if isinstance(v, dict)]

    out: list[dict] = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        name = _planet_name_en(p.get("name", "?"))
        sign = _norm_sign(p.get("sign"))
        deg = p.get("degree_in_sign", p.get("degree"))
        lon = p.get("longitude", p.get("lon"))
        if deg is None and lon is not None:
            _, deg = _lon_to_sign_deg(lon)
        elif deg is None:
            deg = 0.0
        house = p.get("house", 0)
        dignity = _dignity_name(p)
        out.append({
            "name": name,
            "sign": sign,
            "degree": float(deg),
            "longitude": float(lon) if lon is not None else 0.0,
            "house": house,
            "dignity": dignity,
        })
    return out


def _houses_list(natal: dict) -> list[dict]:
    """Devuelve lista de 12 casas con número, signo en cúspide y grado."""
    chart = natal.get("chart", {})
    houses_obj = chart.get("houses", {}) or {}
    raw = houses_obj.get("houses", []) if isinstance(houses_obj, dict) else houses_obj
    out = []
    for h in raw or []:
        if not isinstance(h, dict):
            continue
        num = h.get("house")
        if num is None:
            continue
        cusp = h.get("start", h.get("degree", 0.0))
        sign_raw = h.get("sign")
        if sign_raw:
            sign = _norm_sign(sign_raw)
        else:
            sign, _ = _lon_to_sign_deg(cusp)
        out.append({"house": int(num), "sign": sign, "cusp_lon": float(cusp)})
    return out


def _angles(natal: dict) -> dict:
    """ASC, MC, DSC, IC con sign + degree."""
    chart = natal.get("chart", {})
    houses_obj = chart.get("houses", {}) or {}
    asc = float(houses_obj.get("asc", 0.0))
    mc = float(houses_obj.get("mc", 0.0))
    dsc = _opposite_lon(asc)
    ic = _opposite_lon(mc)
    asc_s, asc_d = _lon_to_sign_deg(asc)
    mc_s, mc_d = _lon_to_sign_deg(mc)
    dsc_s, dsc_d = _lon_to_sign_deg(dsc)
    ic_s, ic_d = _lon_to_sign_deg(ic)
    return {
        "ASC": (asc_s, asc_d, asc),
        "MC":  (mc_s, mc_d, mc),
        "DSC": (dsc_s, dsc_d, dsc),
        "IC":  (ic_s, ic_d, ic),
    }


def _lots_list(natal: dict) -> list[dict]:
    """4 partes árabes: Fortuna, Spirit, Eros, Necessity."""
    derived = natal.get("derived", {})
    raw = derived.get("lots", []) or []
    out: list[dict] = []
    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, dict):
        candidates = [{"name": k, **v} for k, v in raw.items() if isinstance(v, dict)]
    else:
        candidates = []
    for lot in candidates:
        if not isinstance(lot, dict):
            continue
        out.append({
            "name": lot.get("name", "?"),
            "sign": _norm_sign(lot.get("sign")),
            "degree": float(lot.get("degree", 0.0) or 0.0),
            "house": lot.get("house", 0),
            "lord": _planet_name_en(lot.get("lord", "?")),
            "longitude": float(lot.get("longitude", 0.0) or 0.0),
        })
    return out


# ── Cómputos derivados (Capa 3) ────────────────────────────────────

def _compute_aspects(planets: list[dict]) -> list[dict]:
    """
    Aspectos mayores entre pares de planetas con orbes doctrinales.
    Devuelve list de {a, type, b, orb, angle}.
    """
    out: list[dict] = []
    n = len(planets)
    for i in range(n):
        for j in range(i + 1, n):
            a = planets[i]
            b = planets[j]
            diff = abs(a["longitude"] - b["longitude"]) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff
            for asp_type, exact, max_orb in ASPECT_DEFS:
                orb = abs(diff - exact)
                if orb <= max_orb:
                    out.append({
                        "a": a["name"],
                        "b": b["name"],
                        "type": asp_type,
                        "orb": round(orb, 1),
                        "angle": exact,
                    })
                    break
    # Ordenar por orbe ascendente (más exactos primero)
    out.sort(key=lambda x: x["orb"])
    return out


def _detect_mutual_receptions(planets: list[dict]) -> list[tuple[str, str, str]]:
    """
    Recepción mutua por domicilio:
        Planeta A en signo regido por B, y B en signo regido por A.
    Devuelve list de (planet_a, planet_b, "domicilio").
    Solo los 7 tradicionales (transpersonales no participan).
    """
    out: list[tuple[str, str, str]] = []
    classical = [p for p in planets if p["name"] not in TRANSPERSONAL and p["name"] in DOMICILIOS]
    seen: set[tuple[str, str]] = set()
    for a in classical:
        for b in classical:
            if a["name"] == b["name"]:
                continue
            # a está en signo regido por b, y b está en signo regido por a
            lord_of_a_sign = SIGN_LORDS.get(a["sign"])
            lord_of_b_sign = SIGN_LORDS.get(b["sign"])
            if lord_of_a_sign == b["name"] and lord_of_b_sign == a["name"]:
                pair = tuple(sorted([a["name"], b["name"]]))
                if pair not in seen:
                    seen.add(pair)
                    out.append((pair[0], pair[1], "domicilio"))
    return out


def _house_lord(house: dict) -> str:
    """Planeta regente del signo en la cúspide de esta casa."""
    return SIGN_LORDS.get(house["sign"], "?")


# ── Contextos A y B con MISMA información ─────────────────────────

def build_context_a(natal: dict, bio: dict) -> str:
    """Condición A — JSON natal plano. Mismos datos que B, formato narrativo."""
    del bio
    derived = natal.get("derived", {})
    sect = derived.get("sect", "?")

    planets = _planets_list(natal)
    houses = _houses_list(natal)
    angles = _angles(natal)
    lots = _lots_list(natal)
    aspects = _compute_aspects(planets)
    receptions = _detect_mutual_receptions(planets)

    lines = ["=== CIELO NATAL ===", f"Sect: {sect}", "", "PLANETAS:"]
    for p in planets:
        lines.append(f"  {p['name']}: {p['sign']} {p['degree']:.1f}° Casa {p['house']} ({p['dignity']})")

    lines.append("")
    lines.append("ÁNGULOS:")
    for label in ("ASC", "MC", "DSC", "IC"):
        s, d, _ = angles[label]
        lines.append(f"  {label}: {s} {d:.1f}°")

    lines.append("")
    lines.append("SEÑORÍOS DE CASAS (signo en cúspide -> lord):")
    for h in sorted(houses, key=lambda x: x["house"]):
        lord = _house_lord(h)
        lines.append(f"  Casa {h['house']} ({h['sign']}): {lord}")

    lines.append("")
    lines.append("PARTES ÁRABES:")
    for lot in lots:
        lines.append(f"  {lot['name']}: {lot['sign']} {lot['degree']:.1f}° Casa {lot['house']} (lord: {lot['lord']})")

    if aspects:
        lines.append("")
        lines.append("ASPECTOS NATALES:")
        for asp in aspects:
            lines.append(f"  {asp['a']} {asp['type']} {asp['b']} (orbe {asp['orb']:.1f}°)")

    if receptions:
        lines.append("")
        lines.append("RECEPCIONES MUTUAS:")
        for a, b, kind in receptions:
            lines.append(f"  {a} <-> {b} por {kind}")

    lines.append("")
    lines.append("===================")
    return "\n".join(lines)


def build_context_b(natal: dict, bio: dict) -> str:
    """Condición B — KG natal en formato tripletas (schema § Formato de contexto)."""
    del bio
    derived = natal.get("derived", {})
    sect = derived.get("sect", "?")

    planets = _planets_list(natal)
    houses = _houses_list(natal)
    angles = _angles(natal)
    lots = _lots_list(natal)
    aspects = _compute_aspects(planets)
    receptions = _detect_mutual_receptions(planets)

    lines = ["=== CARTA NATAL (KG) ===", "", f"# SECT", f"Carta {sect}", ""]

    # Posicionamiento + dignidad instanciada (Capa 3)
    lines.append("# POSICIONAMIENTO + DIGNIDAD")
    classical_planets = [p for p in planets if p["name"] not in TRANSPERSONAL]
    transpersonal_planets = [p for p in planets if p["name"] in TRANSPERSONAL]

    for p in classical_planets:
        lines.append(f"{p['name']} OCUPA_SIGNO {p['sign']} {p['degree']:.1f}°")
        lines.append(f"{p['name']} OCUPA_CASA {p['house']}")
        lines.append(f"{p['name']} DIGNIDAD {p['dignity']}")
        lines.append("")

    if transpersonal_planets:
        lines.append("# TRANSPERSONALES (sin dignidad esencial doctrinal)")
        for p in transpersonal_planets:
            lines.append(f"{p['name']} OCUPA_SIGNO {p['sign']} {p['degree']:.1f}°")
            lines.append(f"{p['name']} OCUPA_CASA {p['house']}")
        lines.append("")

    # Ángulos como nodos
    lines.append("# ÁNGULOS")
    for label in ("ASC", "MC", "DSC", "IC"):
        s, d, _ = angles[label]
        lines.append(f"{label} EN {s} {d:.1f}°")
    lines.append("")

    # Señoríos de casa (12 entradas)
    lines.append("# SEÑORÍOS DE CASA")
    for h in sorted(houses, key=lambda x: x["house"]):
        lord = _house_lord(h)
        lines.append(f"{lord} SEÑOR_DE_CASA {h['house']}  (cúspide en {h['sign']})")
    lines.append("")

    # Partes árabes
    lines.append("# PARTES ÁRABES")
    for lot in lots:
        lines.append(f"{lot['name']} EN {lot['sign']} {lot['degree']:.1f}° Casa {lot['house']}")
        lines.append(f"{lot['lord']} SEÑOR_DE {lot['name']}")
    lines.append("")

    # Aspectos
    if aspects:
        lines.append("# ASPECTOS")
        for asp in aspects:
            lines.append(f"{asp['a']} {asp['type'].upper()} {asp['b']}  orbe:{asp['orb']:.1f}°")
        lines.append("")

    # Recepciones mutuas
    if receptions:
        lines.append("# RECEPCIONES MUTUAS")
        for a, b, kind in receptions:
            lines.append(f"{a} RECEPCION_MUTUA {b}  via:{kind}")
        lines.append("")

    lines.append("=========================")
    return "\n".join(lines)
