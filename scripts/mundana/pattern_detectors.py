"""
pattern_detectors.py — Librería unificada de detección de patrones astrológicos mundanos.

Detecta ~80-100 patrones en cualquier momento (Julian Day):
  Grupo A: aspectos pares (60) + aspectos a nodo norte (16)
  Grupo B: configuraciones estructurales (7)
  Grupo C: eventos temporales discretos (12)
  Grupo D: ciclos sinódicos (28)

API pública:
  detect_active_patterns(jd: float, *, lookback_days: float = 0, lookforward_days: float = 0) -> list[Pattern]
  catalog() -> list[PatternMeta]

Reusa ephemeris_historical.get_planet_positions().
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Callable, Iterable

import swisseph as swe

sys.path.insert(0, str(Path(__file__).parent))
from ephemeris_historical import get_planet_positions, angular_distance

# ─────────────────────────────────────────────────────────────────────────────
# Catálogo
# ─────────────────────────────────────────────────────────────────────────────

PLANETS_A = ["mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
PLANETS_B = ["sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]
ASPECTS = {
    "conjunction": (0.0,   8.0),
    "opposition":  (180.0, 8.0),
    "square":      (90.0,  6.0),
    "trine":       (120.0, 6.0),
}
NODE_ASPECT_PLANETS = ["sun", "mars", "jupiter", "saturn"]
NODE_ASPECTS = ["conjunction", "opposition", "square", "trine"]

SYNODIC_PAIRS = [
    ("jupiter", "saturn"),
    ("saturn", "uranus"),
    ("saturn", "neptune"),
    ("saturn", "pluto"),
    ("uranus", "neptune"),
    ("uranus", "pluto"),
    ("jupiter", "uranus"),
]
SYNODIC_PHASES = ["cycle_start", "first_quarter", "opposition", "last_quarter"]
SYNODIC_PHASE_ANGLES = {
    "cycle_start":   0.0,
    "first_quarter": 90.0,
    "opposition":    180.0,
    "last_quarter":  270.0,
}
SYNODIC_PHASE_ORB = 10.0  # grados — fase activa


SIGNS = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
         "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
CARDINAL_SIGNS = {"Aries", "Cáncer", "Libra", "Capricornio"}


# ─────────────────────────────────────────────────────────────────────────────
# Estructuras de datos
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Pattern:
    """Detección concreta de un patrón en un JD específico."""
    type:         str            # ej. "conjunction_JS", "grand_trine", "eclipse_solar"
    group:        str            # "A" | "B" | "C" | "D"
    label:        str            # legible humano
    participants: list[str]      # planetas/cuerpos involucrados
    jd:           float          # JD donde se observó
    orb:          float          # orbe efectivo en grados (0 = exacto, None = no aplica)
    details:      dict = field(default_factory=dict)

    def to_jsonable(self) -> dict:
        return asdict(self)


@dataclass
class PatternMeta:
    """Descriptor estático del patrón (sin observación)."""
    type:      str
    group:     str
    label:     str
    requires:  list[str]   # planetas que necesita


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sign_of(lon: float) -> str:
    return SIGNS[int(lon // 30) % 12]

def _orb_to_angle(lon1: float, lon2: float, target: float) -> float:
    """Distancia angular de (lon1-lon2) al target, en [0, 180]."""
    diff = abs(angular_distance(lon1, lon2) - target)
    return min(diff, abs(360 - diff))   # nunca debería pasar pero por seguridad

def _aspect_within(lon1: float, lon2: float, target_deg: float, orb: float) -> Optional[float]:
    """Si el aspecto está dentro de orbe, devuelve la magnitud del orbe efectivo."""
    diff = abs(angular_distance(lon1, lon2) - target_deg)
    return diff if diff <= orb else None


# ─────────────────────────────────────────────────────────────────────────────
# Grupo A — Aspectos pares
# ─────────────────────────────────────────────────────────────────────────────

def _detect_group_a(positions: dict, jd: float) -> list[Pattern]:
    patterns = []
    for i, p1 in enumerate(PLANETS_A):
        for p2 in PLANETS_A[i+1:]:
            lon1, lon2 = positions[p1]["lon"], positions[p2]["lon"]
            for aspect_name, (deg, orb) in ASPECTS.items():
                effective_orb = _aspect_within(lon1, lon2, deg, orb)
                if effective_orb is not None:
                    type_code = f"{aspect_name}_{p1[0].upper()}{p2[0].upper()}"
                    patterns.append(Pattern(
                        type=type_code,
                        group="A",
                        label=f"{aspect_name.title()} {p1.title()}-{p2.title()}",
                        participants=[p1, p2],
                        jd=jd,
                        orb=effective_orb,
                        details={"aspect": aspect_name, "exact_deg": deg},
                    ))
    # Aspectos a nodo norte
    if "true_node" in positions:
        node_lon = positions["true_node"]["lon"]
        for planet in NODE_ASPECT_PLANETS:
            if planet not in positions: continue
            p_lon = positions[planet]["lon"]
            for aspect_name in NODE_ASPECTS:
                deg, orb = ASPECTS[aspect_name]
                effective_orb = _aspect_within(p_lon, node_lon, deg, orb)
                if effective_orb is not None:
                    patterns.append(Pattern(
                        type=f"node_{aspect_name}_{planet}",
                        group="A",
                        label=f"{aspect_name.title()} {planet.title()}-Nodo Norte",
                        participants=[planet, "true_node"],
                        jd=jd,
                        orb=effective_orb,
                        details={"aspect": aspect_name, "node": "true_node"},
                    ))
    return patterns


# ─────────────────────────────────────────────────────────────────────────────
# Grupo B — Configuraciones estructurales
# ─────────────────────────────────────────────────────────────────────────────

def _detect_t_square(positions: dict, jd: float) -> list[Pattern]:
    patterns = []
    planets = [p for p in PLANETS_B if p in positions]
    for i, a in enumerate(planets):
        for j, b in enumerate(planets[i+1:], i+1):
            opp_orb = _aspect_within(positions[a]["lon"], positions[b]["lon"], 180.0, 6.0)
            if opp_orb is None: continue
            for c in planets:
                if c == a or c == b: continue
                sq_a = _aspect_within(positions[a]["lon"], positions[c]["lon"], 90.0, 6.0)
                sq_b = _aspect_within(positions[b]["lon"], positions[c]["lon"], 90.0, 6.0)
                if sq_a is not None and sq_b is not None:
                    patterns.append(Pattern(
                        type="t_square",
                        group="B",
                        label=f"T-Square {a.title()}/{b.title()}/{c.title()}",
                        participants=sorted([a, b, c]),
                        jd=jd,
                        orb=max(opp_orb, sq_a, sq_b),
                        details={"opposition": [a, b], "apex": c},
                    ))
    return _dedupe_by_participants(patterns)

def _detect_grand_trine(positions: dict, jd: float) -> list[Pattern]:
    patterns = []
    planets = [p for p in PLANETS_B if p in positions]
    for i, a in enumerate(planets):
        for j, b in enumerate(planets[i+1:], i+1):
            ab = _aspect_within(positions[a]["lon"], positions[b]["lon"], 120.0, 6.0)
            if ab is None: continue
            for c in planets[j+1:]:
                ac = _aspect_within(positions[a]["lon"], positions[c]["lon"], 120.0, 6.0)
                bc = _aspect_within(positions[b]["lon"], positions[c]["lon"], 120.0, 6.0)
                if ac is not None and bc is not None:
                    patterns.append(Pattern(
                        type="grand_trine",
                        group="B",
                        label=f"Gran Trígono {a.title()}/{b.title()}/{c.title()}",
                        participants=sorted([a, b, c]),
                        jd=jd,
                        orb=max(ab, ac, bc),
                    ))
    return patterns

def _detect_yod(positions: dict, jd: float) -> list[Pattern]:
    patterns = []
    planets = [p for p in PLANETS_B if p in positions]
    for i, a in enumerate(planets):
        for j, b in enumerate(planets[i+1:], i+1):
            sextile = _aspect_within(positions[a]["lon"], positions[b]["lon"], 60.0, 3.0)
            if sextile is None: continue
            for c in planets:
                if c == a or c == b: continue
                qa = _aspect_within(positions[a]["lon"], positions[c]["lon"], 150.0, 3.0)
                qb = _aspect_within(positions[b]["lon"], positions[c]["lon"], 150.0, 3.0)
                if qa is not None and qb is not None:
                    patterns.append(Pattern(
                        type="yod",
                        group="B",
                        label=f"Yod base {a.title()}-{b.title()} → {c.title()}",
                        participants=sorted([a, b, c]),
                        jd=jd,
                        orb=max(sextile, qa, qb),
                        details={"base": [a, b], "apex": c},
                    ))
    return _dedupe_by_participants(patterns)

def _detect_grand_cross(positions: dict, jd: float) -> list[Pattern]:
    """4 planetas con 2 oposiciones (eje 1: A-B, eje 2: C-D) + 4 cuadraturas."""
    patterns = []
    planets = [p for p in PLANETS_B if p in positions]
    for i, a in enumerate(planets):
        for b in planets[i+1:]:
            opp_ab = _aspect_within(positions[a]["lon"], positions[b]["lon"], 180.0, 6.0)
            if opp_ab is None: continue
            for j, c in enumerate(planets):
                if c == a or c == b: continue
                for d in planets[j+1:]:
                    if d == a or d == b or d == c: continue
                    opp_cd = _aspect_within(positions[c]["lon"], positions[d]["lon"], 180.0, 6.0)
                    if opp_cd is None: continue
                    # 4 cuadraturas
                    orbes = [_aspect_within(positions[x]["lon"], positions[y]["lon"], 90.0, 6.0)
                             for (x, y) in [(a, c), (a, d), (b, c), (b, d)]]
                    if all(o is not None for o in orbes):
                        patterns.append(Pattern(
                            type="grand_cross",
                            group="B",
                            label=f"Gran Cruz {a}/{b}//{c}/{d}",
                            participants=sorted([a, b, c, d]),
                            jd=jd,
                            orb=max([opp_ab, opp_cd] + orbes),
                        ))
    return _dedupe_by_participants(patterns)

def _detect_stellium_sign(positions: dict, jd: float) -> list[Pattern]:
    by_sign: dict[str, list[str]] = {}
    for p in PLANETS_B:
        if p not in positions: continue
        by_sign.setdefault(_sign_of(positions[p]["lon"]), []).append(p)
    patterns = []
    for sign, members in by_sign.items():
        if len(members) >= 3:
            patterns.append(Pattern(
                type="stellium_sign",
                group="B",
                label=f"Stellium {sign} ({len(members)} planetas)",
                participants=sorted(members),
                jd=jd,
                orb=0.0,
                details={"sign": sign, "count": len(members), "cardinal": sign in CARDINAL_SIGNS},
            ))
    return patterns

def _detect_stellium_orb(positions: dict, jd: float) -> list[Pattern]:
    """4+ planetas dentro de arco de 30°."""
    planets = [p for p in PLANETS_B if p in positions]
    longs = sorted([(positions[p]["lon"], p) for p in planets])
    n = len(longs)
    best: Optional[tuple[int, list[str]]] = None
    for start in range(n):
        members = [longs[start][1]]
        for offset in range(1, n):
            j = (start + offset) % n
            lon_diff = (longs[j][0] - longs[start][0]) % 360
            if lon_diff <= 30.0:
                members.append(longs[j][1])
            else:
                break
        if len(members) >= 4 and (best is None or len(members) > len(best[1])):
            best = (start, members)
    if best is None: return []
    return [Pattern(
        type="stellium_orb",
        group="B",
        label=f"Stellium en orbe 30° ({len(best[1])} planetas)",
        participants=sorted(best[1]),
        jd=jd,
        orb=30.0,
        details={"count": len(best[1])},
    )]

def _detect_mystic_rectangle(positions: dict, jd: float) -> list[Pattern]:
    """4 planetas con 2 oposiciones + 4 trígonos/sextiles."""
    patterns = []
    planets = [p for p in PLANETS_B if p in positions]
    for i, a in enumerate(planets):
        for b in planets[i+1:]:
            opp_ab = _aspect_within(positions[a]["lon"], positions[b]["lon"], 180.0, 6.0)
            if opp_ab is None: continue
            for j, c in enumerate(planets):
                if c == a or c == b: continue
                for d in planets[j+1:]:
                    if d == a or d == b or d == c: continue
                    opp_cd = _aspect_within(positions[c]["lon"], positions[d]["lon"], 180.0, 6.0)
                    if opp_cd is None: continue
                    pairs = [(a, c), (a, d), (b, c), (b, d)]
                    soft = []
                    for x, y in pairs:
                        trine = _aspect_within(positions[x]["lon"], positions[y]["lon"], 120.0, 6.0)
                        sext  = _aspect_within(positions[x]["lon"], positions[y]["lon"], 60.0, 6.0)
                        if trine is not None: soft.append(trine)
                        elif sext is not None: soft.append(sext)
                        else: soft = None; break
                    if soft is not None:
                        patterns.append(Pattern(
                            type="mystic_rectangle",
                            group="B",
                            label=f"Rectángulo Místico {a}/{b}//{c}/{d}",
                            participants=sorted([a, b, c, d]),
                            jd=jd,
                            orb=max([opp_ab, opp_cd] + soft),
                        ))
    return _dedupe_by_participants(patterns)

def _detect_group_b(positions: dict, jd: float) -> list[Pattern]:
    return (_detect_t_square(positions, jd)
          + _detect_grand_trine(positions, jd)
          + _detect_yod(positions, jd)
          + _detect_grand_cross(positions, jd)
          + _detect_stellium_sign(positions, jd)
          + _detect_stellium_orb(positions, jd)
          + _detect_mystic_rectangle(positions, jd))

def _dedupe_by_participants(patterns: list[Pattern]) -> list[Pattern]:
    seen: dict[tuple, Pattern] = {}
    for p in patterns:
        key = (p.type, tuple(p.participants))
        if key not in seen or p.orb < seen[key].orb:
            seen[key] = p
    return list(seen.values())


# ─────────────────────────────────────────────────────────────────────────────
# Grupo C — Eventos temporales discretos (puntuales)
# ─────────────────────────────────────────────────────────────────────────────
# Estos se detectan escaneando ventanas, no en un JD único.
# La API pública es scan_window_discrete(jd_start, jd_end).

def scan_window_discrete(jd_start: float, jd_end: float) -> list[Pattern]:
    """Detecta eventos puntuales en la ventana [jd_start, jd_end]."""
    out = []
    out += _scan_eclipses(jd_start, jd_end)
    out += _scan_lunations_cardinal(jd_start, jd_end)
    out += _scan_solar_ingress_cardinal(jd_start, jd_end)
    out += _scan_planet_stations(jd_start, jd_end)
    out += _scan_node_sign_change(jd_start, jd_end)
    return out

def _scan_eclipses(jd_start: float, jd_end: float) -> list[Pattern]:
    out: list[Pattern] = []
    # Solar
    jd = jd_start
    while jd < jd_end:
        retval, tret = swe.sol_eclipse_when_glob(jd + 1, swe.FLG_SWIEPH, 0)
        if retval < 0 or tret[0] <= 0 or tret[0] >= jd_end: break
        sun_lon, _ = swe.calc_ut(tret[0], swe.SUN, swe.FLG_SWIEPH)
        ecl_type = ("total" if retval & 4 else "annular" if retval & 2
                    else "hybrid" if retval & 8 else "partial")
        out.append(Pattern(
            type=f"eclipse_solar_{ecl_type}",
            group="C", label=f"Eclipse Solar {ecl_type.title()}",
            participants=["sun", "moon"], jd=tret[0], orb=0.0,
            details={"eclipse_type": ecl_type, "sign": _sign_of(sun_lon[0])},
        ))
        jd = tret[0] + 10
    # Lunar
    jd = jd_start
    while jd < jd_end:
        retval, tret = swe.lun_eclipse_when(jd + 1, swe.FLG_SWIEPH, 0)
        if retval < 0 or tret[0] <= 0 or tret[0] >= jd_end: break
        moon_lon, _ = swe.calc_ut(tret[0], swe.MOON, swe.FLG_SWIEPH)
        ecl_type = ("total" if retval & 4 else "partial" if retval & 16 else "penumbral")
        out.append(Pattern(
            type=f"eclipse_lunar_{ecl_type}",
            group="C", label=f"Eclipse Lunar {ecl_type.title()}",
            participants=["sun", "moon"], jd=tret[0], orb=0.0,
            details={"eclipse_type": ecl_type, "sign": _sign_of(moon_lon[0])},
        ))
        jd = tret[0] + 10
    return out

def _scan_lunations_cardinal(jd_start: float, jd_end: float) -> list[Pattern]:
    """Lunas nuevas y llenas en signos cardinales."""
    out = []
    # Sol-Luna conjuncion (new) y oposicion (full) cada ~14 días
    jd = jd_start
    step = 1.0
    prev_elong = None
    while jd <= jd_end:
        sun, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
        moon, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
        elong = (moon[0] - sun[0]) % 360
        if prev_elong is not None:
            # Cruces de 0° (new moon) y 180° (full moon)
            for target, kind in [(0.0, "new"), (180.0, "full")]:
                if _crosses_target(prev_elong, elong, target):
                    # bisección rápida
                    exact_jd = _bisect_elong(jd - step, jd, target)
                    moon_e, _ = swe.calc_ut(exact_jd, swe.MOON, swe.FLG_SWIEPH)
                    sign = _sign_of(moon_e[0])
                    if sign in CARDINAL_SIGNS:
                        out.append(Pattern(
                            type=f"lunation_{kind}_cardinal",
                            group="C",
                            label=f"Luna {'Nueva' if kind=='new' else 'Llena'} en {sign}",
                            participants=["sun", "moon"], jd=exact_jd, orb=0.0,
                            details={"sign": sign, "kind": kind},
                        ))
        prev_elong = elong
        jd += step
    return out

def _crosses_target(prev: float, curr: float, target: float) -> bool:
    """Detecta cruce de target en una progresión cíclica [0, 360)."""
    if abs(curr - prev) > 300:  # wrap-around
        return False
    return (prev < target <= curr) or (curr < target <= prev)

def _bisect_elong(lo: float, hi: float, target: float) -> float:
    for _ in range(30):
        mid = (lo + hi) / 2
        sun, _ = swe.calc_ut(mid, swe.SUN, swe.FLG_SWIEPH)
        moon, _ = swe.calc_ut(mid, swe.MOON, swe.FLG_SWIEPH)
        elong = (moon[0] - sun[0]) % 360
        diff = (elong - target + 540) % 360 - 180  # signed diff
        if abs(diff) < 1e-4: return mid
        # Heurística simple: si diff > 0 estamos pasados, retroceder
        if diff > 0: hi = mid
        else:        lo = mid
    return (lo + hi) / 2

def _scan_solar_ingress_cardinal(jd_start: float, jd_end: float) -> list[Pattern]:
    out = []
    jd = jd_start; step = 1.0
    prev_lon = None
    while jd <= jd_end:
        sun, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
        lon = sun[0]
        if prev_lon is not None:
            for cardinal_lon, sign in [(0.0, "Aries"), (90.0, "Cáncer"),
                                        (180.0, "Libra"), (270.0, "Capricornio")]:
                if _crosses_target(prev_lon, lon, cardinal_lon):
                    # bisección
                    lo, hi = jd - step, jd
                    for _ in range(20):
                        mid = (lo + hi) / 2
                        m_sun, _ = swe.calc_ut(mid, swe.SUN, swe.FLG_SWIEPH)
                        if _crosses_target(prev_lon, m_sun[0], cardinal_lon): hi = mid
                        else: lo = mid; prev_lon = m_sun[0]
                    exact_jd = (lo + hi) / 2
                    out.append(Pattern(
                        type=f"solar_ingress_{sign.lower()}",
                        group="C",
                        label=f"Sol ingresa en {sign}",
                        participants=["sun"], jd=exact_jd, orb=0.0,
                        details={"sign": sign},
                    ))
        prev_lon = lon
        jd += step
    return out

def _scan_planet_stations(jd_start: float, jd_end: float) -> list[Pattern]:
    out = []
    planet_map = {"mercury": swe.MERCURY, "venus": swe.VENUS, "mars": swe.MARS,
                  "jupiter": swe.JUPITER, "saturn": swe.SATURN}
    for name, code in planet_map.items():
        step = 2.0; jd = jd_start
        _, prev_speed = _planet_lon_speed(code, jd)
        while jd <= jd_end:
            jd += step
            _, curr_speed = _planet_lon_speed(code, jd)
            if prev_speed * curr_speed < 0:
                # bisección
                lo, hi = jd - step, jd
                for _ in range(20):
                    mid = (lo + hi) / 2
                    _, ms = _planet_lon_speed(code, mid)
                    if ms * prev_speed < 0: hi = mid
                    else: lo = mid
                exact_jd = (lo + hi) / 2
                kind = "rx" if curr_speed < 0 else "dx"
                p_lon, _ = _planet_lon_speed(code, exact_jd)
                out.append(Pattern(
                    type=f"station_{kind}_{name}",
                    group="C",
                    label=f"{name.title()} estación {'retrógrada' if kind=='rx' else 'directa'}",
                    participants=[name], jd=exact_jd, orb=0.0,
                    details={"sign": _sign_of(p_lon), "retrograde": kind == "rx"},
                ))
            prev_speed = curr_speed
    return out

def _scan_node_sign_change(jd_start: float, jd_end: float) -> list[Pattern]:
    out = []
    step = 5.0; jd = jd_start
    node_lon, _ = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SWIEPH)
    prev_sign = _sign_of(node_lon[0])
    while jd <= jd_end:
        jd += step
        node_lon, _ = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SWIEPH)
        curr_sign = _sign_of(node_lon[0])
        if curr_sign != prev_sign:
            # bisección
            lo, hi = jd - step, jd
            for _ in range(20):
                mid = (lo + hi) / 2
                m_lon, _ = swe.calc_ut(mid, swe.TRUE_NODE, swe.FLG_SWIEPH)
                if _sign_of(m_lon[0]) == prev_sign: lo = mid
                else: hi = mid
            exact_jd = (lo + hi) / 2
            out.append(Pattern(
                type="node_sign_change",
                group="C",
                label=f"Nodo Norte ingresa en {curr_sign}",
                participants=["true_node"], jd=exact_jd, orb=0.0,
                details={"from": prev_sign, "to": curr_sign},
            ))
            prev_sign = curr_sign
    return out

def _planet_lon_speed(code: int, jd: float) -> tuple[float, float]:
    result, _ = swe.calc_ut(jd, code, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return result[0], result[3]


# ─────────────────────────────────────────────────────────────────────────────
# Grupo D — Ciclos sinódicos
# ─────────────────────────────────────────────────────────────────────────────

def _detect_group_d(positions: dict, jd: float) -> list[Pattern]:
    """Detecta en qué fase del ciclo sinódico está cada par."""
    patterns = []
    for slow, fast in SYNODIC_PAIRS:
        # Convención: ángulo = (lento - rápido) mod 360, pero para que avance positivo,
        # ordenamos por velocidad orbital (lento al final). Para JS: slow=jupiter, fast=saturn
        # NO — saturn es más lento. Ajustar dinámicamente por velocidad media:
        if slow not in positions or fast not in positions: continue
        lon_s = positions[slow]["lon"]
        lon_f = positions[fast]["lon"]
        # Forzar que el "rápido" tenga mayor velocidad orbital
        speed_s = positions[slow].get("speed", 0)
        speed_f = positions[fast].get("speed", 0)
        if abs(speed_f) < abs(speed_s):
            slow, fast = fast, slow
            lon_s, lon_f = lon_f, lon_s
        phase_angle = (lon_f - lon_s) % 360
        for phase_name, target in SYNODIC_PHASE_ANGLES.items():
            diff = min(abs(phase_angle - target), abs(360 - abs(phase_angle - target)))
            if diff <= SYNODIC_PHASE_ORB:
                type_code = f"synodic_{phase_name}_{slow[0].upper()}{fast[0].upper()}"
                patterns.append(Pattern(
                    type=type_code,
                    group="D",
                    label=f"Ciclo {slow.title()}-{fast.title()} fase {phase_name}",
                    participants=[slow, fast],
                    jd=jd, orb=diff,
                    details={"phase": phase_name, "phase_angle": phase_angle},
                ))
    return patterns


# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────

_PLANETS_SWE = {
    "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
    "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
    "saturn": swe.SATURN, "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE, "pluto": swe.PLUTO,
}
_POS_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


def get_positions_with_node(jd: float) -> dict:
    """Calcula posiciones (lon + speed) de planetas mayores + true_node en un JD."""
    positions = {}
    for name, code in _PLANETS_SWE.items():
        result, _ = swe.calc_ut(jd, code, _POS_FLAGS)
        positions[name] = {"lon": result[0], "speed": result[3]}
    node_result, _ = swe.calc_ut(jd, swe.TRUE_NODE, _POS_FLAGS)
    positions["true_node"] = {"lon": node_result[0], "speed": node_result[3]}
    return positions


def detect_active_patterns(
    jd: float, *,
    lookback_days: float = 0,
    lookforward_days: float = 0,
) -> list[Pattern]:
    """
    Detecta todos los patrones activos en jd.
    Si lookback/lookforward > 0, también escanea eventos discretos (Grupo C) en esa ventana.
    """
    positions = get_positions_with_node(jd)
    patterns = []
    patterns += _detect_group_a(positions, jd)
    patterns += _detect_group_b(positions, jd)
    patterns += _detect_group_d(positions, jd)
    if lookback_days > 0 or lookforward_days > 0:
        patterns += scan_window_discrete(jd - lookback_days, jd + lookforward_days)
    return patterns


def catalog() -> list[PatternMeta]:
    """Devuelve el catálogo completo de tipos de patrón soportados."""
    cat = []
    # Grupo A
    for i, p1 in enumerate(PLANETS_A):
        for p2 in PLANETS_A[i+1:]:
            for aspect_name in ASPECTS:
                cat.append(PatternMeta(
                    type=f"{aspect_name}_{p1[0].upper()}{p2[0].upper()}",
                    group="A", label=f"{aspect_name.title()} {p1.title()}-{p2.title()}",
                    requires=[p1, p2]))
    for planet in NODE_ASPECT_PLANETS:
        for aspect_name in NODE_ASPECTS:
            cat.append(PatternMeta(
                type=f"node_{aspect_name}_{planet}",
                group="A", label=f"{aspect_name.title()} {planet.title()}-Nodo",
                requires=[planet, "true_node"]))
    # Grupo B
    for t, lbl in [("t_square", "T-Square"), ("grand_trine", "Gran Trígono"),
                   ("grand_cross", "Gran Cruz"), ("yod", "Yod"),
                   ("stellium_sign", "Stellium signo"), ("stellium_orb", "Stellium orbe"),
                   ("mystic_rectangle", "Rectángulo Místico")]:
        cat.append(PatternMeta(type=t, group="B", label=lbl, requires=PLANETS_B))
    # Grupo C
    for t in ["eclipse_solar_total", "eclipse_solar_partial", "eclipse_solar_annular",
              "eclipse_solar_hybrid", "eclipse_lunar_total", "eclipse_lunar_partial",
              "eclipse_lunar_penumbral", "lunation_new_cardinal", "lunation_full_cardinal",
              "solar_ingress_aries", "solar_ingress_cáncer", "solar_ingress_libra",
              "solar_ingress_capricornio", "node_sign_change"]:
        cat.append(PatternMeta(type=t, group="C", label=t, requires=[]))
    for planet in ["mercury", "venus", "mars", "jupiter", "saturn"]:
        for kind in ["rx", "dx"]:
            cat.append(PatternMeta(
                type=f"station_{kind}_{planet}", group="C",
                label=f"Estación {kind} {planet}", requires=[planet]))
    # Grupo D
    for slow, fast in SYNODIC_PAIRS:
        for phase in SYNODIC_PHASES:
            cat.append(PatternMeta(
                type=f"synodic_{phase}_{slow[0].upper()}{fast[0].upper()}",
                group="D", label=f"Ciclo {slow}-{fast} {phase}",
                requires=[slow, fast]))
    return cat


if __name__ == "__main__":
    import json, datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    jd_now = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60)
    patterns = detect_active_patterns(jd_now, lookback_days=30, lookforward_days=30)
    print(f"Detected {len(patterns)} patterns at JD {jd_now}")
    print(json.dumps([p.to_jsonable() for p in patterns], indent=2, default=str))
