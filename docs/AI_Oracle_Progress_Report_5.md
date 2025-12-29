# AI Oracle – Reporte de Cambios y Estado (2025-11-03)

## Resumen ejecutivo
Hoy completamos la integración de la capa de razonamiento cognitivo en Lilly Engine. Implementamos tres pilares clave: (1) axiomas astrológicos activables, (2) búsqueda semántica preparada para corpus clásico, y (3) razonamiento explícito paso a paso. El stack está operativo con OpenAI habilitado, logs robustos y control por variables de entorno.

---

## Cambios clave implementados

### 1. Axiomas astrológicos (Reasoning Layer)
**Archivo:** `lilly_engine/data/axioms/astrological_axioms.md`

- **5 axiomas base definidos:**
  - AX-001: Aspect Orbs (default 6°)
  - AX-002: Aspect Priority (conj > opp > square > trine > sextile; menor orb = mayor peso)
  - AX-003: House Priority (angular > succedent > cadent)
  - AX-004: Planetary Tempo (lentos marcan ciclos largos, rápidos marcos cortos)
  - AX-005: Reference Frames Consistency (no mezclar tropical/sideral sin declararlo)

- **Formato estructurado:** id, description, scope, rule, weight, examples.

- **Loader implementado en `core/llm.py`:**
  - Función `load_axioms(path, limit)` lee el Markdown y filtra comentarios.
  - Control por env: `LILLY_USE_AXIOMS` (default: `true`).
  - Rutas absolutas (Path relativo a `/app` en contenedor).
  - Log: `[INFO] Injected N axioms into prompt`.

### 2. Módulo de conocimiento clásico (Knowledge Layer)
**Archivo:** `lilly_engine/core/knowledge.py`

- **Función `search_embeddings(query, top_k)`:**
  - Carga `data/embeddings.json` (índice de corpus clásico).
  - Embedding con OpenAI (`text-embedding-3-small`) si hay key; mock hash-based si no.
  - Cosine similarity con numpy.
  - Log: `[INFO] Found N references for query '...'`.
  - Fallback si falta `embeddings.json`: warning + lista vacía.

- **Script de generación:** `lilly_engine/scripts/generate_embeddings.py`
  - CLI: `--corpus`, `--output`, `--backend` (auto|openai|mock), `--model`.
  - Chunking simple por oraciones (max 1400 chars).
  - Salida: JSON con `[{id, text, source, section, embedding}]`.

### 3. Razonamiento explícito (Reasoning Field)
**Modificaciones en `core/llm.py`:**

- **Nuevo campo JSON:** `"reasoning"`.
  - Contiene justificación paso a paso de cómo el modelo aplicó axiomas y referencias.
  - Ejemplo: `"La carta del usuario refleja un momento de transformación profunda, caracterizado por tensiones creativas entre estructuras antiguas y nuevas posibilidades..."`

- **Flag opcional:** `include_reasoning` (parámetro + env var).
  - Variable de entorno: `LILLY_INCLUDE_REASONING` (default: `true`).
  - Si está activo, inyecta instrucción de razonamiento en el prompt.
  - Si está desactivado, skip (ahorra tokens/latencia).

- **Prompt mejorado:**
  - Pide al modelo razonar paso a paso usando axiomas y referencias.
  - Explica cómo cada principio se aplica a la carta y pregunta.
  - Estructura ordenada: Axioms → References → Chart → Question → Task.

- **Parsing robusto:**
  - Extrae `reasoning` del JSON del modelo.
  - Fallback: `"No explicit reasoning provided."` si falta.

- **Logging:**
  - Muestra primeros 80 chars: `[INFO] Lilly produced reasoning: ...`.

### 4. Integración en `build_prompt()`
**Archivo:** `lilly_engine/core/llm.py`

- **Secciones inyectadas:**
  ```
  Reasoning Axioms:
  {axioms_section}

  Classical References (William Lilly):
  {refs_section}

  Chart Context:
  ...
  
  Tarea de razonamiento (si include_reasoning=true):
  1. Razona paso a paso usando axiomas y referencias.
  2. Explica cómo se aplica cada principio.
  3. Incluye razonamiento en JSON bajo clave "reasoning".
  ```

