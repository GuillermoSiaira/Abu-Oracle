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


def _upload_blob(session_token: str, image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """Sube imagen a Bluesky y devuelve el blob ref."""
    response = requests.post(
        f"{ATP_HOST}/xrpc/com.atproto.repo.uploadBlob",
        headers={
            "Content-Type": mime_type,
            "Authorization": f"Bearer {session_token}",
        },
        data=image_bytes,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["blob"]


def publish_bluesky(text: str, image_bytes: bytes | None = None, image_alt: str = "") -> dict:
    """
    Publica un post en Bluesky, opcionalmente con imagen adjunta.

    Args:
        text:        Texto del post (se trunca a 300 chars si es necesario)
        image_bytes: PNG en bytes a adjuntar (opcional)
        image_alt:   Texto alternativo para la imagen

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

        record: dict = {
            "$type":     "app.bsky.feed.post",
            "text":      text,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        # Adjuntar imagen si viene
        if image_bytes:
            try:
                blob_ref = _upload_blob(access_token, image_bytes)
                record["embed"] = {
                    "$type": "app.bsky.embed.images",
                    "images": [{"image": blob_ref, "alt": image_alt}],
                }
                print("[bluesky] Imagen subida OK")
            except Exception as img_err:
                print(f"[bluesky] WARNING — no se pudo subir imagen, publicando sin ella: {img_err}")

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


def publish_thread(posts: list[dict]) -> dict:
    """
    Publica un hilo en Bluesky.
    Cada post en la lista debe ser un diccionario:
      {
         "text": str,
         "images": list[tuple[bytes, str]] | None,   # lista de (image_bytes, alt_text)
         "link": str | None,
      }
    """
    handle   = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_PASSWORD")

    if not handle or not password:
        return {"status": "error", "uris": [], "detail": "BLUESKY_HANDLE o BLUESKY_PASSWORD no configurados"}

    try:
        session = _create_session(handle, password)
        access_token = session.get("accessJwt")
        did          = session.get("did")

        if not access_token or not did:
            return {"status": "error", "uris": [], "detail": "No se obtuvo sesión ATP"}

        root_ref = None
        parent_ref = None
        published_uris = []

        for p in posts:
            text = p.get("text", "")
            if len(text) > 300:
                text = text[:297] + "..."

            record: dict = {
                "$type":     "app.bsky.feed.post",
                "text":      text,
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }

            if root_ref and parent_ref:
                record["reply"] = {
                    "root": root_ref,
                    "parent": parent_ref
                }

            link = p.get("link")
            if link and link in text:
                byte_text = text.encode("utf-8")
                byte_link = link.encode("utf-8")
                start_idx = byte_text.find(byte_link)
                if start_idx != -1:
                    record["facets"] = [{
                        "index": {
                            "byteStart": start_idx,
                            "byteEnd": start_idx + len(byte_link)
                        },
                        "features": [{
                            "$type": "app.bsky.richtext.facet#link",
                            "uri": link
                        }]
                    }]

            images = p.get("images", [])
            if images:
                bsky_images = []
                for img_bytes, alt in images[:4]:
                    try:
                        blob_ref = _upload_blob(access_token, img_bytes)
                        bsky_images.append({"image": blob_ref, "alt": alt})
                    except Exception as img_err:
                        print(f"[bluesky] WARNING — no se pudo subir imagen en hilo: {img_err}")
                
                if bsky_images:
                    record["embed"] = {
                        "$type": "app.bsky.embed.images",
                        "images": bsky_images
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
            resp.raise_for_status()
            data = resp.json()
            uri = data["uri"]
            cid = data["cid"]
            published_uris.append(uri)

            ref = {"uri": uri, "cid": cid}
            if not root_ref:
                root_ref = ref
            parent_ref = ref

        return {"status": "published", "uris": published_uris, "detail": "OK"}

    except Exception as e:
        print(f"[bluesky] Excepcion en hilo: {e}")
        return {"status": "error", "uris": [], "detail": str(e)}
