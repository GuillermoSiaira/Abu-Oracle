# 🜂 Abu Oracle — Semantic Flow for User Queries
**File:** `/docs/semantics.md`  
**Version:** 1.0  
**Purpose:** Define the logical and semantic pipeline that governs Abu’s interpretative process when translating a user’s natural language question into astrological and philosophical meaning.

## 1. Input Layer – User Intent Detection

### Example input
"¿Cómo me va a ir en el amor este año?"

### Processing steps
1. Natural Language Parsing  
2. Intent classification  
3. Emotional tone detection

### Example output
```json
{
  "intent": "relationships",
  "timeframe": "annual",
  "keywords": ["amor", "pareja", "sentimientos"],
  "emotional_tone": "hopeful"
}
```

## 2. Semantic Mapping → Astrological Archetypes

| Domain | Archetype | Key Planets | Relevant Houses | Complementary Points |
|---|---|---|---|---|
| Relationships / Love | Venusian (Eros, Harmony, Desire) | Venus, Moon, Sun | V, VII | Part of Marriage, Nodes |

## 3. Internal Query → Abu Engine

The semantic domain is converted into a structured internal request for the calculation engine.

```json
{
  "topic": "relationships",
  "focus": "love_yearly",
  "metrics": ["transits", "profections", "firdaria", "venus_condition"],
  "houses": [5, 7]
}
```

## 4. Symbolic Interpretation Layer

| Factor | Symbolic Reading |
|---|---|
| Venus combust | purification of desire |
| Venus–Mars square | tension between desire and assertion |
| Venus–Jupiter conjunction | harmony and generosity return |
| Profection House 7 | focus on union and reflection |
| Firdaria ruler Venus | the soul seeks beauty as a path of growth |

## 5. Narrative Generation → Lilly Engine

The Lilly Engine receives the symbolic context and generates natural language following the Persian philosophical tone.

### Example Output
```json
{
  "headline": "El fuego que purifica el corazón",
  "narrative": "Venus, oculta bajo la luz del Sol, enseña a distinguir entre deseo y devoción...",
  "actions": [
    "Practica la paciencia afectiva.",
    "Escucha lo que tu deseo intenta enseñarte."
  ]
}
```

## 6. Ethical Closure

“El sabio no predice, sino que revela los senderos que el alma ya ha comenzado a recorrer.”

## 7. Summary Diagram (Logic Flow)
```
User Query ─▶ Intent Parser ─▶ Semantic Mapper ─▶ Abu Engine
                                │
                                ▼
                       Symbolic Interpreter
                                │
                                ▼
                        Lilly Engine (LLM)
                                │
                                ▼
                    Narrative Response (Ethical Closure)
```

## 8. Temporal Intelligence Layer 🜂

### Purpose
To determine the optimal temporal scope of analysis when the user’s question includes open or flexible horizons, such as:

- “¿Qué influencias debo tener en cuenta en los próximos dos años?”
- “¿Qué puedo esperar de este ciclo que se abre?”

### Process

#### Temporal Scope Detection
The NLP layer identifies references to duration ("años", "meses", "etapas") and sets:

```json
{ "temporal_scope": "auto" }
```

If unspecified, Abu defaults to the Firdaria or annual profection period active at the time of consultation.

#### Dynamic Time Horizon Selection
- For short spans (months) → activates Lunar cycles, progressions, minor transits.
- For 1–2 years → Firdaria, profections, Saturn/Jupiter transits, eclipses.
- For 5+ years → Major planetary cycles (Saturn return, Uranus opposition, etc.).

#### Adaptive Layer Composition
Abu builds a composite dataset:

```json
{
  "2025": {"theme": "discipline and structure", "ruler": "Saturn"},
  "2026": {"theme": "renewal and expansion", "ruler": "Jupiter"}
}
```

#### Narrative Cohesion
Lilly Engine synthesizes these temporal layers into an evolutionary storyline, emphasizing continuity:

“El primer ciclo, bajo Saturno, ordena los cimientos de tu destino.
El segundo, guiado por Júpiter, abre las puertas a la expansión.
Dos años que enseñan el ritmo natural de la maduración.”

#### Ethical Anchor
- Abu never ranks or judges periods as “good” or “bad.”
- It interprets each cycle as a phase of consciousness, turning time into a philosophical map rather than a prediction.

#### Example Query Flow
User: “¿Qué influencias debo tener en cuenta para los próximos 2 años?”

→ Intent: “general life cycles”  
→ temporal_scope: “auto (2 years)”  
→ metrics: [firdaria, profection, transits(Saturn, Jupiter), eclipses]  
→ output: yearly thematic summary + narrative continuity

---

End of Document