- **Query para búsqueda semántica:**
  - Compuesta por transits + question.
  - Ej: `"Saturn square Sun career"` → busca en embeddings.

### 5. Dependencias y configuración
**Archivo:** `lilly_engine/requirements.txt`

- Agregado: `numpy>=1.24.0` (para cosine similarity).

**Variables de entorno recomendadas (`.env`):**
```
OPENAI_API_KEY=sk-xxxx
LILLY_MODEL=gpt-4o-mini
LILLY_USE_AXIOMS=true
LILLY_INCLUDE_REASONING=true
NEXT_PUBLIC_ABU_URL=http://localhost:8000
NEXT_PUBLIC_LILLY_URL=http://localhost:8001
```

---

## Verificaciones realizadas

### Logs de Lilly
- ✅ `[INFO] Injected 8 axioms into prompt` - Axiomas activos.
- ✅ `[WARN] No embeddings loaded` - Esperado (corpus pendiente).
- ✅ `[INFO] Found 0 references for query '...'` - Módulo knowledge activo.
- ✅ `[INFO] Lilly produced reasoning: La carta del usuario refleja...` - Reasoning generado.
- ✅ `POST /api/ai/interpret HTTP/1.1" 200 OK` - Interpretaciones exitosas.

### Respuesta JSON verificada
```json
{
  "reasoning": "Los tránsitos de Saturno y Plutón, junto con la oposición de Urano, sugieren un...",
  "headline": "Emergiendo de la Consciencia Colectiva",
  "narrative": "En este ciclo de introspección y revisión, las energías de Saturno te invitan...",
  "actions": [
    "Dedica tiempo a la meditación o reflexión personal...",
    "Crea un ritual de liberación...",
    "Establece metas claras y alcanzables...",
    "Busca un espacio creativo donde puedas expresar..."
  ],
  "astro_metadata": {
    "model": "gpt-4o-mini",
    "events_interpreted": 41,
    "language": "es",
    "source": "openai"
  }
}
```

---

## Arquitectura actual de Lilly (Cognitive Layers)

| Layer       | Función                                     | Estado      | Archivos clave                    |
|-------------|---------------------------------------------|-------------|-----------------------------------|
| Memory      | Context persistence (últimas 5 entradas)    | Activo      | `core/context_manager.py`          |
| Reasoning   | Axiomas lógicos inyectados al prompt        | ✅ Activo   | `data/axioms/*.md`, `core/llm.py` |
| Knowledge   | Búsqueda semántica en corpus clásico        | ✅ Preparado| `core/knowledge.py`, `scripts/`   |
| Expression  | Salida multilingüe (ES/EN/PT/FR)            | Activo      | `core/llm.py`                     |
| Integration | Abu ↔ Lilly ↔ Frontend                      | Estable     | `main.py`, `docker-compose.yml`   |

---

## Pendientes: Razonamiento del agente

### 1. Corpus clásico (Knowledge Layer)
**Estado:** Preparado pero vacío.

**Pendiente:**
- [ ] Agregar textos de William Lilly ("Christian Astrology") en `lilly_engine/data/lilly_corpus/`.
- [ ] Generar `embeddings.json` con el script:
  ```bash
  python lilly_engine/scripts/generate_embeddings.py --backend openai
  ```
- [ ] Validar que las referencias se inyectan correctamente en prompts.

**Impacto:** Las interpretaciones incluirán citas clásicas con fuente, aumentando trazabilidad y autoridad.

### 2. Validación de coherencia (Reasoning Quality)
**Estado:** Sin implementar.

**Pendiente:**
- [ ] Definir métricas de coherencia (¿el reasoning referencia axiomas activos correctamente?).
- [ ] Crear evals simples (A/B tests con/sin axiomas; verificar que no contradice axiomas).
- [ ] Script de validación automática: `scripts/validate_reasoning.py`.

**Impacto:** Detectar si el modelo inventa razones o aplica mal los axiomas.

### 3. Axiomas avanzados
**Estado:** 5 axiomas base; muchos conceptos clásicos faltan.

