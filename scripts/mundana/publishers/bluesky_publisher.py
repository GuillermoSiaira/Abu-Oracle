"""
bluesky_publisher.py — Publica en Bluesky via AT Protocol.

Variables de entorno requeridas:
  BLUESKY_HANDLE   — ej: abuoracle.bsky.social
  BLUESKY_PASSWORD — app password de Bluesky (Settings > App Passwords)

No requiere paquetes externos más allá de requests.
Implementa el flujo mínimo del AT Protocol: createSession + createRecord.
"""

from __future__ import annotations

import os
import json
import requests
from datetime import datetime, timezone


ATP_HOST = "https://bsky.social"


def _create_session(handle: str, password: str) -> dict:
    """Obtiene token de sesión del ATP."""
    resp = requests.post(
        f"{ATP_HOST}/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def publish_bluesky(text: str) -> dict:
    """
    Publica un post en Bluesky.

    Retorna: { 'status': 'published' | 'error', 'uri': str | None, 'detail': str }
    """
    handle   = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_PASSWORD")

    if not handle or not password:
        return {
            "status": "error",
            "uri": None,
            "detail": "BLUESKY_HANDLE o BLUESKY_PASSWORD no configurados",
        }

    # Truncar si supera límite de Bluesky
    if len(text) > 300:
        text = text[:297] + "..."

    try:
        session = _create_session(handle, password)
        access_token = session.get("accessJwt")
        did          = session.get("did")

        if not access_token or not did:
            return {"status": "error", "uri": None, "detail": "No se obtuvo sesión ATP"}

        record = {
            "$type":     "app.bsky.feed.post",
            "text":      text,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        resp = requests.post(
            f"{ATP_HOST}/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={
                "repo":       did,
                "collection": "app.bsky.feed.post",
                "record":     record,
            },
            timeout=15,
        )
        data = resp.json()

        if resp.ok and data.get("uri"):
            uri = data["uri"]
            print(f"[bluesky] Publicado OK — uri: {uri}")
            return {"status": "published", "uri": uri, "detail": "OK"}
        else:
            error_msg = data.get("message") or str(data)
            print(f"[bluesky] Error API: {error_msg}")
            return {"status": "error", "uri": None, "detail": error_msg}

    except Exception as e:
        print(f"[bluesky] Excepcion: {e}")
        return {"status": "error", "uri": None, "detail": str(e)}
