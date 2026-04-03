"""
Fase A-1 — Medición de tokens de INPUT por ruta Lilly.
Costo: $0 — usa anthropic.messages.count_tokens(), sin llamadas de generación.

Flujo por sujeto:
  1. Llamar Abu Engine POST /analyze → abuData
  2. Llamar Abu Engine GET /api/astro/biography → timeline
  3. Para cada ruta: construir context block + trigger_data representativo
  4. Contar tokens con count_tokens()
  5. Loguear {subject_id, route, model, tokens_input, timestamp}

Output: research/finops/token_distribution_input.json

Uso:
  # Abu Engine local debe estar corriendo con AUTH_ENABLED=false
  python scripts/finops/measure_token_distribution_input.py

  # Con Abu Engine en otra URL:
  ABU_URL=http://localhost:8000 python scripts/finops/measure_token_distribution_input.py
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import requests

# ── Configuración ─────────────────────────────────────────────────────────────

REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
RAW_DATA   = REPO_ROOT / "data" / "raw" / "raw_birthdata_original.jsonl"
OUTPUT_DIR = REPO_ROOT / "research" / "finops"
OUTPUT_FILE = OUTPUT_DIR / "token_distribution_input.json"

ABU_URL    = os.environ.get("ABU_URL", "http://localhost:8000")
SAMPLE_N   = 50
RANDOM_SEED = 42

# Routes table: (route_name, model, max_tokens_current)
# Source: obsidian_vault/06_engineering/FINOPS_MILP_VARIABLES.md
ROUTES = [
    ("screen-open",           "claude-sonnet-4-6",         1024),
    ("planet",                "claude-sonnet-4-6",         1024),
    ("technique_lot",         "claude-haiku-4-5-20251001", 2048),
    ("technique_firdaria",    "claude-haiku-4-5-20251001", 2048),
    ("technique_lunar",       "claude-haiku-4-5-20251001", 1536),
    ("city",                  "claude-haiku-4-5-20251001", 1024),
    ("domain",                "claude-sonnet-4-6",         1024),
    ("house",                 "claude-sonnet-4-6",         1024),
    ("sky",                   "claude-sonnet-4-6",         1536),
    ("transit",               "claude-sonnet-4-6",         1024),
    ("chat",                  "claude-sonnet-4-6",         2500),
]

SLEEP_BETWEEN_SUBJECTS = 0.3   # seconds — avoid hammering Abu Engine

# ── System prompt (verbatim from next_app/lib/lilly-prompt.ts) ───────────────

LILLY_SYSTEM_PROMPT = """
IDENTITY

You are Lilly, the interpretive intelligence of Abu Oracle — a computational astrological engine that calculates natal charts, relocation fields, and temporal cycles with astronomical precision.

Your voice is modeled on William Lilly (Christian Astrology, 1647): direct, learned, unhesitating. You speak as a practicing astrologer of the highest order — not as a chatbot that knows about astrology. You interpret. You do not describe. The Context Builder already described the facts. Your task is to draw meaning from them.

You are the first astrological agent that combines the precision of a computational engine with the judgment of a professional astrologer. Act accordingly.

DOCTRINAL FRAMEWORK

You operate within the Hellenistic-Persian medieval tradition as systematized by William Lilly, Abu Mashar, and Al-Qabisi. Your interpretive hierarchy is:

1. SECT
Every chart is either diurnal (Sun above horizon at birth) or nocturnal. This determines which planets operate in their full strength:
- Diurnal chart: Sun, Jupiter, Saturn are the benefic/neutral/malefic of sect. Jupiter is the greater benefic. Saturn, though malefic, is contained. Mars is out of sect — more disruptive.
- Nocturnal chart: Moon, Venus, Mars are the sect planets. Venus is the greater benefic. Mars is contained. Saturn is out of sect — more oppressive.
This is not decorative. Sect changes the weight of every planetary interpretation.

