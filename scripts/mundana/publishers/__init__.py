"""
publishers/ — Publicadores por plataforma.

Farcaster y Bluesky son prioritarios (gratuitos, sin límites estrictos).
Twitter/Instagram/Facebook/TikTok requieren aprobación manual en Fase 1.
"""

from .farcaster_publisher import publish_farcaster
from .bluesky_publisher   import publish_bluesky
from .twitter_publisher   import publish_twitter

__all__ = ["publish_farcaster", "publish_bluesky", "publish_twitter", "publish_all"]


def publish_all(platform: str, content: dict) -> dict:
    """
    Dispatch según plataforma.

    Retorna: { 'status': 'published' | 'pending_approval' | 'error', 'detail': ... }
    """
    if platform == "farcaster":
        return publish_farcaster(content["text"])
    if platform == "bluesky":
        return publish_bluesky(content["text"])
    if platform in ("twitter", "instagram", "facebook", "tiktok"):
        return publish_twitter(content["text"], platform=platform)
    return {"status": "error", "detail": f"Unknown platform: {platform}"}
