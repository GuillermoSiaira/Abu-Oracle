# AI_Oracle – Concepts and Roadmap (2025)

## 1. Vision and Purpose
AI_Oracle busca construir un sistema de razonamiento astrológico asistido por IA que combine:
- Doctrina clásica (inspirada en William Lilly) con un lenguaje simbólico coherente.
- Lógica y consistencia explícitas (axiomas, marcos de referencia, reglas de inferencia).
- Diálogo natural multilingüe (ES/EN/PT/FR) con transparencia sobre fuentes y criterios.
- Capacidad de razonar a través de marcos y temporalidades: solar, lunar y (a futuro) sidéreo.

Objetivo: interpretaciones claras, verificables y con trazabilidad (referencias clásicas + axiomas) que integren datos computados por Abu con la capa cognitiva de Lilly.

## 2. Cognitive Architecture (Lilly Engine)

| Layer       | Function                                                        | Current Status |
|------------|------------------------------------------------------------------|----------------|
| Memory     | Context persistence and recall (`core/context_manager.py`)       | In progress    |
| Reasoning  | Logical axioms and consistency framework (`/data/axioms`)        | In progress    |
| Knowledge  | Classical corpus via embeddings (`/data/lilly_corpus` + `embeddings.json`) | Planned        |
| Expression | Multilingual natural output (ES/EN/PT/FR)                        | Implemented    |
| Integration| Abu ↔ Lilly data flow and FE visualization                        | Stable         |

Notas:
- Memory: almacena últimas entradas por usuario y permite inyectar contexto relevante.
- Reasoning: axiomas y reglas formales para sostener coherencia (aspectos, dignidades, casas, temporalidad).
- Knowledge: recuperación semántica de citas de la obra clásica para trazabilidad y soporte pedagógico.
- Expression: plantillas y detección de idioma; salida en JSON estructurado.
- Integration: contratos estables con Abu y el Frontend para datos y visualización.

## 3. Classical Corpus Integration
Plan para integrar el corpus clásico (William Lilly, "Christian Astrology") como base de conocimiento mediante embeddings:
- Estructura de carpetas:
  - `/lilly_engine/data/lilly_corpus/` → textos segmentados (capítulos/párrafos) en UTF-8.
  - `/lilly_engine/data/embeddings.json` → índice semántico (vector store minimal) con metadatos (título, sección, cita).
- Script de preparación: `generate_embeddings.py`
  - Tokeniza y normaliza el corpus.
  - Genera embeddings (OpenAI u otro backend) y guarda en `embeddings.json`.
- Búsqueda: `search_embeddings(query, top_k=5)`
  - Recupera citas relevantes por similitud y las inyecta a la construcción de prompt.
- Inyección en prompt: referencias clásicas se añaden a la sección “Classical References” con citas breves y fuente.

## 4. Logical Axioms and Reasoning Framework
Contenidos esperados de `/lilly_engine/data/axioms/astrological_axioms.md`:
- Marcos de referencia: tropical/sidéreo (plan a futuro), solar/lunar.
- Lógica de aspectos: orbes, jerarquía (conjunción/oposición/cuadratura/trígono/sextil), aplicación/separación (si se modela en futuro).
- Tempo planetario: lentos vs rápidos; ciclos mayores; relevancia por período.
- Prioridades de casas: angular > sucedente > cadente; ejes y acentos.
- Reglas de consistencia: no contradecir axiomas activos; en caso de ambigüedad, explicitar supuestos.

Integración dinámica:
- `build_prompt()` incorporará un bloque “Reasoning Axioms” con axiomas activos (según contexto del caso) para guiar la estructura inferencial de la respuesta.
- Estas reglas actúan como “andamiaje” semántico para la narrativa y las acciones propuestas.

## 5. Prompt Composition Flow
Orden recomendado de composición del prompt:
1) Reasoning Axioms  → marco lógico y restricciones
2) Classical References → citas breves con fuente (Lilly)
3) User Context and Chart → perfil, resumen de carta/raíles del caso
4) Question → foco del usuario (idioma detectado)
5) Response → JSON: { headline, narrative, actions }

## 6. Future Roadmap

| Phase | Focus                    | Description                                                  |
|------:|--------------------------|--------------------------------------------------------------|
| v2.1  | Context Memory Integration | Persist previous readings per user; in-context injection      |
| v2.2  | Reasoning Framework      | Active axioms and logical consistency enforcement            |
| v2.3  | Classical Corpus         | Semantic retrieval from Christian Astrology                   |
| v2.4  | Relocation Logic         | Solar return + city suggestions with transparent heuristics   |
| v3.0  | Symbolic Engine          | Internal logical module (posiblemente on-chain/DAO)           |

Hitos complementarios:
- Observabilidad (health checks, métricas, logs enriquecidos).
- Ensayos controlados (tests) y smoke tests en CI.

## 7. Open Research Topics
- Representación simbólica de axiomas astrológicos (formalización ligera vs lógicas modales/temporales).
- Validación algorítmica de consistencia interpretativa (detección de contradicciones y sesgos).
- Interacción de marcos temporales (solar vs lunar vs sidéreo) en narrativas y recomendaciones.
- Priorización de información (qué mostrar, cuándo y con qué justificación) orientada a usuario final.

## 8. Technical Notes
Basado en el estado del reporte `docs/AI_Oracle_Progress_Report_4.md`:
- Estabilidad actual:
  - Docker Compose funcional (Abu, Lilly, Next.js).
  - Integración LLM en Lilly con `OPENAI_API_KEY`; mapeo de eventos de ciclos al esquema LLM.
  - Variables de entorno documentadas; endpoints probados (chart, forecast, life-cycles, solar-return, interpret).
- Pendientes operativos:
  - Tests automatizados (pytest) y smoke tests en CI.
  - Observabilidad (endpoints /health, métricas, logs de warm-up/fallbacks).
  - Tuning de modelo (elegir `LILLY_MODEL` por entorno y evaluar costo/calidad).

## 9. Appendices
- Ejemplos de prompts: antes/después de aplicar axiomas; con/ sin referencias clásicas.
- Muestras de interpretaciones: comparación por idioma y por marco (solar/lunar).
- Placeholder: notas para integración simbólica/DAO (gobernanza de axiomas y versiones de corpus).
