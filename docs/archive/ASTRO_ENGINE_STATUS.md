# ASTRO_ENGINE_STATUS

Estado técnico del motor Abu (cálculo astro) — actualizado: 2026-02-25.

## Cobertura garantizada
- **Rango temporal:** ~1550–2650 (efemérides JPL DE440s). Operativo para casos solicitados (~1600–2600).
- **Cobertura espacial:** Latitudes -90..+90, longitudes -180..+180. Coordenadas geocéntricas con normalización a UTC (DST histórico manejado vía tzdata del sistema).

## Dependencias clave
- **Efemérides:** `abu_engine/data/de440s.bsp` (JPL DE440s).
- **Zona horaria:** `tzdata` instalada en entorno (Windows requiere paquete explícito).
- **Python:** 3.11 recomendado para binarios precompilados (pyswisseph disponible en 3.11; en 3.13 se necesita toolchain para compilar).
- **Librerías núcleo:** `skyfield`, `pyswisseph` (para casas/ASC/MC cuando se habiliten), `numpy`, `pandas`, `fastapi`.

## Limitaciones conocidas
- **Sistemas de casas en latitudes extremas:** Ahora el cálculo intenta Placidus y, si falla o |lat|>66°, hace fallback automático a Whole Sign (`house_system_used` indica cuál se aplicó). La inestabilidad de Placidus en polos sigue siendo del método, no del motor.
- **Fuera de rango efemérides:** Más allá de ~2650 o antes de ~1550 no se garantiza precisión.

## Notas operativas
- Normalizar siempre la entrada a UTC antes de llamar al API; DST histórico queda resuelto si la app cliente convierte a UTC con tzdata.
- Los contratos actuales no cambian: endpoints Abu siguen igual; este documento solo registra capacidades y límites.
