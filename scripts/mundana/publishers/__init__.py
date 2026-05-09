"""
publishers/ - Platform dispatchers.

AUTO:
  Farcaster, Bluesky, Reddit

SEMI-AUTO:
  Twitter/X, Instagram, Facebook, TikTok
"""

from .farcaster_publisher import publish_farcaster
from .bluesky_publisher import publish_bluesky
from .twitter_publisher import publish_twitter
from .reddit_publisher import publish_reddit

__all__ = [
    "publish_farcaster",
    "publish_bluesky",
    "publish_twitter",
    "publish_reddit",
    "publish_all",
]


def publish_all(platform: str, content: dict, lang: str = "es") -> dict:
    """
    Dispatch by platform.
    lang is accepted for multilingual runs; account routing is handled outside.

    Returns: { 'status': 'published' | 'pending_approval' | 'error', 'detail': ... }
    """
    if platform == "farcaster":
        return publish_farcaster(content["text"])
    if platform == "bluesky":
        return publish_bluesky(
            content["text"],
            image_bytes=content.get("image_bytes"),
            image_alt=content.get("image_alt", ""),
        )
    if platform == "reddit":
        return publish_reddit(content["text"], title=content.get("reddit_title"))
    if platform in ("twitter", "instagram", "facebook", "tiktok"):
        return publish_twitter(
            content["text"],
            platform=platform,
            image_bytes=content.get("image_bytes"),
            config_type=content.get("config_type", ""),
        )
    return {"status": "error", "detail": f"Unknown platform: {platform}"}
