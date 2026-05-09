def _first_active(items: list[dict]) -> dict | None:
    return next((item for item in items if item.get("is_active")), None)


def _first_inactive(items: list[dict]) -> dict | None:
    return next((item for item in items if not item.get("is_active")), None)


def _date10(value: object) -> str:
    return str(value or "?")[:10]


def build_timeline_section_a(bio_json: dict, natal_json: dict) -> str:
    """
    Build the baseline LINEA DE TIEMPO section from biography JSON.

    This mirrors the compact timeline facts consumed by Lilly today: active
    profection, next profection, active firdaria, and a capped list of slow
    active conjunction/opposition transits.
    """
    del natal_json

    lines = ["=== LINEA DE TIEMPO ==="]

    profections = bio_json.get("profections", []) or []
    firdaria = bio_json.get("firdaria", []) or []
    transits = bio_json.get("transits_window", []) or []

    active_prof = _first_active(profections)
    if active_prof:
        lines.append(
            "Profeccion activa: "
            f"Casa {active_prof.get('house', '?')} - {active_prof.get('sign', '?')} - "
            f"Senor: {active_prof.get('lord', '?')} - hasta {_date10(active_prof.get('date_end'))}"
        )

    next_prof = _first_inactive(profections)
    if next_prof:
        lines.append(
            "Proxima profeccion: "
            f"Casa {next_prof.get('house', '?')} - {next_prof.get('sign', '?')} - "
            f"desde {_date10(next_prof.get('date_start'))}"
        )

    active_fird = _first_active(firdaria)
    if active_fird:
        lines.append(
            "Firdaria mayor: "
            f"{active_fird.get('major_planet', active_fird.get('major', '?'))} - "
            f"Menor: {active_fird.get('minor_planet', active_fird.get('minor', '?'))} - "
            f"hasta {_date10(active_fird.get('date_end', active_fird.get('end')))}"
        )

    slow_active = [
        transit
        for transit in transits
        if transit.get("is_active")
        and transit.get("speed_class") == "slow"
        and transit.get("aspect") in ("conjunction", "opposition")
    ]

    if slow_active:
        lines.append("Transitos lentos activos:")
        for transit in slow_active[:5]:
            exact = _date10(transit.get("exact_date"))
            lines.append(
                "  "
                f"{transit.get('transit_planet', '?')} {transit.get('aspect', '?')} "
                f"natal {transit.get('natal_planet', '?')} - exacto: {exact}"
            )

    lines.append("=========================")
    return "\n".join(lines)
