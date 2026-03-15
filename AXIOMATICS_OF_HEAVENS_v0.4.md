# Axiomatics of Heavens
v0.4 — Fundamentos epistemológicos para una astrología computacional agentiva
**Fecha:** 2026-03-13
**Estado:** Active Draft
**Supersede:** v0.1, v0.2, v0.3

---

## 0. Prefacio

Este documento no pretende "probar" la astrología ni defenderla frente a criterios externos de cientificidad heredados del siglo XIX.
Su objetivo es axiomatizar los supuestos mínimos que permiten construir sistemas computacionales coherentes, falsables y extensibles basados en tradiciones astrológicas históricas.

El proyecto Abu Oracle / Lilly Swarm parte de una hipótesis fuerte:

> La astrología no es un sistema único, sino una familia de modelos cosmológicos que comparten ciertos invariantes y divergen en axiomas operativos.

Este documento establece esos axiomas, sus divergencias y su traducción directa a arquitectura de agentes.

La v0.4 incorpora dos principios nuevos — Especificidad de Dominio y Activación Condicionada — derivados de validación empírica sobre 527 eventos biográficos y de la doctrina Jeeva/Sareera de la tradición védica (Bhagat, S.P., *Significance of Nakshatras in Astrology*).

---

## 1. Axiomas Ontológicos

**Axioma 1.1 — El cielo como variedad**

El cielo observable constituye una variedad continua, ordenada y diferenciable $\mathcal{H}$, embebida en el espaciotiempo tetradimensional $\mathbb{R}^4$. Los cuerpos celestes son trayectorias localmente diferenciables dentro de $\mathcal{H}$, cada uno con su worldline única $\gamma_i(t)$.

**Axioma 1.2 — Estratificación**

$\mathcal{H}$ se organiza en capas jerárquicas con grados distintos de variabilidad temporal:

| Capa | Variabilidad | Escala |
|---|---|---|
| Firmamento estelar | Mínima | Precesional (~26,000 años) |
| Zodíaco | Simbólico/geométrico | Convencional |
| Planetas | Media | Días a siglos |
| Horizonte local | Máxima | Minutos |
| Tiempo civil y ritual | Convencional | Cultural |

Cada tradición astrológica elige una capa como ancla primaria. Esta elección no es arbitraria — determina la semántica completa del sistema.

**Axioma 1.3 — Fijeza relativa, no absoluta**

La "fijeza" del firmamento es válida localmente e inválida a escalas precesionales. Este axioma explica la divergencia sideral/tropical sin invalidar ninguno de los dos sistemas.

---

## 2. Axiomas Epistémicos

**Axioma 2.1 — Observador situado**

Todo conocimiento astrológico es condicional a las coordenadas espaciotemporales del observador $(t_O, x_O, y_O, z_O)$. No existe carta "universal". Toda carta es topocéntrica, dependiente de latitud, longitud y tiempo.

**Axioma 2.2 — Irreductibilidad observacional**

No es posible observar empíricamente dos configuraciones vitales alternativas para el mismo individuo. Esto introduce una irreductibilidad estructural análoga a los principios cuánticos de medición y a la dependencia del marco de referencia. Esta limitación no invalida el modelo — define el tipo de contrastación posible.

**Axioma 2.3 — Horizonte como operador activo**

El Ascendente no es una abstracción simbólica. Es una función del lugar, del tiempo y de la rotación terrestre. Dos nacimientos separados por ~12 horas generan configuraciones radicalmente distintas, aun con el mismo cielo estelar.

**Axioma 2.4 — Las afirmaciones astrológicas como mapeos semánticos**

Las afirmaciones astrológicas son formalizables como mapeos $f: \mathcal{H} \to \mathcal{S}$, donde $\mathcal{S}$ es un espacio semántico de interpretaciones. El valor de verdad de una afirmación es función tanto de la configuración celeste como del contexto del observador.

