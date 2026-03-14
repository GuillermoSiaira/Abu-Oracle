"""Enrich raw_birthdata.jsonl with reverse geocoding and inferred Rodden rating.

Adds:
  - city            (from reverse_geocoder, offline GeoNames 150K+ places)
  - country         (full country name via pycountry or mapping)
  - country_code    (ISO 3166-1 alpha-2)
  - rodden_rating   (inferred from source + time_precision)

Usage:
    python scripts/enrich_birthdata.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import reverse_geocoder as rg

# ─── Paths ───────────────────────────────────────────────────────────────
INPUT  = Path("data/raw/raw_birthdata.jsonl")
OUTPUT = Path("data/raw/raw_birthdata_enriched.jsonl")

# ─── Country code → country name (top ~60, rest via cc) ─────────────────
CC_TO_COUNTRY = {
    "AD": "Andorra", "AE": "Emiratos Árabes Unidos", "AF": "Afganistán",
    "AG": "Antigua y Barbuda", "AL": "Albania", "AM": "Armenia",
    "AO": "Angola", "AR": "Argentina", "AT": "Austria", "AU": "Australia",
    "AZ": "Azerbaiyán", "BA": "Bosnia y Herzegovina", "BB": "Barbados",
    "BD": "Bangladés", "BE": "Bélgica", "BF": "Burkina Faso",
    "BG": "Bulgaria", "BH": "Baréin", "BI": "Burundi", "BJ": "Benín",
    "BN": "Brunéi", "BO": "Bolivia", "BR": "Brasil", "BS": "Bahamas",
    "BT": "Bután", "BW": "Botsuana", "BY": "Bielorrusia", "BZ": "Belice",
    "CA": "Canadá", "CD": "Rep. Dem. del Congo", "CF": "Rep. Centroafricana",
    "CG": "Congo", "CH": "Suiza", "CI": "Costa de Marfil", "CL": "Chile",
    "CM": "Camerún", "CN": "China", "CO": "Colombia", "CR": "Costa Rica",
    "CU": "Cuba", "CV": "Cabo Verde", "CY": "Chipre", "CZ": "Chequia",
    "DE": "Alemania", "DJ": "Yibuti", "DK": "Dinamarca", "DM": "Dominica",
    "DO": "Rep. Dominicana", "DZ": "Argelia", "EC": "Ecuador", "EE": "Estonia",
    "EG": "Egipto", "ER": "Eritrea", "ES": "España", "ET": "Etiopía",
    "FI": "Finlandia", "FJ": "Fiyi", "FR": "Francia", "GA": "Gabón",
    "GB": "Reino Unido", "GE": "Georgia", "GH": "Ghana", "GN": "Guinea",
    "GQ": "Guinea Ecuatorial", "GR": "Grecia", "GT": "Guatemala",
    "GW": "Guinea-Bisáu", "GY": "Guyana", "HK": "Hong Kong",
    "HN": "Honduras", "HR": "Croacia", "HT": "Haití", "HU": "Hungría",
    "ID": "Indonesia", "IE": "Irlanda", "IL": "Israel", "IN": "India",
    "IQ": "Irak", "IR": "Irán", "IS": "Islandia", "IT": "Italia",
    "JM": "Jamaica", "JO": "Jordania", "JP": "Japón", "KE": "Kenia",
    "KG": "Kirguistán", "KH": "Camboya", "KP": "Corea del Norte",
    "KR": "Corea del Sur", "KW": "Kuwait", "KZ": "Kazajistán",
    "LA": "Laos", "LB": "Líbano", "LI": "Liechtenstein", "LK": "Sri Lanka",
    "LR": "Liberia", "LS": "Lesoto", "LT": "Lituania", "LU": "Luxemburgo",
    "LV": "Letonia", "LY": "Libia", "MA": "Marruecos", "MC": "Mónaco",
    "MD": "Moldavia", "ME": "Montenegro", "MG": "Madagascar", "MK": "Macedonia del Norte",
    "ML": "Malí", "MM": "Myanmar", "MN": "Mongolia", "MO": "Macao",
    "MR": "Mauritania", "MT": "Malta", "MU": "Mauricio", "MV": "Maldivas",
    "MW": "Malaui", "MX": "México", "MY": "Malasia", "MZ": "Mozambique",
    "NA": "Namibia", "NE": "Níger", "NG": "Nigeria", "NI": "Nicaragua",
    "NL": "Países Bajos", "NO": "Noruega", "NP": "Nepal", "NZ": "Nueva Zelanda",
    "OM": "Omán", "PA": "Panamá", "PE": "Perú", "PG": "Papúa Nueva Guinea",
    "PH": "Filipinas", "PK": "Pakistán", "PL": "Polonia", "PR": "Puerto Rico",
    "PS": "Palestina", "PT": "Portugal", "PY": "Paraguay", "QA": "Catar",
    "RO": "Rumania", "RS": "Serbia", "RU": "Rusia", "RW": "Ruanda",
    "SA": "Arabia Saudita", "SC": "Seychelles", "SD": "Sudán", "SE": "Suecia",
    "SG": "Singapur", "SI": "Eslovenia", "SK": "Eslovaquia", "SL": "Sierra Leona",
    "SM": "San Marino", "SN": "Senegal", "SO": "Somalia", "SR": "Surinam",
    "SS": "Sudán del Sur", "SV": "El Salvador", "SY": "Siria",
    "SZ": "Esuatini", "TD": "Chad", "TG": "Togo", "TH": "Tailandia",
    "TJ": "Tayikistán", "TL": "Timor Oriental", "TM": "Turkmenistán",
    "TN": "Túnez", "TO": "Tonga", "TR": "Turquía", "TT": "Trinidad y Tobago",
    "TW": "Taiwán", "TZ": "Tanzania", "UA": "Ucrania", "UG": "Uganda",
    "US": "Estados Unidos", "UY": "Uruguay", "UZ": "Uzbekistán",
    "VA": "Ciudad del Vaticano", "VE": "Venezuela", "VN": "Vietnam",
    "YE": "Yemen", "ZA": "Sudáfrica", "ZM": "Zambia", "ZW": "Zimbabue",
    # Territories / special
    "GF": "Guayana Francesa", "GP": "Guadalupe", "MQ": "Martinica",
    "NC": "Nueva Caledonia", "PF": "Polinesia Francesa", "RE": "Reunión",
    "VI": "Islas Vírgenes de EE.UU.", "AS": "Samoa Americana",
    "GU": "Guam", "MP": "Islas Marianas del Norte", "AW": "Aruba",
    "CW": "Curazao", "SX": "Sint Maarten", "BM": "Bermudas",
    "KY": "Islas Caimán", "TC": "Islas Turcas y Caicos",
    "FK": "Islas Malvinas", "GI": "Gibraltar", "IM": "Isla de Man",
    "JE": "Jersey", "GG": "Guernsey",
}


def country_name(cc: str) -> str:
    """Return Spanish country name for ISO alpha-2 code."""
    return CC_TO_COUNTRY.get(cc, cc)


# ─── Rodden rating inference ────────────────────────────────────────────

# Patterns matched in order; first match wins.
_RODDEN_RULES: list[tuple[str, str]] = [
    # AA — Official birth record
    (r"(?i)certificado|registro\s+de?\s*nacimiento|partida\s+de\s*nacimiento", "AA"),
    # A — From memory
    (r"(?i)^memorias?$|^mamorias$", "A"),
    # B — Biography, database, interview, school, astrologer, news
    (r"(?i)bio|autobiograf|noticias|entrevista|cartas\s+natales|astrodatabank|astro[\-\s]?databank|escuela|astrotheme|astro\.com|astro[\-\s]?sesam|wikipedia|youtube|twitter|blog", "B"),
    # C — Unconfirmed, approximate, rectified
    (r"(?i)sin\s+con?firmar|hora\s+(sin\s+con?firmar|aproximad)|fecha\s+sin\s+con?firmar|fecha\s+y\s+hora\s+sin|rectific", "C"),
    # DD — Conflicting data
    (r"(?i)contradictor|en\s+discusi[oó]n|confuso", "DD"),
]


def infer_rodden(source: str | None, time_precision: str | None) -> str:
    """Infer Rodden-style rating from source text and time precision."""
    if source is None:
        return "XX"

    rating = "B"  # default for named astrologers / misc sources
    for pattern, grade in _RODDEN_RULES:
        if re.search(pattern, source):
            rating = grade
            break

    # Downgrade one level if time precision is unknown
    if time_precision == "unknown":
        _downgrade = {"AA": "A", "A": "B", "B": "C", "C": "DD", "DD": "DD", "XX": "XX"}
        rating = _downgrade.get(rating, rating)

    return rating


# ─── Main ────────────────────────────────────────────────────────────────

def main() -> None:
    records: list[dict] = []
    with open(INPUT, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    print(f"Loaded {len(records)} records from {INPUT}")

    # --- Reverse geocoding (batch) ---
    coords_with_idx: list[tuple[int, float, float]] = []
    for i, rec in enumerate(records):
        lat, lon = rec.get("latitude"), rec.get("longitude")
        if lat is not None and lon is not None:
            coords_with_idx.append((i, lat, lon))

    print(f"Reverse geocoding {len(coords_with_idx)} coordinates...")
    # reverse_geocoder accepts list of (lat, lon) tuples
    query = [(lat, lon) for _, lat, lon in coords_with_idx]
    results = rg.search(query)

    for (idx, _, _), geo in zip(coords_with_idx, results):
        records[idx]["city"] = geo.get("name")
        cc = geo.get("cc", "")
        records[idx]["country_code"] = cc
        records[idx]["country"] = country_name(cc)

    geocoded = len(coords_with_idx)
    no_coords = len(records) - geocoded
    print(f"  Geocoded: {geocoded}, sin coordenadas: {no_coords}")

    # --- Rodden rating inference ---
    from collections import Counter
    rating_dist = Counter()
    for rec in records:
        rating = infer_rodden(rec.get("source"), rec.get("time_precision"))
        rec["rodden_rating"] = rating
        rating_dist[rating] += 1

    print(f"\nRodden rating distribution:")
    for r in ["AA", "A", "B", "C", "DD", "XX"]:
        print(f"  {r:>3}: {rating_dist.get(r, 0):>5}")

    # --- Country distribution (top 20) ---
    country_dist = Counter(r.get("country") for r in records if r.get("country"))
    print(f"\nTop 20 countries:")
    for c_name, cnt in country_dist.most_common(20):
        print(f"  {cnt:>5}  {c_name}")

    # --- Write enriched output ---
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nEnriched dataset written to {OUTPUT}")
    print(f"Total records: {len(records)}")


if __name__ == "__main__":
    main()
