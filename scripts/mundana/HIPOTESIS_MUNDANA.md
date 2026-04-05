# Hipótesis Mundana A — Correlación temporal

**ID:** H_mundana_A  
**Fecha registro:** 2026-04-05  
**Estado:** pendiente

## Enunciado
Las conjunciones Júpiter-Saturno y las oposiciones Marte-Saturno 
coinciden con clusters de eventos históricos de alta intensidad con 
frecuencia significativamente mayor que el azar.

## Métrica
Densidad de eventos en ventana ±30 días alrededor de configuraciones 
planetarias clave vs densidad baseline (días sin configuración activa).

## Test estadístico
Mann-Whitney U — mismo approach que HF_v6.

## Dataset
data/mundana/eventos_raw.jsonl — 23.636 eventos, año 8-2069.

## Efemérides requeridas
pyswisseph + DE431 (cobertura -5400 a +5400).
Archivos: sepl_m54.se1, semo_m54.se1, seas_m54.se1
Fuente: https://www.astro.com/ftp/swisseph/ephe/

## Resultado esperado
Densidad eventos en ventana configuración > densidad baseline (p < 0.05).

## Archivos de output
- scripts/mundana/correlator_temporal.py
- data/mundana/correlations_temporal.json
- data/mundana/RESULTADOS_H_mundana_A.md
