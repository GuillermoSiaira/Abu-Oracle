"""
publication_filter.py — Decide si hay algo digno de publicar hoy.

Criterios (MUNDANA_MODULE_SPEC.md §3.1):
  p_value_max:          0.05   — señal estadísticamente significativa
  density_ratio_min:    2.0    — al menos 2× el baseline
  days_to_exact_max:    7      — dentro de la ventana relevante
  min_days_between_posts: 3    — no publicar más de 1 vez cada 3 días

Estado de última publicación: data/mundana/last_published.json
  { "timestamp": ISO, "config_type": str, "platform": str }

Uso:
  from publication_filter import should_publish, get_best_configuration
  if should_publish():
      config = get_best_configuration()
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sky_calculator import get_upcoming_configurations, get_current_sky

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

REPO_ROOT       = Path(__file__).resolve().parents[2]
LAST_PUB_PATH   = REPO_ROOT / "data" / "mundana" / "last_published.json"
GCS_BUCKET      = os.environ.get("GCS_PREDICTIONS_BUCKET", "abu-oracle-predictions")
GCS_STATE_BLOB  = "state/last_published.json"
_IN_CLOUD_RUN   = bool(os.environ.get("K_SERVICE"))  # True cuando corre en Cloud Run

# ---------------------------------------------------------------------------
# Umbrales (spec §3.1)
# ---------------------------------------------------------------------------

PUBLICATION_THRESHOLDS = {
    "p_value_max":          0.05,
    "density_ratio_min":    2.0,
    "days_to_exact_max":    7,
    "min_days_between_posts": 3,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_last_published() -> dict | None:
    if _IN_CLOUD_RUN:
        try:
            from google.cloud import storage  # type: ignore
            client = storage.Client()
            blob   = client.bucket(GCS_BUCKET).blob(GCS_STATE_BLOB)
            if not blob.exists():
                return None
            return json.loads(blob.download_as_text())
        except Exception:
            return None
    if not LAST_PUB_PATH.exists():
        return None
    try:
        with open(LAST_PUB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_last_published(config_type: str, platform: str) -> None:
    data = {
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "config_type": config_type,
        "platform":    platform,
    }
    payload = json.dumps(data, indent=2)
    if _IN_CLOUD_RUN:
        try:
            from google.cloud import storage  # type: ignore
            client = storage.Client()
            client.bucket(GCS_BUCKET).blob(GCS_STATE_BLOB).upload_from_string(
                payload, content_type="application/json"
            )
            print(f"[filter] Cooldown guardado en GCS: gs://{GCS_BUCKET}/{GCS_STATE_BLOB}")
        except Exception as e:
            print(f"[filter] Warning: no se pudo guardar cooldown en GCS: {e}")
        return
    LAST_PUB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LAST_PUB_PATH, "w", encoding="utf-8") as f:
        f.write(payload)


def _days_since_last_post() -> float:
    last = _load_last_published()
    if not last:
        return float("inf")
    try:
        ts  = datetime.fromisoformat(last["timestamp"])
        now = datetime.now(timezone.utc)
        return (now - ts).total_seconds() / 86_400
    except Exception:
        return float("inf")


def _config_passes_thresholds(config: dict) -> bool:
    """Retorna True si la configuración supera los umbrales de publicación."""
    significance = config.get("significance", "low")
    days         = config.get("days_to_exact")

    # ── Regla C: exactitud inminente (≤3 días) + significance medium/high ────
    # No requiere stats empíricos — la rareza del momento lo justifica.
    if significance in ("high", "medium"):
        if days is not None and days <= 3:
            return True
        # Activo sin fecha exacta (stellium, ingreso ocurrido hoy)
        if days is None and config.get("orb", 999) <= 30:
            if significance == "high":
                return True

    # ── Con datos estadísticos (H_mundana_A) ─────────────────────────────────
    if config.get("p_value") is None or config.get("density_ratio") is None:
        return False

    p_ok       = config["p_value"]       <= PUBLICATION_THRESHOLDS["p_value_max"]
    density_ok = config["density_ratio"] >= PUBLICATION_THRESHOLDS["density_ratio_min"]
    days_ok    = (days is None) or (days <= PUBLICATION_THRESHOLDS["days_to_exact_max"])

    return p_ok and density_ok and days_ok


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def should_publish() -> bool:
    """
    Retorna True si hay al menos una configuración que supera los umbrales
    Y han pasado al menos min_days_between_posts días desde el último post.
    """
    if _days_since_last_post() < PUBLICATION_THRESHOLDS["min_days_between_posts"]:
        print(f"[filter] Publicación reciente — esperar {PUBLICATION_THRESHOLDS['min_days_between_posts']} días.")
        return False

    # Configuraciones activas (ya están en ventana)
    sky = get_current_sky()
    for config in sky.get("active_configurations", []):
        if _config_passes_thresholds(config):
            return True

    # Configuraciones próximas (dentro de la ventana de 7 días)
    upcoming = get_upcoming_configurations(days_ahead=7)
    for config in upcoming:
        if _config_passes_thresholds(config):
            return True

    print("[filter] Sin configuraciones que superen el umbral. No se publica.")
    return False


def get_best_configuration() -> dict | None:
    """
    Retorna la configuración más relevante para publicar hoy.
    Prioridad: (1) activa + alta significancia, (2) próxima + alta, (3) cualquier activa que pase.
    """
    sky      = get_current_sky()
    upcoming = get_upcoming_configurations(days_ahead=7)

    candidates = []

    # Activas primero
    for cfg in sky.get("active_configurations", []):
        if _config_passes_thresholds(cfg):
            score = 3 if cfg["significance"] == "high" else 2
            candidates.append((score, cfg))

    # Próximas
    for cfg in upcoming:
        if _config_passes_thresholds(cfg):
            score = 1 if cfg["significance"] == "high" else 0
            candidates.append((score, cfg))

    if not candidates:
        return None

    # Mayor score primero
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def record_publication(config_type: str, platform: str) -> None:
    """Registra la publicación para respetar min_days_between_posts."""
    _save_last_published(config_type, platform)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== publication_filter.py — test ===\n")
    days_ago = _days_since_last_post()
    print(f"Días desde última publicación: {days_ago:.1f}")

    publish = should_publish()
    print(f"should_publish() -> {publish}")

    if publish:
        config = get_best_configuration()
        print(f"\nMejor configuración: {config}")
    else:
        print("\nNada que publicar hoy.")
