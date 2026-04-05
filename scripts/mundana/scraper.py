"""
Mundana scraper — descarga eventos históricos de:
  https://carta-natal.es/astrodata/acontecimientos/{dia}-{mes}
para los 365 días del año.

Output: data/mundana/eventos_raw.jsonl
Formato: { "fecha": "YYYY-MM-DD", "descripcion": "...", "url": "...", "tipo": "..." }

Uso:
  python scraper.py               → 365 días completos
  python scraper.py --test        → solo los 3 primeros días
  python scraper.py --days 3      → primeros N días
  python scraper.py --resume      → omite fechas ya presentes en el .jsonl
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT / "data" / "mundana"
OUTPUT_FILE = OUTPUT_DIR / "eventos_raw.jsonl"
FAILED_LOG = OUTPUT_DIR / "failed_urls.txt"

# ── Configuración ──────────────────────────────────────────────────────────────
BASE_URL = "https://carta-natal.es/astrodata/acontecimientos/{dia}-{mes}"
RATE_LIMIT_S = 1.5   # segundos entre requests
MAX_RETRIES = 3
BACKOFF_BASE = 2.0   # duplica en cada reintento

MONTHS = [
    ("enero",       1, 31),
    ("febrero",     2, 28),
    ("marzo",       3, 31),
    ("abril",       4, 30),
    ("mayo",        5, 31),
    ("junio",       6, 30),
    ("julio",       7, 31),
    ("agosto",      8, 31),
    ("septiembre",  9, 30),
    ("octubre",    10, 31),
    ("noviembre",  11, 30),
    ("diciembre",  12, 31),
]

MONTH_NUM: dict[str, int] = {name: num for name, num, _ in MONTHS}

# ── HTTP session ───────────────────────────────────────────────────────────────
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "AbuOracleMundanaScraper/1.0 (astrological research; contact@abu-oracle.com)",
    "Accept": "text/html,application/xhtml+xml;q=0.9",
    "Accept-Language": "es-ES,es;q=0.9",
})

logger = logging.getLogger(__name__)

# ── Generador de días ──────────────────────────────────────────────────────────

def all_days() -> list[tuple[int, str, int]]:
    """Retorna lista de (dia, mes_es, mes_num) para los 365 días del año."""
    days: list[tuple[int, str, int]] = []
    for month_name, month_num, n_days in MONTHS:
        for day in range(1, n_days + 1):
            days.append((day, month_name, month_num))
    return days


# ── Parsing ────────────────────────────────────────────────────────────────────
_DATE_RE = re.compile(r"(\d+)\s+de\s+(\w+)\s+de\s+(\d+)", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def _parse_event_date(dt_text: str, page_day: int, page_month_num: int) -> str:
    """
    Convierte '1 de Enero de 0404' → '0404-01-01'.
    Fallback: usa el día/mes de la página con año 0001.
    """
    m = _DATE_RE.search(dt_text)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        month_num = MONTH_NUM.get(month_name, page_month_num)
        return f"{year:04d}-{month_num:02d}-{day:02d}"
    return f"0001-{page_month_num:02d}-{page_day:02d}"


def parse_page(html: str, url: str, page_day: int, page_month_num: int) -> list[dict]:
    """
    Extrae todos los eventos de la página HTML.
    Cada página tiene una o más secciones bajo <dl class="astrodatas">,
    precedidas por <h3> que indica el tipo ("Fallecimientos", etc.).
    La primera sección no tiene h3 — se asume "acontecimiento".
    """
    soup = BeautifulSoup(html, "lxml")
    contenido = soup.find("div", class_="contenido")
    if not contenido:
        logger.warning("No div.contenido en %s", url)
        return []

    # La tabla de navegación (calendario) precede a los eventos
    table = contenido.find("table")
    if not table:
        logger.warning("No tabla de navegación en %s", url)
        return []

    events: list[dict] = []
    current_tipo = "acontecimiento"

    for sibling in table.next_siblings:
        if not hasattr(sibling, "name") or sibling.name is None:
            continue

        # Encabezados de sección → actualizan el tipo activo
        if sibling.name == "h3":
            heading = sibling.get_text(strip=True).lower()
            if "fallecimiento" in heading or "muerte" in heading:
                current_tipo = "fallecimiento"
            elif "nacimiento" in heading:
                current_tipo = "nacimiento"
            else:
                current_tipo = heading or "acontecimiento"
            continue

        # Lista de eventos
        if sibling.name == "dl" and "astrodatas" in (sibling.get("class") or []):
            dts = sibling.find_all("dt")
            dds = sibling.find_all("dd")
            for dt, dd in zip(dts, dds):
                dt_text = dt.get_text(strip=True)
                dd_text = _WHITESPACE_RE.sub(" ", dd.get_text(separator=" ", strip=True))
                fecha = _parse_event_date(dt_text, page_day, page_month_num)
                events.append({
                    "fecha": fecha,
                    "descripcion": dd_text,
                    "url": url,
                    "tipo": current_tipo,
                })

    return events


# ── HTTP con reintentos ────────────────────────────────────────────────────────

def fetch_page(url: str) -> str | None:
    """
    Descarga la URL con reintentos y backoff exponencial.
    Retorna el HTML o None si todos los intentos fallan.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = _SESSION.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            wait = BACKOFF_BASE ** attempt
            if attempt < MAX_RETRIES:
                logger.warning("  [reintento %d/%d] %s  (%s, wait=%.1fs)",
                               attempt, MAX_RETRIES, url, exc, wait)
                time.sleep(wait)
            else:
                logger.error("  [FALLO] %s  (%s)", url, exc)
    return None


