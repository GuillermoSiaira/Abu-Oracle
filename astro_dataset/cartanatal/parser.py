from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Optional, Tuple

from bs4 import BeautifulSoup

from .models import BirthRecord

DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
TIME_RE = re.compile(r"(\d{2}:\d{2}(?::\d{2})?)")
TZ_RE = re.compile(r"Zona Horaria:\s*UT\s*([+-]\d{1,2}:\d{2}:\d{2})", re.IGNORECASE)
LAT_RE = re.compile(r"Latitud:\s*([0-9 .°º′″'\"]+[NS])", re.IGNORECASE)
LON_RE = re.compile(r"Longitud:\s*([0-9 .°º′″'\"]+[EW])", re.IGNORECASE)
NAME_RE = re.compile(r"CARTA NATAL DE\s+(.+)", re.IGNORECASE)
RR_RE = re.compile(r"RR:\s*([A-Z]{1,2})")
SRC_RE = re.compile(r"Fuente:\s*([^\n]+)")
CITY_RE = re.compile(r"CARTA NATAL\s*([^\n]+?)Latitud:", re.IGNORECASE)


def _dms_to_decimal(value: str) -> Optional[float]:
    try:
        v = value.strip()
        sign = -1.0 if v.endswith(("S", "W")) else 1.0
        v = v.rstrip("NSEW ")
        # Normalize separators to spaces
        v = v.replace("°", " ").replace("º", " ").replace("′", " ").replace("″", " ")
        v = v.replace("'", " ").replace('"', " ")
        parts = [p for p in re.split(r"[^0-9.]+", v) if p]
        if not parts:
            return None
        deg = float(parts[0])
        minute = float(parts[1]) if len(parts) > 1 else 0.0
        second = float(parts[2]) if len(parts) > 2 else 0.0
        return sign * (deg + minute / 60.0 + second / 3600.0)
    except Exception:
        return None


def _parse_date(text: str) -> Optional[str]:
    m = DATE_RE.search(text)
    if not m:
        return None
    day, month, year = m.groups()
    try:
        return datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y").date().isoformat()
    except Exception:
        return None


def _parse_time(text: str) -> Tuple[Optional[str], str]:
    m = TIME_RE.search(text)
    if not m:
        return None, "unknown"
    raw = m.group(1)
    if "?" in raw:
        return None, "unknown"
    return raw, "exact"


def _parse_city_country(text: str) -> Tuple[Optional[str], Optional[str]]:
    m = CITY_RE.search(text)
    if not m:
        return None, None
    loc = m.group(1).strip()
    if "Latitud" in loc:
        loc = loc.split("Latitud")[0].strip()
    if "," in loc:
        city, country = loc.split(",", 1)
        return city.strip(), country.strip()
    return loc, None


def _hash_html(html: str) -> str:
    return "sha256:" + hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()


def parse_profile(html: str, profile_id: int, url: str) -> BirthRecord:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)

    name = None
    name_match = NAME_RE.search(text)
    if name_match:
        name = name_match.group(1).strip().title()

    birth_date = _parse_date(text)
    birth_time, time_precision = _parse_time(text)

    tz = None
    tz_match = TZ_RE.search(text)
    if tz_match:
        tz = tz_match.group(1).replace(" ", "")

    lat = None
    lon = None
    lat_match = LAT_RE.search(text)
    if lat_match:
        lat = _dms_to_decimal(lat_match.group(1))
    lon_match = LON_RE.search(text)
    if lon_match:
        lon = _dms_to_decimal(lon_match.group(1))

    city, country = _parse_city_country(text)

    rr = None
    rr_match = RR_RE.search(text)
    if rr_match:
        rr = rr_match.group(1)

    source = None
    src_match = SRC_RE.search(text)
    if src_match:
        source = src_match.group(1).strip()

    html_hash = _hash_html(html)

    return BirthRecord.with_timestamp(
        id=profile_id,
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        time_precision=time_precision,
        timezone=tz,
        latitude=lat,
        longitude=lon,
        city=city,
        country=country,
        rodden_rating=rr,
        source=source,
        url=url,
        scrape_source="carta-natal.es",
        scrape_version="v1",
        html_hash=html_hash,
    )
