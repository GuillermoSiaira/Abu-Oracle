# Dataset Audit Report

## Overview
- Registros totales: **5359**
- Campos detectados: 17

## Fiabilidad (según `source`)
- high: 2318
- low: 687
- medium: 2137
- unknown: 217

## Cobertura temporal
- Primer nacimiento: 0571-04-22T00:00:00
- Último nacimiento: 2015-05-02T00:00:00
- Años muestreados: 421

## Cobertura geográfica
- Anomalías geográficas: 11 filas fuera de rango o con coordenadas faltantes

## Completitud de campos (top 10 nulos)
- city: 100.00% nulos (unique=0)
- rodden_rating: 100.00% nulos (unique=0)
- country: 100.00% nulos (unique=0)
- source: 0.20% nulos (unique=114)
- birth_date: 0.20% nulos (unique=5128)
- latitude: 0.20% nulos (unique=2462)
- longitude: 0.20% nulos (unique=2504)
- timezone: 0.20% nulos (unique=978)
- birth_time: 0.20% nulos (unique=981)
- id: 0.00% nulos (unique=5359)

## Anomalías detectadas
- Registros con anomalías: 11
- Registros duplicados (name + birth_date + city): 15

## Recomendaciones antes de HF
- Filtrar o revisar registros con `invalid_timezone`, `invalid_birth_date` o coordenadas faltantes.
- Priorizar fiabilidad 'high' y 'medium' para ASC/MC precisos.
- Resolver duplicados manualmente o consolidar.
- Confirmar husos horarios poco comunes (offsets fraccionarios).
