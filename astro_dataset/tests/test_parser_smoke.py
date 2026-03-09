from pathlib import Path

from cartanatal.parser import parse_profile


def test_parse_profile_smoke():
    sample_html = (
        "<html><body><h2>CARTA NATAL DE TEST PERSON</h2>"
        "Latitud: 10°00′00″N Longitud: 020°00′00″W"
        "26/04/1912 10:30:00 (CST) Zona Horaria: UT -6:00:00 RR: AA Fuente: Test"
        "</body></html>"
    )
    record = parse_profile(sample_html, 999999, "https://carta-natal.es/astrodata/famosos/carta.php?id=999999")
    assert record.id == 999999
    assert record.name == "Test Person"
    assert record.birth_date == "1912-04-26"
    assert record.birth_time == "10:30:00"
    assert record.time_precision == "exact"
    assert record.timezone == "-6:00:00"
    assert record.latitude is not None
    assert record.longitude is not None
    assert record.rodden_rating == "AA"
    assert record.source == "Test"
    assert record.scrape_source == "carta-natal.es"
    assert record.scrape_version == "v1"
