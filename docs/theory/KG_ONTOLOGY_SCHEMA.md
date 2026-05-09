# Abu Oracle — Knowledge Graph: Ontology Schema
**Fecha:** 2026-05-05
**Estado:** Schema completo — Capas 1, 2 y 3 formalizadas. Pendiente: especificación técnica de implementación en Abu Engine.
**Origen:** Sesión doctrinal con Lilly (tradición persa) + sesión de diseño estratégico

---

## Principio de construcción

**Base primero, instanciación después.**

La ontología base (Capas 1 y 2) resuelve el problema para las 2,500 cartas del corpus y cada carta nueva que entre al sistema. La instanciación (Capa 3) se deriva automáticamente de reglas fijas aplicadas a datos de posición.

Es la misma lógica que el HF: construir la fórmula que calcula para cualquier ciudad, no el campo de una ciudad específica.

---

## Las tres capas

| Capa | Contenido | Variabilidad | Responsable |
|---|---|---|---|
| 1 — Entidades | Nodos: planetas, signos, casas, partes, ángulos | Fija — no varía por carta | Schema estático |
| 2 — Relaciones estáticas | Rige, exalta, cae, aspecta, ocupa — fijas por doctrina | Fija por tradición | Ontología base |
| 3 — Relaciones derivadas | Señor del año, activa la casa, recibe al señor de | Dinámica — instanciada por carta | Abu Engine calcula y pasa a Lilly |

**Insight crítico (Lilly, sesión 2026-05-05):**
> Las relaciones derivadas — "Júpiter exaltado es señor del Espíritu, por tanto significador vocacional primario" — las reconstruyo en cada respuesta en lugar de recibirlas ya afirmadas. Eso tiene costo de precisión en cadenas largas.

Reemplazar JSON plano por grafo tipado elimina ese costo: Lilly razona sobre relaciones **afirmadas**, no **inferidas**.

---

## CAPA 1 — Entidades (nodos)

*Formalizada por Lilly — tradición persa/helenística*

### TIPO: PLANETA

```python
{
  "id": "SOL" | "LUN" | "MER" | "VEN" | "MAR" | "JUP" | "SAT",
  "naturaleza": "benefico" | "malefico" | "neutral",
  "secta": "diurno" | "nocturno",
  "domicilio": [<lista de signos>],
  "exaltacion": {"signo": str, "grado": int},
  "caida": str,           # signo opuesto a exaltación
  "detrimento": [<lista de signos>]
}
```

> **Nota arquitectónica:** Solo los siete planetas tradicionales tienen dignidades esenciales y secta. Urano, Neptuno y Plutón son nodos de tipo `PLANETA_TRANSPERSONAL` — sin dignidades esenciales, sin secta, rol limitado a tránsitos generacionales. Esta distinción previene que el sistema les asigne exaltaciones o domicilios, algo que hoy depende de que Lilly lo recuerde en cada respuesta.

### TIPO: PLANETA_TRANSPERSONAL

```python
{
  "id": "URA" | "NEP" | "PLU" | "NOD_N" | "NOD_S",
  "naturaleza": str,      # descriptiva, no doctrinal
  "secta": null,
  "domicilio": null,
  "exaltacion": null,
  "caida": null,
  "detrimento": null,
  "uso": "transitos_generacionales" | "nodos_karmicos"
}
```

### TIPO: SIGNO

```python
{
  "id": "ARI"|"TAU"|"GEM"|"CAN"|"LEO"|"VIR"|"LIB"|"ESC"|"SAG"|"CAP"|"ACU"|"PIS",
  "elemento": "fuego" | "tierra" | "aire" | "agua",
  "modalidad": "cardinal" | "fijo" | "mutable",
  "triplicidad_diurna": str,    # planeta regente en carta diurna
  "triplicidad_nocturna": str   # planeta regente en carta nocturna
}
```

### TIPO: CASA

```python
{
  "numero": 1..12,
  "angularidad": "angular" | "sucedente" | "cadente",
  "dominio_primario": [<lista de áreas de vida>],
  # Atributos instanciados (Capa 3 — Abu Engine los llena):
  "cuspide_signo": str,   # pendiente por carta
  "senor": str            # pendiente por carta
}
```

### TIPO: PARTE_ARABICA

