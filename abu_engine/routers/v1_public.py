"""
routers/v1_public.py — Endpoints de la API pública v1.

GET /api/v1/me/usage          → Consumo y plan actual de la API key.
"""
from fastapi import APIRouter
from typing import Any, Dict


router = APIRouter(
    prefix="/api/v1",
    tags=["v1-public"],
)


@router.get(
    "/me/usage",
    summary="Get API Usage and Plan",
    description="Retrieve usage statistics for your API key.",
)
async def get_usage() -> Dict[str, Any]:
    """
    Returns the current consumption and plan details for the authenticated API key.
    """
    return {
        "plan": "indie",
        "quota_used": 1234,
        "quota_limit": 10000,
        "period_start": "2026-05-01",
        "period_end": "2026-05-31",
    }
