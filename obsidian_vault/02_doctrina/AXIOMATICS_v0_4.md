---
name: AXIOMATICS_v0_4
description: Axiomática de los Cielos v0.4 — fundamentos epistemológicos para astrología computacional agentiva
tipo: doctrina
version: v0.4
estado: activo
tags: [axiomatica, doctrina, epistemologia, dominio, activacion, jeeva-sareera]
---

# Axiomatics of Heavens — v0.4

Fecha: 2026-03-13 · Estado: Active Draft · Supersede: v0.1, v0.2, [[AXIOMATICS_v0_3]]

Ver también: [[field_v3]] · [[resonance_weights]] · [[HF_EXPERIMENT_LOG]] · [[domain_correlation_report]]

---

## 0. Prefacio

Este documento axiomatiza los supuestos mínimos que permiten construir sistemas computacionales coherentes, falsables y extensibles basados en tradiciones astrológicas históricas.

> La astrología no es un sistema único, sino una familia de modelos cosmológicos que comparten ciertos invariantes y divergen en axiomas operativos.

La v0.4 incorpora dos principios nuevos — **Especificidad de Dominio** y **Activación Condicionada** — derivados de validación empírica sobre 527 eventos biográficos y de la doctrina Jeeva/Sareera (Bhagat, S.P.).

---

## 1. Axiomas Ontológicos

**Axioma 1.1 — El cielo como variedad**
El cielo observable constituye una variedad continua, ordenada y diferenciable $\mathcal{H}$, embebida en el espaciotiempo tetradimensional $\mathbb{R}^4$.

**Axioma 1.2 — Estratificación**

| Capa | Variabilidad | Escala |
|---|---|---|
| Firmamento estelar | Mínima | Precesional (~26,000 años) |
| Zodíaco | Simbólico/geométrico | Convencional |
| Planetas | Media | Días a siglos |
| Horizonte local | Máxima | Minutos |

**Axioma 1.3 — Fijeza relativa, no absoluta**
Explica la divergencia sideral/tropical sin invalidar ninguno de los dos sistemas.

---

## 2. Axiomas Epistémicos

**Axioma 2.1 — Observador situado**
Todo conocimiento astrológico es condicional a las coordenadas $(t_O, x_O, y_O, z_O)$. No existe carta "universal". Toda carta es topocéntrica.

**Axioma 2.2 — Irreductibilidad observacional**
No es posible observar dos configuraciones vitales alternativas para el mismo individuo.

**Axioma 2.3 — Horizonte como operador activo**
El Ascendente es función del lugar, del tiempo y de la rotación terrestre.

**Axioma 2.4 — Afirmaciones astrológicas como mapeos semánticos**
$f: \mathcal{H} \to \mathcal{S}$, donde $\mathcal{S}$ es un espacio semántico de interpretaciones.

---

## 3. Axiomas Computacionales

**Axioma 3.1 — Carta como proyección computable**
Proyección finita $\pi: \mathcal{H} \to \mathbb{R}^n$. Todos los cálculos son reproducibles dado condiciones idénticas.

**Axioma 3.2 — Doble movimiento terrestre**
La Tierra orbita el Sol (año) y rota sobre su eje (día). El motor debe modelar ambos de forma independiente.

**Axioma 3.3 — Extensibilidad sin pérdida de generalidad**
Nuevos cuerpos, sistemas de casas o reglas interpretativas pueden incorporarse sin invalidar módulos existentes.

---

## 4. Axiomas Semánticos

**Axioma 4.1 — Arquetipos como unidades semánticas atómicas**
Cada elemento se mapea a un arquetipo único en $\mathcal{S}$, invariante entre tradiciones.

**Axioma 4.3 — Pluralidad tradicional como diseño**

