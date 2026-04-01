# Diseño del Experimento de Distribución de Tokens

## Objetivo

Medir la distribución real de output_tokens por ruta × tipo de evento
para calibrar el MILP con datos empíricos (no estimaciones).

El percentil 99 de longitud de respuesta define el `max_tokens` mínimo
seguro por ruta — los valores actuales son heurísticos.

## Metodología

1. Correr ~100 llamadas por ruta con inputs representativos
   (26 sujetos históricos del corpus — no requiere usuarios reales)
2. Registrar `output_tokens` de cada llamada (disponible en response Anthropic)
3. Calcular: media, std, percentil 95, percentil 99
4. Percentil 99 → `max_tokens` mínimo seguro (P(truncación) < 1%)
5. Comparar con `budget(plan)` → decidir si vale degradar a Haiku

## Rutas a medir

| Ruta | Tipo de evento | Inputs representativos |
|------|---------------|------------------------|
| `screen-open` | Orientación inicial | 26 cartas × 1 llamada |
| `planet` | click_planet | 10 planetas × 26 cartas |
| `technique` (lot) | click_technique | Fortuna + Espíritu × 26 |
| `technique` (firdaria) | click_technique | Firdaria activa × 26 |
| `technique` (lunar) | click_technique | Luna × 26 |
| `city` | city_select | Top-3 ciudades × 26 |
| `domain` | domain_select | 9 dominios × 26 cartas |
| `house` | click_house | 12 casas × 26 cartas |
| `sky` | sky_open | 26 cartas × 1 llamada |
| `transit` | click_transit | Tránsitos activos × 26 |
| `chat` | conversacional | 10 preguntas tipo × 26 |

Total estimado: ~700 llamadas · costo estimado: < $2 en Sonnet/Haiku mix

## Script de ejecución

```python
# scripts/measure_token_distribution.py (pendiente de crear)
# 1. Para cada ruta: construir context_block con 26 sujetos
# 2. Llamar a la API con max_tokens=4096 (sin restricción)
# 3. Registrar response.usage.output_tokens
# 4. Computar percentiles
# 5. Exportar tabla CSV: ruta, p50, p95, p99, mean, std
```

## Output esperado

```
ruta          p50   p95   p99   mean  std
screen-open   280   520   680   310   95
planet        180   340   420   195   65
technique     150   280   360   165   55
...
```

## Conexión con MILP

Los percentiles son los parámetros `ε_r` del MILP:
- `max_tokens* = percentil_99(ruta)` → P(truncación) < 1%
- Comparar `cost(Sonnet, p99_r)` vs `cost(Haiku, p99_r)` → variable `x_r`

Ver MILP_INITIATIVE.md para la formulación completa.

## Costo del experimento

- Usando sujetos históricos (no usuarios reales): sin riesgo de privacidad
- ~700 llamadas: ~$0.50-$2 según mix de modelos
- Ejecutable en < 1 hora con script paralelo
- No requiere infraestructura adicional — solo CLI local

## Estado

Pendiente de ejecución. No requiere usuarios en producción.
Puede ejecutarse en cualquier momento post-lanzamiento.
