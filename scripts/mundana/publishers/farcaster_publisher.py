"""
farcaster_publisher.py — Publica en Farcaster via Neynar API.

Variables de entorno requeridas:
  NEYNAR_API_KEY        — API key de neynar.com (gratuito hasta 1000 casts/mes)
  FARCASTER_SIGNER_UUID — Signer UUID del dashboard Neynar

Referencia: https://docs.neynar.com/reference/publish-cast
"""

from __future__ import annotations

import os
import requests


NEYNAR_API_URL = "https://api.neynar.com/v2/farcaster/cast"


def publish_farcaster(text: str) -> dict:
    """
    Publica un cast en Farcaster.

    Retorna: { 'status': 'published' | 'error', 'cast_hash': str | None, 'detail': str }
    """
    api_key    = os.environ.get("NEYNAR_API_KEY")
    signer_uuid = os.environ.get("FARCASTER_SIGNER_UUID")

    if not api_key or not signer_uuid:
        return {
            "status": "error",
            "cast_hash": None,
            "detail": "NEYNAR_API_KEY o FARCASTER_SIGNER_UUID no configurados",
        }

    # Truncar si supera el límite de Farcaster
    if len(text) > 320:
        text = text[:317] + "..."

    try:
        response = requests.post(
            NEYNAR_API_URL,
            headers={"api_key": api_key, "Content-Type": "application/json"},
            json={"signer_uuid": signer_uuid, "text": text},
            timeout=15,
        )
        data = response.json()

        if response.ok and data.get("cast", {}).get("hash"):
            cast_hash = data["cast"]["hash"]
            print(f"[farcaster] Publicado OK — hash: {cast_hash}")
            return {"status": "published", "cast_hash": cast_hash, "detail": "OK"}
        else:
            error_msg = data.get("message") or str(data)
            print(f"[farcaster] Error API: {error_msg}")
            return {"status": "error", "cast_hash": None, "detail": error_msg}

    except Exception as e:
        print(f"[farcaster] Excepcion: {e}")
        return {"status": "error", "cast_hash": None, "detail": str(e)}