# ── URLs ya procesadas (para --resume) ────────────────────────────────────────

def _load_scraped_urls() -> set[str]:
    """Lee el .jsonl existente y retorna el conjunto de URLs ya procesadas."""
    scraped: set[str] = set()
    if not OUTPUT_FILE.exists():
        return scraped
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "url" in obj:
                    scraped.add(obj["url"])
            except json.JSONDecodeError:
                pass
    return scraped


# ── Runner principal ───────────────────────────────────────────────────────────

def run(
    days: list[tuple[int, str, int]] | None = None,
    resume: bool = False,
) -> None:
    """
    Descarga y parsea los días indicados (o todos si `days` es None).
    Escribe en modo append para soportar ejecuciones parciales.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    target = days if days is not None else all_days()
    total = len(target)

    already_done: set[str] = set()
    if resume:
        already_done = _load_scraped_urls()
        logger.info("Resume mode: %d URLs ya procesadas", len(already_done))

    failed: list[str] = []
    n_written = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as out_f, \
         open(FAILED_LOG, "a", encoding="utf-8") as fail_f:

        for idx, (day, month_name, month_num) in enumerate(target, start=1):
            url = BASE_URL.format(dia=day, mes=month_name)

            if url in already_done:
                print(f"[{idx:3d}/{total}] {day:2d}-{month_name:<11}  SKIP (ya procesado)",
                      flush=True)
                continue

            print(f"[{idx:3d}/{total}] {day:2d}-{month_name:<11}  {url}", flush=True)

            html = fetch_page(url)
            if html is None:
                failed.append(url)
                fail_f.write(url + "\n")
                fail_f.flush()
                print(f"         -> ERROR (ver {FAILED_LOG.name})", flush=True)
                continue

            events = parse_page(html, url, day, month_num)
            for evt in events:
                out_f.write(json.dumps(evt, ensure_ascii=False) + "\n")
            out_f.flush()
            n_written += len(events)

            print(f"         -> {len(events)} eventos", flush=True)

            # Rate limiting (omitir en el último)
            if idx < total:
                time.sleep(RATE_LIMIT_S)

    # Resumen final
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  Dias procesados : {total - len(failed)}/{total}")
    print(f"  Eventos escritos: {n_written}")
    print(f"  URLs fallidas   : {len(failed)}")
    print(f"  Output          : {OUTPUT_FILE}")
    if failed:
        print(f"  Log de fallos   : {FAILED_LOG}")
    print(sep)


# ── CLI ────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper de eventos históricos – carta-natal.es/astrodata/acontecimientos/"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Procesar solo los 3 primeros días (1, 2, 3 de enero)"
    )
    parser.add_argument(
        "--days", type=int, default=None,
        help="Procesar solo los primeros N días del año"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Omitir URLs que ya están en eventos_raw.jsonl"
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s  %(message)s",
        stream=sys.stderr,
    )

    args = _parse_args()
    days = all_days()

    if args.test:
        days = days[:3]
    elif args.days is not None:
        days = days[: args.days]

    run(days=days, resume=args.resume)
