# Lilly como nuevo paradigma en aprendizaje de LLMs — Diálogo y análisis

**Fecha:** 2026-04-26  
**Contexto:** Conversación entre el operador (Guillermo) y Lilly sobre cómo documentar y publicar el argumento de que Abu Oracle representa un paradigma distinto en el uso de LLMs.

---

## Diálogo

### Lilly — argumento central

Abu Oracle no es un chatbot que "sabe astrología". Es un experimento documentado de cómo un LLM opera una tradición doctrinal con jerarquía axiomática explícita — sect, dignidades esenciales, angularidad, profección, firdaria — en ese orden preciso, sin saltarse ningún nivel. Eso es distinto de lo que hace cualquier LLM genérico respondiendo preguntas astrológicas, que opera por asociación estadística sobre texto popular, no por jerarquía doctrinal persa-helenística.

### Lilly — estructura de demostración prescrita

**Primera capa:** Abu Oracle lee una carta conocida — figura pública con datos Rodden AA — con precisión doctrinal verificable por cualquier astrólogo formado en la tradición. No predicción. Interpretación estructurada según la jerarquía.

**Segunda capa:** un documento corto, tres páginas máximo, explicando qué instrucciones recibe Lilly, qué jerarquía doctrinal aplica, y cómo eso produce resultados distintos a un LLM sin formalización doctrinal.

### Lilly — lo que ya existe y solo falta escribir hacia afuera

Los axiomas doctrinales están formalizados. La validación empírica contra 527 eventos biográficos con Cohen's d ≈ 0.44 existe. El system prompt que traduce la doctrina de Lilly en reglas computables existe. Nada de eso está documentado públicamente. La demostración no requiere construir nada nuevo — requiere escribir lo que ya opera.

### Operador — objeción

> "¿Tiene algo de novedoso esto? A verdad es que me parece bastante trivial."

### Lilly — respuesta a la objeción de trivialidad

**Lo que es trivial:** que un LLM siga instrucciones estructuradas. Eso lo hace cualquier system prompt bien escrito. No es novedad en 2026.

**Lo que no es trivial — tres puntos específicos:**

1. **Falsificabilidad.** La jerarquía doctrinal produce interpretaciones verificables: dado sect nocturno, dado Júpiter en exaltación como mayor benefic de secta, dado profección Casa 5 activa, *este* dominio de vida debería mostrar activación en *esta* ventana temporal. Cohen's d ≈ 0.44 sobre 527 eventos biográficos es el número. Eso no existe en la literatura de LLMs aplicados a tradiciones hermenéuticas.

2. **Arquitectura.** El Harmony Field es geometría computacional pura — no semántica, no estadística de texto. Un LLM que integra cálculo astronómico topocéntrico con interpretación doctrinal en tiempo real es arquitectónicamente distinto de un LLM que "sabe astrología" por haber leído libros de astrología.

3. **Pregunta de fondo.** No es astrología. Es: *¿puede un LLM operar una tradición de conocimiento tácito con suficiente fidelidad doctrinal como para producir outputs que expertos en esa tradición validen como correctos?* Eso tiene implicaciones para medicina tradicional china, jurisprudencia islámica, derecho romano, cualquier corpus con estructura axiomática no formalizada en código.

**Conclusión de Lilly:** el ángulo trivial es "LLM aprende astrología". El ángulo no trivial es "LLM como vehículo de formalización de tradiciones doctrinales con validación empírica". Son propuestas distintas. La primera no vale un paper. La segunda sí.

---

## Análisis externo (Claude Code, 2026-04-26)

### Lo que está bien construido

El pivote de "LLM aprende astrología" a "LLM como vehículo de formalización de tradiciones doctrinales con validación empírica" es el encuadre correcto para que esto tenga peso académico. Sin ese pivote, la objeción del operador es válida.

El ángulo de falsificabilidad es el más fuerte de todo el argumento. Pasar de interpretaciones irrefutables por diseño a predicciones temporalmente acotadas y verificables contra eventos biográficos es una distinción real, no retórica. Es el núcleo del paper si se decide escribir uno.

### Lo que está documentado y es más sólido de lo que parecía

**Cohen's d = 0.441 sobre 527 eventos biográficos** tiene metodología explícita y reproducible documentada en `docs/HF_EXPERIMENT_LOG.md` (Experimento 6, 2026-04-01):

- Dataset: 527 eventos, 26 sujetos históricos (`data/biographical_events/events_detailed.csv`)
- Métrica: separación HF_weighted entre eventos positivos vs negativos (pooled std)
- Script reproducible: `python scripts/correlate_by_domain.py`
- Artefactos públicos en `abu-oracle-research/` con SHA256 de integridad

Adicionalmente existe un análisis por dominio (H04–H10) con Cohen's d por casa, bootstrap de 10,000 iteraciones para H10, y justificación explícita de por qué Cohen's d es la métrica correcta sobre Pearson para distribuciones asimétricas de valencias.

**Corrección al análisis anterior:** la crítica sobre falta de metodología era incorrecta. La metodología existe, está versionada y es reproducible. El punto débil real es distinto: el corpus tiene 26 sujetos históricos, lo que es una muestra pequeña de sujetos aunque los eventos por sujeto sean múltiples. Eso es lo que hay que anticipar en una revisión académica.

### Lo que es técnicamente débil

La afirmación de que la arquitectura es "distinta" a otros LLMs. Seguir una jerarquía doctrinal detallada es esencialmente un system prompt muy elaborado — eso no es novedad arquitectónica en sí misma. La novedad real está en el *dominio de aplicación* y en la *validación empírica*, no en la arquitectura subyacente. Conviene ser preciso sobre este punto para no quedar expuesto a crítica fácil desde la comunidad de ML.

### Conclusión

El argumento tiene sentido y es defendible. La generalización a otras tradiciones (medicina china, jurisprudencia islámica, derecho romano) es lo más interesante y lo más difícil de refutar. Es el ángulo que vale la pena desarrollar con prioridad si el objetivo es publicación académica o divulgación técnica seria.

El riesgo principal no es la solidez del argumento — es la documentación del Cohen's d. Si ese número no tiene metodología explícita y reproducible detrás, es el punto débil más atacable.
