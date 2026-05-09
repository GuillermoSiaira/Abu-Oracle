# -*- coding: utf-8 -*-
"""
NetworkX chart graph builder for KG Phase 1.

The graph is intentionally in-memory and side-effect free. It accepts the
current /analyze JSON shape plus the KG-C02 draft shape used in tests.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import networkx as nx


DOMICILIOS: Dict[str, List[str]] = {
    "Sol": ["Leo"],
    "Luna": ["Cancer", "Cáncer"],
    "Mercurio": ["Geminis", "Géminis", "Virgo"],
    "Venus": ["Tauro", "Libra"],
    "Marte": ["Aries", "Escorpio"],
    "Júpiter": ["Sagitario", "Piscis"],
    "Saturno": ["Capricornio", "Acuario"],
}

ENGLISH_TO_SPANISH_PLANETS = {
    "Sun": "Sol",
    "Moon": "Luna",
    "Mercury": "Mercurio",
    "Venus": "Venus",
    "Mars": "Marte",
    "Jupiter": "Júpiter",
    "Saturn": "Saturno",
    "Uranus": "Urano",
    "Neptune": "Neptuno",
    "Pluto": "Plutón",
}

SPANISH_TO_ENGLISH_PLANETS = {
    spanish: english for english, spanish in ENGLISH_TO_SPANISH_PLANETS.items()
}

SIGN_ALIASES = {
    "Aries": "Aries",
    "Taurus": "Tauro",
    "Tauro": "Tauro",
    "Gemini": "Géminis",
    "Geminis": "Géminis",
    "Géminis": "Géminis",
    "Cancer": "Cáncer",
    "Cáncer": "Cáncer",
    "Leo": "Leo",
    "Virgo": "Virgo",
    "Libra": "Libra",
    "Scorpio": "Escorpio",
    "Escorpio": "Escorpio",
    "Sagittarius": "Sagitario",
    "Sagitario": "Sagitario",
    "Capricorn": "Capricornio",
    "Capricornio": "Capricornio",
    "Aquarius": "Acuario",
    "Acuario": "Acuario",
    "Pisces": "Piscis",
    "Piscis": "Piscis",
}

SIGNS_BY_LONGITUDE = [
    "Aries",
    "Tauro",
    "Géminis",
    "Cáncer",
    "Leo",
    "Virgo",
    "Libra",
    "Escorpio",
    "Sagitario",
    "Capricornio",
    "Acuario",
    "Piscis",
]


def _planet_name(name: Any) -> str:
    text = str(name or "")
    return ENGLISH_TO_SPANISH_PLANETS.get(text, text)


def _possible_planet_names(name: str) -> List[str]:
    names = [name]
    english = SPANISH_TO_ENGLISH_PLANETS.get(name)
    spanish = ENGLISH_TO_SPANISH_PLANETS.get(name)
    if english:
        names.append(english)
    if spanish:
        names.append(spanish)
    return names


def _sign_name(sign: Any) -> str:
    text = str(sign or "")
    return SIGN_ALIASES.get(text, text)


def _sign_from_longitude(longitude: Any) -> str:
    try:
        lon = float(longitude) % 360.0
    except (TypeError, ValueError):
        return ""
    return SIGNS_BY_LONGITUDE[int(lon // 30)]


def _house_number(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _planets_from_chart(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    planets = chart.get("planets", [])
    if isinstance(planets, dict):
        result = []
        for name, data in planets.items():
            if isinstance(data, dict):
                result.append({"name": name, **data})
        return result
    return _as_list(planets)


def _houses_from_chart(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    houses = chart.get("houses", [])
    if isinstance(houses, dict):
        houses = houses.get("houses", [])
    return _as_list(houses)


def _node_for_planet(G: nx.DiGraph, name: Any) -> str:
    canonical = _planet_name(name)
    if G.has_node(canonical):
        return canonical
    for candidate in _possible_planet_names(canonical):
        if G.has_node(candidate):
            return candidate
    return canonical


def _sign_lord(sign: str) -> Optional[str]:
    canonical = _sign_name(sign)
    for planet, signs in DOMICILIOS.items():
        if canonical in [_sign_name(s) for s in signs]:
            return planet
    return None


def _active_profection(derived: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    profections = derived.get("profections")
    if isinstance(profections, list):
        return next((p for p in profections if p.get("is_active")), None)

    profection = derived.get("profection")
    if isinstance(profection, dict):
        return profection
    return None


def _active_firdaria(derived: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    firdaria = derived.get("firdaria")
    if isinstance(firdaria, list):
        return next((f for f in firdaria if f.get("is_active")), None)
    if isinstance(firdaria, dict):
        current = firdaria.get("current")
        if isinstance(current, dict):
            return current
        return firdaria
    return None


def _iter_lots(lots: Any) -> Iterable[tuple[str, Dict[str, Any]]]:
    if isinstance(lots, dict):
        for key, value in lots.items():
            if isinstance(value, dict):
                yield str(key), value
    elif isinstance(lots, list):
        for lot in lots:
            if isinstance(lot, dict):
                key = str(lot.get("key") or lot.get("name") or "").lower()
                if key:
                    yield key, lot


def build_chart_graph(abu_json: dict) -> nx.DiGraph:
    """
    Build an in-memory directed graph for a natal chart from Abu /analyze JSON.
    """
    chart = abu_json.get("chart", {}) if isinstance(abu_json, dict) else {}
    derived = abu_json.get("derived", {}) if isinstance(abu_json, dict) else {}

    G = nx.DiGraph()
    planets = _planets_from_chart(chart)
    houses = _houses_from_chart(chart)

    for planet in planets:
        name = _planet_name(planet.get("name"))
        if not name:
            continue
        longitude = planet.get("longitude", planet.get("lon", 0.0))
        sign = _sign_name(planet.get("sign")) or _sign_from_longitude(longitude)
        degree = planet.get("degree", planet.get("deg", 0.0))
        house = _house_number(planet.get("house"))
        G.add_node(
            name,
            type="planet",
            sign=sign,
            house=house,
            degree=degree,
            dignity=planet.get("dignity", "peregrine"),
            retrograde=planet.get("retrograde", False),
            longitude=longitude,
        )
        if house is not None:
            G.add_edge(name, f"Casa{house}", relation="ocupa", degree=degree)

    for house in houses:
        number = _house_number(house.get("house"))
        if number is None:
            continue
        cusp = house.get("degree", house.get("start", 0.0))
        sign = _sign_name(house.get("sign")) or _sign_from_longitude(cusp)
        G.add_node(f"Casa{number}", type="house", sign=sign, cusp_degree=cusp)

    for aspect in _as_list(chart.get("aspects", [])):
        planet_a = _node_for_planet(G, aspect.get("planet_a", aspect.get("a")))
        planet_b = _node_for_planet(G, aspect.get("planet_b", aspect.get("b")))
        if not planet_a or not planet_b:
            continue
        attrs = {
            "relation": "aspecto",
            "type": aspect.get("type", ""),
            "orb": aspect.get("orb", 0.0),
            "applying": aspect.get("applying", False),
        }
        G.add_edge(planet_a, planet_b, **attrs)
        G.add_edge(planet_b, planet_a, **attrs)

    for planet, signs in DOMICILIOS.items():
        for sign in signs:
            canonical_sign = _sign_name(sign)
            G.add_node(canonical_sign, type="sign")
            G.add_edge(
                planet,
                canonical_sign,
                relation="rige",
                type="domicilio",
                tradition="hellenistic",
            )

    if houses:
        asc_lord = houses[0].get("lord") or _sign_lord(houses[0].get("sign") or _sign_from_longitude(houses[0].get("degree", houses[0].get("start"))))
        if asc_lord:
            G.add_edge(_node_for_planet(G, asc_lord), "Casa1", relation="señor_ASC")

        house10 = next((h for h in houses if _house_number(h.get("house")) == 10), None)
        if house10:
            mc_lord = house10.get("lord") or _sign_lord(house10.get("sign") or _sign_from_longitude(house10.get("degree", house10.get("start"))))
            if mc_lord:
                G.add_edge(_node_for_planet(G, mc_lord), "Casa10", relation="señor_MC")

    prof = _active_profection(derived)
    if prof and prof.get("lord"):
        house = _house_number(prof.get("house"))
        if house is not None:
            G.add_edge(
                _node_for_planet(G, prof["lord"]),
                f"Casa{house}",
                relation="señor_del_año",
                house=house,
                sign=_sign_name(prof.get("sign")),
                date_end=prof.get("date_end", ""),
            )

    fird = _active_firdaria(derived)
    if fird:
        G.add_node("firdaria_node", type="cycle")
        major = fird.get("major_planet", fird.get("major"))
        minor = fird.get("minor_planet", fird.get("minor"))
        if major:
            G.add_edge(
                _node_for_planet(G, major),
                "firdaria_node",
                relation="firdaria_mayor",
                date_end=fird.get("date_end", fird.get("end", "")),
            )
        if minor and minor != major:
            G.add_edge(
                _node_for_planet(G, minor),
                "firdaria_node",
                relation="firdaria_menor",
                date_end=fird.get("date_end", fird.get("end", "")),
            )

    for lot_key, lot_data in _iter_lots(derived.get("lots", {})):
        lot_lord = lot_data.get("lord")
        if not lot_lord:
            continue
        lot_node = f"Lote_{lot_key}"
        G.add_node(
            lot_node,
            type="lot",
            sign=_sign_name(lot_data.get("sign")),
            house=_house_number(lot_data.get("house")),
            degree=lot_data.get("degree", 0.0),
        )
        G.add_edge(
            _node_for_planet(G, lot_lord),
            lot_node,
            relation=f"señor_{lot_key}",
            lot_sign=_sign_name(lot_data.get("sign")),
            lot_house=_house_number(lot_data.get("house")) or 0,
        )

    return G


def get_key_planets(G: nx.DiGraph, derived: dict) -> List[str]:
    """
    Return active planets in KG-C02 priority order, without duplicates.
    """

    def _lord_of(relation: str) -> Optional[str]:
        for u, _, data in G.edges(data=True):
            if data.get("relation") == relation:
                return u
        return None

    prof = _active_profection(derived or {})
    fird = _active_firdaria(derived or {})
    candidates = [
        prof.get("lord") if prof else None,
        fird.get("major_planet", fird.get("major")) if fird else None,
        fird.get("minor_planet", fird.get("minor")) if fird else None,
        _lord_of("señor_ASC"),
        _lord_of("señor_MC"),
        _lord_of("señor_fortuna"),
        _lord_of("señor_spirit"),
    ]

    key = []
    seen = set()
    for candidate in candidates:
        if not candidate:
            continue
        node = _node_for_planet(G, candidate)
        if node and node not in seen and G.has_node(node):
            key.append(node)
            seen.add(node)
    return key


def serialize_subgraph(G: nx.DiGraph, key_planets: List[str]) -> str:
    """
    Serialize the active lordship subgraph to structured text for Lilly.
    """
    if not key_planets:
        return ""

    lines = ["SEÑORÍOS ACTIVOS (KG)"]
    for planet in key_planets:
        if not G.has_node(planet):
            continue

        node = G.nodes[planet]
        dignity = str(node.get("dignity", "peregrine")).capitalize()
        sign = node.get("sign", "?")
        try:
            degree = float(node.get("degree", 0.0))
        except (TypeError, ValueError):
            degree = 0.0
        house = node.get("house", 0)
        retrograde = " R" if node.get("retrograde") else ""

        lines.append(f"{planet} [{dignity} - {sign} {degree:.1f} deg - Casa {house}{retrograde}]")

        for _, target, edge in G.out_edges(planet, data=True):
            relation = edge.get("relation", "")
            if relation == "señor_ASC":
                target_sign = G.nodes.get(target, {}).get("sign", "")
                lines.append(f"  -> señor_ASC -> {target} ({target_sign})")
            elif relation == "señor_MC":
                target_sign = G.nodes.get(target, {}).get("sign", "")
                lines.append(f"  -> señor_MC -> {target} ({target_sign})")
            elif relation == "señor_del_año":
                date_end = edge.get("date_end", "?")
                target_sign = edge.get("sign", "")
                lines.append(f"  -> señor_del_año -> {target} ({target_sign}) - hasta {date_end}")
            elif relation == "firdaria_mayor":
                date_end = edge.get("date_end", "?")
                lines.append(f"  -> firdaria_mayor - periodo hasta {date_end}")
            elif relation == "firdaria_menor":
                date_end = edge.get("date_end", "?")
                lines.append(f"  -> firdaria_menor - hasta {date_end}")
            elif relation.startswith("señor_"):
                lot_sign = edge.get("lot_sign", "")
                lot_house = edge.get("lot_house", 0)
                lines.append(f"  -> {relation} -> [{lot_sign} - Casa {lot_house}]")

        aspects = [
            (target, edge)
            for _, target, edge in G.out_edges(planet, data=True)
            if edge.get("relation") == "aspecto"
        ]
        aspects.sort(key=lambda item: item[1].get("orb", 99))
        for target, edge in aspects[:3]:
            aspect_type = edge.get("type", "")
            try:
                orb = float(edge.get("orb", 0.0))
            except (TypeError, ValueError):
                orb = 0.0
            app_marker = " applying" if edge.get("applying") else ""
            lines.append(f"  -> {aspect_type} -> {target} ({orb:.1f} deg{app_marker})")

    return "\n".join(lines)
