"""
Profecciones (Profections)
Sistema de direcciones primarias anual para determinar el regente del año.
"""

from datetime import datetime, timedelta
from typing import Dict


SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Regentes tradicionales de cada signo
SIGN_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}


def calculate_profection_year(birth_date: datetime, current_date: datetime = None, utc_offset: float = 0.0) -> Dict:
    """
    Calcula la profección anual del Ascendente.

    El Ascendente avanza un signo por año de vida.

    Args:
        birth_date: Fecha de nacimiento (UTC)
        current_date: Fecha actual (default: hoy)
        utc_offset: Offset UTC del lugar de nacimiento en horas (ej: -3 para Argentina)

    Returns:
        dict: {
            "year": int (edad),
            "sign_offset": int (0-11),
            "note": str
        }
    """
    if current_date is None:
        current_date = datetime.utcnow()

    # Convertir birth_date UTC a fecha local usando el offset del nativo.
    # Ejemplo: 1978-07-06T00:15Z + offset(-3h) → 1978-07-05 21:15 local
    birth_date_local = birth_date + timedelta(hours=utc_offset)
    if hasattr(birth_date_local, 'tzinfo') and birth_date_local.tzinfo is not None:
        birth_date_local = birth_date_local.replace(tzinfo=None)
    if hasattr(current_date, 'tzinfo') and current_date.tzinfo is not None:
        current_date = current_date.replace(tzinfo=None)

    # Calcular edad (años completos) usando la fecha LOCAL de nacimiento
    age = current_date.year - birth_date_local.year
    if (current_date.month, current_date.day) < (birth_date_local.month, birth_date_local.day):
        age -= 1
    
    # Offset de signo (módulo 12)
    sign_offset = age % 12
    
    return {
        "year": age,
        "sign_offset": sign_offset,
        "note": f"Profection advances {sign_offset} signs from natal Ascendant"
    }


def get_profected_sign(natal_asc_sign: str, year_offset: int) -> str:
    """
    Calcula el signo profectado dado el ASC natal y el offset de año.
    
    Args:
        natal_asc_sign: Signo del Ascendente natal
        year_offset: Offset de años (0-11)
    
    Returns:
        str: Signo profectado
    """
    if natal_asc_sign not in SIGNS:
        raise ValueError(f"Invalid sign: {natal_asc_sign}")
    
    natal_index = SIGNS.index(natal_asc_sign)
    profected_index = (natal_index + year_offset) % 12
    
    return SIGNS[profected_index]


def calculate_annual_profection(
    birth_date: datetime,
    natal_asc_sign: str,
    current_date: datetime = None,
    utc_offset: float = 0.0,
) -> Dict:
    """
    Calcula la profección anual completa con regente del año.

    Args:
        birth_date: Fecha de nacimiento (UTC)
        natal_asc_sign: Signo del Ascendente natal (ej: "Gemini")
        current_date: Fecha actual (default: hoy)
        utc_offset: Offset UTC del lugar de nacimiento en horas (ej: -3 para Argentina)

    Returns:
        dict: {
            "year": int,
            "profected_sign": str,
            "time_lord": str (planeta regente del año),
            "sign_offset": int
        }
    """
    profection = calculate_profection_year(birth_date, current_date, utc_offset=utc_offset)
    
    profected_sign = get_profected_sign(natal_asc_sign, profection["sign_offset"])
    time_lord = SIGN_RULERS[profected_sign]
    
    return {
        "year": profection["year"],
        "profected_sign": profected_sign,
        "time_lord": time_lord,
        "sign_offset": profection["sign_offset"]
    }


def calculate_monthly_profection(
    birth_date: datetime,
    natal_asc_sign: str,
    current_date: datetime = None
) -> Dict:
    """
    Calcula la profección mensual (opcional, más refinada).
    
    El signo del año se subdivide: cada mes avanza un signo.
    
    Returns:
        dict: {
            "month": int (0-11 dentro del año),
            "monthly_sign": str,
            "monthly_lord": str
        }
    """
    if current_date is None:
        current_date = datetime.utcnow()

    # Normalize timezone awareness like in annual calculation
    if hasattr(birth_date, 'tzinfo') and birth_date.tzinfo is not None:
        birth_date = birth_date.replace(tzinfo=None)
    if hasattr(current_date, 'tzinfo') and current_date.tzinfo is not None:
        current_date = current_date.replace(tzinfo=None)
    
    # Calcular profección anual primero
    annual = calculate_annual_profection(birth_date, natal_asc_sign, current_date)
    
    # Calcular mes dentro del año solar (desde cumpleaños)
    last_birthday = datetime(current_date.year, birth_date.month, birth_date.day)
    if last_birthday > current_date:
        last_birthday = datetime(current_date.year - 1, birth_date.month, birth_date.day)
    
    # Meses desde último cumpleaños
    months_since = (current_date.year - last_birthday.year) * 12 + (current_date.month - last_birthday.month)
    month_offset = months_since % 12
    
    # Signo mensual: profección anual + offset mensual
    annual_sign_index = SIGNS.index(annual["profected_sign"])
    monthly_sign_index = (annual_sign_index + month_offset) % 12
    monthly_sign = SIGNS[monthly_sign_index]
    
    return {
        "month": month_offset,
        "monthly_sign": monthly_sign,
        "monthly_lord": SIGN_RULERS[monthly_sign]
    }
