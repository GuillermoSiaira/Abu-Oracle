# BLIND_VALIDATION_EXPERIMENT.md

---
name: BLIND_VALIDATION_EXPERIMENT
description: Protocolo experimental de validación ciega — recuperación de conocimiento latente en LLMs via razonamiento doctrinal astrológico
tipo: experimento
version: 2026-04-06
estado: diseñado — fix alias pendiente, sesión piloto pendiente
tags: [blind-validation, heuristica, LLM, doctrina, validacion, paper, anthropic]
---

## Hipótesis central

> El razonamiento doctrinal astrológico estructurado (Ptolomeo, Al-Biruni,
> William Lilly 1647) es suficiente para recuperar conocimiento latente en un LLM
> sobre un individuo, sin acceso explícito a su identidad.

Si Lilly identifica correctamente al nativo siguiendo exclusivamente la cadena
doctrinal, dos cosas son validadas simultáneamente:

1. **La doctrina como sistema inferencial** con poder discriminativo real sobre
   configuraciones planetarias individuales
2. **El LLM como razonador dentro de sistemas axiomáticos formales** — no como
   recuperador de memoria por similitud de casos

## Por qué es interesante para la comunidad de IA

Los sistemas ML convencionales generalizan por exposición repetida a casos similares.
Este experimento propone una modalidad distinta: **inferencia dentro de un sistema
axiomático formal** que permite llegar a una conclusión sin haber visto casos
similares previos.

No es que Lilly "aprende" en el sentido de actualizar pesos — la inferencia no
modifica el modelo. Lo que se demuestra es que el conocimiento latente del LLM
puede ser *navegado* mediante una heurística doctrinal externa, de manera
análoga a como un árbol de decisión navega un espacio de hipótesis.

Esto es cualitativamente distinto de cualquier benchmark existente de LLMs
porque la métrica no es accuracy en un task estándar — es **la capacidad de
un sistema axiomático pre-moderno de actuar como oráculo de búsqueda
sobre conocimiento latente en un modelo de lenguaje moderno**.

---

## Diseño del experimento

### Input a Lilly (ciego)

```
- Output de Abu Engine para el nativo:
  · Posiciones planetarias (lon, sign, house)
  · Dignidades esenciales y accidentales (sistema tradicional)
  · Aspectos natales con orbes
  · Angularidad (HF angularity scores)
  · Profección anual + Firdaria activa
  · HF score en lugar de nacimiento
- Corpus doctrinal inyectado en system prompt:
  · Tetrabiblos (Ptolomeo)
  · Al-Biruni — Kitab al-Tafhim
  · Christian Astrology (William Lilly, 1647)
- Alias opaco del nativo: "NTV-XXXX" (sin semántica)
- Sin nombre, sin fecha explícita como texto, sin contexto biográfico
```

### Protocolo de consulta binaria progresiva

Sesión estructurada de preguntas binarias en orden de discriminación decreciente:

**Nivel 1 — Categoría social:**
- ¿Figura pública o privada?
- ¿Varón o mujer?
- ¿Vivo o muerto?

**Nivel 2 — Dominio de actividad:**
- ¿Científico/intelectual o artista/creador?
- ¿Político/líder o técnico/especialista?
- ¿Pensador teórico o hombre de acción?

**Nivel 3 — Época y geografía:**
- ¿Siglo XX o anterior/posterior?
- ¿Occidental u oriental?
- ¿Europeo o americano? (si occidental)

**Nivel 4 — Campo específico:**
- ¿Físico, matemático, o biólogo? (si científico)
- ¿Escritor, músico, o artista visual? (si artista)
- etc. — árbol adaptativo según respuestas previas

**Convergencia:** el modelo propone un nombre cuando su estimación doctrinal
converge en un individuo con suficiente confianza. Se registra el número de
preguntas necesarias para llegar a la propuesta.

### Variables registradas por sesión

