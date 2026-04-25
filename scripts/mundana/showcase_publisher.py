"""
showcase_publisher.py — Publica HF maps de figuras históricas en RRSS.

Uso:
  python scripts/mundana/showcase_publisher.py \\
    --subject einstein \\
    --domain h10 \\
    --platform bluesky \\
    --lang es \\
    [--dry-run]

  python scripts/mundana/showcase_publisher.py --subject einstein --domain h10 --dry-run

Variables de entorno requeridas:
  ANTHROPIC_API_KEY  — para generar caption
  BLUESKY_HANDLE     — si --platform bluesky
  BLUESKY_PASSWORD   — si --platform bluesky
  RESEND_API_KEY     — si --platform twitter (email de aprobación)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Asegurar imports relativos dentro de scripts/mundana/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from image_generator import generate_hf_map_image
from content_generator import generate_showcase_caption, SUBJECT_NAMES, DOMAIN_LABELS
from publishers import publish_all

REPO_ROOT    = Path(__file__).resolve().parents[2]
RANKINGS_DIR = REPO_ROOT / "next_app" / "public" / "rankings"
LOGS_DIR     = REPO_ROOT / "data" / "mundana" / "logs"

# ID de sujetos demo (slug → ID del archivo de ranking)
SUBJECT_IDS: dict[str, int] = {
    "einstein": 308660,
    "freud":    337730,
    "jung":     366580,
    "tesla":    357700,
    "gandhi":   61360,
    "frida":    35255,
    "picasso":  76835,
    "vangogh":  317785,
    "borges":   12145,
    "bowie":    232650,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_top3_cities(subject_slug: str, domain: str) -> list[str]:
    """
    Intenta leer las 3 mejores ciudades del ranking del sujeto.

    Busca en dos ubicaciones:
      1. next_app/public/rankings/{subject_slug}_top20.json  (por slug)
      2. next_app/public/rankings/subject_{id}_ranking.json  (por ID)

    Retorna lista vacía si no hay archivo de ranking.
    """
    # Opción 1: por slug
    path_slug = RANKINGS_DIR / f"{subject_slug}_top20.json"
    if path_slug.exists():
        return _parse_cities(path_slug, domain)

    # Opción 2: por ID numérico
    subject_id = SUBJECT_IDS.get(subject_slug)
    if subject_id:
        path_id = RANKINGS_DIR / f"subject_{subject_id}_ranking.json"
        if path_id.exists():
            return _parse_cities(path_id, domain)

    print(f"[showcase] No se encontró ranking para '{subject_slug}' — sin ciudades")
    return []


def _parse_cities(path: Path, domain: str) -> list[str]:
    """Extrae top 3 ciudades del JSON de ranking."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # El array puede estar en la raíz o en data["rankings"][domain]
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Intentar extraer por dominio
            items = (
                data.get(domain)
                or data.get("global")
                or data.get("rankings", {}).get(domain)
                or []
            )
            if not items and data.get("cities"):
                items = data["cities"]

        cities = []
        for item in items[:3]:
            if isinstance(item, dict):
                city = item.get("city") or item.get("name") or item.get("city_name", "")
                if city:
                    cities.append(str(city))
            elif isinstance(item, str):
                cities.append(item)

        return cities[:3]
    except Exception as e:
        print(f"[showcase] Error leyendo ranking {path}: {e}")
        return []


def _log_result(subject: str, domain: str, platform: str, result: dict) -> None:
    """Loggea resultado en data/mundana/logs/showcase_{date}.log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    today    = datetime.now(timezone.utc).strftime("%Y%m%d")
    log_path = LOGS_DIR / f"showcase_{today}.log"

    ts    = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] subject={subject} domain={domain} platform={platform} status={result.get('status')} detail={result.get('detail', '')}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"[showcase] Log: {log_path}")


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def run_showcase(
    subject: str,
    domain: str = "global",
    platform: str = "bluesky",
    lang: str = "es",
    dry_run: bool = False,
) -> dict:
    """
    Genera y publica (o simula) un post HF showcase.

    Returns:
        dict con resultado de publicación
    """
    print(f"\n[showcase] Iniciando — sujeto={subject} dominio={domain} plataforma={platform} lang={lang} dry_run={dry_run}")

    # Validaciones básicas
    if subject not in SUBJECT_NAMES:
        known = list(SUBJECT_NAMES.keys())
        raise ValueError(f"Sujeto '{subject}' desconocido. Disponibles: {known}")

    # 1. Generar imagen HF
    print(f"[showcase] Generando mapa HF...")
    image_bytes = generate_hf_map_image(subject, domain)
    print(f"[showcase] Imagen generada — {len(image_bytes):,} bytes")

    # 2. Leer ranking top-3
    top3 = _load_top3_cities(subject, domain)
    print(f"[showcase] Top-3 ciudades: {top3 or '(no disponible)'}")

    # 3. Generar caption
    print(f"[showcase] Generando caption con Claude...")
    caption = generate_showcase_caption(subject, domain, top3, lang=lang, platform=platform)
    print(f"\n[showcase] Caption ({len(caption)} chars):\n{caption}\n")

    if dry_run:
        # Guardar imagen localmente para inspección
        ts         = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        img_path   = REPO_ROOT / f"test_showcase_{subject}_{domain}.png"
        img_path.write_bytes(image_bytes)
        print(f"[showcase] DRY RUN — imagen guardada en: {img_path}")
        return {
            "status":  "dry_run",
            "caption": caption,
            "image":   str(img_path),
            "top3":    top3,
        }

    # 4. Publicar
    content = {
        "text":        caption,
        "image_bytes": image_bytes,
        "image_alt":   f"Harmony Field de {SUBJECT_NAMES[subject]} — dominio {DOMAIN_LABELS.get(domain, domain)}",
        "config_type": f"showcase_{subject}_{domain}",
    }

    platforms_to_publish = (
        ["bluesky", "twitter"] if platform == "all" else [platform]
    )

    results = {}
    for p in platforms_to_publish:
        result = publish_all(p, content)
        results[p] = result
        _log_result(subject, domain, p, result)
        print(f"[showcase] {p}: {result}")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publica HF map de una figura histórica en RRSS"
    )
    parser.add_argument("--subject",  required=True,
                        help=f"Slug del sujeto. Opciones: {', '.join(SUBJECT_NAMES)}")
    parser.add_argument("--domain",   default="global",
                        help="Dominio HF (global, h1, h2, h4, h5, h6, h7, h9, h10). Default: global")
    parser.add_argument("--platform", default="bluesky",
                        choices=["bluesky", "twitter", "all"],
                        help="Plataforma destino. Default: bluesky")
    parser.add_argument("--lang",     default="es",
                        choices=["es", "en"],
                        help="Idioma del caption. Default: es")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Genera imagen y texto pero no publica")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_showcase(
        subject=args.subject,
        domain=args.domain,
        platform=args.platform,
        lang=args.lang,
        dry_run=args.dry_run,
    )
