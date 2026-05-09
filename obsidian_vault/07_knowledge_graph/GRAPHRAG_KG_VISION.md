# Abu Oracle — Knowledge Graph Architecture Vision
**Fecha:** 2026-05-05
**Estado:** Active Draft
**Origen:** Sesión de diseño estratégico — conversación con Claude

---

## 1. La tesis central

La Axiomática de los Cielos (v0.4) es el meta-esquema de un Knowledge Graph de doctrinas astrológicas.
No es la ontología de grafo — es algo más valioso: define las condiciones bajo las cuales construirla.

La conversión de la Axiomática a infraestructura de grafo ejecutable es lo que distingue Abu Oracle de cualquier otro sistema de astrología computacional. No es una feature de producto — es la diferencia entre un sistema que *sabe lo que hace* y uno que *parece que sabe*.

---

## 2. Por qué GraphRAG es la arquitectura correcta

Los LLMs (incluido Claude / Lilly) codifican conocimiento como representaciones distribuidas en un espacio vectorial de altísima dimensión. Las relaciones entre conceptos son **implícitas y probabilísticas** — no hay una arista etiquetada `Marte → rige → Aries`. Hay una geometría aprendida estadísticamente.

Consecuencias prácticas:

| | LLM (Lilly) | Knowledge Graph |
|---|---|---|
| Relaciones | Implícitas, aprendidas | Explícitas, declaradas |
| Manejo de ambigüedad | Bueno | Malo |
| Precisión doctrinal | Probabilística | Determinística |
| Auditabilidad | Ninguna | Completa |
| Alucinación de reglas | Posible | Imposible por diseño |
| Cross-tradición | Mezcla sin control | Subgrafos independientes |

**GraphRAG combina ambos**: el grafo hace el traversal preciso y entrega el subgrafo relevante; Lilly lo convierte en lenguaje natural. Es exactamente lo que el Axioma 6.3 ya describe: el Orchestrator coordina semánticas, no decide verdad. El KG decide verdad.

Evidencia empírica ya disponible en Abu Oracle:
- HF_global ↔ valencia de eventos: correlación 0.155
- HF_dominio ↔ eventos del dominio: correlación 0.615

La diferencia de 0.46 **es el valor de seleccionar el subgrafo correcto** (Axioma 8.3). GraphRAG produce exactamente este efecto en cualquier dominio.

---

## 3. Lo que la Axiomática v0.4 ya define como grafo

### Arquitectura de dos capas

**Axioma 4.1 + 4.3** definen una arquitectura de grafo de dos capas:

- **Capa 1 — Universal (invariante entre tradiciones)**: Arquetipos como nodos atómicos — planetas, casas, aspectos, signos, dominios de vida
- **Capa 2 — Tradition-specific (variable)**: Aristas de interpretación con pesos distintos por tradición — dignidades, jerarquías, reglas composicionales

Esto es arquitecturamente más correcto que la mayoría de implementaciones KG que aplanan todo en un grafo único.

### `house_significators` ya es una query de grafo

```python
planet_subset = house_significators(natal, house=k)  # Axioma 8.3
```

Esta función selecciona un **subgrafo**: los nodos significadores de una casa con sus aristas de dominio. Está implementada como función Python — la conversión a query Cypher/NetworkX es un detalle de implementación, no de diseño.

### El traversal multi-hop ya está formalizado

**Axioma 9.4** define tres hops:

```
significador natal (hop 1)
  → resonancia geográfica HF (hop 2)  [implementado]
  → activación temporal dasha (hop 3)  [próximo horizonte]
```

El sistema actual implementa hops 1+2. La incorporación de dashas completa el grafo.

---

## 4. Capacidades que el KG habilita y no existen en ningún sistema actual

### 4.1 Razonamiento multi-hop trazable
> "¿Por qué Berlín es favorable para mi carrera?"

**Hoy**: output de LLM con fundamento opaco.

