from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

import httpx


ABU_ENGINE_URL = os.environ.get("ABU_ENGINE_URL", "http://abu-engine:8000")
LILLY_URL = os.environ.get("LILLY_URL", "https://app.abu-oracle.com")


async def get_sky() -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ABU_ENGINE_URL}/api/mundana/sky", timeout=15)
        response.raise_for_status()
        return response.json()


async def get_calendar(months: int = 1) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ABU_ENGINE_URL}/api/mundana/calendar",
            params={"months": months},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("events") or payload.get("calendar") or []


def next_seven_days(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    today = date.today()
    end = today + timedelta(days=7)
    filtered = []
    for event in events:
        try:
            event_date = date.fromisoformat(str(event.get("date", ""))[:10])
        except ValueError:
            continue
        if today <= event_date <= end:
            filtered.append(event)
    return filtered


async def ask_lilly(question: str, birth: dict[str, Any], lang: str) -> str:
    headers = {}
    token = os.environ.get("LILLY_INTERNAL_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    birth_context = {
        "birthDate": birth.get("birth_date"),
        "birthTime": birth.get("birth_time"),
        "birthCity": birth.get("birth_city"),
        "lat": birth.get("birth_lat"),
        "lon": birth.get("birth_lon"),
        "lang": lang,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LILLY_URL}/api/chat",
            json={
                "messages": [{"role": "user", "content": question}],
                "context": {"meta": birth_context, "calculations": None},
                "birthData": birth_context,
                "lang": lang,
                "session_id": f"telegram-{birth.get('telegram_user_id', 'unknown')}",
            },
            timeout=30,
            headers=headers,
        )
        response.raise_for_status()
        return response.json().get("response", "-")
