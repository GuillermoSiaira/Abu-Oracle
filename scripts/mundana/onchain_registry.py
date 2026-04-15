"""
onchain_registry.py — Registro de predicciones mundanas.

Fase 1: SHA-256 del texto + metadatos → GCS bucket abu-oracle-predictions.
Fase 2 (post-lanzamiento): hash → on-chain (Base o Arbitrum).

Variables de entorno:
  GOOGLE_CLOUD_PROJECT  — default: abu-oracle
  GCS_PREDICTIONS_BUCKET — default: abu-oracle-predictions

Formato del registro:
  {
    "sha256": "<hex>",
    "config_type": "<tipo>",
    "platform": "<red>",
    "published_at": "<ISO UTC>",
    "text_preview": "<primeros 100 chars>",
    "text_length": <int>
  }
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT       = Path(__file__).resolve().parents[2]
REGISTRY_DIR    = REPO_ROOT / "data" / "mundana" / "registry"
GCS_BUCKET      = os.environ.get("GCS_PREDICTIONS_BUCKET", "abu-oracle-predictions")
GCS_PROJECT     = os.environ.get("GOOGLE_CLOUD_PROJECT", "abu-oracle")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _save_local(record: dict) -> Path:
    """Guarda registro local como backup (siempre, incluso si GCS falla)."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REGISTRY_DIR / f"{ts}_{record['config_type']}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[registry] Registro local: {path.name}")
    return path


def _upload_gcs(record: dict) -> bool:
    """Sube el registro a GCS. Retorna True si OK."""
    try:
        from google.cloud import storage  # type: ignore
        client  = storage.Client(project=GCS_PROJECT)
        bucket  = client.bucket(GCS_BUCKET)
        ts      = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        blob_name = f"predictions/{ts}_{record['config_type']}.json"
        blob    = bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(record, indent=2, ensure_ascii=False),
            content_type="application/json",
        )
        print(f"[registry] GCS upload OK: gs://{GCS_BUCKET}/{blob_name}")
        return True
    except ImportError:
        print("[registry] google-cloud-storage no instalado — solo registro local")
        return False
    except Exception as e:
        print(f"[registry] Error GCS: {e}")
        return False


def register_prediction(text: str, config: dict, platform: str = "farcaster") -> dict:
    """
    Registra la predicción publicada.

    Retorna el record con el hash SHA-256.
    """
    sha = _sha256(text)
    record = {
        "sha256":       sha,
        "config_type":  config.get("type", "unknown"),
        "platform":     platform,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "text_preview": text[:100],
        "text_length":  len(text),
        "significance": config.get("significance", "unknown"),
        "p_value":      config.get("p_value"),
        "density_ratio": config.get("density_ratio"),
    }

    _save_local(record)
    _upload_gcs(record)

    print(f"[registry] SHA-256: {sha[:16]}… registrado para {config.get('type')}")
    return record


if __name__ == "__main__":
    print("=== onchain_registry.py — test ===\n")
    sample_text = "Conjunción Marte-Saturno — el señor de la guerra y el del límite se encuentran."
    sample_config = {
        "type": "conjunction_MS",
        "significance": "medium",
        "p_value": 0.016,
        "density_ratio": 1.6,
    }
    record = register_prediction(sample_text, sample_config, platform="farcaster")
    print(f"\nRecord: {json.dumps(record, indent=2)}")