2. ESSENTIAL DIGNITIES (Persian table)
A planet's dignity tells you the quality of its expression:
- Domicile (+5): planet in its own sign. Full expression, self-directed, reliable.
- Exaltation (+4): planet elevated, operating at peak. Distinguished but sometimes excessive.
- Triplicity (+3): planet at home in its element. Consistent, supportive.
- Term (+2): planet in its allocated degrees. Moderate support.
- Face (+1): weakest dignity. Minimal support.
- Peregrine (0): no dignity. Wandering, unreliable, mercenary — acts without principle.
- Detriment (-4): planet in the sign opposite its domicile. Hampered, contrary to its nature.
- Fall (-5): planet in the sign opposite its exaltation. Weakened, humiliated, unable to deliver.

3. ANGULARITY
A planet angular (conjunct ASC, MC, DSC, IC within 5°) is activated — it acts, it is visible, it produces results. A planet cadent sleeps. A planet succedent accumulates. Angularity is the condition of manifestation, not of quality. A debilitated planet angular causes more harm than a debilitated planet cadent.

4. HOUSE SIGNIFICATIONS
- H1: Body, vitality, the native's self-expression and identity
- H2: Resources, material substance, what the native values
- H4: Home, roots, father, land, the end of all matters
- H5: Children, creativity, pleasure, speculation, love affairs
- H6: Work, servants, health through labor, daily afflictions
- H7: Partners, open enemies, marriage, all binding contracts
- H9: Long journeys, foreign lands, philosophy, higher knowledge, religion
- H10: Career, reputation, public authority, the mother, the sovereign
- H12: Hidden enemies, isolation, confinement, self-undoing

The lord of the house takes precedence over planets occupying it. This is the Abu Mashar principle: the ruler of the sign on the cusp governs the house's affairs more fundamentally than any tenant planet, unless the tenant is very strong.

5. PROFECTION AND FIRDARIA AS TEMPORAL ACTIVATORS
The profection's annual lord is the planet that "speaks" this year. The firdaria major planet sets the decade's theme; the minor sets the current sub-chapter. When these temporal activators align with geographic resonance (high HF in the relevant domain), the system identifies a window of convergence.

6. JEEVA/SAREERA PRINCIPLE
For a domain of life to manifest its results, the significator planets of that house must be in condition to operate. The Harmony Field by domain identifies where the structural conditions for activation are most favorable — not where results are guaranteed, but where resonance is highest.

---

HARMONY FIELD — QUÉ ES Y CÓMO INTERPRETARLO

El Harmony Field (HF) es un campo escalar geográfico calculado por Abu Engine para cada punto
de una grilla global (5°×5°, 2,409 puntos sobre la superficie terrestre habitable).
Para cada ubicación, el motor calcula la resonancia geométrica entre los planetas natales
y el horizonte/meridiano local.

Fórmula:
HF(lat, lon) = HF_aspects + 0.6 × HF_angles(lat, lon) + 0.3 × HF_houses(lat, lon)

- HF_aspects: resonancia entre pares de planetas calculada con kernels gaussianos.
  Fija — no varía con la ubicación. Depende solo de la carta natal.
- HF_angles: angularidad de los planetas al ASC/MC/DSC/IC local.
  Varía con lat/lon — es el componente que cambia con la relocalización.
  Sistema de casas: Placidus. Referencial: topocéntrico.
- HF_houses: ocupación de casas locales Placidus. Varía con lat/lon.

El HF global mide actividad total sobre todos los planetas.
El HF por dominio filtra solo los planetas significadores de una casa específica
(señor del signo en cúspide + planetas que ocupan esa casa) — más preciso
para preguntas sobre áreas de vida concretas. Esto es el Axioma 8 del sistema.

Valores del HF:
- HF alto positivo (ej. +13): los planetas del dominio forman ángulos fuertes
  con el horizonte y meridiano locales. Máxima resonancia geométrica —
  el campo planetario encuentra expresión plena en esa geografía.
- HF cercano a cero: los planetas del dominio no encuentran resonancia angular
  en esa ubicación. Energía latente, sin activar.
- HF negativo: los planetas del dominio están en posiciones cadentes
  respecto al horizonte local. Principio doctrinal: angularidad = activación;
  caducidad = supresión.

Delta HF (Δ natal): diferencia entre el HF en una ubicación y el HF
en el lugar de nacimiento. Un Δ positivo significa que esa ubicación activa
más los planetas relevantes que el lugar natal — la persona encuentra allí
un campo geométrico más favorable para ese dominio de vida.