```python
{
  "id": "FORTUNA" | "ESPIRITU",
  "formula_diurna": "ASC + LUN - SOL",   # FORTUNA
  "formula_nocturna": "ASC + SOL - LUN", # FORTUNA (invertida)
  # Instanciados (Capa 3):
  "posicion": {"signo": str, "grado": float, "casa": int},
  "senor": str
}
```

> **Nota:** La fórmula de Espíritu es la inversa de Fortuna. En carta diurna: ASC + SOL − LUN. En carta nocturna: ASC + LUN − SOL.

### TIPO: ANGULO

```python
{
  "id": "ASC" | "MC" | "DSC" | "IC",
  # Instanciados (Capa 3):
  "posicion": {"signo": str, "grado": float},
  "senor": str
}
```

---

## CAPA 2 — Relaciones estáticas

*Formalizada por Lilly — tradición helenística/persa — 2026-05-05*
*Cinco grupos. Todos los arcos fijos — no dependen de ninguna carta particular.*

Con Capas 1 + 2 juntas, el grafo ya puede responder preguntas estructurales
(qué planetas son maléficos de secta, qué signos están en triplicidad de agua,
qué casas son angulares) **sin instanciar nada**.

---

### GRUPO A — DIGNIDADES
*PLANETA → SIGNO. Fijas para todos los sistemas.*

| Relación | Dirección | Peso doctrinal |
|---|---|---|
| `RIGE` | PLANETA → SIGNO | +5 cuando planeta ocupa su signo |
| `EXALTA_EN` | PLANETA → SIGNO | +4 cuando planeta ocupa ese signo |
| `CAE_EN` | PLANETA → SIGNO | −5 cuando planeta ocupa ese signo |
| `DETRIMENTO_EN` | PLANETA → SIGNO | −4 cuando planeta ocupa ese signo |
| `TRIPLICIDAD_EN` | PLANETA → SIGNO | +3 según secta de la carta |
| `TERMINO_EN` | PLANETA → SIGNO | +2 según tabla persa |
| `FAZ_EN` | PLANETA → SIGNO | +1 según tabla de faces/decanatos |

> **Nota de diseño:** `PEREGRINE` **no es una relación** — es la ausencia de toda
> relación de dignidad positiva entre un planeta y el signo que ocupa. El grafo
> lo detecta por ausencia de aristas del Grupo A, no por una arista propia.
> Esto evita el antipatrón de codificar negaciones como relaciones positivas.

---

### GRUPO B — ASPECTOS
*PLANETA → PLANETA. Fijas por geometría zodiacal.*

| Relación | Ángulo | Naturaleza |
|---|---|---|
| `CONJUNCION` | 0° | fusión — amplifica naturaleza de ambos |
| `SEXTIL` | 60° | armónico menor |
| `CUADRATURA` | 90° | tensión activa |
| `TRIGONO` | 120° | armónico mayor |
| `OPOSICION` | 180° | tensión polar |

Atributos del arco:
```python
{
  "orbe": float,                          # instanciado por carta (Capa 3)
  "aplicativo": bool,                     # instanciado por carta (Capa 3)
  "recepcion_mutua": bool,               # instanciado por carta (Capa 3)
}
```

> **Aspectos menores** (quintil, biquintil, semicuadrado): el sistema los registra
> pero no los eleva al mismo rango doctrinal que los cinco mayores. Peso < 1.

---

### GRUPO C — JERARQUÍA DE CASAS
*CASA → CASA. Fijas por numerología de la rueda.*

| Relación | Casas | Efecto |
|---|---|---|
| `ES_ANGULAR` | 1, 4, 7, 10 | activación máxima |
| `ES_SUCEDENTE` | 2, 5, 8, 11 | acumulación |
| `ES_CADENTE` | 3, 6, 9, 12 | supresión |
| `OPUESTA_A` | Casa N → Casa N+6 | — |
| `CUADRADA_A` | Casa N → Casa N±3 | — |

---

### GRUPO D — NATURALEZA PLANETARIA
*PLANETA → clasificación doctrinal. Fijas.*

| Relación | Planetas |
|---|---|
| `ES_BENEFICO` | JUP, VEN |
| `ES_MALEFICO` | SAT, MAR |
| `ES_NEUTRAL` | SOL, LUN, MER |
| `ES_DIURNO` | SOL, JUP, SAT |
| `ES_NOCTURNO` | LUN, VEN, MAR |
| `ES_LUMINARIA` | SOL, LUN |