```json
{
  "session_id": "BV-001",
  "subject_alias": "NTV-2847",
  "subject_real": "Carl Gustav Jung",
  "gs_file": "GS_001.json",
  "questions_count": 12,
  "correct_at_step": [true, true, false, true, ...],
  "first_wrong_step": 3,
  "final_guess": "Carl Jung",
  "correct_final": true,
  "doctrine_path": ["Saturn dominant", "12th house emphasis", "nocturnal sect", ...],
  "notes": "El modelo vaciló en la distinción médico/psicólogo en paso 3"
}
```

---

## Dimensión meta-experimental: diseño del árbol de preguntas

La calidad de las preguntas binarias es en sí misma una variable experimental.

**Pregunta abierta:** ¿qué secuencia de preguntas converge más rápido hacia la
identidad correcta, dado un output doctrinal astrológico?

Esto es un problema de diseño de heurísticas independiente de la astrología:
**diseño óptimo de árboles de decisión para recuperación de conocimiento latente
en LLMs mediante predicados externos**.

Métricas de calidad de una secuencia de preguntas:
- **Información mutua promedio** entre la pregunta y la identidad del nativo
- **Velocidad de convergencia** (preguntas hasta propuesta correcta)
- **Robustez** (¿el árbol falla graciosamente o colapsa ante el primer error?)

Esto abre una segunda contribución publicable: el diseño del árbol de decisión
óptimo para este tipo de experimentos, generalizable a otros dominios donde
se quiera "navegar" conocimiento latente de un LLM con razonadores externos.

---

## Issues técnicos pendientes

### Bug `--alias` (CRÍTICO antes de primera sesión)

El parámetro `--alias` en Abu Engine actualmente puede filtrar información del
perfil del nativo (nombre u otros campos identificables) en el output.

**Fix requerido (CC):** auto-generar alias opaco sin semántica:
- Formato: `NTV-{hash(subject_id)[:4].upper()}` — e.g., `NTV-2A4F`
- Verificar que ningún campo del output de Abu Engine contenga el nombre real
- Campos a limpiar: `subject_name`, `birth_city` (si es ciudad natal famosa),
  cualquier campo libre de texto en el JSON de respuesta

**No iniciar sesiones BV hasta que este fix esté confirmado.**

---

## Casos del gold standard para primeras sesiones

| Alias sugerido | Sujeto real | Archivo | Dificultad estimada |
|---------------|-------------|---------|---------------------|
| NTV-A001 | Carl Gustav Jung | GS_001.json | Media (Saturno 12H muy característico) |
| NTV-A002 | Nikola Tesla | GS_002.json | Alta (configuración menos obvia) |
| NTV-A003 | Alan Turing | GS_003.json | Alta (pocos indicadores públicos en doctrina) |
| NTV-A004 | Guillermo Siaira | GS_004_siaira.json | Control — el fundador conoce su propia carta |

---

## Orden de implementación

1. **Fix alias en CC** → auto-generación opaca sin semántica
2. **Sesión piloto BV-001** con Jung (NTV-A001) → registrar resultado completo
3. **Calibrar árbol de preguntas** según lo aprendido en BV-001
4. **Sesiones BV-002 y BV-003** con Tesla y Turing
5. **Hilo X/@AbuOracle** con BV-001 como demostración pública (pre-launch)
6. **Protocolo estandarizado** para incorporar nativos adicionales post-launch
7. **arXiv preprint** con 10+ sesiones documentadas

---

## Referencias cruzadas

- [[ANTHROPIC_STRATEGY]] — contexto de publicación y relación con Anthropic
- [[finops_milp]] — Eje 1 del experimento (eficiencia económica)
- `data/gold_standard/` — casos de prueba disponibles
- `abu_engine/` — generador del output doctrinal (input del experimento)
- `next_app/lib/lilly-prompt.ts` — system prompt de Lilly con corpus doctrinal
