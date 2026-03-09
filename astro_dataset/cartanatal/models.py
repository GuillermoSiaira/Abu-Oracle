from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class BirthRecord:
    id: int
    name: Optional[str]
    birth_date: Optional[str]
    birth_time: Optional[str]
    time_precision: str
    timezone: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    city: Optional[str]
    country: Optional[str]
    rodden_rating: Optional[str]
    source: Optional[str]
    url: str
    scrape_timestamp: str
    scrape_source: str
    scrape_version: str
    html_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def with_timestamp(
        cls,
        *,
        id: int,
        name: Optional[str],
        birth_date: Optional[str],
        birth_time: Optional[str],
        time_precision: str,
        timezone: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
        city: Optional[str],
        country: Optional[str],
        rodden_rating: Optional[str],
        source: Optional[str],
        url: str,
        scrape_source: str,
        scrape_version: str,
        html_hash: str,
    ) -> "BirthRecord":
        return cls(
            id=id,
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            time_precision=time_precision,
            timezone=timezone,
            latitude=latitude,
            longitude=longitude,
            city=city,
            country=country,
            rodden_rating=rodden_rating,
            source=source,
            url=url,
            scrape_timestamp=datetime.utcnow().isoformat() + "Z",
            scrape_source=scrape_source,
            scrape_version=scrape_version,
            html_hash=html_hash,
        )