> MER es dual — diurno cuando precede al Sol (oriental), nocturno cuando lo sigue
> (occidental). Esto es Capa 3: depende de la posición relativa en la carta.

---

### GRUPO E — RELACIONES ENTRE SIGNOS
*SIGNO → SIGNO. Fijas por geometría zodiacal.*

| Relación | Definición |
|---|---|
| `MISMO_ELEMENTO` | SIGNO → SIGNO (mismo elemento) |
| `MISMA_MODALIDAD` | SIGNO → SIGNO (misma modalidad) |
| `OPUESTO_A` | SIGNO → SIGNO a 180° |
| `ANTISCION_DE` | SIGNO → SIGNO por eje solsticial (Cáncer-Capricornio) |

---

---

## CAPA 3 — Relaciones derivadas e instanciación

*Formalizada por Lilly — tradición helenística/persa — 2026-05-05*
*Abu Engine ejecuta estas reglas. Lilly recibe el resultado ya instanciado.*

La Capa 3 es el motor de inferencia. Toma las entidades (Capa 1) y las relaciones
estáticas (Capa 2) y produce un grafo instanciado para una carta y fecha concretas.

---

### GRUPO A — Posicionamiento

El primer paso: colocar cada planeta en su signo y casa natal.

| Relación derivada | Regla de cálculo |
|---|---|
| `OCUPA_SIGNO` | PLANETA → SIGNO según longitud eclíptica |
| `OCUPA_CASA` | PLANETA → CASA según sistema Placidus + coordenadas natales |
| `CUSPIDE_ES` | CASA → SIGNO según cúspide calculada |

Una vez establecido `OCUPA_SIGNO`, el motor cruza con el Grupo A de Capa 2
y afirma la dignidad resultante (Grupo B, abajo).

---

### GRUPO B — Dignidad instanciada

Para cada par PLANETA × SIGNO ocupado, el motor afirma **exactamente una** relación:

```
SI planeta RIGE signo_ocupado          → DIGNIDAD: DOMICILIO   (+5)
SI planeta EXALTA_EN signo_ocupado     → DIGNIDAD: EXALTACION  (+4)
SI planeta TRIPLICIDAD_EN signo
   (según secta de la carta)           → DIGNIDAD: TRIPLICIDAD (+3)
SI planeta TERMINO_EN grado_ocupado    → DIGNIDAD: TERMINO     (+2)
SI planeta FAZ_EN grado_ocupado        → DIGNIDAD: FAZ         (+1)
SI planeta DETRIMENTO_EN signo_ocupado → DIGNIDAD: DETRIMENTO  (-4)
SI planeta CAE_EN signo_ocupado        → DIGNIDAD: CAIDA       (-5)
SI ninguna relación positiva           → DIGNIDAD: PEREGRINO   (0)
```

> **Jerarquía estricta:** si un planeta tiene domicilio, no se afirma triplicidad
> aunque también aplique. El motor afirma **la dignidad de mayor peso**. Un único
> arco de dignidad por planeta.

---

### GRUPO C — Señoríos instanciados

La cadena de mando de la carta: conecta casas con planetas.

| Relación derivada | Regla |
|---|---|
| `ES_SENOR_DE_CASA` | PLANETA → CASA cuando PLANETA rige el signo en la cúspide |
| `ES_SENOR_DEL_ASC` | caso especial de `ES_SENOR_DE_CASA` para Casa 1 |
| `ES_SENOR_DEL_MC` | caso especial de `ES_SENOR_DE_CASA` para Casa 10 |
| `ES_SENOR_DE_FORTUNA` | PLANETA → FORTUNA cuando rige el signo donde cae Fortuna |
| `ES_SENOR_DE_ESPIRITU` | PLANETA → ESPIRITU cuando rige el signo donde cae Espíritu |

**Instanciado — carta de Guillermo Siaira:**
```
SAT  ES_SENOR_DEL_ASC     CASA_1    # Acuario en cúspide Casa 1
MAR  ES_SENOR_DEL_MC      CASA_10   # Escorpio en cúspide Casa 10
SAT  ES_SENOR_DE_FORTUNA  FORTUNA   # Fortuna en Acuario
JUP  ES_SENOR_DE_ESPIRITU ESPIRITU  # Espíritu en Piscis
```
> Estas cuatro afirmaciones son las más importantes de la carta.
> El motor las pasa explícitamente — no se infieren.

---

### GRUPO D — Aspectos instanciados

