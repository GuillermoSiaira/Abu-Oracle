# -*- coding: utf-8 -*-
"""Tests for the KG-C02 NetworkX chart graph builder."""

import sys
from pathlib import Path

ABU_DIR = Path(__file__).resolve().parents[1]
if str(ABU_DIR) not in sys.path:
    sys.path.insert(0, str(ABU_DIR))

from core.chart_graph import build_chart_graph, get_key_planets, serialize_subgraph


SAMPLE_CHART_JSON = {
    "chart": {
        "planets": [
            {"name": "Sol", "sign": "Piscis", "house": 12, "degree": 12.3, "longitude": 342.3},
            {
                "name": "Júpiter",
                "sign": "Cáncer",
                "house": 1,
                "degree": 3.4,
                "longitude": 93.4,
                "dignity": "exaltation",
            },
            {
                "name": "Saturno",
                "sign": "Leo",
                "house": 4,
                "degree": 18.2,
                "longitude": 138.2,
                "dignity": "detriment",
            },
        ],
        "houses": [
            {"house": 1, "sign": "Cáncer", "degree": 1.2},
            {"house": 10, "sign": "Aries", "degree": 5.6},
        ],
        "aspects": [
            {
                "planet_a": "Sol",
                "planet_b": "Júpiter",
                "type": "sextile",
                "orb": 2.1,
                "applying": True,
            },
        ],
    },
    "derived": {
        "profections": [
            {
                "house": 12,
                "sign": "Piscis",
                "lord": "Júpiter",
                "is_active": True,
                "date_end": "2026-07-05",
            }
        ],
        "firdaria": [
            {
                "major_planet": "Sol",
                "minor_planet": "Júpiter",
                "is_active": True,
                "date_end": "2026-04-05",
            }
        ],
        "lots": {
            "fortuna": {"sign": "Sagitario", "house": 6, "degree": 14.2, "lord": "Júpiter"},
        },
    },
}


def test_build_chart_graph_nodes():
    G = build_chart_graph(SAMPLE_CHART_JSON)

    assert G.has_node("Sol")
    assert G.has_node("Júpiter")
    assert G.has_node("Casa1")
    assert G.nodes["Júpiter"]["type"] == "planet"


def test_build_chart_graph_ocupa_edges():
    G = build_chart_graph(SAMPLE_CHART_JSON)

    assert G.has_edge("Sol", "Casa12")
    assert G.edges["Sol", "Casa12"]["relation"] == "ocupa"
    assert G.has_edge("Júpiter", "Casa1")


def test_build_chart_graph_aspect_edges_are_bidirectional():
    G = build_chart_graph(SAMPLE_CHART_JSON)

    assert G.has_edge("Sol", "Júpiter")
    assert G.has_edge("Júpiter", "Sol")
    assert G.edges["Sol", "Júpiter"]["relation"] == "aspecto"
    assert G.edges["Júpiter", "Sol"]["type"] == "sextile"


def test_build_chart_graph_layer3_profection():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    prof_edges = [
        (u, v, d)
        for u, v, d in G.edges(data=True)
        if d.get("relation") == "señor_del_año"
    ]

    assert len(prof_edges) >= 1
    assert any(u == "Júpiter" and v == "Casa12" for u, v, _ in prof_edges)


def test_build_chart_graph_layer3_asc_mc_and_lots():
    G = build_chart_graph(SAMPLE_CHART_JSON)

    assert G.edges["Luna", "Casa1"]["relation"] == "señor_ASC"
    assert G.edges["Marte", "Casa10"]["relation"] == "señor_MC"
    assert G.edges["Júpiter", "Lote_fortuna"]["relation"] == "señor_fortuna"


def test_get_key_planets():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    key = get_key_planets(G, SAMPLE_CHART_JSON["derived"])

    assert key[0] == "Júpiter"
    assert "Sol" in key
    assert key.count("Júpiter") == 1


def test_serialize_subgraph_not_empty():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    key = get_key_planets(G, SAMPLE_CHART_JSON["derived"])
    text = serialize_subgraph(G, key)

    assert "SEÑORÍOS ACTIVOS" in text
    assert "Júpiter" in text
    assert "señor_del_año" in text
    assert "sextile" in text


def test_serialize_subgraph_empty_key():
    G = build_chart_graph(SAMPLE_CHART_JSON)

    assert serialize_subgraph(G, []) == ""


def test_build_chart_graph_without_aspects_is_ok():
    abu_json = {
        "chart": {
            "planets": [{"name": "Sol", "sign": "Leo", "house": 1, "degree": 1.0}],
            "houses": [{"house": 1, "sign": "Leo", "degree": 0.0}],
        },
        "derived": {},
    }

    G = build_chart_graph(abu_json)

    assert G.has_node("Sol")
    assert G.has_edge("Sol", "Casa1")


def test_build_chart_graph_accepts_existing_analyze_house_shape():
    abu_json = {
        "chart": {
            "planets": [{"name": "Sun", "lon": 125.0, "sign": "Leo", "house": 1}],
            "houses": {
                "houses": [
                    {"house": 1, "start": 120.0, "end": 150.0},
                    {"house": 10, "start": 30.0, "end": 60.0},
                ]
            },
            "aspects": [{"a": "Sun", "b": "Jupiter", "type": "trine", "orb": 1.5}],
        },
        "derived": {"profection": {"house": 1, "sign": "Leo", "lord": "Sun"}},
    }

    G = build_chart_graph(abu_json)

    assert G.has_node("Sol")
    assert G.nodes["Casa1"]["sign"] == "Leo"
    assert G.has_edge("Sol", "Casa1")