**Pendiente:**
- [ ] Dignidades/debilities (domicilio, exaltación, caída, exilio).
- [ ] Aplicación vs separación (aspectos aplicativos más fuertes).
- [ ] Sect (día/noche) y condiciones especiales.
- [ ] Velocidad planetaria (directo/retrógrado/estacionario).

**Impacto:** Razonamiento más refinado y alineado con doctrina tradicional.

### 4. Control dinámico de axiomas
**Estado:** Todos los axiomas se inyectan siempre (hasta 8).

**Pendiente:**
- [ ] Selector de axiomas por contexto (ej: solo aspectos si no hay eventos de casas).
- [ ] Pesos dinámicos (ajustar importancia según pregunta).
- [ ] API para activar/desactivar axiomas individualmente.

**Impacto:** Prompts más enfocados; menos ruido; mejor uso de contexto.

### 5. Feedback loop y mejora continua
**Estado:** Sin implementar.

**Pendiente:**
- [ ] Guardar pares (prompt + reasoning + calificación humana) para evals.
- [ ] Dashboard de calidad de reasoning (% con citas, % sin contradicciones).
- [ ] Fine-tuning opcional con ejemplos anotados.

**Impacto:** Mejora iterativa de la calidad del razonamiento.

### 6. UX: Visualización del reasoning
**Estado:** Campo presente en JSON pero no renderizado en frontend.

**Pendiente:**
- [ ] Diseñar cómo mostrar `reasoning` en la UI (collapsible, tooltip, pestaña aparte).
- [ ] Renderizar axiomas activos y referencias clásicas citadas.
- [ ] Indicador de "confianza" o score de coherencia.

**Impacto:** Transparencia total para el usuario; educación sobre razonamiento astrológico.

---

## Cómo probar (validación manual)

### 1. Verificar axiomas
```powershell
docker logs lilly_engine --tail 50
```
Buscar: `[INFO] Injected 8 axioms into prompt`.

### 2. Verificar reasoning
Hacer interpretación desde `/interpret` y revisar logs:
```
[INFO] Lilly produced reasoning: Los tránsitos de Saturno...
```

### 3. Inspeccionar JSON
En el navegador (Network tab), buscar respuesta de `POST /api/ai/interpret`:
```json
{
  "reasoning": "...",
  "headline": "...",
  ...
}
```

### 4. Desactivar reasoning (opcional)
Editar `.env`:
```
LILLY_INCLUDE_REASONING=false
```
Rebuild/restart Lilly; el campo `reasoning` será `"No explicit reasoning provided."`.

---

## Quality gates (sesión actual)

- ✅ Build: Lilly rebuildeada con axiomas, knowledge y reasoning.
- ✅ Runtime: Contenedores estables; logs confirmados.
- ✅ Endpoints: `/api/ai/interpret` responde 200 con reasoning.
- ⚠️ Tests: No ejecutados (pendiente).
- ⚠️ Corpus: Vacío (embeddings.json no generado).

---

## Notas técnicas

### Tokens y costos
- **Sin reasoning:** ~600-800 tokens/interpretación.
- **Con reasoning:** ~750-950 tokens/interpretación (+15-20%).
- Con `gpt-4o-mini`: impacto bajo en costo (~$0.0001/interpretación).

### Latencia
- Reasoning agrega ~1-2s de generación (depende de complejidad).

### Rutas absolutas en contenedor
- Axiomas: `/app/data/axioms/astrological_axioms.md`
- Embeddings: `/app/data/embeddings.json`
- Corpus: `/app/data/lilly_corpus/*.txt`

---

## Próximos pasos sugeridos

1. **UX consolidation (prioritario según usuario):**
   - Diseñar y renderizar `reasoning` en frontend.
   - Mostrar axiomas activos y referencias clásicas.
   - Mejorar layout de interpretaciones.

2. **Corpus clásico (opcional):**
   - Agregar textos de Lilly.
   - Generar embeddings.
   - Probar búsqueda semántica.

3. **Validación de coherencia:**
   - Script de evals simple.
   - Métricas básicas (citas presentes, contradicciones).

4. **Tests automatizados:**
   - Pytest para axiomas, knowledge, reasoning.
   - Smoke tests en CI.

---

Actualizado: 2025-11-03  
Versión: Lilly v2.1 (Reasoning Layer activa)