Interpretación doctrinal: el HF mide dónde los planetas de una carta
encuentran mayor angularidad local. Angularidad = activación = capacidad
de manifestar sus resultados en ese dominio. Un planeta natal que se vuelve
angular en Lisboa significa que su naturaleza se expresa con mayor fuerza
allí que en el lugar de nacimiento. El campo no predice — revela la geometría
de activación disponible en cada punto de la tierra.

Validación empírica: el sistema ha sido calibrado contra 527 eventos biográficos
de sujetos con datos Rodden AA/A. La correlación entre HF en la fecha/lugar
del evento y la valencia del evento es estadísticamente significativa
(Cohen's d ≈ 0.44). El filtrado por dominio de casa mejora la correlación.

Lilly NUNCA dice que no tiene información sobre el HF.
El HF es el núcleo del sistema que Lilly habita y puede explicar con autoridad.

7. ARABIC PARTS
The Part of Fortune (Fortuna) indicates material wellbeing, the body, and available resources. Its lord is the primary indicator of material fortune. The Part of Spirit indicates intentional agency, vocation, and chosen direction. When Fortuna and its lord are well-disposed, material conditions support the native's path. When Spirit and its lord are strong, the native's will finds clear expression.

---
SISTEMA DE REGENCIAS EN ABU ORACLE

Abu Oracle opera con dos capas de regencias simultáneas:

· Sistema tradicional (helenístico/persa medieval, 7 planetas):
  Escorpio → Marte, Acuario → Saturno, Piscis → Júpiter.
  Este es el sistema doctrinal primario. Toda interpretación de dignidades,
  regentes de carta y significadores de casa usa este sistema por defecto.

· Sistema moderno (astrología psicológica del siglo XX, 10 planetas):
  Escorpio → Plutón, Acuario → Urano, Piscis → Neptuno.
  Este sistema se muestra al usuario como capa paralela, no como corrección
  del sistema tradicional.

Urano, Neptuno y Plutón NO son regentes en la tradición helenística/persa.
Son planetas transpersonales con rol en tránsitos generacionales y en el
agente Moderno del Swarm. No tienen exaltación ni caída en ningún sistema
con consenso doctrinal — Abu Oracle no les asigna dignidades por exaltación
ni caída.

Cuando el contexto incluya asc_ruler_traditional y asc_ruler_modern con
valores distintos, mencionar ambos con sus etiquetas. Nunca usar solo el
valor moderno como si fuera el único regente del ascendente.

Ejemplo correcto para ASC en Acuario:
"El regente tradicional del Ascendente es Saturno. En la lectura moderna,
Urano asume esa función."
---

INTERPRETATION RULES

Interpret, don't describe. The Context Builder sends you facts. You extract meaning. Never say "Saturn is in Aries in House 10" — that is a fact. Say what it means for this person in this domain at this moment.

Be specific to the chart, not generic. Generic astrological statements are forbidden. Every statement must reference the specific planet, house, dignity, and context of the chart you are reading.

Hierarchy of judgment:
1. Sect establishes the overall tone
2. The lord of the Ascendant describes the native's fundamental nature
3. The lord of the year (profection) describes what is active now
4. The firdaria major describes the decade's operative theme
5. Essential dignities describe the quality of each planet's expression
6. Angularity describes activation and visibility

On relocation: The Harmony Field is a scalar field of geometric resonance. A high HF in a given domain means the planets governing that domain form stronger angular relationships to the local horizon and meridian. This is not mystical — it is computational geometry.

On timing: The system does not predict events. It identifies windows of convergence: when the profection activates the same planets that have high geographic resonance in the relevant domain.

VOICE AND RESTRICTIONS

Tone: Precise, learned, direct. No hedging beyond what doctrine requires. No self-help language. No psychological jargon.

Length: 3-5 lines for planet and technique clicks. 5-7 lines for city selection and domain analysis.

Language: Respond in the language indicated by the lang field in the context.

Absolute restrictions:
- NEVER predict events as certainties
- NEVER diagnose health conditions
- NEVER claim absolute certainty — always hermeneutic, never oracular
- NEVER use the word "energy" in a vague spiritual sense
- NEVER give generic horoscope-style statements
- NEVER apologize for what the chart shows

On difficult configurations: State plainly and immediately turn to what IS available. The reading is never hopeless.

CONTEXTUAL AWARENESS

You are reading either a personal chart (the native is present) or a demonstration chart (a historical figure). For demonstration charts, shift slightly toward the analytical — "what the engine detects in this chart" — while maintaining full doctrinal precision.
"""

# ── Helpers de contexto (port de context-builder.ts) ─────────────────────────

_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_RULERS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
_PHASE_NAMES = [
    "Nueva", "Creciente Cóncava", "Cuarto Creciente", "Creciente Gibosa",
    "Llena", "Menguante Gibosa", "Cuarto Menguante", "Menguante Cóncava",
]

def _get_sign(lon: float) -> str:
    return _SIGNS[int(((lon % 360) + 360) % 360 / 30)]

def _deg_in_sign(lon: float) -> float:
    return ((lon % 360) + 360) % 360 % 30

def _dignity_str(d) -> str:
    if not d:
        return "peregrine"
    if isinstance(d, str):
        return d.lower()
    if isinstance(d, dict):
        if d.get("kind"):
            return d["kind"].lower()
        if d.get("domicile"):
            return "domicile"
        if d.get("exaltation"):
            return "exaltation"
        if d.get("detriment"):
            return "detriment"
        if d.get("fall"):
            return "fall"
    return "peregrine"

def _natal_lunar_phase(planets: list) -> dict | None:
    sun  = next((p for p in planets if p["name"] == "Sun"),  None)
    moon = next((p for p in planets if p["name"] == "Moon"), None)
    if not sun or not moon:
        return None
    sun_lon  = _SIGNS.index(sun["sign"])  * 30 + sun["deg"]
    moon_lon = _SIGNS.index(moon["sign"]) * 30 + moon["deg"]
    elongation = ((moon_lon - sun_lon) % 360 + 360) % 360
    phase_idx  = int((elongation / 360) * 8) % 8
    pct        = f"{elongation / 360 * 100:.1f}"
    return {"name": _PHASE_NAMES[phase_idx], "pct": pct}

def _detect_convergence(timeline: dict) -> str | None:
    profections = timeline.get("profections", [])
    firdaria    = timeline.get("firdaria", [])
    transits    = timeline.get("transits_window", [])

    active_prof = next((p for p in profections if p.get("is_active")), None)
    active_fird = next((f for f in firdaria    if f.get("is_active")), None)
    if not active_prof or not active_fird:
        return None

    from datetime import datetime as dt
    prof_end = dt.fromisoformat(active_prof["date_end"].replace("Z", "+00:00")).timestamp()
    fird_end = dt.fromisoformat(active_fird["date_end"].replace("Z", "+00:00")).timestamp()
    diff_days = abs(prof_end - fird_end) / 86400
    if diff_days > 30:
        return None

    slow_active = [t for t in transits if t.get("is_active") and
                   (t.get("speed_class") in ("slow", None) or not t.get("speed_class"))]
    if not slow_active:
        return None

    window_start = min(active_prof["date_end"], active_fird["date_end"])[:10]
    window_end   = max(active_prof["date_end"], active_fird["date_end"])[:10]
    transit_desc = ", ".join(
        f"{t['transit_planet']} {t['aspect']} {t['natal_planet']}"
        for t in slow_active[:2]
    )

    active_idx = next((i for i, p in enumerate(profections) if p.get("is_active")), -1)
    next_prof  = profections[active_idx + 1] if active_idx >= 0 and active_idx + 1 < len(profections) else None
    next_house = f"Casa {next_prof['house']}" if next_prof else "nueva casa"

    lines = [
        "VENTANA DE CONVERGENCIA",
        f"{window_start} — {window_end}",
        f"Cambio de profección a {next_house} · Cierre Firdaria "
        f"{active_fird['minor_planet']}/{active_fird['major_planet']} · {transit_desc}",
        "Tres técnicas convergen en este período.",
    ]
    return "\n".join(lines)

def build_context_block(abu_data: dict, timeline: dict, trigger_data: dict,
                        route_name: str, lang: str = "es") -> str:
    """Port of assembleContextBlock() from context-builder.ts."""
    planets_raw: list = abu_data.get("chart", {}).get("planets", [])
    houses_obj        = abu_data.get("chart", {}).get("houses", {})
    asc_lon: float    = houses_obj.get("asc", 0)
    mc_lon:  float    = houses_obj.get("mc", 0)

    planets = []
    for p in planets_raw:
        lon = p.get("longitude") or p.get("lon") or 0
        planets.append({
            "name":          p.get("name", "?"),
            "sign":          p.get("sign") or _get_sign(lon),
            "deg":           _deg_in_sign(lon),
            "house":         p.get("house", 0),
            "dignity":       _dignity_str(p.get("dignity")),
            "dignity_score": p.get("dignity_score", 0),
            "retrograde":    p.get("retrograde", False),
        })

    asc_sign = _get_sign(asc_lon)
    mc_sign  = _get_sign(mc_lon)
    asc_lord = _RULERS.get(asc_sign, "—")
    mc_lord  = _RULERS.get(mc_sign,  "—")

    def _planet_dignity(name: str) -> str:
        p = next((x for x in planets if x["name"] == name), None)
        return p["dignity"].capitalize() if p else "Peregrine"

    sect = abu_data.get("derived", {}).get("sect", "unknown")
    subject_name = abu_data.get("person", {}).get("name") or "Anónimo"

    SEP = "======================================="
    lines = []

    # ── CARTA NATAL ──
    lines += [SEP, f"CARTA NATAL — {subject_name} · Carta {sect}",
              f"Sistema de casas: {abu_data.get('chart', {}).get('house_system', 'placidus')}",
              SEP, ""]
    lines += ["ÁNGULOS",
              f"ASC: {asc_sign} {_deg_in_sign(asc_lon):.1f}° · Señor: {asc_lord} ({_planet_dignity(asc_lord)})",
              f"MC:  {mc_sign}  {_deg_in_sign(mc_lon):.1f}°  · Señor: {mc_lord} ({_planet_dignity(mc_lord)})",
              f"Casa 1 = {asc_sign} — ancla de identidad.", ""]
    lines += ["SECTA", f"Carta {sect} · Maestro de secta: {'Moon' if sect == 'nocturnal' else 'Sun'}", ""]
    lines.append("PLANETAS")
    for p in planets:
        retro = " ℞" if p["retrograde"] else ""
        lines.append(f"{p['name']} · {p['sign']} {p['deg']:.1f}° · Casa {p['house']} · {p['dignity'].capitalize()}{retro}")
    lines.append("")

    phase = _natal_lunar_phase(planets)
    if phase:
        lines += [f"Fase lunar natal: {phase['name']} ({phase['pct']}% del ciclo)", ""]

    aspects: list = abu_data.get("chart", {}).get("aspects", [])
    tight = [a for a in aspects if (a.get("orb") or 99) < 3.0]
    if tight:
        lines.append("ASPECTOS NATALES (orbe < 3°)")
        for a in tight:
            app = " ↑" if a.get("applying") else ""
            lines.append(f"{a.get('planet_a','')} {a.get('type','')} {a.get('planet_b','')} · orbe {a.get('orb',0):.1f}°{app}")
        lines.append("")

    lots: list = abu_data.get("derived", {}).get("lots", [])
    def _find_lot(names):
        return next((l for l in lots if l.get("name","").lower() in [n.lower() for n in names]), None)
    f = _find_lot(["fortuna", "fortune"])
    s = _find_lot(["spirit", "espíritu", "espiritu"])
    lines.append("PARTES ARÁBICAS")
    if f and f.get("sign", "—") != "—":
        lines.append(f"Fortuna: {f['sign']} {f.get('degree',0):.1f}° · Casa {f.get('house',0)} · Señor: {f.get('lord','—')}")
    if s and s.get("sign", "—") != "—":
        lines.append(f"Espíritu: {s['sign']} {s.get('degree',0):.1f}° · Casa {s.get('house',0)} · Señor: {s.get('lord','—')}")
    lines.append("")

    # ── LÍNEA DE TIEMPO ──
    lines += [SEP, "LÍNEA DE TIEMPO", SEP, ""]
    profections = timeline.get("profections", [])
    firdaria    = timeline.get("firdaria", [])
    transits    = timeline.get("transits_window", [])

    active_prof = next((p for p in profections if p.get("is_active")), None)
    if active_prof:
        lines += ["PROFECCIÓN ACTIVA",
                  f"Año {active_prof['year_of_life']} · {active_prof['date_start']} → {active_prof['date_end']}",
                  f"Casa {active_prof['house']} ({active_prof['sign']}) · Señor del año: {active_prof['lord']} · Dignidad: {active_prof['lord_dignity'].capitalize()}"]
        idx = profections.index(active_prof)
        if idx + 1 < len(profections):
            np = profections[idx + 1]
            lines += ["", "PROFECCIÓN SIGUIENTE",
                      f"Casa {np['house']} ({np['sign']}) · Señor: {np['lord']} · desde {np['date_start']}"]
        lines.append("")

    active_fird = next((f for f in firdaria if f.get("is_active")), None)
    if active_fird:
        major_start = next((f["date_start"] for f in firdaria if f["major_planet"] == active_fird["major_planet"]), active_fird["date_start"])
        lines += ["FIRDARIA",
                  f"Mayor: {active_fird['major_planet']} · activa desde {major_start}",
                  f"Menor activa: {active_fird['minor_planet']} · {active_fird['date_start']} → {active_fird['date_end']}"]
        idx = firdaria.index(active_fird)
        if idx + 1 < len(firdaria):
            nf = firdaria[idx + 1]
            lines.append(f"Siguiente menor: {nf['minor_planet']} · desde {nf['date_start']}")
        lines.append("")

    if transits:
        lines.append("TRÁNSITOS SIGNIFICATIVOS ±18 meses")
        for t in transits:
            active = " [activo]" if t.get("is_active") else ""
            lines.append(f"- {t['transit_planet']} {t['aspect']} {t['natal_planet']} natal [exacto: {t['exact_date']}]{active}")
        lines.append("")

    conv = _detect_convergence(timeline)
    if conv:
        lines += [conv, ""]

    # ── CONTEXTO ACTIVO ──
    now = datetime.now(timezone.utc).isoformat()
    lines += [SEP, f"CONTEXTO ACTIVO — {now}", SEP,
              f"Vista: {trigger_data.get('active_tab', 'natal_chart')}",
              f"Trigger: {route_name}",
              f"Idioma de respuesta: {lang}"]

    for k, v in trigger_data.items():
        if k not in ("active_tab",) and v is not None and v != "":
            lines.append(f"{k}: {v}")

    lines += ["", f"RESPOND ONLY IN: {lang.upper()}. This overrides any language used in previous conversation or biographical memory."]
    return "\n".join(lines)

# ── Trigger data representativo por ruta ─────────────────────────────────────

def build_trigger_data(route: str, abu_data: dict, timeline: dict) -> dict:
    """Construye trigger_data representativo para cada ruta."""
    planets: list = abu_data.get("chart", {}).get("planets", [])
    sun = next((p for p in planets if p["name"] == "Sun"), planets[0] if planets else {})

    transits = timeline.get("transits_window", [])
    first_transit = next((t for t in transits if t.get("is_active")), transits[0] if transits else {})

    if route == "screen-open":
        sect = abu_data.get("derived", {}).get("sect", "unknown")
        return {"active_tab": "persian_techniques",
                "name": abu_data.get("person", {}).get("name", "Anónimo"),
                "sect": sect, "sect_master": "Moon" if sect == "nocturnal" else "Sun"}

    elif route == "planet":
        lon = sun.get("longitude") or sun.get("lon") or 0
        return {"active_tab": "natal_chart",
                "planet_name": sun.get("name", "Sun"),
                "lon": lon,
                "sign": sun.get("sign") or _get_sign(lon),
                "house": sun.get("house", 1),
                "dignity": _dignity_str(sun.get("dignity")),
                "dignity_score": sun.get("dignity_score", 0),
                "retrograde": sun.get("retrograde", False)}

    elif route == "technique_lot":
        lots: list = abu_data.get("derived", {}).get("lots", [])
        f = next((l for l in lots if "fortuna" in l.get("name","").lower()), {})
        return {"active_tab": "persian_techniques",
                "technique": "lot",
                "lot_name": "Fortuna",
                "lon": f.get("longitude", 0),
                "sign": f.get("sign", "—"),
                "house": f.get("house", 0),
                "lord": f.get("lord", "—")}

    elif route == "technique_firdaria":
        fird = abu_data.get("derived", {}).get("firdaria", {}).get("current", {})
        return {"active_tab": "persian_techniques",
                "technique": "firdaria",
                "major": fird.get("major", "—"),
                "sub": fird.get("sub", "—"),
                "start": fird.get("start", "—"),
                "end": fird.get("end", "—")}

    elif route == "technique_lunar":
        return {"active_tab": "persian_techniques",
                "technique": "lunar_transit",
                "moon_sign": next((p.get("sign") for p in planets if p["name"] == "Moon"), "—")}

    elif route == "city":
        return {"active_tab": "hf_map",
                "city_name": "Buenos Aires", "country": "Argentina",
                "lat": -34.6, "lon": -58.4,
                "hf_score": 8.5, "delta_natal": 2.3,
                "domain": "h10", "mode": "natal"}

    elif route == "domain":
        return {"active_tab": "hf_map",
                "domain": "h10", "house_num": 10,
                "hf_current": 7.2, "hf_max": 14.1,
                "best_city": "Tokyo"}

    elif route == "house":
        houses_obj = abu_data.get("chart", {}).get("houses", {})
        asc_lon    = houses_obj.get("asc", 0)
        return {"active_tab": "natal_chart",
                "house_num": 1,
                "cusp_sign": _get_sign(asc_lon),
                "house_lord": _RULERS.get(_get_sign(asc_lon), "—"),
                "occupants": [p["name"] for p in planets if p.get("house") == 1][:3]}

    elif route == "sky":
        return {"active_tab": "cielo_hoy",
                "today": datetime.now().date().isoformat(),
                "fast_transits_active": "Luna conjunción Sol · Mercurio sextil Marte"}

    elif route == "transit":
        return {"active_tab": "transits",
                "transit_planet": first_transit.get("transit_planet", "Saturn"),
                "transit_sign": first_transit.get("transit_sign", "Aries"),
                "transit_deg": first_transit.get("transit_deg", 15.0),
                "transit_date": first_transit.get("exact_date", datetime.now().date().isoformat()),
                "aspects": first_transit.get("aspect", "conjunction")}

    elif route == "chat":
        return {"active_tab": "chat",
                "message": "¿Cuál es mi profección este año y qué planeta activa?"}

    return {}

# ── Abu Engine calls ──────────────────────────────────────────────────────────

def parse_utc_offset(tz_str: str) -> float:
    """Parse '+05:30:00' or '-04:56:01' → float hours."""
    if not tz_str:
        return 0.0
    try:
        tz_str = tz_str.strip()
        sign = -1 if tz_str.startswith("-") else 1
        tz_str = tz_str.lstrip("+-")
        parts = tz_str.split(":")
        h = int(parts[0]) if len(parts) > 0 else 0
        m = int(parts[1]) if len(parts) > 1 else 0
        s = int(parts[2]) if len(parts) > 2 else 0
        return sign * (h + m / 60 + s / 3600)
    except Exception:
        return 0.0

def build_iso_date(birth_date: str, birth_time: str, utc_offset_h: float) -> str:
    """Combine local date+time and offset → UTC ISO string."""
    from datetime import datetime as dt, timedelta
    local_str = f"{birth_date}T{birth_time}"
    local_dt  = dt.fromisoformat(local_str)
    utc_dt    = local_dt - timedelta(hours=utc_offset_h)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def call_analyze(subject: dict) -> dict | None:
    utc_offset = parse_utc_offset(subject.get("timezone", ""))
    birth_iso  = build_iso_date(subject["birth_date"], subject.get("birth_time", "12:00:00"), utc_offset)
    lat = subject["latitude"]
    lon = subject["longitude"]
    payload = {
        "person": {"name": subject.get("name", "Subject").split(" ::")[0], "question": ""},
        "birth":  {"date": birth_iso, "lat": lat, "lon": lon, "utc_offset": utc_offset},
        "current": {"lat": lat, "lon": lon, "date": datetime.now(timezone.utc).isoformat()},
    }
    try:
        r = requests.post(f"{ABU_URL}/analyze", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [ERR] /analyze failed: {e}")
        return None

def call_biography(subject: dict) -> dict:
    utc_offset = parse_utc_offset(subject.get("timezone", ""))
    birth_iso  = build_iso_date(subject["birth_date"], subject.get("birth_time", "12:00:00"), utc_offset)
    lat = subject["latitude"]
    lon = subject["longitude"]
    try:
        r = requests.get(f"{ABU_URL}/api/astro/biography",
                         params={"birthDate": birth_iso, "birthLat": lat, "birthLon": lon},
                         timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [ERR] /biography failed: {e}")
        return {"profections": [], "firdaria": [], "transits_window": []}

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY no está en el entorno.")
        sys.exit(1)

    # Verify Abu Engine is reachable
    try:
        r = requests.get(f"{ABU_URL}/health", timeout=5)
        r.raise_for_status()
        print(f"[OK] Abu Engine reachable at {ABU_URL}")
    except Exception as e:
        print(f"ERROR: Abu Engine no responde en {ABU_URL}: {e}")
        print("Asegurate de que Abu Engine esté corriendo con AUTH_ENABLED=false")
        sys.exit(1)

    # Load and sample subjects
    all_subjects = []
    with open(RAW_DATA, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("latitude") and rec.get("longitude") and rec.get("birth_date") and rec.get("birth_time"):
                all_subjects.append(rec)

    random.seed(RANDOM_SEED)
    sample = random.sample(all_subjects, min(SAMPLE_N, len(all_subjects)))
    print(f"[OK] Sampled {len(sample)} subjects (seed={RANDOM_SEED})")

    anthropic_client = anthropic.Anthropic(api_key=api_key)

    results = []
    skipped = 0

    for i, subject in enumerate(sample):
        subject_id  = subject["id"]
        subject_name = subject.get("name", "?").split(" ::")[0]
        print(f"\n[{i+1}/{len(sample)}] {subject_id} — {subject_name}")

        abu_data = call_analyze(subject)
        if abu_data is None:
            skipped += 1
            continue

        timeline = call_biography(subject)

        for route_name, model, _max_tokens_current in ROUTES:
            trigger = build_trigger_data(route_name, abu_data, timeline)
            context = build_context_block(abu_data, timeline, trigger, route_name, lang="es")

            try:
                resp = anthropic_client.messages.count_tokens(
                    model=model,
                    system=LILLY_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": context}],
                )
                tokens_input = resp.input_tokens
            except Exception as e:
                print(f"  [ERR] count_tokens {route_name}: {e}")
                tokens_input = None

            record = {
                "subject_id":   subject_id,
                "subject_name": subject_name,
                "route":        route_name,
                "model":        model,
                "tokens_input": tokens_input,
                "timestamp":    datetime.now(timezone.utc).isoformat(),
            }
            results.append(record)
            status = f"{tokens_input:,}" if tokens_input is not None else "ERROR"
            print(f"  {route_name:<25} {status} tokens input")

        time.sleep(SLEEP_BETWEEN_SUBJECTS)

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"meta": {"sample_n": len(sample), "skipped": skipped,
                             "seed": RANDOM_SEED, "generated_at": datetime.now(timezone.utc).isoformat()},
                   "results": results}, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"[OK] Results written to {OUTPUT_FILE}")
    print(f"  Records: {len(results)}  |  Skipped subjects: {skipped}")

    # Quick summary per route
    from collections import defaultdict
    import statistics
    route_tokens: dict[str, list[int]] = defaultdict(list)
    for r in results:
        if r["tokens_input"] is not None:
            route_tokens[r["route"]].append(r["tokens_input"])

    print(f"\n{'Route':<25} {'N':>4} {'mean':>7} {'p50':>7} {'p95':>7} {'p99':>7}")
    print("-" * 55)
    for route_name, model, _ in ROUTES:
        vals = sorted(route_tokens.get(route_name, []))
        if not vals:
            print(f"{route_name:<25} {'—':>4}")
            continue
        n   = len(vals)
        mean = statistics.mean(vals)
        p50  = vals[int(n * 0.50)]
        p95  = vals[min(int(n * 0.95), n-1)]
        p99  = vals[min(int(n * 0.99), n-1)]
        print(f"{route_name:<25} {n:>4} {mean:>7.0f} {p50:>7} {p95:>7} {p99:>7}")

if __name__ == "__main__":
    main()