---

## 3. Axiomas Computacionales

**Axioma 3.1 — Carta como proyección computable**

La carta astrológica es una proyección finita y computable $\pi: \mathcal{H} \to \mathbb{R}^n$, parametrizada por el contexto del observador y la época. Todos los cálculos son reproducibles dado un conjunto idéntico de condiciones iniciales y datos de efemérides.

**Axioma 3.2 — Doble movimiento terrestre**

La Tierra orbita el Sol (año) y rota sobre su eje (día). Esto genera estaciones, alternancia día/noche e inversión del horizonte observable. El motor de cómputo debe modelar ambos movimientos de forma independiente y composable.

**Axioma 3.3 — Extensibilidad sin pérdida de generalidad**

El sistema soporta extensión algorítmica: nuevos cuerpos celestes, sistemas de casas o reglas interpretativas pueden incorporarse sin invalidar los módulos existentes. La compatibilidad hacia atrás es un requisito de diseño.

---

## 4. Axiomas Semánticos

**Axioma 4.1 — Arquetipos como unidades semánticas atómicas**

Cada elemento de la carta (planeta, casa, aspecto) se mapea a un arquetipo semántico único en $\mathcal{S}$. Los arquetipos son invariantes entre tradiciones — lo que varía es su ponderación, jerarquía y relación con otros arquetipos.

**Axioma 4.2 — Interpretación como composición**

Las interpretaciones se generan mediante reglas composicionales sobre $\mathcal{S}$, restringidas por contexto y conocimiento previo. El sistema es agnóstico al lenguaje natural en el nivel semántico — el output en lenguaje natural es un rendering de $\mathcal{S}$ en el idioma destino.

**Axioma 4.3 — Pluralidad tradicional como diseño**

No existe *la* astrología. Existen tradiciones, cada una con axiomas propios, criterios de verdad internos y semántica distinta:

| Tradición | Ancla principal | Marco temporal |
|---|---|---|
| Helenística | Horizonte + casas | Cualitativo |
| Persa medieval | Ciclos largos | Historiográfico |
| Védica (Jyotish) | Firmamento sideral | Kármico |
| Horaria | Momento de la pregunta | Eventual |
| Moderna | Psicología simbólica | Narrativo |

La pluralidad es un rasgo estructural del dominio, no un error a resolver. El sistema la gestiona mediante agentes independientes, no mediante síntesis forzada.

---

## 5. Principio de Plasticidad Temporal (Revolución Solar)

**Axioma 5.1 — Retorno solar**

Cada año, el Sol retorna a su longitud natal. Ese instante define una nueva carta, dependiente del lugar donde se encuentre el nativo.

**Axioma 5.2 — Geografía como operador de destino**

Cambiar de ubicación geográfica en el retorno solar modifica el Ascendente, reorganiza las casas y altera la distribución de significadores. Esto fundamenta la astrología de reubicación y la hipótesis de intervención consciente en la trayectoria vital.

---

## 6. Principio de Agencialidad Astrológica

**Axioma 6.1 — Cada tradición es un agente**

Una tradición astrológica puede formalizarse como un agente cognitivo con reglas internas, corpus textual propio y criterios interpretativos consistentes. Esto fundamenta el diseño de Lilly Swarm.

**Axioma 6.2 — Contrato mínimo de agente**

```json
{
  "tradition": "persian_medieval",
  "axioms": ["..."],
  "inputs": ["abu_json"],
  "interpretation_rules": "...",
  "sources": ["texts", "tables"],
  "output_schema": {}
}
```

**Axioma 6.3 — Orchestrator como coordinador semántico**

El Orchestrator recibe la intención del usuario, enruta a uno o varios agentes y consolida o contrasta interpretaciones. No decide verdad: coordina semánticas.

**Axioma 6.4 — RAG por tradición**

Cada agente accede solo a su propio corpus. La contaminación semántica entre tradiciones es un defecto de diseño, no una síntesis enriquecedora.

