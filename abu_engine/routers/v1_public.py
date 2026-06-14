"""
routers/v1_public.py — Endpoints de la API pública v1.

GET /api/v1/me/usage          → Consumo y plan actual de la API key.
"""
from fastapi import APIRouter, Depends
from typing import Any, Dict

from core.auth import verify_token_or_service_key, DEFAULT_DAILY_LIMITS


router = APIRouter(
    prefix="/api/v1",
    tags=["v1-public"],
)


@router.get(
    "/me/usage",
    summary="Get API Usage and Plan",
    description="Retrieve usage statistics for your API key.",
)
async def get_usage(user: dict = Depends(verify_token_or_service_key)) -> Dict[str, Any]:
    """
    Returns the current consumption and plan details for the authenticated API key.
    """
    api_key = user.get("api_key_used", "")
    plan = user.get("plan", "free")
    usage_data = user.get("usage", {})
    calls_today = usage_data.get("calls_today", 0)

    # El límite diario se lee del doc, con fallback a los defaults del plan
    daily_limit = user.get("daily_limit") or DEFAULT_DAILY_LIMITS.get(plan, 20)

    return {
        "key_prefix": f"{api_key[:8]}..." if api_key else "N/A",
        "tier": plan,
        "usage": {
            "total_calls": user.get("quota_used", 0),
            "calls_today": calls_today,
            "calls_this_month": user.get("quota_used", 0), # Nota: Mismo que total_calls por ahora
            "last_call_date": usage_data.get("daily_date"),
            "by_endpoint": usage_data.get("by_endpoint", {}), # Futuro, según spec
        },
        "limits": {
            "daily": daily_limit,
            "monthly": user.get("quota_limit", 0),
            "remaining_today": max(0, daily_limit - calls_today),
        },
    }
