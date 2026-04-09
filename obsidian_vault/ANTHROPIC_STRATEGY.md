# Estrategia de Relación con Anthropic — Abu Oracle

> Creado: 2026-04-06. Nodo vivo — actualizar ante cualquier contacto o progreso.
> Estado: pre-launch. Ejecutar después del 18 de abril con datos reales.
> Referencias cruzadas: [[finops_milp]] · [[BLIND_VALIDATION_EXPERIMENT]] · [[COST_OPTIMIZATION]]

---

## Encuadre general

Abu Oracle no le vende un producto a Anthropic — le ofrece ser un
**caso de referencia técnico del ecosistema Claude** en un dominio
que Anthropic no tiene cubierto: pricing sustentable de SaaS vertical
sobre LLMs, con validación estadística propia y dataset de producción real.

El intercambio natural es: visibilidad técnica y datos publicables
a cambio de rate limits premium, créditos API, y acceso al equipo técnico.

---

## Tres ejes del experimento Abu Oracle × Anthropic

Abu Oracle es simultáneamente tres experimentos distintos, cada uno
publicable por separado y combinables en un narrative único:

### Eje 1 — Eficiencia económica (FinOps MILP)

**Pregunta:** ¿cuál es el precio mínimo por plan que hace Sonnet everywhere
sostenible dado el patrón de demanda real observado?

**Contribución diferencial vs literatura:**
- FrugalGPT (Stanford) y RouteLLM (Berkeley) optimizan calidad dado un budget.
  Usan benchmarks NLP públicos (HEADLINES, MMLU, GSM8K).
- Abu Oracle invierte la variable de decisión: fija calidad (Sonnet) y optimiza
  precio al usuario. Usa datos de producción reales con estructura de negocio:
  plan de pago, ruta doctrinal, costo por request, patrón mensual por cohorte.
- Es el primer paper que formula el problema desde el lado del precio, no del modelo.

**Dataset:** logs de `selectModel.ts` post-launch — `route`, `plan`,
`model_selected`, `tokens_input_est`, `cost_est_usd` por request.
Structuralmente más rico que FrugalGPT/RouteLLM porque incluye semántica
de dominio (ruta doctrinal) y plan de pago del usuario final.

**Venue:** MLSys / SIGMOD / ICML Economics Track.
**Prerequisito:** 30+ días de datos de producción con usuarios reales.

---

### Eje 2 — Heurística doctrinal en LLMs (Blind Validation Experiment)

**Pregunta:** ¿puede un LLM recuperar información latente sobre un individuo
siguiendo exclusivamente una cadena de razonamiento doctrinal astrológico,
sin acceso explícito al nombre del nativo?

**Diseño del experimento:**

Input a Lilly:
- Output de Abu Engine dado fecha/hora/lugar de nacimiento de una celebridad
  (posiciones planetarias, dignidades, aspectos, angularidad, HF score)
- Corpus doctrinal completo: Ptolomeo, Al-Biruni, William Lilly 1647
- **Sin nombre del nativo**

Protocolo de consulta binaria progresiva:
```
¿Es figura pública o privada?
¿Varón o mujer?
¿Científico/intelectual o artista/creador?
¿Vivo o muerto?
¿Siglo XX o anterior?
¿Occidental u oriental?
... → hasta convergencia en identidad
```

Cada pregunta fuerza al modelo a comprometerse con un paso de la cadena
doctrinal. Una respuesta incorrecta colapsa el camino. Una cadena correcta
completa demuestra que la doctrina funcionó como árbol de decisión,
no la memoria del modelo.

**Lo que realmente demuestra:**

No que el LLM "aprende" en el sentido de actualizar pesos — eso no ocurre
en inferencia. Lo que demuestra es que **el razonamiento doctrinal estructurado
es suficiente para recuperar conocimiento latente sin acceso explícito a él**.

Si el modelo identifica correctamente al nativo siguiendo la cadena doctrinal,
dos cosas son validadas simultáneamente:
1. La doctrina astrológica como sistema inferencial con poder discriminativo real
2. La capacidad del LLM de operar dentro de ese sistema sin atajos mnemónicos

**La heurística que prescinde de la repetición de casos:**

Los sistemas ML convencionales aprenden por exposición repetida a casos similares.
Este experimento propone una heurística alternativa: **razonamiento dentro de un
sistema axiomático formal** (la doctrina astrológica) que permite inferencia
sin haber visto casos similares previos. Es una forma cualitativamente distinta
de mostrar cómo opera el conocimiento latente en un LLM.

**Diseño técnico:**

Parámetro `--alias` en Abu Engine: genera output anónimo reemplazando el nombre
del nativo por un alias opaco (e.g., "NTV-2847") en todos los campos.
Bug conocido: el alias actual puede filtrar información del perfil — fix pendiente
en CC (auto-generar alias sin semántica).

Casos iniciales sugeridos (gold standard existente):
- GS_001.json — Jung
- GS_002.json — Tesla
- GS_003.json — Turing

