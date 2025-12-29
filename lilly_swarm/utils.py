from typing import Dict, Any, List, Optional
from rules_persian import element_of_sign, ruler_of_sign, is_angular_house

def find_ascendant(chart: Dict[str, Any]) -> Dict[str, Any]:
    angles = chart.get("angles") or {}
    asc = angles.get("ASC") or angles.get("Ascendant")
    if not asc:
        houses = chart.get("houses") or []
        for h in houses:
            if h.get("number") == 1:
                return {"sign": h.get("sign"), "degree": h.get("degree"), "house": 1}
    return asc or {}

def count_elements(planets: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    for p in planets:
        sign = p.get("sign")
        elem = element_of_sign(sign)
        if elem in counts:
            counts[elem] += 1
    return counts

def infer_year_element(asc_sign: str, sun_sign: str, counts_by_element: Dict[str, int]) -> str:
    from collections import Counter
    c = Counter(counts_by_element)
    asc_elem = element_of_sign(asc_sign)
    sun_elem = element_of_sign(sun_sign)
    if asc_elem in c:
        c[asc_elem] += 2
    if sun_elem in c:
        c[sun_elem] += 2
    if not c:
        return "unknown"
    return c.most_common(1)[0][0]

def extract_rs_data(extended: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return extended.get("solar_return") or None

def get_profections(extended: Dict[str, Any]) -> Dict[str, Any]:
    return extended.get("profections") or {}

def get_fardars(extended: Dict[str, Any]) -> Dict[str, Any]:
    return extended.get("fardars") or {}

def get_lots(extended: Dict[str, Any]) -> List[Dict[str, Any]]:
    return extended.get("lots") or []

def get_lunar_mansion(extended: Dict[str, Any]) -> Dict[str, Any]:
    return extended.get("lunar_mansion") or {}

def summarize_angularity(chart: Dict[str, Any]) -> Dict[str, Any]:
    planets = chart.get("planets") or []
    strong, weak = [], []
    for p in planets:
        house = p.get("house")
        name = p.get("name")
        if not house or not name:
            continue
        reason = []
        if is_angular_house(int(house)):
            reason.append("angular")
        if p.get("dignity") in ("domicile", "exaltation"):
            reason.append("essential_dignity")
        if "fall" in str(p.get("dignity") or "").lower() or "detriment" in str(p.get("dignity") or "").lower():
            reason.append("essential_debility")
        if "angular" in reason or "essential_dignity" in reason:
            strong.append({"planet": name, "reason": ", ".join(reason)})
        if "essential_debility" in reason:
            weak.append({"planet": name, "reason": ", ".join(reason)})
    return {"strong": strong, "weak": weak}
