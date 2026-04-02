# Abu Chrono – Motor Astronómico JAX: Propósito y Relación Arquitectónica

**Fecha:** 2026-01-09  
**Autor:** Abu Oracle Project

---

## Propósito del Módulo `abu_chrono/planets.py`
- Proveer un motor astronómico minimalista, vectorizado y diferenciable usando JAX.
- Simular posiciones y movimientos planetarios (incluyendo retrogradación) de manera eficiente, reproducible y auditable.
- Servir como laboratorio para la migración de lógica astronómica tradicional (Skyfield, PyEphem, core.chart, core.ephemeris) a un stack JAX puro.
- Permitir benchmarking, instrumentación y validación de cálculos astronómicos “core” bajo la estrategia JAX Core (ver docs/ABU_MEDICION_EFICIENCIA_COMPUTACIONAL_2026-01-03.md).
- Facilitar la integración futura de Harmony Fields y funciones de costo diferenciables para optimización y relocación astrológica.

---

## Relación con Otros Módulos
- **Compite/reemplaza parcialmente:**
  - `core.chart`, `core.ephemeris`, motores basados en Skyfield/PyEphem (para cálculos planetarios básicos y experimentos de eficiencia).
- **Se complementa con:**
  - Módulos de alto nivel (`forecast`, `scoring`, `interpret`), que pueden consumir sus outputs vectorizados y diferenciables.
- **Visión:** Primer paso hacia un stack astronómico 100% JAX, auditable y acelerado, compatible con la visión de reputación y eficiencia de Abu.

---

## Características Clave
- Cálculo funcional, sin efectos colaterales, vectorizable y jiteable.
- Telemetría básica (tiempos de ejecución, % retrogradación) para benchmarking.
- Modular y extensible: permite agregar cuerpos, refinar física, conectar con otros módulos.

---

## Referencias Cruzadas
- docs/ABU_MEDICION_EFICIENCIA_COMPUTACIONAL_2026-01-03.md
- docs/ABU_ORACLE_EFICIENCIA_REGULARIDAD_REPUTACION_2025-12-28.md
- docs/ABU_ENGINE_ASTRO_VARIABLES_AND_ROADMAP_2025-12-23.md

---

Este documento resume la intención y el rol arquitectónico de `abu_chrono/planets.py` en el ecosistema Abu Oracle, y debe acompañar la evolución del stack JAX en el proyecto.
