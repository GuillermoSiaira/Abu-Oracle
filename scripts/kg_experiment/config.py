ABU_ENGINE_URL = "http://localhost:8000"

# Nota: las fechas se tratan como UTC para el experimento. Para los
# 3 sujetos históricos esto introduce un offset de ~0-1h respecto a
# su hora local real, pero el experimento mide la diferencia A vs B
# (misma fecha en ambas condiciones), así que el offset no afecta
# el resultado del A/B.
#
# SYNTH_001: carta sintética usada en KG-C03 v1..v5 (corridas 2026-05-18/19).
#   Originalmente mal etiquetada como "GS_004 — Guillermo Siaira" en config.py
#   desde commit f5f73db (2026-05-08). NO corresponde a la carta del autor.
#   Se conserva para reproducibilidad de los resultados publicados.
#
# GS_004: carta natal real del autor (Guillermo Siaira).
#   Fecha: 1978-07-05 21:15 hora local Balcarce (Argentina, UTC-3, sin DST en
#   1978) → 1978-07-06T00:15:00Z UTC. Coordenadas Balcarce: -37.8464, -58.2556.
#   Eventos biográficos verificados: data/biographical_events/GS_004_siaira.json
SUBJECTS = [
    {
        "id": "einstein",
        "birthDate": "1879-03-14T11:30:00Z",
        "lat": 48.4,
        "lon": 10.0,
        "name": "Einstein",
    },
    {
        "id": "jung",
        "birthDate": "1875-07-26T19:32:00Z",
        "lat": 47.5,
        "lon": 7.5,
        "name": "Jung",
    },
    {
        "id": "tesla",
        "birthDate": "1856-07-10T00:00:00Z",
        "lat": 44.3,
        "lon": 19.8,
        "name": "Tesla",
    },
    {
        "id": "synth001",
        "birthDate": "1983-10-10T08:20:00Z",  # 05:20 local Buenos Aires (UTC-3)
        "lat": -34.6,
        "lon": -58.4,
        "name": "SYNTH_001",
    },
    {
        "id": "gs004",
        "birthDate": "1978-07-06T00:15:00Z",  # 21:15 local Balcarce 1978-07-05 (UTC-3)
        "lat": -37.8464,
        "lon": -58.2556,
        "name": "GS_004",
    },
]

EVAL_PROMPT = """Un astrologo clasico recibe el siguiente contexto sobre una carta natal.
Responde como lo haria: menciona el senor del ano, la firdaria activa,
y como se relacionan con la vida del nativo ahora mismo. Maximo 200 palabras."""

JUDGE_CRITERIA = [
    "coherencia_doctrinal",
    "especificidad",
    "multi_hop_reasoning",
    "ausencia_de_generico",
    "sintesis",
]