| Tradición | Ancla | Marco temporal |
|---|---|---|
| Helenística | Horizonte + casas | Cualitativo |
| Persa medieval | Ciclos largos | Historiográfico |
| Védica (Jyotish) | Firmamento sideral | Kármico |
| Horaria | Momento de la pregunta | Eventual |
| Moderna | Psicología simbólica | Narrativo |

---

## 5. Principio de Plasticidad Temporal (Revolución Solar)

**Axioma 5.2 — Geografía como operador de destino**
Cambiar de ubicación geográfica en el retorno solar modifica el Ascendente y reorganiza las casas. Fundamenta la astrología de reubicación.

---

## 6. Principio de Agencialidad Astrológica

**Axioma 6.1 — Cada tradición es un agente**
Fundamenta el diseño de Lilly Swarm.

**Axioma 6.4 — RAG por tradición**
Cada agente accede solo a su propio corpus. La contaminación semántica entre tradiciones es un defecto de diseño.

---

## 7. Principio de Aprendizaje Histórico

**Axioma 7.2 — No predicción dura**
El sistema no predice eventos — afina la hermenéutica. La correlación es una señal estadística, no una ley determinista.

---

## 8. Principio de Especificidad de Dominio *(nuevo — v0.4)*

**Axioma 8.1 — Opacidad del campo global**
El campo calculado sobre todos los planetas es un campo de *actividad total*. Su señal es débil porque la pregunta está incompleta.

