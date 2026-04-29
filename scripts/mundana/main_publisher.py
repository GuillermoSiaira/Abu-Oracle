"""
main_publisher.py — Entry point del Cloud Run Job de publicación mundana.

MODOS DE PUBLICACIÓN (env var PUBLISH_MODE):
  mundana  — publica cuando hay configuración astronómica significativa (default)
  doctrine — publica un post sobre la arquitectura HF_v6 (slides de presentación)
             independientemente de si hay evento mundano activo
  auto     — intenta mundana primero; si no hay nada, publica doctrine como fallback

Flujo mundana:
  1. Verificar si hay algo digno de publicar (publication_filter)
  2. Obtener la mejor configuración del cielo actual
  3. Seleccionar estilo de contenido (rotación diaria: stats/individual/geographic/doctrine)
  4. Generar contenido adaptado por plataforma y estilo (content_generator → Claude Sonnet 4.6)
  5. Publicar en cada plataforma (publishers/)
  6. Registrar hash SHA-256 del contenido publicado (onchain_registry)
  7. Marcar publicación para respetar min_days_between_posts

Flujo doctrine:
  1. Seleccionar slide del día (rotación de 11 conceptos, cada 3 días)
  2. Generar post doctrinal por plataforma e idioma
  3. Publicar / enviar borrador
  4. Registrar hash SHA-256

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
  PUBLISH_MODE              — mundana | doctrine | auto (default: mundana)
  LANG                      — idioma de publicación: es | en | fr | pt (default: es)
  CONTENT_STYLE             — forzar estilo mundana (stats|individual|geographic|doctrine).
                               Si no se define, rota automáticamente por día de la semana.
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
from content_generator  import (
    generate_post, generate_doctrine_post, get_doctrine_slide, _select_style,
)
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

def _publish_platforms(
    platforms: list[str],
    content_factory,
    config_for_record: dict | None,
    dry_run: bool,
) -> tuple[list[dict], str | None]:
    """
    Genera y publica contenido en cada plataforma.
    content_factory(platform) → content dict
    Retorna (run_log, first_published_platform).
    """
    run_log: list[dict] = []
    first_published: str | None = None

    for platform in platforms:
        print(f"\n[main] Plataforma: {platform}")

        try:
            content = content_factory(platform)
            print(f"       Texto ({len(content['text'])} chars): {content['text'][:80]}…")
        except Exception as e:
            print(f"       ERROR generando contenido: {e}")
            run_log.append({"platform": platform, "status": "error_generation", "detail": str(e)})
            continue

        if dry_run:
            print("       [DRY_RUN] No se publica.")
            run_log.append({"platform": platform, "status": "dry_run", "text_preview": content["text"][:100]})
            continue

        try:
            result = publish_all(platform, content)
            print(f"       Resultado: {result.get('status')} — {result}")
        except Exception as e:
            print(f"       ERROR publicando: {e}")
            run_log.append({"platform": platform, "status": "error_publish", "detail": str(e)})
            continue

        try:
            meta = config_for_record or {"type": content.get("config_type", "doctrine")}
            register_prediction(content["text"], meta, platform=platform)
        except Exception as e:
            print(f"       Warning: registro fallido: {e}")

        run_log.append({
            "platform": platform,
            "status":   result.get("status"),
            "style":    content.get("style"),
            "lang":     content.get("lang"),
            "detail":   result,
        })

        if result.get("status") in ("published", "pending_approval") and first_published is None:
            first_published = platform

    return run_log, first_published


def main() -> int:
    """Entry point principal. Retorna 0 si OK, 1 si hubo error."""
    print(f"[main] Abu Oracle Mundana Publisher — {datetime.now(timezone.utc).isoformat()}")

    dry_run      = _is_dry_run()
    platforms    = _get_platforms()
    publish_mode = os.environ.get("PUBLISH_MODE", "mundana").lower()
    lang         = os.environ.get("LANG", "es").lower()

    if dry_run:
        print("[main] DRY_RUN=true — se generará contenido pero NO se publicará")

    print(f"[main] Modo: {publish_mode} | Idioma: {lang} | Plataformas: {', '.join(platforms)}")

    run_log: list[dict]   = []
    first_published:  str | None = None
    mundana_config:  dict | None = None

    # -----------------------------------------------------------------------
    # MODO MUNDANA (o intento mundana en modo auto)
    # -----------------------------------------------------------------------
    if publish_mode in ("mundana", "auto"):
        if not should_publish():
            if publish_mode == "mundana":
                print("[main] No hay configuraciones que superen el umbral. Job sin publicación.")
                return 0
            else:
                print("[main] No hay configuraciones mundanas — fallback a modo doctrine.")
        else:
            mundana_config = get_best_configuration()
            if not mundana_config:
                print("[main] get_best_configuration() retornó None.")
                if publish_mode == "mundana":
                    return 0
            else:
                print(f"\n[main] Configuración: {mundana_config.get('label', mundana_config.get('type'))}")
                print(f"       Significancia: {mundana_config.get('significance')} | p={mundana_config.get('p_value')} | density={mundana_config.get('density_ratio')}×")

                content_style = os.environ.get("CONTENT_STYLE") or _select_style(mundana_config)
                print(f"       Estilo: {content_style} | Idioma: {lang}")

                history = None
                try:
                    from sky_calculator import get_historical_context
                    history = get_historical_context(mundana_config.get("type", ""))
                except Exception as e:
                    print(f"[main] Warning: contexto histórico no disponible: {e}")

                def mundana_factory(platform: str) -> dict:
                    return generate_post(
                        mundana_config, platform=platform,
                        history=history, style=content_style, lang=lang,
                    )

                run_log, first_published = _publish_platforms(
                    platforms, mundana_factory, mundana_config, dry_run,
                )

    # -----------------------------------------------------------------------
    # MODO DOCTRINE (o fallback desde auto cuando no hubo evento mundano)
    # -----------------------------------------------------------------------
    if publish_mode == "doctrine" or (publish_mode == "auto" and mundana_config is None):
        slide = get_doctrine_slide()
        key   = "en" if lang == "en" else "es"
        print(f"\n[main] Doctrine slide: {slide['id']} — {slide.get(f'title_{key}', slide['id'])}")

        def doctrine_factory(platform: str) -> dict:
            return generate_doctrine_post(slide, platform=platform, lang=lang)

        doctrine_log, first_doctrine = _publish_platforms(
            platforms, doctrine_factory, None, dry_run,
        )
        run_log.extend(doctrine_log)
        if first_published is None:
            first_published = first_doctrine

    # -----------------------------------------------------------------------
    # Registrar cooldown
    # -----------------------------------------------------------------------
    if not dry_run and first_published:
        config_type = mundana_config.get("type", "unknown") if mundana_config else f"doctrine_{get_doctrine_slide()['id']}"
        record_publication(config_type, first_published)
        print(f"\n[main] Cooldown registrado — plataforma: {first_published}")

    # -----------------------------------------------------------------------
    # Log final
    # -----------------------------------------------------------------------
    _log_run(run_log)
    published_count = sum(1 for e in run_log if e.get("status") in ("published", "pending_approval"))
    print(f"\n[main] Completado. Plataformas: {len(run_log)} | Publicadas/pendientes: {published_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
