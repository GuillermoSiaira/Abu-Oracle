"""
main_publisher.py — Entry point del Cloud Run Job de publicación mundana.

Flujo:
  1. Verificar si hay algo digno de publicar (publication_filter)
  2. Obtener la mejor configuración del cielo actual
  3. Generar contenido adaptado por plataforma (content_generator → Claude Sonnet 4.6)
  4. Publicar en cada plataforma (publishers/)
  5. Registrar hash SHA-256 del contenido publicado (onchain_registry)
  6. Marcar publicación para respetar min_days_between_posts

Plataformas:
  - Fase 1 AUTO:    farcaster, bluesky
  - Fase 1 MANUAL:  twitter, instagram, facebook, tiktok (borrador + email aprobación)

Variables de entorno requeridas:
  ANTHROPIC_API_KEY         — generación de contenido
  BLUESKY_HANDLE            — ej: abuoracle.bsky.social
  BLUESKY_PASSWORD          — app password
  NEYNAR_API_KEY            — Farcaster via Neynar
  FARCASTER_SIGNER_UUID     — del dashboard Neynar
  RESEND_API_KEY            — emails de aprobación manual
  OPERATOR_EMAIL            — destinatario de borradores (default: guillermosiaira@gmail.com)

Variables opcionales:
  GOOGLE_CLOUD_PROJECT      — para GCS registry (default: abu-oracle)
  GCS_PREDICTIONS_BUCKET    — bucket de predicciones (default: abu-oracle-predictions)
  PLATFORMS                 — CSV de plataformas activas (default: farcaster,bluesky,twitter)
  DRY_RUN                   — si "true", genera contenido pero no publica
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Asegurar que el directorio del script está en el path
sys.path.insert(0, str(Path(__file__).parent))

from publication_filter import should_publish, get_best_configuration, record_publication
from content_generator  import generate_post
from publishers         import publish_all
from onchain_registry   import register_prediction


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

DEFAULT_PLATFORMS = ["farcaster", "bluesky", "twitter"]
REPO_ROOT         = Path(__file__).resolve().parents[2]
LOG_DIR           = REPO_ROOT / "data" / "mundana" / "logs"


def _get_platforms() -> list[str]:
    raw = os.environ.get("PLATFORMS", ",".join(DEFAULT_PLATFORMS))
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def _is_dry_run() -> bool:
    return os.environ.get("DRY_RUN", "false").lower() == "true"


def _log_run(entries: list[dict]) -> None:
    """Escribe el log de la ejecución en data/mundana/logs/."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = LOG_DIR / f"{ts}_run.json"
    path.write_text(
        json.dumps({"timestamp": ts, "entries": entries}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[main] Log: {path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Entry point principal. Retorna 0 si OK, 1 si hubo error.
    """
    print(f"[main] Abu Oracle Mundana Publisher — {datetime.now(timezone.utc).isoformat()}")
    dry_run   = _is_dry_run()
    platforms = _get_platforms()

    if dry_run:
        print("[main] DRY_RUN=true — se generará contenido pero NO se publicará")

    # -----------------------------------------------------------------------
    # 1. ¿Hay algo que publicar?
    # -----------------------------------------------------------------------
    if not should_publish():
        print("[main] No hay configuraciones que superen el umbral. Job completado sin publicación.")
        return 0

    # -----------------------------------------------------------------------
    # 2. Obtener la mejor configuración
    # -----------------------------------------------------------------------
    config = get_best_configuration()
    if not config:
        print("[main] get_best_configuration() retornó None. No se publica.")
        return 0

    print(f"\n[main] Configuración seleccionada: {config.get('label', config.get('type'))}")
    print(f"       Significancia: {config.get('significance')}  |  p={config.get('p_value')}  |  density={config.get('density_ratio')}×")

    # -----------------------------------------------------------------------
    # 3. Obtener contexto histórico (opcional, non-fatal)
    # -----------------------------------------------------------------------
    history = None
    try:
        from sky_calculator import get_historical_context
        history = get_historical_context(config.get("type", ""))
    except Exception as e:
        print(f"[main] Warning: no se pudo obtener contexto histórico: {e}")

    # -----------------------------------------------------------------------
    # 4. Generar + publicar en cada plataforma
    # -----------------------------------------------------------------------
    run_log: list[dict] = []
    first_published_platform: str | None = None

    for platform in platforms:
        print(f"\n[main] Plataforma: {platform}")

        # Generar contenido
        try:
            content = generate_post(config, platform=platform, history=history)
            print(f"       Texto ({len(content['text'])} chars): {content['text'][:80]}…")
        except Exception as e:
            print(f"       ERROR generando contenido: {e}")
            run_log.append({"platform": platform, "status": "error_generation", "detail": str(e)})
            continue

        if dry_run:
            print(f"       [DRY_RUN] No se publica.")
            run_log.append({"platform": platform, "status": "dry_run", "text_preview": content["text"][:100]})
            continue

        # Publicar
        try:
            result = publish_all(platform, content)
            print(f"       Resultado: {result.get('status')} — {result}")
        except Exception as e:
            print(f"       ERROR publicando: {e}")
            run_log.append({"platform": platform, "status": "error_publish", "detail": str(e)})
            continue

        # Registrar hash del contenido (non-fatal)
        try:
            register_prediction(content["text"], config, platform=platform)
        except Exception as e:
            print(f"       Warning: registro fallido: {e}")

        run_log.append({
            "platform": platform,
            "status":   result.get("status"),
            "detail":   result,
        })

        # Marcar la primera plataforma auto-publicada para cooldown
        if result.get("status") in ("published", "pending_approval") and first_published_platform is None:
            first_published_platform = platform

    # -----------------------------------------------------------------------
    # 5. Registrar publicación para cooldown
    # -----------------------------------------------------------------------
    if not dry_run and first_published_platform:
        record_publication(config.get("type", "unknown"), first_published_platform)
        print(f"\n[main] Cooldown registrado — plataforma: {first_published_platform}")

    # -----------------------------------------------------------------------
    # 6. Log final
    # -----------------------------------------------------------------------
    _log_run(run_log)

    published_count = sum(1 for e in run_log if e.get("status") in ("published", "pending_approval"))
    print(f"\n[main] Completado. Plataformas procesadas: {len(run_log)} | Publicadas/pendientes: {published_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