**Con KG**:
```
Saturno (significador Casa 10)
  → en Berlín: dignidad accidental alta [HF score: 0.73]
  → aspecto trino → Sol natal
  → Sol rige Casa 1 (identidad, proyección pública)
```
Lilly muestra el camino, no solo la conclusión. Trazabilidad completa (Axioma 10.2 ejecutable).

### 4.2 Comparación cross-tradición sin contaminación semántica
> "¿Qué dice helenística vs. jyotish sobre esta configuración?"

**Hoy**: los LLMs mezclan. Un prompt no puede mantener separación semántica entre tradiciones.

**Con KG**: dos subgrafos con nodos arquetipos compartidos (capa 1) pero aristas de interpretación independientes (capa 2). La comparación es una query, no una esperanza. (Axioma 6.4.)

### 4.3 Detección formal de contradicción inter-tradición
Cuando helenística dice "favorable" y védica dice "significador latente" sobre el mismo nodo, el sistema detecta conflicto de grafo y lo reporta como tal — no lo suaviza en síntesis.

### 4.4 JOIN temporal-geográfico (horizonte más potente)
```
significador Casa 7
  → activo en dasha Venus (2027-2030)
  → HF score alto en Lisboa [dominio: relaciones]
```
Esta consulta unifica timing y geografía sobre el mismo nodo en el grafo. No existe en ningún sistema de astrología computacional actual. (Axioma 9.3.)

---

## 5. Lo que falta: el schema (v0.5 de la Axiomática)

> **Schema en desarrollo:** `docs/theory/KG_ONTOLOGY_SCHEMA.md` — Capa 1 completa, Capas 2 y 3 pendientes. Co-desarrollado con Lilly (tradición persa) el 2026-05-05.

### La distinción crítica: estático vs. derivado

Lilly articuló independientemente la misma arquitectura, con una precisión adicional relevante — las tres capas no son solo "nodos y aristas" sino:

| Capa | Contenido | Responsable |
|---|---|---|
| 1 — Entidades | Nodos con atributos fijos | Schema estático |
| 2 — Relaciones estáticas | Dignidades, aspectos — fijos por doctrina | Ontología base |
| 3 — Relaciones derivadas | Señor del año, firdaria activa, recepciones | **Abu Engine calcula y pasa a Lilly** |

El insight clave: las relaciones derivadas son las que hoy tienen mayor costo de precisión — Lilly las reconstruye por inferencia en cada respuesta en vez de recibirlas como hechos afirmados.

### PLANETA vs. PLANETA_TRANSPERSONAL

Distinción arquitectónica necesaria: los siete planetas tradicionales tienen dignidades esenciales y secta. Urano, Neptuno y Plutón no — son nodos `PLANETA_TRANSPERSONAL` sin dignidades, sin secta, sin domicilio. Hoy depende de la memoria de Lilly en cada sesión. Con el schema, es estructural.

La Axiomática opera en nivel meta-epistémico — define las condiciones para construir el grafo. La v0.5 debería agregar una **Sección 13: Schema de Grafo** que traduzca cada axioma a tipos de nodo y aristas.

### Tipos de nodo necesarios

| Tipo | Ejemplos |
|---|---|
| `Planet` | Sol, Luna, Marte, Venus, Saturno... |
| `Sign` | Aries, Tauro, Géminis... |
| `House` | Casa1, Casa2... Casa12 |
| `Aspect` | Conjunción, Cuadratura, Trino, Sextil, Oposición |
| `LifeDomain` | Carrera, Relaciones, Salud, Finanzas... |
| `Tradition` | Helenística, Persa, Védica, Horaria, Moderna |
| `Archetype` | Los arquetipos semánticos de $\mathcal{S}$ |
| `GeoZone` | Zonas de la grilla HF 5°×5° |
| `TimePeriod` | Dashas, tránsitos, progresiones |

### Tipos de arista necesarios

