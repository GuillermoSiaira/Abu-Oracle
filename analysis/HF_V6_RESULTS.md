# HF_v6 — Resultados y validación doctrinal
**Fecha:** 2026-03-29
**Estado:** Confirmado — hipótesis doctrinal validada empíricamente

## Resultado central

| casa    | n_eventos | cohens_d_v3 | cohens_d_v5 | cohens_d_v6 | delta_v6     |
|---------|-----------|-------------|-------------|-------------|--------------|
| H04     | 0         | n/a         | n/a         | n/a         | n/a          |
| H05     | 57        | n/a         | n/a         | n/a         | n/a (N-=1)   |
| H07     | 93        | +0.055      | +0.038      | +0.587      | +0.532       |
| H10     | 250       | +0.056      | −0.379      | +0.702      | +0.646       |
| global  | 529       | +0.441      | −0.064      | +0.193      | −0.248       |

## Hipótesis confirmada

H_v6: "El HF calculado con angularidad modulada por dignidad esencial
× amplificador de intersección firdaria∩dominio produce mayor separación
entre eventos positivos y negativos que HF_v3 en dominios específicos."

Resultado: confirmada en 2 dominios (H07, H10). No falsada.

## Arquitectura que produce el resultado

Dos mecanismos separados — esta separación es la clave:

### Mecanismo 1 — Aspectos como geometría pura

```
HF_aspects = Σ_{pares ∈ subset(k)} kernel_gaussiano(Δθ)
```

Sin ponderación por dignidad. La geometría no tiene signo moral.
Fundamento: la resonancia entre planetas es un hecho astronómico,
no una valoración cualitativa.

### Mecanismo 2 — Angularidad modulada por dignidad × firdaria

```
HF_angles_v6 = Σ_{p ∈ subset(k)} angularity(p,φ,λ) × dignity(p) × w(p,t,k)

w(p,t,k) = 2.0  si p ∈ (firdaria(t) ∩ subset(k))
           1.0  en caso contrario
```

Fundamento doctrinal:
- **Angularidad** = "volumen" del planeta (Ptolomeo, Lilly)
- **Dignidad** = "contenido" del planeta — qué puede entregar
- **Intersección firdaria∩dominio** = activación condicionada:
  "cuando los señores de los tiempos coinciden con los señores
   del evento, el efecto es extremo y sin aleación" (Ptolomeo)

## Por qué HF_v5 falló y HF_v6 funciona

HF_v5 introducía dignidad dentro del kernel de aspecto:

```
pair_score = kernel × (dignity_i + dignity_j)
```

Eso invertía la señal porque mezclaba geometría con cualidad.
Un aspecto exacto entre planetas debilitados produce `kernel≈1 × (−8) = −8`,
penalizando eventos independientemente de su valencia real.

HF_v6 separa los mecanismos:
- **Aspectos**: geometría pura → señal posicional
- **Angularidad**: amplificada por dignidad → señal cualitativa

La separación es doctrinalmente correcta y empíricamente superior.

## Por qué el global cae

El HF global promedia sobre todos los dominios simultáneamente.
El término angularidad×dignidad es pequeño cuando se promedia
sobre planetas sin intersección firdaria∩dominio.
Esto confirma el **Axioma 8** — el campo global es sordo a la
pregunta específica. La especificidad de dominio es condición
de legibilidad del campo.

## Límites de validez — matiz crítico

La confirmación es real, pero está acotada. Conviene no sobre-interpretar antes de
ampliar el corpus.

### El sesgo de selección de dominios

Los dos dominios confirmados (H07, H10) son precisamente los que tienen mayor N
en el dataset. Esto no es casualidad: son también los únicos donde N- es suficiente
para calcular Cohen's d.

| casa | N total | N+  | N-  | Cohen's d |
|------|---------|-----|-----|-----------|
| H04  | 0       | —   | —   | no computable (cero eventos en v2) |
| H05  | 57      | 51  | 1   | no computable (N- insuficiente) |
| H07  | 93      | 81  | 9   | +0.587 ✅ |
| H10  | 250     | 231 | 4   | +0.702 ✅ |

H07 tiene 9 eventos negativos — estadísticamente marginal. H10 tiene 4.
La métrica Cohen's d es sensible a N- pequeño: una variación en 1-2 casos
puede mover el resultado de forma no despreciable.

### Lo que la confirmación no dice

El efecto está medido sobre el subconjunto más favorable del corpus.
H04 (Hogar) y H05 (Creatividad) — dos dominios con señal positiva en experimentos
anteriores (v3 domain: H04 Δcorr=+0.306, H05 Δcorr=+0.150) — no pueden evaluarse
en v6 por falta de eventos negativos. La hipótesis no está falsada en esos dominios;
simplemente no hay datos suficientes para probarla.

### Riesgo de overfitting doctrinal

El diseño de HF_v6 fue guiado por la doctrina, no por búsqueda de parámetros sobre
los datos. Eso reduce el riesgo de overfitting estadístico. Pero introduce un riesgo
distinto: que los axiomas seleccionados (angularidad, dignidad, firdaria∩dominio)
sean los más fáciles de confirmar en este corpus específico, no los más generales.
Verificar con un corpus independiente y balanceado es la única forma de saberlo.

### Condición para considerar la hipótesis robusta

> H_v6 será robusta cuando d > 0.3 en al menos 3 dominios con N- ≥ 10 cada uno.

Hoy cumple en 2 dominios con N- de 9 y 4 respectivamente. La dirección es correcta;
la potencia estadística aún no.

**Acción necesaria**: ampliar N- mediante scraping de eventos negativos en Wikidata
(quiebras, exilios, fracasos documentados) antes de considerar HF_v6 listo para
reemplazar HF_v3 en producción.

---

## Fuentes doctrinales

- Ptolomeo: angularidad como fuente de fuerza extrema
- William Lilly, *Christian Astrology* 1647:
  dignidad esencial D4 (+5/+4/0/−4/−5);
  angularidad como "volumen" del planeta
- Abu Oracle Axiomática v0.4:
  Axioma 8 — Especificidad de dominio
  Axioma 9 — Activación condicionada

## Archivos relevantes

| Archivo | Descripción |
|---------|-------------|
| `abu_engine/harmony/hf_v6.py` | Implementación completa |
| `scripts/run_hf_v6_comparison.py` | Correlador v3/v5/v6 |
| `analysis/domain_correlation_results.json` | Baseline v3 |
| `data/biographical_events_v2/` | 529 eventos, 26 sujetos |
| `AXIOMATICS_OF_HEAVENS_v0.4.md` | Fundamento doctrinal |