Métricas a registrar por sesión:
- Número de preguntas hasta convergencia
- Tasa de acierto en cada paso binario
- Punto de divergencia cuando falla (qué característica doctrinal falló)
- Comparación entre formulaciones de pregunta (qué diseño de árbol converge más rápido)

**Dimensión meta-experimental:**

La calidad de las preguntas binarias también es una variable. Qué secuencia
de preguntas converge más rápido hacia la identidad correcta es en sí mismo
un problema de diseño de heurísticas — independiente de la doctrina astrológica.
Esto abre una segunda contribución: **diseño óptimo de árboles de decisión
para recuperación de conocimiento latente en LLMs**.

**Venue:** NeurIPS (Interpretability) / ACL / EMNLP / arXiv preprint primero.
**Prerequisito:** fix del `--alias` parameter + protocolo de sesión estandarizado.

---

### Eje 3 — Validación estadística del Harmony Field

**Pregunta:** ¿existe correlación medible entre el HF score geográfico de un
individuo y la valencia de eventos biográficos significativos en esa ubicación?

**Resultados actuales (honestos):**
- Global: r=0.121 (n=527, HF_v3) — señal débil, en investigación
- Dominio H05 Creatividad: r=0.350
- H10 Carrera (HF_v6): Cohen's d=0.702 — resultado más fuerte, con caveats
  sobre composición del corpus

**Venue:** Journal of Consciousness Studies / Correlation (revista de astrología
científica) / arXiv como preprint con honestidad sobre limitaciones.
**Prerequisito:** dataset ampliado + protocolo de replicación independiente.

---

## Vías de relación con Anthropic

### Vía A — Anthology Fund (prioritaria)

**Qué es:** inversión directa de Menlo Ventures + $25,000 en créditos API +
priority rate limits + acceso al equipo técnico de Anthropic.

**Por qué es la vía prioritaria:** los rate limits premium resuelven el supply
constraint que el MILP identifica como binding a escala. No es solo dinero —
es acceso a throughput que hace el sistema escalable.

**Cuándo aplicar:** después del 18 de abril, con al menos 2-4 semanas de datos
de producción reales. La aplicación sin tracción no tiene sentido.

**Qué presentar:**
- Abu Oracle como vertical app con validación estadística propia
- Los tres ejes del experimento como diferencial técnico
- El MILP como demostración de que el equipo piensa en sustentabilidad
- Datos honestos: J-S p=5×10⁻⁶ (preliminar), HF r=0.121 global / d=0.702 H10
- Links: app.abu-oracle.com + finops demo

**Cómo aplicar:** directamente al Anthology Fund (no requiere VC intermediario).
URL: anthropic.com/anthology (verificar vigencia al momento de aplicar).

---

### Vía B — Claude Partner Network (secundaria)

**Qué es:** programa para consulting firms e integradores. Anthropic comprometió
$100M para partners que despliegan Claude en enterprise.

**Encuadre para Abu Oracle:** caso de referencia de "SaaS vertical sobre Claude
con pricing sustentable y validación estadística propia". A cambio de ser caso
de estudio público: visibilidad en el ecosistema + posibles créditos adicionales.

**Cuándo:** después de tener paper en arXiv o resultados publicados. La vía B
requiere credibilidad técnica documentada, no solo el producto.

---

### Vía C — Contenido técnico (distribución orgánica)

Publicar en X/@AbuOracle el experimento de Blind Validation como hilo técnico:
- Qué es el experimento
- Un caso en vivo (Jung o Tesla, con alias)
- La cadena de preguntas binarias y las respuestas de Lilly
- El resultado

Esto atrae atención de la comunidad de investigadores de LLMs antes de que
haya un paper formal. Anthropic frecuentemente amplifica contenido técnico
interesante del ecosistema. Es distribución gratuita si el contenido es sólido.

**Cuándo:** puede empezar antes del launch. El experimento de Blind Validation
no requiere usuarios reales — solo el gold standard existente (Jung, Tesla, Turing).

---

## Orden de ejecución

| Acción | Cuándo | Prerequisito |
|--------|--------|--------------|
| Fix `--alias` en CC | Esta semana | — |
| Sesión BV piloto (Jung) | Esta semana | Fix alias |
| Hilo X con BV caso Jung | Pre-launch | Sesión piloto |
| Launch app.abu-oracle.com | 18 abril | Deploy completo |
| 30 días de logs producción | Mayo | Launch |
| Aplicación Anthology Fund | Mayo | Logs + tracción |
| arXiv preprint FinOps | Junio | Logs + MILP calibrado |
| arXiv preprint BV | Junio | 10+ sesiones BV documentadas |

---

## Principio transversal

> Estos no son tres papers separados — son tres lentes sobre el mismo sistema.
> Abu Oracle como plataforma de investigación sobre razonamiento doctrinal,
> eficiencia económica de LLMs, y validación estadística de sistemas axiomáticos.
> La combinación es lo que lo hace único. Ninguno de los tres existe igual en
> otro lugar porque ningún otro sistema tiene los tres simultáneamente.