> Correlato empírico (Abu Oracle, 2026): corr HF_global ↔ valencia = 0.155 (d=0.44). corr HF_dominio_salud ↔ eventos_salud = 0.615 (mejora +0.93). Ver [[HF_EXPERIMENT_LOG#Experimento 5]].

**Axioma 8.2 — Especificidad como condición de legibilidad**
Para que el campo sea interpretable, debe filtrarse por dominio.

**Axioma 8.3 — El subset planetario es la pregunta**

```python
planet_subset = house_significators(natal, house=k)
```

Implementado en [[field_v3]] como parámetro `planet_subset`.

**Axioma 8.4 — Implicación de diseño**
El selector de dominio en la UI no es una feature de navegación — es la implementación directa de este axioma.

---

## 9. Principio de Activación Condicionada *(nuevo — v0.4)*

*Fundamento doctrinal: Bhagat, S.P. — Significance of Nakshatras in Astrology. Doctrina Jeeva/Sareera.*

**Axioma 9.1 — Latencia estructural**
La presencia de un dominio en la carta natal no garantiza su activación. Una casa puede ser permanentemente latente si sus significadores carecen de condiciones de operación.

**Axioma 9.2 — El campo geográfico como facilitador**
> El sistema no dice "aquí tendrás éxito profesional."
> Dice "aquí los principios que rigen tu carrera encuentran mayor resonancia."

**Axioma 9.3 — Timing y geografía como dimensiones del mismo principio**

- El dasha/firdaria responde *cuándo* se activa un dominio.
- El HF por dominio responde *dónde*.

**Axioma 9.4 — Jerarquía de condiciones para la manifestación**

1. **Potencial natal** — significadores bien dispuestos
2. **Resonancia geográfica** — HF por dominio favorable
3. **Activación temporal** — período planetario activa los mismos significadores

El sistema actual modela (1) y (2). La incorporación de (3) es el siguiente horizonte.

---

## 10. Meta-Axiomas

**Axioma 10.1 — Revisabilidad**
Todos los axiomas son sujetos a revisión ante nueva evidencia empírica, computacional o semántica.

**Axioma 10.3 — Coherencia entre capas**
Todo código debe referenciar explícitamente los axiomas que implementa.

---

## 11. Principio de Estratificación de Niveles Operativos *(nuevo — v0.4.1)*

*Fundamento doctrinal: Abu Mashar al-Balkhi (787–886), De Magnis Coniunctionibus — los ciclos planetarios largos como marcadores de épocas históricas, independientes de cualquier carta natal individual.*

**Axioma 11.1 — Dos niveles del mismo campo**
El campo $\mathcal{H}$ admite dos modos de proyección no equivalentes:

| Nivel | Proyección | Pregunta operativa |
|---|---|---|
| **Individual** | $f(\pi_{natal}, \phi(t,x))$ | ¿Cómo afecta esta configuración a *este* nativo? |
| **Colectivo (mundano)** | $f(\phi(t))$ | ¿Qué configuración tiene el cielo *en sí*, sin anclaje natal? |

El nivel individual requiere un código natal $\pi_{natal}$ como invariante (ver [[AXIOM_0_MECANISMO]]). El nivel mundano opera sobre el cielo sin necesidad de anclaje individual — la configuración planetaria *es* el objeto de lectura.

**Axioma 11.2 — Conjunciones de ciclo largo como marcadores epocales**
Las conjunciones Júpiter-Saturno (~20 años, gran ciclo ~960 años) y oposiciones/conjunciones Marte-Saturno funcionan como marcadores discretos de transiciones epocales en el corpus histórico colectivo.

> Correlato empírico (Abu Oracle, 2026-04-05, corpus 23.636 eventos año 8–2069):
> - Conjunción J-S: densidad 4.3× baseline, p=5×10⁻⁶, r=+0.204
> - Oposición M-S: densidad 1.6× baseline, p=0.016, r=+0.056
> - Ver [[MUNDANA_H_A_RESULTADOS]]

**Axioma 11.3 — Independencia entre niveles**
Un evento puede ser legible en el nivel mundano sin requerir lectura individual, y viceversa. La señal estadística de J-S sobre el corpus colectivo no depende de las cartas natales de los protagonistas — opera sobre el calendario histórico mismo.

**Axioma 11.4 — Convergencia entre niveles**
Cuando un nativo experimenta un período cuya configuración mundana (J-S, M-S, eclipses) coincide con su activación temporal individual (firdaria, profección, tránsito a planeta natal), la lectura debe componer ambos niveles. La convergencia no es aditiva — es estructural.

**Axioma 11.5 — Implicación de diseño**
El módulo mundana no es una feature paralela al motor natal. Es la implementación del nivel colectivo del campo, doctrinalmente justificada en [[AXIOMATICS_v0_3#Abu Mashar]] y empíricamente validada en [[MUNDANA_H_A_RESULTADOS]]. Su arquitectura de producto está descrita en [[MUNDANA_PHASE12]].

---

## 12. Mapeo a Arquitectura

| Axioma | Implementación |
|---|---|
| 2.1 Observador situado | Topocéntrico, Placidus, Swiss Ephemeris DE440s |
| 5.2 Geografía como operador | [[field_v3]] — campo escalar grilla global |
| 7.1 Aprendizaje histórico | 527 eventos biográficos, correlator HF↔valencia |
| 8.3 Subset como pregunta | `planet_subset = house_significators(natal, house=k)` |
| 8.4 Selector como requisito | `DomainSelector.tsx` — frontend |
| 9.3 Timing + geografía | HF por dominio (implementado) + firdaria (activo) |
| 11.1 Niveles individual/colectivo | Engine natal (`/analyze`) + módulo mundana (`/api/mundana/*`) |
| 11.2 Conjunciones como marcadores | `abu_engine/core/mundana.py` — detección J-S, M-S, M-J + stellium |
| 11.5 Mundana como nivel del campo | [[MUNDANA_PHASE12]] — pipeline + publisher autónomo |

---

## Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| v0.1 | 2025-12-30 | Draft fundacional |
| v0.3 | 2025-12-30 | Formalización matemática |
| **v0.4** | **2026-03-13** | Axiomas 8 y 9 nuevos. Fundamento empírico y doctrinal Jeeva/Sareera |
| **v0.4.1** | **2026-04-25** | Axioma 11 — Estratificación niveles individual/colectivo. Fundamento Abu Mashar + validación H_mundana_A |
