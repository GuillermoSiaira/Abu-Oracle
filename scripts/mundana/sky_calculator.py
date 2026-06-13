"""
sky_calculator.py — Cliente CLI para el motor de astrología mundana.

Este script importa y utiliza el módulo canónico `abu_engine.core.mundana`
para mostrar el estado actual del cielo, las configuraciones próximas y
el contexto histórico de una configuración.
"""

import sys
import pprint
from pathlib import Path

# Añadir el root del proyecto al path para poder importar abu_engine
# Esto asume que el script se ejecuta desde su ubicación en scripts/mundana
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from abu_engine.core import mundana


def main():
    """Función principal que ejecuta las demostraciones."""
    print("=== sky_calculator.py (cliente de abu_engine.core.mundana) ===\n")

    print("--- get_current_sky() ---")
    sky = mundana.get_current_sky()
    pprint.pprint(sky)
    print()

    print("--- get_upcoming_configurations(days_ahead=90) ---")
    upcoming = mundana.get_upcoming_configurations(days_ahead=90)
    if not upcoming:
        print("  No hay configuraciones mayores en los próximos 90 días.")
    for u in upcoming:
        days_str = f"días: {u.get('days_to_exact', 'N/A')}"
        print(f"  [{u['significance'].upper()}] {u['label']} — exacto: {u['exact_date']} "
              f"(orbe: {u['orb']}°, {days_str})")
    print()

    print("--- get_historical_context('conjunction_JS') ---")
    hist = mundana.get_historical_context("conjunction_JS")
    print(f"  density_ratio={hist['density_ratio']}x  p={hist['p_value']}")
    print(f"  {len(hist['sample_events'])} eventos de muestra encontrados:")
    if not hist['sample_events']:
        print("    (El corpus `eventos_raw.jsonl` podría no estar disponible o no contener eventos relevantes)")
    for ev in hist["sample_events"]:
        desc = ev['description']
        print(f"    - {ev['date']}: {desc[:80]}{'...' if len(desc) > 80 else ''}")
    print()


if __name__ == "__main__":
    main()
