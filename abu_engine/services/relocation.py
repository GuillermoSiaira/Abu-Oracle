# -*- coding: utf-8 -*-
"""Relocation HF field computation service.

Extracted from scripts/regenerate_demo_hires.py for use in the
GET /api/astro/relocation endpoint.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from core.chart import chart_json
from core.houses_swiss import HOUSE_SYSTEM_PLACIDUS, calculate_houses
from harmony.field_v3 import compute_hf_v3

logger = logging.getLogger(__name__)

CITIES_PATH = Path(__file__).resolve().parent.parent / "data" / "cities.json"

# ISO-2 → full country name (246 codes from worldcities.csv)
_ISO2_TO_COUNTRY: Dict[str, str] = {
    "AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan", "AG": "Antigua and Barbuda",
    "AI": "Anguilla", "AL": "Albania", "AM": "Armenia", "AO": "Angola", "AQ": "Antarctica",
    "AR": "Argentina", "AS": "American Samoa", "AT": "Austria", "AU": "Australia", "AW": "Aruba",
    "AX": "\u00c5land Islands", "AZ": "Azerbaijan", "BA": "Bosnia and Herzegovina", "BB": "Barbados",
    "BD": "Bangladesh", "BE": "Belgium", "BF": "Burkina Faso", "BG": "Bulgaria", "BH": "Bahrain",
    "BI": "Burundi", "BJ": "Benin", "BL": "Saint Barth\u00e9lemy", "BM": "Bermuda", "BN": "Brunei",
    "BO": "Bolivia", "BQ": "Caribbean Netherlands", "BR": "Brazil", "BS": "Bahamas", "BT": "Bhutan",
    "BV": "Bouvet Island", "BW": "Botswana", "BY": "Belarus", "BZ": "Belize", "CA": "Canada",
    "CC": "Cocos Islands", "CD": "DR Congo", "CF": "Central African Republic", "CG": "Congo",
    "CH": "Switzerland", "CI": "C\u00f4te d'Ivoire", "CK": "Cook Islands", "CL": "Chile",
    "CM": "Cameroon", "CN": "China", "CO": "Colombia", "CR": "Costa Rica", "CU": "Cuba",
    "CV": "Cape Verde", "CW": "Cura\u00e7ao", "CX": "Christmas Island", "CY": "Cyprus",
    "CZ": "Czech Republic", "DE": "Germany", "DJ": "Djibouti", "DK": "Denmark", "DM": "Dominica",
    "DO": "Dominican Republic", "DZ": "Algeria", "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt",
    "EH": "Western Sahara", "ER": "Eritrea", "ES": "Spain", "ET": "Ethiopia", "FI": "Finland",
    "FJ": "Fiji", "FK": "Falkland Islands", "FM": "Micronesia", "FO": "Faroe Islands",
    "FR": "France", "GA": "Gabon", "GB": "United Kingdom", "GD": "Grenada", "GE": "Georgia",
    "GF": "French Guiana", "GG": "Guernsey", "GH": "Ghana", "GI": "Gibraltar", "GL": "Greenland",
    "GM": "Gambia", "GN": "Guinea", "GP": "Guadeloupe", "GQ": "Equatorial Guinea", "GR": "Greece",
    "GS": "South Georgia", "GT": "Guatemala", "GU": "Guam", "GW": "Guinea-Bissau", "GY": "Guyana",
    "HK": "Hong Kong", "HM": "Heard Island", "HN": "Honduras", "HR": "Croatia", "HT": "Haiti",
    "HU": "Hungary", "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IM": "Isle of Man",
    "IN": "India", "IO": "British Indian Ocean Territory", "IQ": "Iraq", "IR": "Iran",
    "IS": "Iceland", "IT": "Italy", "JE": "Jersey", "JM": "Jamaica", "JO": "Jordan",
    "JP": "Japan", "KE": "Kenya", "KG": "Kyrgyzstan", "KH": "Cambodia", "KI": "Kiribati",
    "KM": "Comoros", "KN": "Saint Kitts and Nevis", "KP": "North Korea", "KR": "South Korea",
    "KW": "Kuwait", "KY": "Cayman Islands", "KZ": "Kazakhstan", "LA": "Laos", "LB": "Lebanon",
    "LC": "Saint Lucia", "LI": "Liechtenstein", "LK": "Sri Lanka", "LR": "Liberia",
    "LS": "Lesotho", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia", "LY": "Libya",
    "MA": "Morocco", "MC": "Monaco", "MD": "Moldova", "ME": "Montenegro", "MF": "Saint Martin",
    "MG": "Madagascar", "MH": "Marshall Islands", "MK": "North Macedonia", "ML": "Mali",
    "MM": "Myanmar", "MN": "Mongolia", "MO": "Macau", "MP": "Northern Mariana Islands",
    "MQ": "Martinique", "MR": "Mauritania", "MS": "Montserrat", "MT": "Malta", "MU": "Mauritius",
    "MV": "Maldives", "MW": "Malawi", "MX": "Mexico", "MY": "Malaysia", "MZ": "Mozambique",
    "NA": "Namibia", "NC": "New Caledonia", "NE": "Niger", "NF": "Norfolk Island",
    "NG": "Nigeria", "NI": "Nicaragua", "NL": "Netherlands", "NO": "Norway", "NP": "Nepal",
    "NR": "Nauru", "NU": "Niue", "NZ": "New Zealand", "OM": "Oman", "PA": "Panama",
    "PE": "Peru", "PF": "French Polynesia", "PG": "Papua New Guinea", "PH": "Philippines",
    "PK": "Pakistan", "PL": "Poland", "PM": "Saint Pierre and Miquelon", "PN": "Pitcairn Islands",
    "PR": "Puerto Rico", "PS": "Palestine", "PT": "Portugal", "PW": "Palau", "PY": "Paraguay",
    "QA": "Qatar", "RE": "R\u00e9union", "RO": "Romania", "RS": "Serbia", "RU": "Russia",
    "RW": "Rwanda", "SA": "Saudi Arabia", "SB": "Solomon Islands", "SC": "Seychelles",
    "SD": "Sudan", "SE": "Sweden", "SG": "Singapore", "SH": "Saint Helena",
    "SI": "Slovenia", "SJ": "Svalbard", "SK": "Slovakia", "SL": "Sierra Leone",
    "SM": "San Marino", "SN": "Senegal", "SO": "Somalia", "SR": "Suriname", "SS": "South Sudan",
    "ST": "S\u00e3o Tom\u00e9 and Pr\u00edncipe", "SV": "El Salvador", "SX": "Sint Maarten", "SY": "Syria",
    "SZ": "Eswatini", "TC": "Turks and Caicos Islands", "TD": "Chad",
    "TF": "French Southern Territories", "TG": "Togo", "TH": "Thailand", "TJ": "Tajikistan",
    "TK": "Tokelau", "TL": "Timor-Leste", "TM": "Turkmenistan", "TN": "Tunisia", "TO": "Tonga",
    "TR": "Turkey", "TT": "Trinidad and Tobago", "TV": "Tuvalu", "TW": "Taiwan",
    "TZ": "Tanzania", "UA": "Ukraine", "UG": "Uganda", "UM": "US Minor Outlying Islands",
    "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan", "VA": "Vatican City",
    "VC": "Saint Vincent", "VE": "Venezuela", "VG": "British Virgin Islands",
    "VI": "US Virgin Islands", "VN": "Vietnam", "VU": "Vanuatu", "WF": "Wallis and Futuna",
    "WS": "Samoa", "XK": "Kosovo", "YE": "Yemen", "YT": "Mayotte", "ZA": "South Africa",
    "ZM": "Zambia", "ZW": "Zimbabwe",
}

# ── Grid ──────────────────────────────────────────────────────────────

def make_grid(step: float) -> List[Tuple[float, float]]:
    lats = np.arange(-80, 80 + step / 2, step)
    lons = np.arange(-180, 180 + step / 2, step)
    return [(float(lat), float(lon)) for lat in lats for lon in lons]


# ── Cities ────────────────────────────────────────────────────────────

_cities_cache: dict | None = None


def _load_cities() -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
    global _cities_cache
    if _cities_cache is not None:
        return _cities_cache["lat"], _cities_cache["lon"], _cities_cache["names"], _cities_cache["countries"]

    import json
    lats, lons, names, countries = [], [], [], []
    with open(CITIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for row in data:
        try:
            lats.append(float(row["lat"]))
            lons.append(float(row["lon"]))
            names.append(row["city"])
            countries.append(row["country"])
        except (ValueError, KeyError):
            continue

    result = {
        "lat": np.array(lats),
        "lon": np.array(lons),
        "names": names,
        "countries": countries,
    }
    _cities_cache = result
    return result["lat"], result["lon"], names, countries


# ── HF Computation ───────────────────────────────────────────────────

def compute_field(
    birth_dt: datetime,
    natal_lat: float,
    natal_lon: float,
    grid: List[Tuple[float, float]],
) -> Tuple[Dict[str, float], List[dict]]:
    """Compute natal HF + full relocation grid. Returns (natal_metrics, rows)."""
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=timezone.utc)

    chart = chart_json(natal_lat, natal_lon, birth_dt)
    planet_pos = {p.name: float(p.lon) for p in chart.planets}

    # Natal HF
    natal_houses = calculate_houses(birth_dt, natal_lat, natal_lon, HOUSE_SYSTEM_PLACIDUS)
    natal_angles = dict(planet_pos)
    natal_angles["ASC"] = float(natal_houses["asc"])
    natal_angles["MC"] = float(natal_houses["mc"])
    natal_cusps = list(natal_houses["cusps"])
    natal_hf = compute_hf_v3(natal_angles, cusps=natal_cusps)
    natal_total = float(natal_hf["hf_total_v3"])

    rows: List[dict] = []
    for rlat, rlon in grid:
        try:
            h = calculate_houses(birth_dt, rlat, rlon, HOUSE_SYSTEM_PLACIDUS)
            cusps = list(h["cusps"])
            angles = dict(planet_pos)
            angles["ASC"] = float(h["asc"])
            angles["MC"] = float(h["mc"])
            hf = compute_hf_v3(angles, cusps=cusps)
            total = float(hf["hf_total_v3"])
            rows.append({
                "lat": rlat, "lon": rlon,
                "hf_total": round(total, 4),
                "delta_hf": round(total - natal_total, 4),
                "hf_aspects": round(float(hf["hf_aspects"]), 4),
                "hf_angles": round(float(hf["hf_angles"]), 4),
                "hf_houses": round(float(hf["hf_houses"]), 4),
                "asc_lon": round(float(h["asc"]), 4),
                "mc_lon": round(float(h["mc"]), 4),
            })
        except Exception:
            rows.append({
                "lat": rlat, "lon": rlon,
                "hf_total": natal_total, "delta_hf": 0.0,
                "hf_aspects": 0, "hf_angles": 0, "hf_houses": 0,
                "asc_lon": 0, "mc_lon": 0,
            })

    natal_metrics = {
        "hf_total_v3": natal_total,
        "hf_aspects": float(natal_hf["hf_aspects"]),
        "hf_angles": float(natal_hf["hf_angles"]),
        "hf_houses": float(natal_hf["hf_houses"]),
    }
    return natal_metrics, rows


# ── GeoJSON ───────────────────────────────────────────────────────────

def build_geojson(rows: List[dict]) -> dict:
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                k: r[k]
                for k in ("hf_total", "delta_hf", "hf_aspects", "hf_angles", "hf_houses")
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features}


# ── Ranking (deduped by city) ─────────────────────────────────────────

def make_ranking(rows: List[dict], top_n: int = 20) -> List[dict]:
    c_lat, c_lon, c_names, c_countries = _load_cities()

    sorted_rows = sorted(rows, key=lambda r: r["hf_total"], reverse=True)
    candidates = sorted_rows[: top_n * 5]

    seen: dict[str, dict] = {}
    for r in candidates:
        dlat = np.radians(c_lat - r["lat"])
        dlon = np.radians(c_lon - r["lon"])
        a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(r["lat"])) * np.cos(np.radians(c_lat)) * np.sin(dlon / 2) ** 2
        dist = 6371.0 * 2 * np.arcsin(np.sqrt(a))
        idx = int(np.argmin(dist))
        city_key = f"{c_names[idx]}|{c_countries[idx]}"

        if city_key in seen and seen[city_key]["hf_total_v3"] >= r["hf_total"]:
            continue

        iso2 = c_countries[idx]
        seen[city_key] = {
            "relocation_latitude": r["lat"],
            "relocation_longitude": r["lon"],
            "hf_total_v3": r["hf_total"],
            "hf_aspects": r["hf_aspects"],
            "hf_angles": r["hf_angles"],
            "hf_houses": r["hf_houses"],
            "asc_lon": r["asc_lon"],
            "mc_lon": r["mc_lon"],
            "city": c_names[idx],
            "country": _ISO2_TO_COUNTRY.get(iso2, iso2),
            "country_code": iso2,
            "city_lat": float(c_lat[idx]),
            "city_lon": float(c_lon[idx]),
            "distance_km": round(float(dist[idx]), 2),
        }

    return sorted(seen.values(), key=lambda x: x["hf_total_v3"], reverse=True)[:top_n]


# ── Main entry point ─────────────────────────────────────────────────

def compute_relocation(
    birth_dt: datetime,
    natal_lat: float,
    natal_lon: float,
    step: float = 5.0,
    top_n: int = 20,
) -> dict:
    """Full relocation pipeline: grid → HF field → GeoJSON + ranking."""
    grid = make_grid(step)
    natal_metrics, rows = compute_field(birth_dt, natal_lat, natal_lon, grid)
    geojson = build_geojson(rows)
    rankings = make_ranking(rows, top_n)

    max_hf = max((r["hf_total"] for r in rows), default=natal_metrics["hf_total_v3"])

    return {
        "geojson": geojson,
        "rankings": rankings,
        "natal_hf": natal_metrics["hf_total_v3"],
        "max_hf": round(max_hf, 4),
        "grid_points": len(grid),
    }
