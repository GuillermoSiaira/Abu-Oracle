---
name: sonic_capa2_transitos
description: Capa 2 del Sonic Field — voces de tránsitos activos sobre la firma natal
tipo: implementation-log
version: 2026-03-31
estado: completo
tags: [sonic, tone.js, transits, capa2]
---

# Sonic Field — Capa 2: Tránsitos Activos

Status: ✅ Implementado · Deploy producción `6a9b316` · 2026-03-31

## Concepto

La Capa 2 agrega voces efímeras sobre la firma natal estática (Capa 1). Cada tránsito activo con posición eclíptica conocida (`transit_lon`) genera un synth que suena más rápido y más suave que los planetas natales — textura en movimiento sobre el sustrato permanente.

## Mapeo astrológico → síntesis

| Parámetro astrológico | Parámetro de síntesis | Rango |
|---|---|---|
| `transit_lon` (posición actual del planeta transitante) | Frecuencia Cousto | misma escala que natales |
| Orb (0°–8°) ajustado | Volumen | −24 dB (orb=8°) → −12 dB (orb=0°) |
| trine / sextile | **Synth/sine** — consonante, flujo suave | — |
| square / opposition | **FMSynth** harmonicity=3, modIndex=8 — disonante | — |
| conjunction / resto | **AMSynth** harmonicity=1.5 — fusión | — |

**Regla de volumen**: los tránsitos son siempre softer que los planetas natales angulares (−6 dB). La firma natal domina estructuralmente; los tránsitos son coloraciones transitorias.

## Parámetros temporales

| | Natal (Capa 1) | Tránsito (Capa 2) |
|---|---|---|
| Duración de nota | 14s ± 2s | 8s ± 2s |
| Intervalo de loop | 10s | 6s |
| Stagger entre voces | 400ms | 300ms |
| Arranque | 0s (primera voz inmediata) | `nPlanetas × 0.4s` (después de todos los natales) |

El loop más corto (6s vs 10s) hace que las voces de tránsito ciclen más rápido → sensación perceptible de movimiento sobre el fondo estático natal.

## Fuente de datos: `transit_lon`

Abu Engine parchea `transit_lon` en los tránsitos activos de `/api/astro/biography`:
- Solo tránsitos con `is_active: true`
- Calcula la longitud actual por planeta único (no por tránsito), eficiente
- Si `transit_lon == null` (tránsito activo pero sin lon calculado) → la voz se omite silenciosamente

```python
# abu_engine/main.py (patch post-sort)
active_planets = {t["transit_planet"] for t in transits_window if t.get("is_active")}
current_lons = {pl: _bio_planet_lon(from_dt_utc, pl) for pl in active_planets}
for t in transits_window:
    if t.get("is_active"):
        lon = current_lons.get(t["transit_planet"])
        if lon is not None:
            t["transit_lon"] = round(lon, 4)
```

## Decisión arquitectónica

Las voces de tránsito se agregan al mismo `voicesRef[]` que las natales. `stop()`, el cleanup y `setVolume` operan sobre la totalidad sin conocer qué tipo es cada voz. La separación natal/tránsito solo existe durante la construcción del synth — no en el runtime.

## Archivos

- `next_app/components/sonic/useSonicEngine.ts` — Paso 5 dentro de `initEngine()`
- `next_app/lib/context-builder.ts` — `transit_lon?: number` en `BiographicalTimeline.transits_window`
- `abu_engine/main.py` — patch `transit_lon` en `/api/astro/biography`
- `next_app/components/sonic/sonicMapping.ts` — `buildSonicInput()` mapea `active_transits` desde `timeline.transits_window`

## Siguiente

- [[sonic_capa3_hf_paisaje]] — frecuencias moduladas por HF score de la ubicación actual del nativo

## Links

[[SONIC_FIELD_SPEC]] · [[sonic_capa1_natal]] · [[ARCHITECTURE]]
