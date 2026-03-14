"""Subject list: 26 subjects with Wikidata Q-IDs and Wikipedia titles."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Subject:
    id: str
    slug: str
    name: str
    birth_date: str  # YYYY-MM-DD
    wikidata_qid: str
    wikipedia_title: str  # English Wikipedia article title
    wikipedia_title_es: Optional[str] = None  # Spanish Wikipedia if richer


SUBJECTS: list[Subject] = [
    # --- Gold Standard (ampliar) ---
    Subject(
        id="GS_001", slug="jung", name="Carl Gustav Jung",
        birth_date="1875-07-26", wikidata_qid="Q38193",
        wikipedia_title="Carl_Jung",
        wikipedia_title_es="Carl_Gustav_Jung",
    ),
    Subject(
        id="GS_002", slug="tesla", name="Nikola Tesla",
        birth_date="1856-07-10", wikidata_qid="Q9036",
        wikipedia_title="Nikola_Tesla",
    ),
    Subject(
        id="GS_003", slug="turing", name="Alan Turing",
        birth_date="1912-06-23", wikidata_qid="Q7251",
        wikipedia_title="Alan_Turing",
    ),
    # --- Demo pack ---
    Subject(
        id="308660", slug="einstein", name="Albert Einstein",
        birth_date="1879-03-14", wikidata_qid="Q937",
        wikipedia_title="Albert_Einstein",
    ),
    Subject(
        id="12145", slug="borges", name="Jorge Luis Borges",
        birth_date="1899-08-24", wikidata_qid="Q44326",
        wikipedia_title="Jorge_Luis_Borges",
    ),
    Subject(
        id="35255", slug="frida", name="Frida Kahlo",
        birth_date="1907-07-06", wikidata_qid="Q5588",
        wikipedia_title="Frida_Kahlo",
    ),
    Subject(
        id="76835", slug="picasso", name="Pablo Picasso",
        birth_date="1881-10-25", wikidata_qid="Q5593",
        wikipedia_title="Pablo_Picasso",
    ),
    Subject(
        id="317785", slug="vangogh", name="Vincent van Gogh",
        birth_date="1853-03-30", wikidata_qid="Q5582",
        wikipedia_title="Vincent_van_Gogh",
    ),
    Subject(
        id="337730", slug="freud", name="Sigmund Freud",
        birth_date="1856-05-06", wikidata_qid="Q9215",
        wikipedia_title="Sigmund_Freud",
    ),
    Subject(
        id="61360", slug="gandhi", name="Mohandas Gandhi",
        birth_date="1869-10-02", wikidata_qid="Q1001",
        wikipedia_title="Mahatma_Gandhi",
    ),
    Subject(
        id="232650", slug="bowie", name="David Bowie",
        birth_date="1947-01-08", wikidata_qid="Q5383",
        wikipedia_title="David_Bowie",
    ),
    # --- Expansion wave (Session 8) ---
    Subject(
        id="16510", slug="monroe", name="Marilyn Monroe",
        birth_date="1926-06-01", wikidata_qid="Q4616",
        wikipedia_title="Marilyn_Monroe",
    ),
    Subject(
        id="232580", slug="elvis", name="Elvis Presley",
        birth_date="1935-01-08", wikidata_qid="Q303",
        wikipedia_title="Elvis_Presley",
    ),
    Subject(
        id="239610", slug="ali", name="Muhammad Ali",
        birth_date="1942-01-17", wikidata_qid="Q36107",
        wikipedia_title="Muhammad_Ali",
    ),
    Subject(
        id="99835", slug="hendrix", name="Jimi Hendrix",
        birth_date="1942-11-27", wikidata_qid="Q5928",
        wikipedia_title="Jimi_Hendrix",
    ),
    Subject(
        id="240895", slug="joplin", name="Janis Joplin",
        birth_date="1943-01-19", wikidata_qid="Q1514",
        wikipedia_title="Janis_Joplin",
    ),
    Subject(
        id="106715", slug="morrison", name="Jim Morrison",
        birth_date="1943-12-08", wikidata_qid="Q44301",
        wikipedia_title="Jim_Morrison",
    ),
    Subject(
        id="288130", slug="dean", name="James Dean",
        birth_date="1931-02-08", wikidata_qid="Q83359",
        wikipedia_title="James_Dean",
    ),
    Subject(
        id="349770", slug="miles", name="Miles Davis",
        birth_date="1926-05-26", wikidata_qid="Q93341",
        wikipedia_title="Miles_Davis",
    ),
    Subject(
        id="2280", slug="armstrong", name="Neil Armstrong",
        birth_date="1930-08-05", wikidata_qid="Q1615",
        wikipedia_title="Neil_Armstrong",
    ),
    Subject(
        id="99810", slug="brucelee", name="Bruce Lee",
        birth_date="1940-11-27", wikidata_qid="Q16397",
        wikipedia_title="Bruce_Lee",
    ),
    Subject(
        id="113610", slug="piaf", name="Edith Piaf",
        birth_date="1915-12-19", wikidata_qid="Q1631",
        wikipedia_title="Edith_Piaf",
    ),
    Subject(
        id="336770", slug="hepburn", name="Audrey Hepburn",
        birth_date="1929-05-04", wikidata_qid="Q30875",
        wikipedia_title="Audrey_Hepburn",
    ),
    Subject(
        id="14525", slug="bergman", name="Ingrid Bergman",
        birth_date="1915-08-29", wikidata_qid="Q43247",
        wikipedia_title="Ingrid_Bergman",
    ),
    Subject(
        id="9945", slug="chanel", name="Coco Chanel",
        birth_date="1883-08-19", wikidata_qid="Q45661",
        wikipedia_title="Coco_Chanel",
    ),
    Subject(
        id="70110", slug="wilde", name="Oscar Wilde",
        birth_date="1854-10-16", wikidata_qid="Q1267",
        wikipedia_title="Oscar_Wilde",
    ),
]


def get_subject(slug: str) -> Subject | None:
    return next((s for s in SUBJECTS if s.slug == slug), None)
