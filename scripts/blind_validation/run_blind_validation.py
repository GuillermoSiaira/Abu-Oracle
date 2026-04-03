"""
run_blind_validation.py — Protocolo de Validación Doctrinal por Carta Ciega

Ejecuta un experimento BV completo:
  1. Obtiene la carta natal extendida desde Abu Engine
  2. Genera lectura doctrinal con Lilly (Haiku para análisis batch)
  3. Guarda ficha BV_NNN_alias.md en data/blind_validation/
  4. Genera nota equivalente en obsidian_vault/03_experimentos/
  5. Actualiza BV_index.json

IMPORTANTE: subject_real nunca aparece en stdout. Solo en archivos internos.

Uso:
    python scripts/blind_validation/run_blind_validation.py \\
        --date 1946-06-14 --time 10:54 \\
        --lat 40.7128 --lon -74.0060 \\
        --alias "Mr. X" \\
        --subject-real "Donald Trump" \\
        --rodden AA
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "blind_validation"
OBSIDIAN_DIR = REPO_ROOT / "obsidian_vault" / "03_experimentos"
INDEX_PATH = DATA_DIR / "BV_index.json"

# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(REPO_ROOT / "next_app" / ".env.local")  # fallback
except ImportError:
    pass

ABU_ENGINE_URL = os.environ.get("ABU_ENGINE_URL", "http://localhost:8000")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Modelo para análisis batch — no producción
# Equivalente a selectModel() para rutas de baja complejidad doctrinal
BV_MODEL = "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Protocolo de carta ciega BV")
    p.add_argument("--date", required=True, help="Fecha de nacimiento YYYY-MM-DD")
    p.add_argument("--time", required=True, help="Hora local HH:MM")
    p.add_argument("--lat", required=True, type=float, help="Latitud decimal")
    p.add_argument("--lon", required=True, type=float, help="Longitud decimal")
    p.add_argument("--alias", default="Mr. X", help="Alias operativo (no revela identidad)")
    p.add_argument("--subject-real", required=True, help="Identidad real (solo registro interno)")
    p.add_argument("--rodden", default="?", help="Rodden Rating de los datos (AA/A/B/C)")
    p.add_argument(
        "--abu-url",
        default=None,
        help="URL base del Abu Engine (por defecto: ABU_ENGINE_URL env o localhost:8000)",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _next_bv_id() -> str:
    """Calcula el próximo ID autoincremental BV_NNN."""
    if not INDEX_PATH.exists():
        return "BV_001"
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not data:
        return "BV_001"
    nums = []
    for entry in data:
        m = re.match(r"BV_(\d+)", entry.get("id", ""))
        if m:
            nums.append(int(m.group(1)))
    return f"BV_{max(nums) + 1:03d}" if nums else "BV_001"


def _slug(alias: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", alias.lower()).strip("_")


def _fetch_chart_extended(
    birth_date: str, birth_time: str, lat: float, lon: float, abu_url: str
) -> dict:
    """Llama a /api/astro/chart/extended — sin auth (dev local, AUTH_ENABLED=false)."""
    import urllib.request
    import urllib.parse

    params = urllib.parse.urlencode(
        {
            "birthDate": f"{birth_date}T{birth_time}:00",
            "lat": lat,
            "lon": lon,
        }
    )
    url = f"{abu_url}/api/astro/chart/extended?{params}"
    print(f"[BV] Fetching chart: {url}", flush=True)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def _build_doctrinal_context(chart: dict, alias: str) -> str:
    """Construye el contextBlock para la lectura doctrinal ciega."""
    planets = chart.get("chart", {}).get("planets", [])
    asc_sign = chart.get("chart", {}).get("asc_sign", "?")
    mc_sign = chart.get("chart", {}).get("mc_sign", "?")
    sect = chart.get("chart", {}).get("sect", "?")
    profection = chart.get("derived", {}).get("profection", {})
    firdaria = chart.get("derived", {}).get("firdaria", {})

    planet_lines = []
    for p in planets:
        name = p.get("name", "?")
        sign = p.get("sign", "?")
        house = p.get("house", "?")
        dignity = p.get("dignity_traditional", p.get("dignity", "?"))
        retro = " ℞" if p.get("retrograde") else ""
        planet_lines.append(f"  {name}: {sign} H{house} ({dignity}){retro}")

    prof_house = profection.get("annual_house", "?")
    prof_lord = profection.get("annual_lord", "?")
    fird_major = firdaria.get("major_planet", "?")
    fird_minor = firdaria.get("minor_planet", "?")
    fird_end = firdaria.get("end_date", "?")

    return f"""╔══ CARTA NATAL — {alias} ══╗
Secta: {sect}
ASC: {asc_sign} · MC: {mc_sign}

