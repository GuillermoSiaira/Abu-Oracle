"""Data models for biographical events (mirrors gold_standard JSON schema v1.2)."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, List
import json

VALID_EVENT_TYPES = {
    "death", "birth_child", "marriage", "divorce", "relocation",
    "professional_milestone", "award", "publication", "exhibition",
    "health_critical", "psychological_crisis", "accident",
    "political_event", "arrest", "exile", "legal",
    "artistic_creation", "discovery", "invention",
    "financial_crisis", "financial_success",
    "relationship_start", "relationship_end",
    "education_start", "education_end",
    "military_service", "retirement",
}

VALID_VALENCE = {"positive", "negative", "neutral"}
VALID_CONFIDENCE = {"high", "medium", "low"}


@dataclass
class Location:
    city: str
    country: str
    lat: Optional[float] = None
    lon: Optional[float] = None


@dataclass
class ValidationTarget:
    axiom_id: Optional[str] = None
    label: Optional[str] = None


@dataclass
class BioEvent:
    date: str  # YYYY-MM-DD
    event_type: str
    description: str
    valence: str = "neutral"
    confidence: str = "medium"
    location: Optional[Location] = None
    validation_target: Optional[ValidationTarget] = None

    def validate(self) -> List[str]:
        errors = []
        if self.event_type not in VALID_EVENT_TYPES:
            errors.append(f"Invalid event_type: {self.event_type}")
        if self.valence not in VALID_VALENCE:
            errors.append(f"Invalid valence: {self.valence}")
        if self.confidence not in VALID_CONFIDENCE:
            errors.append(f"Invalid confidence: {self.confidence}")
        if not self.date or len(self.date) < 4:
            errors.append(f"Invalid date: {self.date}")
        return errors

    def to_dict(self) -> dict:
        d: dict = {
            "date": self.date,
            "event_type": self.event_type,
            "description": self.description,
            "valence": self.valence,
            "confidence": self.confidence,
        }
        if self.location:
            d["location"] = asdict(self.location)
        if self.validation_target:
            d["validation_target"] = asdict(self.validation_target)
        return d


@dataclass
class SubjectMeta:
    id: str
    name: str
    source_origin: str = "Wikipedia + Wikidata"
    schema_version: str = "1.2"


@dataclass
class BioEventFile:
    meta: SubjectMeta
    biographical_events: List[BioEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "meta": asdict(self.meta),
            "biographical_events": [e.to_dict() for e in self.biographical_events],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
