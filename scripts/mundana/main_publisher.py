"""
Entry point for the Abu Oracle mundana publisher Cloud Run Job.

Modes:
  mundana  - publish a significant current-sky configuration, or a calendar fallback
  doctrine - publish one HF/doctrinal system concept
  auto     - try mundana first, then doctrine
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

import requests

sys.path.insert(0, str(Path(__file__).parent))

from calendar_content import CalendarEvent, generate_calendar_post, should_announce
from content_generator import (
    generate_doctrine_post,
    generate_post,
    get_doctrine_slide,
    _select_style,
)
from onchain_registry import register_prediction
from publication_filter import get_best_configuration, record_publication, should_publish
from publishers import publish_all


DEFAULT_PLATFORMS = ["farcaster", "bluesky", "twitter"]
REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = REPO_ROOT / "data" / "mundana" / "logs"

ABU_ENGINE_URL = os.environ.get("ABU_ENGINE_URL", "http://localhost:8000")
CALENDAR_MONTHS = int(os.environ.get("CALENDAR_MONTHS", "3"))
LANGUAGES = [l.strip().lower() for l in os.environ.get("LANGUAGES", os.environ.get("LANG", "es")).split(",") if l.strip()]


def _get_platforms() -> list[str]:
    raw = os.environ.get("PLATFORMS", ",".join(DEFAULT_PLATFORMS))
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def _is_dry_run() -> bool:
    return os.environ.get("DRY_RUN", "false").lower() == "true"


def _active_languages(dry_run: bool) -> list[str]:
    """Preview all requested languages in dry runs; publish one rotating language in real runs."""
    languages = LANGUAGES or ["es"]
    if dry_run or len(languages) <= 1:
        return languages
    index = date.today().toordinal() % len(languages)
    selected = languages[index]
    print(f"[main] Multilang publish guard: selected {selected} for today from {languages}")
    return [selected]


def _log_run(entries: list[dict]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = LOG_DIR / f"{ts}_run.json"
    path.write_text(
        json.dumps({"timestamp": ts, "entries": entries}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[main] Log: {path.name}")


def fetch_calendar() -> list[dict]:
    """Fetch /api/mundana/calendar?months=N from Abu Engine."""
    try:
        response = requests.get(
            f"{ABU_ENGINE_URL}/api/mundana/calendar",
            params={"months": CALENDAR_MONTHS},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("events") or payload.get("calendar") or []
    except Exception as exc:
        print(f"[calendar] fetch failed: {exc}")
        return []


def _upcoming_calendar_events(dry_run: bool) -> list[dict]:
    if dry_run:
        return [
            {
                "type": "mercury_retrograde",
                "date": date.today().isoformat(),
                "description": "Mercurio estaciona retrogrado: revision, demora y relectura del juicio.",
                "significance": "medium",
                "details": {"dry_run": True},
            }
        ]

    today = date.today().isoformat()
    candidates = []
    for raw in fetch_calendar():
        if raw.get("significance") not in ("high", "medium"):
            continue
        try:
            event = CalendarEvent(**raw)
        except TypeError as exc:
            print(f"[calendar] skipping malformed event: {exc}")
            continue
        if should_announce(event, today):
            candidates.append(raw)
    candidates.sort(key=lambda e: (e.get("significance") != "high", e.get("date", "")))
    return candidates


def _dry_content(platform: str, lang: str, source: str, label: str) -> dict:
    text = f"[DRY_RUN/{lang}/{platform}] {source}: {label}"
    return {
        "text": text,
        "hashtags": [],
        "thread": None,
        "reddit_title": None,
        "image_prompt": "",
        "image_bytes": None,
        "image_alt": None,
        "platform": platform,
        "config_type": source,
        "style": "dry_run",
        "lang": lang,
    }


def _publish_platforms(
    platforms: list[str],
    languages: list[str],
    content_factory: Callable[[str, str], dict],
    config_for_record: dict | None,
    dry_run: bool,
) -> tuple[list[dict], str | None]:
    run_log: list[dict] = []
    first_published: str | None = None

    approval_mode = os.environ.get("APPROVAL_MODE", "direct").lower()
    telegram_bot_url = os.environ.get("TELEGRAM_BOT_URL", "http://localhost:8000")
    internal_secret = os.environ.get("INTERNAL_SECRET", "")

    for lang in languages:
        queue_payload = None
        queue_platforms = []

        for platform in platforms:
            print(f"\n[main] Platform: {platform} | Lang: {lang}")

            try:
                content = content_factory(platform, lang)
                print(f"       Text ({len(content['text'])} chars): {content['text'][:120]}")
            except Exception as exc:
                print(f"       ERROR generating content: {exc}")
                run_log.append({"platform": platform, "lang": lang, "status": "error_generation", "detail": str(exc)})
                continue

            if dry_run:
                print("       [DRY_RUN] No publish/network dispatch.")
                run_log.append({
                    "platform": platform,
                    "lang": lang,
                    "status": "dry_run",
                    "style": content.get("style"),
                    "config_type": content.get("config_type"),
                    "text_preview": content["text"][:160],
                })
                continue

            if approval_mode == "direct" or platform == "bluesky":
                try:
                    result = publish_all(platform, content, lang=lang)
                    print(f"       Result: {result.get('status')} - {result}")
                except Exception as exc:
                    print(f"       ERROR publishing: {exc}")
                    run_log.append({"platform": platform, "lang": lang, "status": "error_publish", "detail": str(exc)})
                    continue

                try:
                    meta = config_for_record or {"type": content.get("config_type", "unknown")}
                    register_prediction(content["text"], meta, platform=platform)
                except Exception as exc:
                    print(f"       Warning: registry failed: {exc}")

                run_log.append({
                    "platform": platform,
                    "lang": lang,
                    "status": result.get("status"),
                    "style": content.get("style"),
                    "config_type": content.get("config_type"),
                    "detail": result,
                })

                if result.get("status") in ("published", "pending_approval") and first_published is None:
                    first_published = platform
            else:
                import uuid
                if queue_payload is None:
                    queue_payload = {
                        "id": str(uuid.uuid4()),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "status": "pending",
                        "cielo_fecha": date.today().isoformat(),
                        "configuracion": (config_for_record or {}).get("label") or (config_for_record or {}).get("type", "unknown"),
                        "estilo": content.get("style"),
                        "lang": lang,
                        "posts": {},
                        "doctrina_usada": content.get("doctrina_usada", []),
                        "approved_by": None,
                        "approved_at": None,
                        "published_at": None,
                        "publish_errors": {}
                    }
                
                post_data = {
                    "text": content["text"],
                    "chars": len(content["text"]),
                }
                
                if content.get("image_bytes"):
                    from google.cloud import storage
                    bucket_name = os.environ.get("GCS_DRAFTS_BUCKET")
                    if not bucket_name:
                        print("       ERROR: GCS_DRAFTS_BUCKET not set. Cannot queue image.")
                    else:
                        try:
                            storage_client = storage.Client()
                            bucket = storage_client.bucket(bucket_name)
                            blob_name = f"drafts/{queue_payload['id']}_{platform}.png"
                            blob = bucket.blob(blob_name)
                            blob.upload_from_string(content["image_bytes"], content_type="image/png")
                            post_data["image_gcs_uri"] = f"gs://{bucket_name}/{blob_name}"
                            print(f"       [queue] Image uploaded to {post_data['image_gcs_uri']}")
                        except Exception as exc:
                            print(f"       ERROR uploading image to GCS: {exc}")
                
                queue_payload["posts"][platform] = post_data
                queue_platforms.append(platform)
                
                run_log.append({
                    "platform": platform,
                    "lang": lang,
                    "status": "queued",
                    "style": content.get("style"),
                    "config_type": content.get("config_type"),
                    "queue_id": queue_payload["id"]
                })

        if queue_payload and queue_platforms:
            try:
                from google.cloud import firestore
                db = firestore.Client()
                db.collection("post_queue").document(queue_payload["id"]).set(queue_payload)
                print(f"       [queue] Document {queue_payload['id']} saved to Firestore post_queue.")
                
                notify_url = f"{telegram_bot_url}/admin_notify_queue"
                resp = requests.post(
                    notify_url,
                    json={"queue_id": queue_payload["id"]},
                    headers={"X-Internal-Secret": internal_secret},
                    timeout=10
                )
                if resp.ok:
                    print("       [queue] Admin notified via telegram_bot.")
                else:
                    print(f"       [queue] Failed to notify admin: {resp.status_code} {resp.text}")
                    
                if first_published is None:
                    first_published = queue_platforms[0]
            except Exception as exc:
                print(f"       ERROR queueing draft to Firestore/Telegram: {exc}")

    return run_log, first_published


def main() -> int:
    print(f"[main] Abu Oracle Mundana Publisher - {datetime.now(timezone.utc).isoformat()}")

    dry_run = _is_dry_run()
    platforms = _get_platforms()
    publish_mode = os.environ.get("PUBLISH_MODE", "mundana").lower()
    languages = _active_languages(dry_run)

    if dry_run:
        print("[main] DRY_RUN=true - preview only; no publish calls and no Claude/API fetches.")

    print(f"[main] Mode: {publish_mode} | Languages: {languages} | Platforms: {', '.join(platforms)}")

    run_log: list[dict] = []
    first_published: str | None = None
    mundana_config: dict | None = None

    if publish_mode in ("mundana", "auto"):
        publish_current_sky = False if dry_run else should_publish()
        if publish_current_sky:
            mundana_config = get_best_configuration()

        if mundana_config:
            label = mundana_config.get("label", mundana_config.get("type", "mundana"))
            content_style = os.environ.get("CONTENT_STYLE") or _select_style(mundana_config)
            print(f"\n[main] Sky config: {label} | Style: {content_style}")

            history = None
            try:
                from sky_calculator import get_historical_context
                history = get_historical_context(mundana_config.get("type", ""))
            except Exception as exc:
                print(f"[main] Warning: historical context unavailable: {exc}")

            def sky_factory(platform: str, lang: str) -> dict:
                if dry_run:
                    return _dry_content(platform, lang, "mundana", label)
                return generate_post(mundana_config, platform=platform, history=history, style=content_style, lang=lang)

            sky_log, first_published = _publish_platforms(platforms, languages, sky_factory, mundana_config, dry_run)
            run_log.extend(sky_log)
        else:
            upcoming = _upcoming_calendar_events(dry_run)
            if upcoming:
                selected = upcoming[0]
                event = CalendarEvent(**selected)
                print(f"\n[main] Calendar fallback: {event.date} | {event.description}")

                def calendar_factory(platform: str, lang: str) -> dict:
                    if dry_run:
                        return _dry_content(platform, lang, f"calendar_{event.type}", event.description)
                    return generate_calendar_post(event, platform, lang)

                calendar_log, first_calendar = _publish_platforms(platforms, languages, calendar_factory, None, dry_run)
                run_log.extend(calendar_log)
                first_published = first_published or first_calendar
            elif publish_mode == "mundana":
                print("[main] Nothing to publish today.")
                _log_run(run_log)
                return 0
            else:
                print("[main] No mundana/calendar content - fallback to doctrine.")

    if publish_mode == "doctrine" or (publish_mode == "auto" and not run_log):
        slide = get_doctrine_slide()
        print(f"\n[main] Doctrine slide: {slide['id']}")

        def doctrine_factory(platform: str, lang: str) -> dict:
            if dry_run:
                return _dry_content(platform, lang, f"doctrine_{slide['id']}", slide.get("title_es", slide["id"]))
            return generate_doctrine_post(slide, platform=platform, lang=lang)

        doctrine_log, first_doctrine = _publish_platforms(platforms, languages, doctrine_factory, None, dry_run)
        run_log.extend(doctrine_log)
        first_published = first_published or first_doctrine

    if not dry_run and first_published:
        if mundana_config:
            config_type = mundana_config.get("type", "unknown")
        else:
            first_entry = next((e for e in run_log if e.get("config_type")), {})
            config_type = first_entry.get("config_type", "unknown")
        record_publication(config_type, first_published)
        print(f"\n[main] Cooldown recorded - platform: {first_published}")

    _log_run(run_log)
    published_count = sum(1 for e in run_log if e.get("status") in ("published", "pending_approval"))
    print(f"\n[main] Done. Entries: {len(run_log)} | Published/pending: {published_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
