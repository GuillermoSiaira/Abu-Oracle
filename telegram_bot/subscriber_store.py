from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore


COLLECTION = "telegram_subscribers"


def _db():
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.ApplicationDefault())
    return firestore.client()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def ensure_user(user_id: str, lang: str = "es") -> dict[str, Any]:
    ref = _db().collection(COLLECTION).document(user_id)
    snap = ref.get()
    if snap.exists:
        data = snap.to_dict() or {}
        if "lang" not in data:
            ref.set({"lang": lang, "updated_at": _now()}, merge=True)
        return data

    data = {
        "lang": lang,
        "subscribed": False,
        "birth_date": None,
        "birth_time": None,
        "birth_city": None,
        "birth_lat": None,
        "birth_lon": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    ref.set(data)
    return data


async def get_lang(user_id: str) -> str | None:
    snap = _db().collection(COLLECTION).document(user_id).get()
    if not snap.exists:
        return None
    return (snap.to_dict() or {}).get("lang")


async def set_lang(user_id: str, lang: str) -> None:
    await ensure_user(user_id, lang=lang)
    _db().collection(COLLECTION).document(user_id).set(
        {"lang": lang, "updated_at": _now()},
        merge=True,
    )


async def subscribe(user_id: str, lang: str = "es") -> None:
    await ensure_user(user_id, lang=lang)
    _db().collection(COLLECTION).document(user_id).set(
        {"subscribed": True, "lang": lang, "updated_at": _now()},
        merge=True,
    )


async def unsubscribe(user_id: str) -> None:
    await ensure_user(user_id)
    _db().collection(COLLECTION).document(user_id).set(
        {"subscribed": False, "updated_at": _now()},
        merge=True,
    )


async def set_birth(user_id: str, birth: dict[str, Any]) -> None:
    await ensure_user(user_id)
    payload = {
        "birth_date": birth.get("birth_date"),
        "birth_time": birth.get("birth_time"),
        "birth_city": birth.get("birth_city"),
        "birth_lat": birth.get("birth_lat"),
        "birth_lon": birth.get("birth_lon"),
        "updated_at": _now(),
    }
    _db().collection(COLLECTION).document(user_id).set(payload, merge=True)


async def get_birth(user_id: str) -> dict[str, Any] | None:
    snap = _db().collection(COLLECTION).document(user_id).get()
    if not snap.exists:
        return None
    data = snap.to_dict() or {}
    if not data.get("birth_date") or not data.get("birth_time") or not data.get("birth_city"):
        return None
    return data


async def list_subscribers() -> list[dict[str, Any]]:
    query = _db().collection(COLLECTION).where("subscribed", "==", True).stream()
    subscribers: list[dict[str, Any]] = []
    for doc in query:
        data = doc.to_dict() or {}
        data["telegram_user_id"] = doc.id
        subscribers.append(data)
    return subscribers
