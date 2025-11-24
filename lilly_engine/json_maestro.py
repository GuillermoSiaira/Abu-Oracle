from typing import Dict, Any, List, Optional
from datetime import datetime
from rules_persian import element_of_sign, ruler_of_sign, PLANET_NATURE
from utils import (
    find_ascendant,
    count_elements,
    infer_year_element,
    extract_rs_data,
    get_profections,
    get_fardars,
    get_lots,
    get_lunar_mansion,
    summarize_angularity,
)

def _build_metadata(metadata_context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mode": "persian_cosmology",
        "calculated_by": "abu_engine",
        "interpreted_by": "lilly_engine",
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "request_context": metadata_context or {},
    }

def _build_cosmology_context() -> Dict[str, Any]:
    return {
        "system": "persian_medieval",
        "key_principles": [
            "Four Qualities Framework (heat, cold, moisture, dryness)",
            "Four Elements (fire, air, water, earth)",
            "Planetary natures (Saturn cold+dry, Jupiter hot+moist, etc.)",
            "Essential and accidental dignities",
            "Lord of the Year methodology (Ṣāḥib al-Sana)",
            "Annual revolution as renewal of cosmic decree",
            "Use of profections, Fardars and lunar mansions for timing",
        ],
    }

def _build_year_overview(chart: Dict[str, Any], extended: Dict[str, Any]) -> Dict[str, Any]:
    asc = find_ascendant(chart)
    asc_sign = asc.get("sign")
    asc_deg = asc.get("degree")
    sun = next((p for p in chart.get("planets", []) if p.get("name") == "Sun"), None)
    rs = extract_rs_data(extended)
    rs_location = None
    rs_sun = None
    if rs:
        rs_location = rs.get("location") or rs.get("place")
        rs_sun = rs.get("sun")
    planets = chart.get("planets") or []
    counts_by_element = count_elements(planets)
    year_element = infer_year_element(
        asc_sign,
        sun.get("sign") if sun else None,
        counts_by_element,
    )
    year_tone_keywords = {
        "water": ["emotional depth", "family focus", "inner work", "intuition", "healing", "memory"],
        "fire": ["initiative", "courage", "visibility", "risk-taking", "leadership"],
        "earth": ["stability", "work", "material consolidation", "discipline"],
        "air": ["ideas", "communication", "networks", "mobility", "learning"],
    }.get(year_element, [])
    return {
        "rs_location": rs_location,
        "ascendant_rs": {
            "sign": asc_sign,
            "degree": asc_deg,
            "element": element_of_sign(asc_sign) if asc_sign else None,
        },
        "sun_rs": rs_sun or {
            "sign": sun.get("sign") if sun else None,
            "house_rs": sun.get("house") if sun else None,
        },
        "year_element": year_element,
        "year_tone_keywords": year_tone_keywords,
    }, counts_by_element

def _build_elemental_analysis(counts_by_element: Dict[str, int], chart: Dict[str, Any], extended: Dict[str, Any]) -> Dict[str, Any]:
    asc = find_ascendant(chart)
    asc_elem = element_of_sign(asc.get("sign")) if asc else None
    sun = next((p for p in chart.get("planets", []) if p.get("name") == "Sun"), None)
    sun_elem = element_of_sign(sun.get("sign")) if sun else None
    angularity_info = summarize_angularity(chart)
    dominant_element = max(counts_by_element, key=counts_by_element.get) if counts_by_element else None
    return {
        "counts_by_element": counts_by_element,
        "dominant_element_reasoning": {
            "ascendant_element": asc_elem,
            "sun_element": sun_elem,
            "angular_water_planets": [
                p["planet"] for p in angularity_info["strong"]
                if element_of_sign(
                    next((pl.get("sign") for pl in chart.get("planets", []) if pl.get("name") == p["planet"]), "")
                ) == "water"
            ],
            "additional_notes": "Derived from chart.planets and house positions (angularity).",
        },
        "interpretation": {
            "core_drivers": []
        },
    }

