# Axiomatics of Heavens
v0.1 — Fundamentos epistemológicos para una astrología computacional agentiva
**Fecha:** 2025-12-30
**Estado:** Foundational Draft

---

## 0. Prefacio

Este documento no pretende “probar” la astrología ni defenderla frente a criterios externos de cientificidad heredados del siglo XIX.
Su objetivo es axiomatizar los supuestos mínimos que permiten construir sistemas computacionales coherentes, falsables y extensibles basados en tradiciones astrológicas históricas.

El proyecto Abu Oracle / Lilly Swarm parte de una hipótesis fuerte:

La astrología no es un sistema único, sino una familia de modelos cosmológicos que comparten ciertos invariantes y divergen en axiomas operativos.

Este documento establece esos axiomas, sus divergencias y su traducción directa a arquitectura de agentes.

---

## 1. Principio de Estratificación Celeste (Onionization of Heavens)
**Axioma 1.1 — Estratificación**

El cielo observable se organiza en capas jerárquicas, cada una con un grado distinto de variabilidad temporal:
- Firmamento estelar (estrellas “fijas”)
- Zodíaco (marco simbólico/geométrico)
- Planetas (movimiento relativo)
- Horizonte local (dependiente del observador)
- Tiempo civil y ritual

Cada tradición astrológica elige una capa como ancla primaria.

---

## 2. Principio de Referencia Inercial (Firmamento)
**Axioma 2.1 — Estrellas como referencia**

Las estrellas visibles pertenecen mayoritariamente a la Vía Láctea y mantienen posiciones relativas estables en escalas humanas.

Esto fundamenta:
- el zodíaco sideral (védico)
- las constelaciones helenísticas originales
- la noción de “firmamento” como marco de referencia

**Axioma 2.2 — Fijeza relativa, no absoluta**

La “fijeza” es:
- válida localmente
- inválida a escalas precesionales

Este axioma explica la divergencia sideral vs tropical sin invalidar ninguno.

---

## 3. Principio Helio–Geo Dinámico
**Axioma 3.1 — Doble movimiento**

La Tierra:
- orbita el Sol (año)
- rota sobre su eje (día)

Esto genera:
- estaciones
- alternancia día/noche
- inversión del horizonte observable

**Axioma 3.2 — Horizonte como operador activo**

El Ascendente no es una abstracción simbólica, sino:
- una función del lugar
- una función del tiempo
- una función de la rotación terrestre

Por lo tanto:
Dos nacimientos separados por ~12 horas generan configuraciones radicalmente distintas, aun con el mismo cielo estelar.

---

## 4. Principio de Dependencia del Observador
**Axioma 4.1 — Observador situado**

Toda carta es:
- topocéntrica
- dependiente de latitud, longitud y tiempo

No existe carta “universal”.

**Axioma 4.2 — Irreductibilidad observacional**

No es posible:
- observar empíricamente dos configuraciones vitales alternativas para el mismo individuo

Esto introduce una irreductibilidad estructural, análoga a:
- principios cuánticos de medición
- dependencia del marco de referencia

Esto no invalida el modelo, pero sí limita el tipo de contrastación posible.

---

## 5. Principio de Plasticidad Temporal (Revolución Solar)
**Axioma 5.1 — Retorno solar**

Cada año, el Sol retorna a su longitud natal.
Ese instante define una nueva carta, dependiente del lugar donde se encuentre el nativo.

**Axioma 5.2 — Geografía como operador de destino**

Cambiar de ubicación geográfica en el retorno solar:
- modifica el Ascendente
- reorganiza las casas
- altera la distribución de significadores

Esto fundamenta:
- astrología de reubicación
- hipótesis de intervención consciente en la trayectoria vital

---

## 6. Principio de Pluralidad Tradicional
**Axioma 6.1 — No unicidad del sistema**

No existe la astrología.
Existen tradiciones, cada una con:
- axiomas propios
- criterios de verdad internos
- semántica distinta

Ejemplos:

| Tradición         | Ancla principal         | Tiempo         |
|-------------------|------------------------|---------------|
| Helenística       | Horizonte + casas      | Cualitativo    |
| Persa medieval    | Ciclos largos          | Historiográfico|
| Védica (Jyotish)  | Firmamento sideral     | Kármico        |
| Horaria           | Momento de la pregunta | Eventual       |
| Moderna           | Psicología simbólica   | Narrativo      |

---

## 7. Principio de Agencialidad Astrológica
**Axioma 7.1 — Cada tradición es un agente**

Una tradición puede formalizarse como:
- un agente cognitivo
- con reglas internas
- con corpus textual propio
- con criterios interpretativos consistentes

Esto fundamenta el diseño de Lilly Swarm.

---

## 8. Mapeo a Arquitectura de Agentes (Lilly Swarm)
### 8.1 Contrato mínimo de agente

Cada agente astrológico debe definirse por:
```json
{
  "tradition": "persian_medieval",
  "axioms": [...],
  "inputs": ["abu_json"],
  "interpretation_rules": "...",
  "sources": ["texts", "tables"],
  "output_schema": {...}
}
```

### 8.2 Orchestrator

El Orchestrator:
- recibe la intención del usuario
- enruta a uno o varios agentes
- consolida o contrasta interpretaciones

No decide verdad: coordina semánticas.

### 8.3 RAG por tradición

Cada agente:
- accede solo a su propio corpus
- evita contaminación semántica
- preserva coherencia histórica

Ejemplo:
- Lilly (inglesa)
- Abu Maʿshar (persa)
- Jyotish clásico
- Astrología horaria medieval

---

## 9. Principio de Aprendizaje Histórico
**Axioma 9.1 — Casos históricos como dataset**

La astrología se refina mediante:
- cartas natales de figuras históricas
- eventos biográficos datados
- correlación no determinista

Esto habilita:
- aprendizaje por refuerzo débil
- ajuste de pesos interpretativos
- validación cruzada entre agentes

No es predicción dura: es afinación hermenéutica.

---

## 10. Hacia el Astro-Matrix Dashboard

El Frontend no es solo UI.
Es un sistema cognitivo que integra:
- Terminal (diálogo simbólico)
- Rueda zodiacal
- Panel de agentes (ERC-8004)
- IGP (geografía + destino)
- Comparación entre tradiciones

Inspiración:
- cyberpunk
- matrix
- observatorio astrológico interactivo

---

## 11. Cierre

Este documento establece el suelo ontológico del sistema.

Todo código posterior debe:
- referenciar explícitamente estos axiomas
- declarar qué tradición implementa
- aceptar la pluralidad como diseño, no como error

---

## Referencias cruzadas
- Whitepaper: fundamentos matemáticos y operativos ([WHITEPAPER_ABU_ORACLE_2025-12-23.md])
- Eficiencia, regularidad y reputación: criterios de evaluación y trazabilidad ([ABU_ORACLE_EFICIENCIA_REGULARIDAD_REPUTACION_2025-12-28.md])
- Roadmap técnico y variables computacionales ([ABU_ENGINE_ASTRO_VARIABLES_AND_ROADMAP_2025-12-23.md])
- Experimentos preregistrados y validación ([ABU_ORACLE_EXPERIMENT_001_HARMONY_FIELD.md])

---

Axiomatics of Heavens — v0.1
Foundational Draft