| Arista | Desde → Hasta | Atributo |
|---|---|---|
| `rige` | Planet → Sign | `tradition`, `type: domicilio\|exaltacion\|caida\|detrimento` |
| `ocupa` | Planet → Sign, House | `degree`, `natal_chart_id` |
| `aspecto` | Planet → Planet | `type`, `orb`, `applying\|separating` |
| `gobierna` | House → LifeDomain | `tradition` |
| `pertenece_a` | Sign → Element, Modality | — |
| `tiene_resonancia` | Planet → GeoZone | `hf_score`, `domain`, `fecha` |
| `activa` | TimePeriod → Planet | `dasha_lord`, `start`, `end` |
| `interpreta_segun` | Tradition → Archetype | `peso`, `jerarquia` |

### Aristas universales vs. tradition-specific

- **Universales** (capa 1): `ocupa`, `aspecto`, `pertenece_a` — iguales en todas las tradiciones
- **Tradition-specific** (capa 2): `rige`, `gobierna`, `interpreta_segun` — con atributo `tradition`

---

## 6. Ruta de implementación sugerida

### Fase 1 — Sin cambiar infraestructura (quick win)
Construir el chart natal como `NetworkX` grafo en memoria al momento de interpretación. Hacer traversal del subgrafo relevante para la pregunta. Pasar ese subgrafo serializado a Lilly en vez del JSON plano.

```python
# Hoy Lilly recibe:
{"saturn": "Gemini 18° house 10", "moon": "Capricorn 3° house 4", ...}

# Con grafo Lilly recibe:
"""
Saturn [house:10, sign:Gemini, deg:18]
  ← square ← Moon [house:4, sign:Capricorn, deg:3, orb:2°]
  → rules → House6 [domain:DailyWork, Health]
  ← transit_conjunct ← Jupiter [2026-05-10]
"""
```

### Fase 2 — Ontología universal persistida
KG separado con el conocimiento canónico de todas las tradiciones: dignidades, regencias, significados de casas y aspectos por tradición. Este es el "libro de Lilly" estructurado. Todas las interpretaciones hacen traversal sobre esta ontología.

### Fase 3 — Charts persistidos como grafos
Migrar charts de Firestore (documentos planos) a un modelo híbrido. Cada chart de usuario es un grafo personal conectado a la ontología universal.

### Fase 4 — JOIN temporal-geográfico
Incorporar dashas como `TimePeriod` nodes. Habilitar queries que crucen activación temporal con resonancia geográfica HF sobre los mismos significadores.

---

## 7. Ruta de publicación

### Publicable ahora
Axiomática v0.4 + datos empíricos (HF_global 0.155 vs HF_dominio 0.615, 527 eventos) + arquitectura Lilly Swarm = paper de diseño de sistema con validación empírica preliminar.

**Venues**: ResearchHub (preprint) → Digital Humanities Quarterly, AI & Society (Springer), o Journal of Astronomical History and Heritage.

### Para el claim fuerte (paper de sistema completo)
- Schema de grafo formalizado (v0.5 Axiomática)
- Ontología poblada para al menos dos tradiciones (helenística + védica básica)
- Demostración de al menos una capacidad de las 4 descriptas en sección 4
- Comparación cuantitativa vs. RAG vectorial puro (el diferencial ya existe: 0.615 vs 0.155)

---

## 8. El riesgo principal

**No es tecnológico.** Neo4j, NetworkX, LlamaIndex — todo existe y está maduro.

**Es scholarship.** Codificar correctamente las dignidades de Ptolomeo, el sistema de firdarías persa, los dispositors de nakshatras jyotish requiere conocimiento profundo de cada tradición. Un error de codificación en el grafo es determinístico — siempre da mal. Requiere validación por alguien con conocimiento doctrinal de cada tradición, no solo ingeniería.

---

## Referencias

- `AXIOMATICS_OF_HEAVENS_v0.4.md` — fundamento epistemológico
- `HF_EXPERIMENT_LOG.md` — datos de correlación HF_global vs HF_dominio
- `lilly_swarm/` — implementación actual del swarm de agentes
- `abu_engine/` — motor de cómputo de charts
- Emil Eifrem, "GraphRAG: The Marriage of Knowledge Graphs and RAG" — AI Engineer World's Fair 2023
- Microsoft GraphRAG (open source, 2024)

---

*Abu Oracle Project — 2026-05-05*
*Generado desde sesión de diseño estratégico*
