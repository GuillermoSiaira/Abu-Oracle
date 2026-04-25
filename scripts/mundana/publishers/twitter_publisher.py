"""
twitter_publisher.py — Manejo de plataformas que requieren aprobación manual en Fase 1.

Twitter/X, Instagram, Facebook, TikTok: en lugar de publicar directamente,
guarda el borrador en data/mundana/drafts/ y envía un email de aprobación
via Resend (ya configurado en el proyecto).

Variables de entorno:
  RESEND_API_KEY      — ya existe en Cloud Run
  OPERATOR_EMAIL      — email del operador (default: guillermosiaira@gmail.com)

En Fase 2 (post-lanzamiento): reemplazar con publicación directa via API de cada red.
"""

from __future__ import annotations

import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT      = Path(__file__).resolve().parents[3]
DRAFTS_DIR     = REPO_ROOT / "data" / "mundana" / "drafts"
RESEND_API_URL = "https://api.resend.com/emails"
OPERATOR_EMAIL = os.environ.get("OPERATOR_EMAIL", "guillermosiaira@gmail.com")
FROM_EMAIL     = "Abu Oracle <noreply@abu-oracle.com>"


def _save_draft(text: str, platform: str) -> Path:
    """Guarda el borrador en disco y retorna el path."""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = DRAFTS_DIR / f"{ts}_{platform}.txt"
    path.write_text(text, encoding="utf-8")
    print(f"[{platform}] Borrador guardado: {path}")
    return path


def _save_image_draft(image_bytes: bytes, config_type: str) -> Path:
    """Guarda imagen PNG del borrador en disco y retorna el path."""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_type = config_type.replace("/", "_").replace(" ", "_")
    path = DRAFTS_DIR / f"{ts}_{safe_type}.png"
    path.write_bytes(image_bytes)
    print(f"[twitter] Imagen guardada: {path}")
    return path


def _send_approval_email(
    text: str,
    platform: str,
    draft_path: Path,
    image_path: Path | None = None,
) -> bool:
    """Envía email de aprobación via Resend. Retorna True si OK."""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print(f"[{platform}] RESEND_API_KEY no configurado — solo borrador guardado")
        return False

    char_count = len(text)

    image_section = ""
    if image_path:
        image_section = f"""
<hr>
<p><strong>📎 Imagen generada:</strong></p>
<p><code>{image_path}</code></p>
<p style="color:#888">Adjuntar esta imagen al tweet.</p>
"""

    html_body = f"""
<h2>Borrador pendiente de aprobación — {platform.upper()}</h2>
<p><strong>Caracteres:</strong> {char_count}</p>
<hr>
<blockquote style="font-family: monospace; white-space: pre-wrap; background: #f5f5f5; padding: 12px; border-left: 4px solid #d4a008;">
{text}
</blockquote>
<hr>
<p>Archivo: <code>{draft_path.name}</code></p>
<p>Para publicar manualmente, copia el texto y pégalo en {platform.title()}.</p>
{image_section}
"""

    try:
        resp = requests.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from":    FROM_EMAIL,
                "to":      [OPERATOR_EMAIL],
                "subject": f"[Abu Oracle] Borrador {platform} pendiente de aprobación",
                "html":    html_body,
            },
            timeout=10,
        )
        if resp.ok:
            print(f"[{platform}] Email de aprobación enviado a {OPERATOR_EMAIL}")
            return True
        else:
            print(f"[{platform}] Error enviando email: {resp.status_code} {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"[{platform}] Excepcion Resend: {e}")
        return False


def publish_twitter(
    text: str,
    platform: str = "twitter",
    image_bytes: bytes | None = None,
    config_type: str = "",
) -> dict:
    """
    Fase 1: guarda borrador + envía email de aprobación.
    La firma es publish_twitter(text, platform) para reutilizarla en IG/FB/TikTok.

    Args:
        text:        Texto del borrador
        platform:    Plataforma destino ("twitter", "instagram", etc.)
        image_bytes: PNG en bytes a guardar localmente (opcional)
        config_type: Tipo de configuración para nombrar el archivo de imagen

    Retorna: { 'status': 'pending_approval', 'text': str, 'draft_path': str }
    """
    draft_path = _save_draft(text, platform)

    image_path: Path | None = None
    if image_bytes:
        image_path = _save_image_draft(image_bytes, config_type or platform)

    _send_approval_email(text, platform, draft_path, image_path=image_path)
    return {
        "status":     "pending_approval",
        "text":       text,
        "draft_path": str(draft_path),
    }
