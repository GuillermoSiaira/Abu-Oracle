"""
routers/mundana.py — Endpoints de astrología mundana.

GET /api/mundana/sky          → cielo actual + configuraciones activas
GET /api/mundana/forecast     → configuraciones próximas (filtradas por significancia)
GET /api/mundana/history      → estadísticas empíricas + eventos representativos
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query
import swisseph as swe

from core.mundana import get_current_sky, get_upcoming_configurations, get_historical_context
from core.mundana_calendar import build_mundana_calendar

router = APIRouter(tags=["mundana"])


@router.get("/sky")
def sky_endpoint(
    date: Optional[str] = Query(
        default=None,
        description="Fecha en formato YYYY-MM-DD. Si se omite, usa la fecha y hora actual.",
    )
):
    """
    Posiciones planetarias y configuraciones activas para una fecha dada (o la actual).

    Retorna configuraciones mundanas detectadas (conjunciones, oposiciones, stellia)
    con estadísticas empíricas de H_mundana_A cuando están disponibles.
    """
    ref_dt = None
    if date:
        try:
            # Se asume mediodía UTC para una fecha dada, para evitar ambigüedades de zona horaria.
            ref_dt = datetime.fromisoformat(date).replace(
                hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
        except ValueError:
            # Si el formato es inválido, se usa la fecha actual (ref_dt=None)
            pass
    return get_current_sky(ref_dt=ref_dt)


@router.get("/forecast")
def forecast_endpoint(days: int = Query(default=90, ge=1, le=365)):
    """
    Configuraciones mundanas próximas en ventana de N días.

    Ordena por fecha exacta ascendente.
    Incluye configuraciones de baja significancia (p_value=None) para referencia.
    """
    return get_upcoming_configurations(days_ahead=days)


@router.get("/history")
def history_endpoint(
    config_type: str = Query(
        default="conjunction_JS",
        description="Tipo de configuración: conjunction_JS, opposition_MS, conjunction_MS, ...",
    ),
    limit: int = Query(default=5, ge=1, le=20),
):
    """
    Estadísticas empíricas y eventos representativos del corpus (H_mundana_A).

    Retorna p_value y density_ratio de la hipótesis confirmada.
    El corpus completo (23.636 eventos) no está disponible en producción —
    los eventos de muestra solo se retornan en entorno de desarrollo local.
    """
    return get_historical_context(config_type=config_type, limit=limit)


@router.get("/calendar")
async def calendar_endpoint(
    months: int = Query(default=12, ge=1, le=24),
):
    """
    Current mundane sky plus a chronological calendar for the next N months.
    """
    now = datetime.now(timezone.utc)
    jd_now = swe.julday(
        now.year,
        now.month,
        now.day,
        now.hour + now.minute / 60 + now.second / 3600,
    )

    return {
        "current_sky": get_current_sky(),
        "calendar": build_mundana_calendar(jd_now, months_ahead=months),
    }
