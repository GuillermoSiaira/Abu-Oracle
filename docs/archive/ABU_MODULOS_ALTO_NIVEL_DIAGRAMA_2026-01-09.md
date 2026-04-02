# Abu Oracle – Módulos de Alto Nivel: Diagrama y Descripción

**Fecha:** 2026-01-09  
**Autor:** Abu Oracle Project

---

## Diagrama de Dependencias (Simplificado)

```
[abu_chrono/planets.py] ──▶ [core/chart.py, core/ephemeris.py]
         │
         ▼
[core/forecast.py] ──▶ [core/scoring.py] ──▶ [core/solar_return.py, core/life_cycles.py]
         │                    │
         ▼                    ▼
[core/igp_optimizer.py]   [core/solar_return_ranking.py]
         │                    │
         ▼                    ▼
[core/interpreter_llm.py] ──▶ [main.py (API)]
         │
         ▼
[services/logger.py, logging.py, pubsub.py]
```

---

## Descripción de Módulos de Alto Nivel

- **abu_engine/main.py**: Orquestador principal. Expone la API, integra todos los módulos y define los endpoints públicos.
- **core/forecast.py**: Genera series temporales, predicciones y análisis de tendencias astrológicas a partir de datos planetarios y de eventos.
- **core/life_cycles.py**: Detecta y modela ciclos vitales (retornos de planetas lentos, oposiciones, cuadraturas) y los expone como eventos clave.
- **core/scoring.py**: Calcula scores compuestos, rankings y métricas de síntesis a partir de outputs astronómicos y reglas astrológicas.
- **core/solar_return.py, solar_return_ranking.py, solar_return_summary.py**: Implementan lógica avanzada de retornos solares, cálculo de fechas, análisis de ubicaciones y ranking de ciudades óptimas.
- **core/interpreter_llm.py**: Integra la capa interpretativa (Lilly/LLM), conectando cálculos y eventos con generación de narrativa y respuestas estructuradas.
- **core/igp_optimizer.py**: Realiza optimización geodésica y búsqueda de ubicaciones óptimas para eventos astrológicos, usando algoritmos de optimización y scoring espacial.
- **services/logger.py, logging.py, pubsub.py**: Infraestructura de telemetría, logging estructurado y comunicación entre servicios y módulos.

---

## Relación con Módulos de Bajo Nivel
- **core/chart.py, core/ephemeris.py, abu_chrono/planets.py**: Proveen los cálculos astronómicos básicos (posiciones, velocidades, efemérides) que alimentan a los módulos de alto nivel.
- Los módulos de alto nivel consumen estos outputs y los combinan para ofrecer análisis, predicciones, interpretaciones y recomendaciones completas.

---

## Referencias Cruzadas
- docs/ABU_MEDICION_EFICIENCIA_COMPUTACIONAL_2026-01-03.md
- docs/ABU_CHRONO_PLANETS_PROPÓSITO_2026-01-09.md
- docs/ABU_ORACLE_EFICIENCIA_REGULARIDAD_REPUTACION_2025-12-28.md

---

Este documento debe acompañar la documentación técnica y servir de guía para la integración y evolución del stack Abu Oracle.