PLANETAS:
{chr(10).join(planet_lines)}

PROFECCIÓN ANUAL:
  Casa activa: H{prof_house} · Señor del año: {fird_major}

FIRDARIA ACTIVO:
  Mayor: {fird_major} · Menor: {fird_minor} · Cierre: {fird_end}

TAREA:
Lee esta carta como si no conocieras la identidad del nativo.
Proporciona:
1. Perfil de carácter (secta, benéfico/maléfico dominante, disposición general)
2. Dominio de vida más activo y comprometido
3. Período temporal más crítico en los próximos 18 meses y por qué
4. Señor del año: qué tipo de año indica esta profección
5. Una configuración natal que consideres la más determinante de la vida del nativo

Responde con rigor doctrinal persa-helenístico. Máximo 400 palabras.
"""


def _call_lilly(context_block: str) -> str:
    """Llama a Anthropic Haiku con el contextBlock doctrinal."""
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=BV_MODEL,
        max_tokens=600,
        system=(
            "Eres Lilly, un agente de astrología helenística y persa medieval. "
            "Tu voz sigue a William Lilly (1647) y Abu Mashar. "
            "Derivas toda afirmación de la geometría natal — no de conocimiento externo. "
            "El nativo que lees es desconocido para ti. Opera solo con los datos que recibes."
        ),
        messages=[{"role": "user", "content": context_block}],
    )
    return response.content[0].text if response.content else ""


def _render_bv_md(
    bv_id: str,
    alias: str,
    subject_real: str,
    rodden: str,
    birth_date: str,
    birth_time: str,
    lat: float,
    lon: float,
    chart: dict,
    lilly_reading: str,
    experiment_date: str,
) -> str:
    """Genera el contenido Markdown de la ficha BV (versión data/)."""
    asc_sign = chart.get("chart", {}).get("asc_sign", "?")
    sect = chart.get("chart", {}).get("sect", "?")

    return f"""# {bv_id} — Carta Ciega: {alias}

> **ID:** {bv_id}
> **Alias operativo:** {alias}
> **Identidad real:** {subject_real} *(solo para registro interno — no revelar en ejecución del protocolo)*
> **Fecha del experimento:** {experiment_date}
> **Estado:** Completado (pendiente verificación manual)
> **Rodden Rating:** {rodden}

---

## Datos de carta

| Campo | Valor |
|---|---|
| Fecha de nacimiento | {birth_date} |
| Hora | {birth_time} |
| Latitud | {lat} |
| Longitud | {lon} |
| Rodden Rating | {rodden} |
| Tipo de carta | {sect} |
| Ascendente | {asc_sign} |

---

## Lectura doctrinal de Lilly (carta ciega)

*Generada por `{BV_MODEL}` — alias activo: {alias} — identidad no revelada al modelo*

{lilly_reading}

---

## Verificación del operador

> Completar esta sección tras confrontar la lectura con hechos biográficos verificables.

| Dimensión | Inferencia de Lilly | Score | Verificación |
|---|---|---|---|
| Perfil de carácter | *(extraer de la lectura)* | ⏳ | |
| Dominio dominante | *(extraer de la lectura)* | ⏳ | |
| Período de crisis/auge | *(extraer de la lectura)* | ⏳ | |
| Señor del año | *(extraer de la lectura)* | ⏳ | |
| Configuración determinante | *(extraer de la lectura)* | ⏳ | |

**Score final:** ?/5 · **¿Valida?** Pendiente

**Leyenda:** ✅ Alta coherencia · ⚠️ Coherencia parcial · ❌ Divergencia · ⏳ Pendiente

---

## Observaciones

*(Completar tras la verificación)*

---

*Generado automáticamente por `scripts/blind_validation/run_blind_validation.py` — {experiment_date}*
*Protocolo completo: `BLIND_VALIDATION_PROTOCOL.md`*
"""


def _render_obsidian_md(
    bv_id: str,
    alias: str,
    subject_real: str,
    rodden: str,
    birth_date: str,
    birth_time: str,
    chart: dict,
    lilly_reading: str,
    experiment_date: str,
) -> str:
    """Genera la nota Obsidian (versión vault)."""
    asc_sign = chart.get("chart", {}).get("asc_sign", "?")
    sect = chart.get("chart", {}).get("sect", "?")
    slug = _slug(alias)

    return f"""---
id: {bv_id}
alias: {alias}
subject_real: {subject_real}
rodden: {rodden}
birth_date: "{birth_date}"
birth_time: "{birth_time}"
experiment_date: "{experiment_date}"
status: pending_verification
score_summary: "pendiente"
tags: [blind_validation, carta_ciega, lilly]
---

# {bv_id} — Carta Ciega: {alias}

