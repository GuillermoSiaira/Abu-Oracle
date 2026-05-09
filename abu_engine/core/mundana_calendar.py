"""
Mundane astrology calendar for the next N months.

The module keeps the output lightweight and deterministic for UI use:
eclipses, Mercury stations, Jupiter/Saturn ingresses, validated mundane
configurations, and simple stellium detections.
"""

from __future__ import annotations

import swisseph as swe

from core.mundana import _FLAGS, _get_positions, get_upcoming_configurations

SIGNS_ES = [
    "Aries",
    "Tauro",
    "Geminis",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Escorpio",
    "Sagitario",
    "Capricornio",
    "Acuario",
    "Piscis",
]

PLANET_NAMES_ES = {
    swe.SUN: "Sol",
    swe.MOON: "Luna",
    swe.MERCURY: "Mercurio",
    swe.VENUS: "Venus",
    swe.MARS: "Marte",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturno",
    swe.URANUS: "Urano",
    swe.NEPTUNE: "Neptuno",
    swe.PLUTO: "Pluton",
}


def _jd_to_iso(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _get_sign(lon: float) -> str:
    return SIGNS_ES[int(lon // 30) % 12]


def _planet_lon(planet_id: int, jd: float) -> float:
    result, _ = swe.calc_ut(jd, planet_id, _FLAGS | swe.FLG_SPEED)
    return result[0] % 360


def _planet_speed(planet_id: int, jd: float) -> float:
    result, _ = swe.calc_ut(jd, planet_id, _FLAGS | swe.FLG_SPEED)
    return result[3]


def _collect_eclipses(jd_start: float, jd_end: float) -> list[dict]:
    events: list[dict] = []

    jd = jd_start
    while jd < jd_end:
        try:
            retval, tret = swe.sol_eclipse_when_glob(jd + 1, _FLAGS, 0)
        except Exception:
            break
        if retval < 0 or tret[0] <= 0 or tret[0] >= jd_end:
            break
        lon = _planet_lon(swe.SUN, tret[0])
        eclipse_type = (
            "Total"
            if retval & 4
            else "Anular"
            if retval & 2
            else "Hibrido"
            if retval & 8
            else "Parcial"
        )
        sign = _get_sign(lon)
        events.append(
            {
                "type": "eclipse_solar",
                "date": _jd_to_iso(tret[0]),
                "jd": tret[0],
                "description": f"Eclipse Solar {eclipse_type} - {sign}",
                "significance": "high",
                "icon": "SOL",
                "details": {"eclipse_type": eclipse_type, "sign": sign},
            }
        )
        jd = tret[0] + 10

    jd = jd_start
    while jd < jd_end:
        try:
            retval, tret = swe.lun_eclipse_when(jd + 1, _FLAGS, 0)
        except Exception:
            break
        if retval < 0 or tret[0] <= 0 or tret[0] >= jd_end:
            break
        lon = _planet_lon(swe.MOON, tret[0])
        eclipse_type = "Total" if retval & 4 else "Parcial" if retval & 16 else "Penumbral"
        sign = _get_sign(lon)
        events.append(
            {
                "type": "eclipse_lunar",
                "date": _jd_to_iso(tret[0]),
                "jd": tret[0],
                "description": f"Eclipse Lunar {eclipse_type} - {sign}",
                "significance": "high" if eclipse_type == "Total" else "medium",
                "icon": "LUNA",
                "details": {"eclipse_type": eclipse_type, "sign": sign},
            }
        )
        jd = tret[0] + 10

    return events


def _collect_mercury_stations(jd_start: float, jd_end: float) -> list[dict]:
    events: list[dict] = []
    step = 5.0
    jd = jd_start
    prev_speed = _planet_speed(swe.MERCURY, jd)

    while jd < jd_end:
        jd += step
        curr_speed = _planet_speed(swe.MERCURY, jd)
        if prev_speed * curr_speed < 0:
            lo, hi = jd - step, jd
            for _ in range(24):
                mid = (lo + hi) / 2
                if _planet_speed(swe.MERCURY, mid) * prev_speed < 0:
                    hi = mid
                else:
                    lo = mid
            exact_jd = (lo + hi) / 2
            sign = _get_sign(_planet_lon(swe.MERCURY, exact_jd))
            is_rx = curr_speed < 0
            events.append(
                {
                    "type": "mercury_retrograde" if is_rx else "mercury_direct",
                    "date": _jd_to_iso(exact_jd),
                    "jd": exact_jd,
                    "description": f"Mercurio {'retrogrado' if is_rx else 'directo'} en {sign}",
                    "significance": "medium",
                    "icon": "MER",
                    "details": {"sign": sign, "retrograde": is_rx},
                }
            )
        prev_speed = curr_speed

    return events


def _collect_planet_ingresses(jd_start: float, jd_end: float) -> list[dict]:
    events: list[dict] = []
    for planet_id in (swe.JUPITER, swe.SATURN):
        step = 10.0
        jd = jd_start
        prev_sign = _get_sign(_planet_lon(planet_id, jd))
        while jd < jd_end:
            jd += step
            curr_sign = _get_sign(_planet_lon(planet_id, jd))
            if curr_sign != prev_sign:
                lo, hi = jd - step, jd
                for _ in range(24):
                    mid = (lo + hi) / 2
                    if _get_sign(_planet_lon(planet_id, mid)) == prev_sign:
                        lo = mid
                    else:
                        hi = mid
                exact_jd = (lo + hi) / 2
                name = PLANET_NAMES_ES[planet_id]
                events.append(
                    {
                        "type": "planet_ingress",
                        "date": _jd_to_iso(exact_jd),
                        "jd": exact_jd,
                        "description": f"{name} ingresa en {curr_sign}",
                        "significance": "high" if planet_id == swe.SATURN else "medium",
                        "icon": "SAT" if planet_id == swe.SATURN else "JUP",
                        "details": {
                            "planet": name,
                            "sign": curr_sign,
                            "from_sign": prev_sign,
                        },
                    }
                )
                prev_sign = curr_sign

    return events


def _collect_validated_configs(jd_start: float, jd_end: float) -> list[dict]:
    days = int(jd_end - jd_start)
    events: list[dict] = []
    for config in get_upcoming_configurations(days_ahead=days):
        p_value = config.get("p_value")
        if p_value is None or p_value > 0.1:
            continue
        exact_date = (config.get("exact_date") or "")[:10]
        if not exact_date:
            continue
        events.append(
            {
                "type": "configuration",
                "date": exact_date,
                "jd": jd_start,
                "description": config.get("label") or config.get("type", "Configuracion"),
                "significance": config.get("significance", "medium"),
                "icon": "CFG",
                "details": config,
            }
        )
    return events


def _collect_stelliums(jd_start: float, jd_end: float) -> list[dict]:
    events: list[dict] = []
    jd = jd_start
    seen: set[tuple[str, str]] = set()

    while jd < jd_end:
        y, m, d, h = swe.revjul(jd)
        positions = _get_positions(int(y), int(m), int(d), h)
        by_sign: dict[str, list[str]] = {}
        for planet, lon in positions.items():
            by_sign.setdefault(_get_sign(lon), []).append(planet)

        for sign, planets in by_sign.items():
            if len(planets) >= 4:
                date = _jd_to_iso(jd)
                key = (date[:7], sign)
                if key in seen:
                    continue
                seen.add(key)
                events.append(
                    {
                        "type": "stellium",
                        "date": date,
                        "jd": jd,
                        "description": f"Stellium en {sign} ({len(planets)} planetas)",
                        "significance": "high" if len(planets) >= 5 else "medium",
                        "icon": "STEL",
                        "details": {"sign": sign, "planets": planets},
                    }
                )
        jd += 7

    return events


def build_mundana_calendar(jd_start: float, months_ahead: int = 12) -> list[dict]:
    jd_end = jd_start + months_ahead * 30.44
    events: list[dict] = []
    events.extend(_collect_eclipses(jd_start, jd_end))
    events.extend(_collect_mercury_stations(jd_start, jd_end))
    events.extend(_collect_planet_ingresses(jd_start, jd_end))
    events.extend(_collect_validated_configs(jd_start, jd_end))
    events.extend(_collect_stelliums(jd_start, jd_end))

    events.sort(key=lambda event: (event.get("date", "9999"), event.get("type", "")))
    for event in events:
        event.pop("jd", None)
    return events