def _build_lord_of_year(chart: Dict[str, Any], extended: Dict[str, Any]) -> Dict[str, Any]:
    prof = extended.get("profections") or {}
    time_lord_name = prof.get("time_lord")
    planets = chart.get("planets") or []
    candidates = {}
    if time_lord_name:
        candidates["time_lord"] = time_lord_name
    asc = find_ascendant(chart)
    asc_sign = asc.get("sign")
    if asc_sign:
        candidates["ascendant_ruler"] = ruler_of_sign(asc_sign)
    angularity_scores = {}
    essential_scores = {}
    accidental_scores = {}
    for label, planet_name in candidates.items():
        pl = next((p for p in planets if p.get("name") == planet_name), None)
        if not pl:
            continue
        base = 0
        house = pl.get("house")
        if house:
            h = int(house)
            if h in {1, 4, 7, 10}:
                base += 4
            elif h in {2, 5, 8, 11}:
                base += 2
            else:
                base += 1
        angularity_scores[planet_name] = base
        dignity = str(pl.get("dignity") or "").lower()
        ess = 0
        if "domicile" in dignity or "ruler" in dignity:
            ess += 5
        if "exalt" in dignity:
            ess += 4
        if "detriment" in dignity or "fall" in dignity:
            ess -= 4
        essential_scores[planet_name] = ess
        accidental_scores[planet_name] = base
    totals = {}
    for p in set(angularity_scores) | set(essential_scores) | set(accidental_scores):
        totals[p] = angularity_scores.get(p, 0) + essential_scores.get(p, 0) + accidental_scores.get(p, 0)
    final_lord = None
    if totals:
        final_lord = max(totals, key=totals.get)
    lord_keywords = []
    if final_lord:
        nature = PLANET_NATURE.get(final_lord, [])
        lord_keywords.append("planet_nature: " + ", ".join(nature))
    return {
        "candidates": candidates,
        "evaluation": {
            "angularity_scores": angularity_scores,
            "essential_dignity_scores": essential_scores,
            "accidental_dignity_scores": accidental_scores,
        },
        "final_lord": final_lord,
        "lord_keywords": lord_keywords,
    }

def _build_angularity_and_dignities(chart: Dict[str, Any]) -> Dict[str, Any]:
    ang = summarize_angularity(chart)
    combustion_flags: List[Dict[str, Any]] = []
    for p in chart.get("planets", []):
        if p.get("combust"):
            combustion_flags.append({
                "planet": p.get("name"),
                "status": "combust",
                "effect": "potential obscuration of that planet's topics",
            })
    return {
        "strong_planets": ang["strong"],
        "weak_planets": ang["weak"],
        "combustion_flags": combustion_flags,
    }

def _build_rs_natal_interplay(chart: Dict[str, Any], extended: Dict[str, Any]) -> Dict[str, Any]:
    prof = extended.get("profections") or {}
    lunar_mansion = get_lunar_mansion(extended)
    return {
        "rs_asc_falls_in_natal_house": None,
        "rs_sun_falls_in_natal_house": None,
        "themes_unlocked": [
            "Will be refined when RS–Natal overlay is fully integrated.",
            f"Lunar mansion of the year: {lunar_mansion.get('name')}" if lunar_mansion else "",
        ],
    }

def _build_transits_contextualized(extended: Dict[str, Any]) -> Dict[str, Any]:
    transits = extended.get("transits") or []
    contextualized = []
    for t in transits:
        contextualized.append({
            "transit": t.get("label") or f"{t.get('transiting')} {t.get('aspect')} {t.get('natal')}",
            "timing": t.get("timing") or t.get("date"),
            "interpretation_depends_on_rs": "To be filled by rule-based engine or LLM layer.",
        })
    return {"major_transits": contextualized}

def _build_monthly_windows(extended: Dict[str, Any]) -> Dict[str, Any]:
    prof = extended.get("profections") or {}
    monthly = prof.get("monthly") or {}
    primary_by_sign = []
    if prof.get("profected_sign"):
        primary_by_sign.append({
            "month": monthly.get("month"),
            "sign": monthly.get("monthly_sign"),
            "theme": "Derived from profection lord and house; to be refined.",
        })
    return {
        "primary_by_sign": primary_by_sign,
        "secondary_by_house": [],
    }

def _build_critical_days(extended: Dict[str, Any]) -> List[Dict[str, Any]]:
    return []

def build_json_maestro(
    chart_extended: Dict[str, Any],
    metadata_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    chart = chart_extended.get("chart") or {}
    extended = chart_extended.get("extended") or {}
    metadata = _build_metadata(metadata_context or {})
    cosmology_context = _build_cosmology_context()
    year_overview, counts_by_element = _build_year_overview(chart, extended)
    elemental_analysis = _build_elemental_analysis(counts_by_element, chart, extended)
    lord_of_year = _build_lord_of_year(chart, extended)
    ang_digs = _build_angularity_and_dignities(chart)
    rs_natal = _build_rs_natal_interplay(chart, extended)
    transits_ctx = _build_transits_contextualized(extended)
    monthly_windows = _build_monthly_windows(extended)
    critical_days = _build_critical_days(extended)
    maestro = {
        "metadata": metadata,
        "cosmology_context": cosmology_context,
        "year_overview": year_overview,
        "elemental_analysis": elemental_analysis,
        "lord_of_year": lord_of_year,
        "angularity_and_dignities": ang_digs,
        "rs_natal_interplay": rs_natal,
        "transits_contextualized": transits_ctx,
        "monthly_windows": monthly_windows,
        "critical_days": critical_days,
    }
    return maestro