**Alias:** {alias} · **Rodden:** {rodden}
**Nacimiento:** {birth_date} {birth_time}
**Tipo:** {sect} · **ASC:** {asc_sign}

Experimento generado el **{experiment_date}**.
Ficha técnica: `data/blind_validation/{bv_id}_{slug}.md`

---

## Lectura doctrinal de Lilly

{lilly_reading}

---

## Verificación

*(Completar tras confrontar con hechos biográficos verificables)*

---

## Links

- [[AXIOMATICS_v0_4]]
- [[HF_EXPERIMENT_LOG]]
- [[persian_techniques]]
"""


def _update_index(
    bv_id: str,
    alias: str,
    subject_real: str,
    rodden: str,
    birth_date: str,
    birth_time: str,
    lat: float,
    lon: float,
    experiment_date: str,
    filename: str,
    obsidian_filename: str,
) -> None:
    """Agrega o actualiza la entrada en BV_index.json."""
    if INDEX_PATH.exists():
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    else:
        data = []

    # No duplicar si ya existe el ID
    if any(e.get("id") == bv_id for e in data):
        print(f"[BV] {bv_id} ya existe en el índice — no se duplica.", flush=True)
        return

    data.append(
        {
            "id": bv_id,
            "alias": alias,
            "subject_real": subject_real,
            "rodden": rodden,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "lat": lat,
            "lon": lon,
            "experiment_date": experiment_date,
            "status": "pending_verification",
            "score": {"dimensions_passed": None, "dimensions_total": 5, "validates": None},
            "file": filename,
            "obsidian_file": f"obsidian_vault/03_experimentos/{obsidian_filename}",
            "notes": f"Generado automáticamente — alias: {alias}",
        }
    )

    INDEX_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    abu_url = args.abu_url or ABU_ENGINE_URL

    if not ANTHROPIC_API_KEY:
        print("[BV] ERROR: ANTHROPIC_API_KEY no configurada.", file=sys.stderr)
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_DIR.mkdir(parents=True, exist_ok=True)

    experiment_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bv_id = _next_bv_id()
    slug = _slug(args.alias)

    print(f"[BV] Iniciando experimento {bv_id} — alias: {args.alias}", flush=True)

    # 1. Obtener carta natal extendida
    try:
        chart = _fetch_chart_extended(
            args.date, args.time, args.lat, args.lon, abu_url
        )
    except Exception as exc:
        print(f"[BV] ERROR al obtener carta del engine: {exc}", file=sys.stderr)
        print(
            "[BV] Asegúrate de que Abu Engine esté corriendo en: "
            f"{abu_url}  (o pasa --abu-url)",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Construir contextBlock y llamar a Lilly
    print(f"[BV] Generando lectura doctrinal con {BV_MODEL}...", flush=True)
    context_block = _build_doctrinal_context(chart, args.alias)
    lilly_reading = _call_lilly(context_block)

    # 3. Renderizar fichas
    bv_filename = f"{bv_id}_{slug}.md"
    obs_filename = f"{bv_id}_{slug}.md"

    bv_md = _render_bv_md(
        bv_id=bv_id,
        alias=args.alias,
        subject_real=args.subject_real,
        rodden=args.rodden,
        birth_date=args.date,
        birth_time=args.time,
        lat=args.lat,
        lon=args.lon,
        chart=chart,
        lilly_reading=lilly_reading,
        experiment_date=experiment_date,
    )

    obs_md = _render_obsidian_md(
        bv_id=bv_id,
        alias=args.alias,
        subject_real=args.subject_real,
        rodden=args.rodden,
        birth_date=args.date,
        birth_time=args.time,
        chart=chart,
        lilly_reading=lilly_reading,
        experiment_date=experiment_date,
    )

    # 4. Guardar archivos
    (DATA_DIR / bv_filename).write_text(bv_md, encoding="utf-8")
    (OBSIDIAN_DIR / obs_filename).write_text(obs_md, encoding="utf-8")

    # 5. Actualizar índice
    _update_index(
        bv_id=bv_id,
        alias=args.alias,
        subject_real=args.subject_real,
        rodden=args.rodden,
        birth_date=args.date,
        birth_time=args.time,
        lat=args.lat,
        lon=args.lon,
        experiment_date=experiment_date,
        filename=bv_filename,
        obsidian_filename=obs_filename,
    )

    print(f"[BV] ✓ Ficha guardada: data/blind_validation/{bv_filename}", flush=True)
    print(f"[BV] ✓ Nota Obsidian: obsidian_vault/03_experimentos/{obs_filename}", flush=True)
    print(f"[BV] ✓ Índice actualizado: {bv_id} — alias: {args.alias}", flush=True)
    print(
        "[BV] Próximo paso: completar la sección de Verificación en la ficha.", flush=True
    )


if __name__ == "__main__":
    main()
