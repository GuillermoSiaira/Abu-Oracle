# ABU ORACLE — EXPERIMENTO 001: Harmony Field & Geodesia

**Fecha de preregistro:** 2025-12-29
**Estado:** No ejecutado (preregistro)

---

## Objetivo del experimento

Evaluar si el modelo geodésico (WGS84) implementado en Abu Oracle produce un campo de armonía (Harmony Field) más estable y coherente, en comparación con un modelo plano (sin corrección geodésica), bajo condiciones controladas de simulación astrológica.

---

## Hipótesis principal (H₁)

El modelo geodésico (WGS84) produce un Harmony Field más estable/coherente que un modelo plano, para la misma configuración astral y variando únicamente la localización geográfica.

---

## Variables

- **Independiente:** Localización geográfica (latitud, longitud, elevación)
- **Dependiente:** Variación del valor escalar de Harmony Field ($H_{scalar}$)

---

## Baseline explícito

- Modelo plano: cálculo del Harmony Field asumiendo una proyección plana (sin corrección geodésica, e.g., lat/lon tratados como coordenadas cartesianas simples).
- Modelo experimental: cálculo del Harmony Field usando el modelo geodésico WGS84 (definición canónica, ver whitepaper sección 2.X).

---

## Métrica de evaluación

- Desviación estándar y rango de $H_{scalar}$ al variar la localización en ambos modelos, bajo la misma configuración astral.
- Coherencia: menor variabilidad y mayor continuidad espacial en el modelo geodésico respecto al plano.

---

## Criterio de falsación

La hipótesis H₁ se considera falsada si el modelo geodésico (WGS84) no muestra una reducción significativa en la variabilidad de $H_{scalar}$, o si el modelo plano iguala o supera la coherencia espacial del modelo geodésico bajo las mismas condiciones.

---

## Estado actual

- Experimento definido y preregistrado.
- No ejecutado.
- No se reportan resultados ni conclusiones.

---

**Este documento constituye un preregistro experimental y no debe interpretarse como afirmación de resultados ni de validez del modelo.**
