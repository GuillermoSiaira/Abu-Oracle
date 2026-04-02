# ROADMAP_NEXT

Prioridades y líneas de trabajo (2026-02-25)

## Corto plazo (API / skill)
- Exponer Abu como skill/Tool API-first (sin depender de UI): describir contratos actuales (chart, forecast, life-cycles, solar-return, chart-detailed) y empaquetarlos como función callable por agente.
- Contenedor ligero para Runpod con solo Abu + dependencias de cálculo (sin Next.js).
- Healthcheck y logging mínimo para agente (latencia, errores de cálculo).

## Mediano plazo (UI y geocoding)
- Entrada por ciudad: integrar geocoding (ej. Nominatim/Geonames) para resolver lat/lon desde nombre de ciudad antes de llamar a Abu.
- UI simplificada opcional: formulario mínimo + selector de ciudad y fecha (opcional si se usa solo agente).
- Cache local de ciudades frecuentes para latencias bajas.

## Largo plazo (investigación)
- Evaluar sistemas de casas alternativos/robustos para altas latitudes (p.ej. Porphyry, Whole Sign adaptado, experimentales) fuera del core estable.
- Benchmarks de precisión y estabilidad vs Placidus/Koch en latitudes extremas.

## Arquitectura mínima: Abu como skill en agente OpenClaw (Runpod)
- **API-first:** Reutilizar endpoints REST de Abu. Definir herramienta/skill en el agente que haga fetch a: `/api/astro/chart`, `/forecast`, `/life-cycles`, `/solar-return`, `/chart-detailed`.
- **Empaquetado:** Imagen ligera con Abu + efemérides + tzdata. Sin frontend. Montar `de440s.bsp` en la imagen.
- **Punto de entrada agente:** OpenClaw llama a la skill vía HTTP al pod; skill hace pass-through a Abu y devuelve JSON tal cual (no modificar contratos).
- **Observabilidad mínima:** `/health` simple, logs estructurados (latencia, status_code, endpoint).
- **Seguridad:** Rate limiting básico en el pod; validar parámetros antes de reenviar a Abu para evitar cargas inválidas.
- **Red:** Exponer puerto HTTP interno; usar API key opcional en el pod para llamadas del agente.