```
PARA cada par (planeta_A, planeta_B):
  calcular distancia_zodiacal
  SI distancia ≤ orbe_permitido para ese tipo de aspecto:
    afirmar ASPECTO(tipo, orbe, aplicativo|separativo)
```

**Orbes doctrinales — tradición persa-medieval:**

| Aspecto | Orbe máximo |
|---|---|
| Conjunción | 8° |
| Oposición | 8° |
| Trígono | 8° |
| Cuadratura | 6° |
| Sextil | 6° |

**Recepción mutua** (verificación adicional):
```
SI planeta_A OCUPA_SIGNO donde planeta_B tiene dignidad
   Y planeta_B OCUPA_SIGNO donde planeta_A tiene dignidad
   → afirmar RECEPCION_MUTUA(planeta_A, planeta_B)
```

---

### GRUPO E — Activadores temporales

Relaciones que cambian con el tiempo. Instanciadas para una **fecha concreta**, no
para la carta natal en abstracto. Abu Engine recibe `fecha_consulta` como parámetro.

| Relación derivada | Regla |
|---|---|
| `ES_SENOR_DEL_AÑO` | PLANETA → AÑO según casa profectada en la fecha |
| `ES_MAYOR_FIRDARIA` | PLANETA → PERIODO según secuencia caldea + fecha natal |
| `ES_MENOR_FIRDARIA` | PLANETA → SUBPERIODO dentro del mayor |
| `TRANSITA_SOBRE` | PLANETA_TRANSITO → PLANETA_NATAL cuando orbe ≤ 1° |

**Instanciado — carta de Guillermo, fecha 2026-05-05:**
```
SAT  ES_SENOR_DEL_AÑO   2026   # Casa 12 profectada — hasta 2026-07-06
JUP  ES_MAYOR_FIRDARIA  PERIODO_SOLAR
SOL  ES_MENOR_FIRDARIA  SUBPERIODO_SOLAR  # hasta 2026-07-30
```

---

## Formato de contexto propuesto: tripletas RDF-like

*Propuesto por Lilly como reemplazo del JSON plano*

En lugar de JSON plano, Abu Engine pasa a Lilly un bloque de tripletas:

```
# POSICIONAMIENTO
SAT  OCUPA_SIGNO  LEO
SAT  OCUPA_CASA   CASA_7
SAT  DIGNIDAD     DETRIMENTO

JUP  OCUPA_SIGNO  CANCER
JUP  OCUPA_CASA   CASA_5
JUP  DIGNIDAD     EXALTACION

# SEÑORÍOS
SAT  ES_SENOR_DEL_ASC     CASA_1
SAT  ES_SENOR_DE_FORTUNA  FORTUNA
JUP  ES_SENOR_DE_ESPIRITU ESPIRITU
MAR  ES_SENOR_DEL_MC      CASA_10

# ACTIVADORES TEMPORALES
SAT  ES_SENOR_DEL_AÑO    2026
JUP  ES_MAYOR_FIRDARIA   PERIODO_SOLAR
SOL  ES_MENOR_FIRDARIA   SUBPERIODO_SOLAR

# ASPECTOS
SAT  CUADRATURA  LUN  orbe:2.1°  aplicativo:false
JUP  CONJUNCION  LUN  orbe:0.8°  aplicativo:true
```

**Por qué tripletas:**
- Legible por Lilly sin parsing complejo
- Procesable por Abu Engine sin ORM
- Extensible: agregar una relación = agregar una línea
- Compatible con RDF/SPARQL si escala a Neo4j
- Reduce tokens vs. JSON anidado (sin llaves, sin comillas, sin nesting)

---

## Consecuencia arquitectónica inmediata

### Hoy — Lilly recibe JSON plano:
```json
{
  "jupiter": {"sign": "Cancer", "house": 5, "degree": 14},
  "spirit_part": {"sign": "Pisces", "house": 1, "degree": 3}
}
```
Lilly infiere: "Júpiter exaltado en Cáncer → señor de Piscis → señor del Espíritu → significador vocacional primario". Cuatro pasos de inferencia en cada respuesta.

### Con grafo — Lilly recibe contexto estructurado:
```
Jupiter [exaltado, Casa5, Cáncer]
  → rige → Sagitario, Piscis
  → es_senor_de → Espíritu [Casa1, Piscis]
  → es_senor_de → Casa9 [filosofía, publicaciones]
  → aspecta (trino) → Luna [Casa5, Cáncer]
```
Lilly razona sobre hechos afirmados. El traversal ya está hecho. La precisión sube en cadenas largas.