---

## 7. Principio de Aprendizaje Histórico

**Axioma 7.1 — Casos históricos como dataset**

La astrología se refina mediante cartas natales de figuras históricas, eventos biográficos datados y correlación no determinista. Esto habilita aprendizaje por refuerzo débil, ajuste de pesos interpretativos y validación cruzada entre agentes.

**Axioma 7.2 — No predicción dura**

El sistema no predice eventos — afina la hermenéutica. La correlación entre configuración celeste y evento biográfico es una señal estadística, no una ley determinista.

---

## 8. Principio de Especificidad de Dominio *(nuevo — v0.4)*

**Axioma 8.1 — Opacidad del campo global**

La lectura del campo celeste no es homogénea. Un campo calculado sobre la totalidad de los planetas es un campo de *actividad total*, no de armonía específica para ningún dominio de vida en particular. Su señal es débil no porque el modelo esté equivocado, sino porque la pregunta está incompleta.

> Correlato empírico (Abu Oracle, 2026): correlación HF_global ↔ valencia de eventos = 0.155 (Cohen's d = 0.44). Correlación HF_dominio_salud ↔ eventos de salud = 0.615 (mejora de +0.93). El campo global no es falso — es sordo a la pregunta específica.

**Axioma 8.2 — Especificidad como condición de legibilidad**

Para que el campo geográfico sea interpretable, debe filtrarse por el dominio de la pregunta. Cada dominio de experiencia humana está regido por un subconjunto específico de principios activos: los planetas que rigen y ocupan la casa correspondiente en la carta natal.

La geografía óptima para la carrera de una persona no es la misma que la geografía óptima para su salud, y ambas difieren de la geografía de máxima actividad total.

**Axioma 8.3 — El subset planetario es la pregunta**

En términos computacionales:

```python
planet_subset = house_significators(natal, house=k)
```

Este filtro no es una optimización técnica. Es la formalización de la intención del consultante. El sistema no puede responder "¿dónde desarrollo mejor mi carrera?" si le preguntamos "¿dónde es todo mejor?". Una pregunta bien formulada activa un subconjunto. Una pregunta sin formular activa el campo completo, que contiene todas las respuestas simultáneamente y por lo tanto no responde ninguna con claridad.

**Axioma 8.4 — Implicación de diseño**

El selector de dominio en la interfaz de usuario no es una feature de navegación. Es la implementación directa de este axioma. El sistema debe solicitar la intención del consultante antes de calcular el campo — no como cortesía de UX, sino como requisito epistémico.

---

## 9. Principio de Activación Condicionada *(nuevo — v0.4)*

*Fundamento doctrinal: Bhagat, S.P. — Significance of Nakshatras in Astrology. Doctrina Jeeva/Sareera.*

**Axioma 9.1 — Latencia estructural**

La presencia de un dominio en la carta natal no garantiza su activación. Para que una casa manifieste sus resultados, sus planetas significadores deben estar en condición de operar: bien dispuestos, sin debilitamiento por dignidad adversa, sin bloqueo por planetas contrarios.

Una casa puede estar presente y ser permanentemente latente si sus significadores carecen de condiciones de operación. La relocalización no crea potencial donde no hay — facilita la expresión del potencial que ya existe en forma latente.

**Axioma 9.2 — El campo geográfico como facilitador**

El Harmony Field por dominio no predice eventos. Identifica los lugares donde las condiciones estructurales para la activación de un dominio son más favorables.

La diferencia es epistemológicamente importante:

> El sistema no dice "aquí tendrás éxito profesional."
> Dice "aquí los principios que rigen tu carrera encuentran mayor resonancia."

**Axioma 9.3 — Timing y geografía como dimensiones del mismo principio**

En Jyotish, la activación temporal se mide mediante dashas — períodos planetarios que determinan qué planeta "habla" en cada momento de la vida. En Abu Oracle, la geografía opera como la dimensión espacial del mismo problema:

- El dasha responde *cuándo* se activa un dominio.
- El HF por dominio responde *dónde*.

Son coordenadas distintas del mismo espacio de manifestación. Un sistema completo requiere ambas.

**Axioma 9.4 — Jerarquía de condiciones para la manifestación**

Para que un dominio de vida se active plenamente se requiere la confluencia de:

1. **Potencial natal** — los significadores de la casa están bien dispuestos en la carta natal.
2. **Resonancia geográfica** — el HF por dominio es favorable en la ubicación actual o propuesta.
3. **Activación temporal** — el período planetario (dasha/tránsito) activa los mismos significadores.

El sistema actual modela (1) y (2). La incorporación de (3) es el siguiente horizonte de desarrollo.

---

## 10. Meta-Axiomas

**Axioma 10.1 — Revisabilidad**

Todos los axiomas son sujetos a revisión ante nueva evidencia empírica, computacional o semántica. La v0.4 es una versión activa, no un documento cerrado.

**Axioma 10.2 — Trazabilidad**

El sistema mantiene trazabilidad completa de todos los cambios a axiomas y reglas interpretativas. Cada versión de esta Axiomática debe referenciar los datos o razonamientos que motivaron sus cambios.

**Axioma 10.3 — Coherencia entre capas**

Todo código del sistema debe referenciar explícitamente los axiomas que implementa, declarar qué tradición implementa, y aceptar la pluralidad como diseño, no como error.

---

## 11. Mapeo a Arquitectura (Abu Oracle / Lilly Swarm)

| Axioma | Implementación |
|---|---|
| 1.2 Estratificación | Abu Engine: capas independientes (efemérides, casas, aspectos) |
| 2.1 Observador situado | Cómputo topocéntrico, Placidus, Swiss Ephemeris DE440s |
| 3.1 Carta computable | `abu_engine/` — output JSON por sujeto |
| 4.3 Pluralidad | Lilly Swarm — agente por tradición con RAG independiente |
| 5.2 Geografía como operador | HF v3 — campo escalar sobre grilla global 5°×5° |
| 7.1 Aprendizaje histórico | 527 eventos biográficos, correlator HF↔valencia |
| 8.3 Subset como pregunta | `planet_subset = house_significators(natal, house=k)` |
| 8.4 Selector como requisito epistémico | `DomainSelector.tsx` — frontend |
| 9.3 Timing + geografía | HF por dominio (implementado) + dashas (próximo horizonte) |

---

## 12. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| v0.1 | 2025-12-30 | Draft fundacional. Principios 1-9, mapeo a arquitectura. |
| v0.2 | 2025-12-30 | Revisión menor. |
| v0.3 | 2025-12-30 | Formalización matemática. Pérdida parcial de contenido doctrinal. |
| v0.4 | 2026-03-13 | Reintegración de v0.1 + rigor de v0.3. Axiomas 8 y 9 nuevos: Especificidad de Dominio y Activación Condicionada. Fundamento empírico: correlación HF_dominio vs HF_global sobre 527 eventos. Fundamento doctrinal: Jeeva/Sareera (Bhagat). |

---

## Referencias cruzadas

- Whitepaper: fundamentos matemáticos y operativos — `WHITEPAPER_ABU_ORACLE.md`
- Estado del repositorio y plan de desarrollo — `CLAUDE.md`
- Estructura de datos — `DATABASE_STRUCTURE.md`
- Log de experimentos HF — `HF_EXPERIMENT_LOG.md`
- Spec técnica HF v4 — `SESSION_B_HF_V4_CORRELATOR.md`
- Bhagat, S.P. — *Significance of Nakshatras in Astrology* (corpus Jyotish)

---

*Axiomatics of Heavens — v0.4*
*Abu Oracle Project — 2026-03-13*