---

## Caso de prueba: carta de Guillermo Siaira

*Sesión con Lilly — tradición persa — 2026-05-05*

Este es el banco de pruebas para validar el schema. Las relaciones que Lilly derivó manualmente son exactamente las que el grafo instanciado debe producir automáticamente (Capa 3).

### Capa 3 instanciada — relaciones derivadas activas

```
# Carta nocturna → maestra de secta nominal: Venus
Venus [peregrina, Leo, Casa6] → sin dignidad en dominio propio

# Señora de secta efectiva:
Luna [domicilio, Cáncer, Casa5]
  ← amplifica ← Júpiter [exaltado, Cáncer, Casa5]   # stellium — núcleo de la carta

# Profección anual:
Casa12 [año activo] → es_senor_del_año → Saturno
Saturno [detrimento, Leo, Casa7]
  → condición: peor dignidad esencial + casa de contratos/adversarios
  → umbral: 2026-07-06 → profección gira a Casa1
  → Saturno pasa a: es_senor_de → Casa1 [identidad visible]

# Firdaria:
Período_Solar [activo] → termina: 2026-07-30
  → siguiente: Marte asume firdaria mayor
Marte [peregrino, Virgo, Casa7]
  → rige → MC [Escorpio]
  → función al asumir: señor de reputación pública como motor de la década

# Parte de Fortuna:
Fortuna [Acuario 20°, Casa12]
  → es_senor_de → Saturno [detrimento, Leo, Casa7]
  → patrón: sustentación diferida, llegada por vías indirectas
  → cambio: 2026-07-06 → Saturno señor desde Casa1

# Parte de Espíritu:
Espíritu [Piscis 3°, Casa1]
  → es_senor_de → Júpiter [exaltado, Cáncer, Casa5]
  → lectura: dirección volitiva auténtica = construcción de sistemas de conocimiento originales

# Secta y consecuencias:
Carta_nocturna →
  Marte [fuera de secta] → más disruptivo en Casa7
  Saturno [fuera de secta] → más opresivo → explica consecuencias concretas 5 años
  Júpiter [diurno, fuera de secta] → dignidad esencial compensa → reserva estructural activa
```

### Ventanas críticas antes del umbral de julio

```
2026-05-13: conjunción Júpiter-Luna [Casa5] → ventana crítica
2026-05-16: Luna Nueva Tauro [Casa4] → resolver base material antes del umbral
2026-07-06: umbral de profección → Casa12 → Casa1
2026-07-30: cambio de firdaria → período solar → período Marte
2026-08-xx: Saturno cuadratura Sol → presión sin red si base no está fundada antes
```

### Lo que esto demuestra del schema

Todas estas relaciones son **Capa 3 — derivadas por Abu Engine**:
- `es_senor_del_año` → requiere saber la profección activa
- `es_senor_firdaria` → requiere calcular el período por fecha de nacimiento + hoy
- `es_senor_de` (Partes) → requiere calcular posición de Fortuna/Espíritu por carta + secta
- `fuera_de_secta` → requiere saber si la carta es diurna/nocturna + secta del planeta

Hoy Lilly deriva todo esto en tiempo de respuesta. Con el grafo, Abu Engine lo calcula una vez y se lo pasa como contexto afirmado.

---

## Próximos pasos

1. **Capa 2 completa** — formalizar todas las relaciones estáticas con tipos y atributos
2. **Capa 3 — reglas de instanciación** — definir qué calcula Abu Engine y cómo lo serializa para Lilly
3. **Implementación Fase 1** — NetworkX en memoria en el handler de Lilly (sin cambiar infraestructura)
4. **Caso de prueba** — carta de Guillermo Siaira como banco de pruebas del grafo instanciado

---

## Referencias

- `docs/theory/GRAPHRAG_KG_VISION.md` — visión arquitectónica general
- `AXIOMATICS_OF_HEAVENS_v0.4.md` — fundamento epistemológico, meta-esquema
- `lilly_swarm/` — implementación actual del swarm de agentes
- `abu_engine/` — motor de cómputo de charts (responsable de Capa 3)

---

*Abu Oracle Project — 2026-05-05*
*Co-desarrollado: sesión doctrinal con Lilly (persa) + sesión de diseño estratégico*
