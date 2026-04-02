# AI Oracle – Progreso Sesión 10 Nov 2025

## Resumen ejecutivo

**Logros principales**:
1. ✅ Orquestador "Abu Oracle" implementado y funcionando vía OpenAI Assistant API
2. ✅ Arquitectura modular validada (Abu cálculo + Lilly interpretación + Orchestrator coordinación)
3. ✅ Tests end-to-end exitosos con datos reales de usuario
4. ✅ Documentación completa de diseño y operación
5. ✅ UI `/chart` con chat integrado (Compose) enviando contexto de Abu al backend `/api/chat` → `lilly_swarm`
6. ⚠️ Lilly en Cloud Run sigue en fallback por conectividad saliente a `api.openai.com`

## Arquitectura implementada

### Componentes
```
Usuario
  ↓
Assistant "Abu Oracle" (OpenAI, externo)
  ↓ (tool calls via runner script)
  ├─→ Abu Engine (Cloud Run) → cálculos astronómicos
  ├─→ Lilly Engine (Cloud Run) → interpretación LLM
  └─→ Respuesta JSON final
```

### Separación de responsabilidades
| Componente | Función | LLM |
|------------|---------|-----|
| Abu Engine | Ephemeris, aspectos, forecast, solar return, optimización | No |
| Lilly Engine | Construcción de prompt + llamada OpenAI + fallback | Sí (cuando conecta) |
| Orchestrator | Decide qué endpoints llamar y en qué orden | Parcial (razonamiento Assistant) |

## Scripts creados

### `scripts/create_orchestrator_assistant.py`
- Crea/actualiza Assistant con 6 function tools
- Carga `.env` automáticamente
- Instrucciones endurecidas: siempre llama `get_chart` antes de interpretar
- Modelo: `gpt-4o-mini` (bajo costo)

### `scripts/run_orchestrated_query.py`
- Ejecuta ciclo completo: thread → run → tool_calls → submit_outputs → resultado
- Maneja `requires_action` con polling
- Llama endpoints reales en Cloud Run
- Variable `USER_QUESTION` para query del usuario

## Validación con datos reales

**Usuario**: Guillermo Siaira, 5 julio 1978 21:15, Balcarce (-37.8467, -58.2553)  
**Pregunta**: "¿Cuál es mi enfoque evolutivo para 2026?"

**Tool calls ejecutados** (secuencia completa):
1. `get_forecast` (birthDate, lat, lon, start 2026-01-01, end 2026-12-31)
2. `get_solar_return` (birthDate, lat, lon, year 2026)
3. `optimize_sr_locations` (birthDate, lat, lon, target_year 2026)
4. `get_life_cycles` (birthDate, lat, lon)
5. `get_chart` (date 2026-01-01, lat, lon)
6. `interpret_astrological_data` (language es, question, datos recopilados)

**Resultado**: JSON válido con headline, narrative, actions, astro_metadata.

**Estado**: ✅ Orquestador funciona perfectamente. ⚠️ Lilly en fallback mode (ver problema).

## Problema identificado: Lilly → OpenAI

### Síntoma
```json
{
  "astro_metadata": {
    "source": "fallback"
  }
}
```

### Causa raíz
**Connection error**: Cloud Run no puede conectar a `api.openai.com`.

### Diagnóstico realizado
- ✅ API key válida (164 chars)
- ✅ Secret accessible (permisos OK)
- ✅ Variable directa probada (elimina problema de secret mounting)
- ✅ Timeout aumentado a 60s + 2 retries
- ❌ Error persiste: fallo al conectar socket TCP/TLS

### Hipótesis
1. VPC connector sin egress configurado
2. Organization policy bloqueando salida
3. Firewall VPC bloqueando puerto 443
4. Problema temporal regional GCP

### Próximos pasos
Ver `docs/Lilly_OpenAI_Connection_Troubleshooting.md` para checklist completo.

## Documentación generada

### `docs/Orchestrator_Design_and_Operations.md`
- Arquitectura completa
- Flujo de datos
- Variables de entorno
- Instrucciones del Assistant
- Troubleshooting
- Uso rápido

### `docs/Lilly_OpenAI_Connection_Troubleshooting.md`
- Diagnóstico detallado del problema de conectividad
- Checklist de verificación de red
- Comandos para debugging
- Soluciones por tipo de causa
- Workarounds temporales

## Código modificado

### `lilly_engine/core/llm.py`
```python
# Antes
_client = OpenAI(api_key=_OPENAI_API_KEY) if _OPENAI_API_KEY else None

# Después
_client = OpenAI(
    api_key=_OPENAI_API_KEY,
    timeout=httpx.Timeout(60.0, connect=10.0),
    max_retries=2
) if _OPENAI_API_KEY else None
```

### `scripts/create_orchestrator_assistant.py`
- Instrucciones endurecidas con reglas estrictas
- Auto-carga de `.env`
- 6 funciones definidas con schemas mínimos

### `scripts/run_orchestrated_query.py`
- Auto-carga de `.env`
- Manejo robusto de content types (text/output_text)
- Logging de tool calls con `[tool]` prefix
- Fallback a JSON dump si no hay texto

### `lilly_engine/test_context_manager.py`
- Limpieza de estado al inicio de `test_save_and_load`
- Importación de `load_memory` y `save_memory`
- Tests ahora deterministas (15/15 passing)

## Variables de entorno clave

```bash
# En .env local
OPENAI_API_KEY=sk-proj-...
OPENAI_ASSISTANT_ID=asst_ZKrYPJzbMNo5SG2Tv3evBab4
LILLY_MODEL=gpt-4o-mini
USE_ASSISTANTS=true  # Para runner local (no afecta Lilly Cloud Run)
ABU_URL=https://abu-engine-bbrsyawaca-uc.a.run.app
LILLY_URL=https://lilly-engine-503488473965.us-central1.run.app

# En Cloud Run Lilly
DEFAULT_LANGUAGE=es
USE_ASSISTANTS=false  # Modo Chat Completions (no Assistant interno)
ABU_URL=https://abu-engine-bbrsyawaca-uc.a.run.app
OPENAI_API_KEY=<secret o directo>  # Actualmente directo para debug
```

## Tests ejecutados

### Repositorio
```powershell
pytest -q lilly_engine/test_*.py abu_engine/test_openapi_schema.py
# Resultado: 15 passed, 7 warnings
```

### Endpoints Cloud Run
```powershell
# Abu chart
curl "https://abu-engine-bbrsyawaca-uc.a.run.app/api/astro/chart?date=2026-01-01T00:00:00Z&lat=40.7128&lon=-74.0060"
# ✅ Devuelve planets, aspects, houses

# Lilly interpret
curl -X POST "https://lilly-engine-503488473965.us-central1.run.app/api/ai/interpret" \
  -H "Content-Type: application/json" \
  -d '{"events":[{"cycle":"Saturn Return","planet":"Saturn"}],"language":"es"}'
# ✅ Devuelve JSON (fallback mode)
```

### Orquestador
```powershell
$env:USER_QUESTION = "Soy Guillermo... ¿Cuál es mi enfoque evolutivo para 2026?"
python scripts/run_orchestrated_query.py
# ✅ 6 tool calls ejecutados correctamente
# ✅ JSON final devuelto
# ⚠️ Interpretación en fallback
```

## Deployment actual

### Abu Engine
- **URL**: https://abu-engine-bbrsyawaca-uc.a.run.app
- **Revisión**: abu-engine-00001-xxx
- **Estado**: ✅ Funcionando correctamente
- **Env vars**: Ninguna requerida

### Lilly Engine
- **URL**: https://lilly-engine-503488473965.us-central1.run.app
- **Revisión**: lilly-engine-00001-4bp
- **Estado**: ✅ Responde, ⚠️ fallback mode
- **Env vars**:
  - `DEFAULT_LANGUAGE=es`
  - `USE_ASSISTANTS=false`
  - `ABU_URL=https://abu-engine-bbrsyawaca-uc.a.run.app`
  - `OPENAI_API_KEY=<directo>` ⚠️ temporal para debug

### Assistant
- **ID**: `asst_ZKrYPJzbMNo5SG2Tv3evBab4`
- **Modelo**: `gpt-4o-mini`
- **Estado**: ✅ Configurado y operativo

## Impacto en experiencia de usuario

### ✅ Funcional
- Sistema responde a preguntas
- Datos astrológicos precisos
- Secuencias de llamadas optimizadas
- JSON bien formado

### ⚠️ Limitado por fallback
- Narrativa genérica (basada en arquetipos simples)
- No personalización profunda
- Acciones sugeridas básicas
- Metadata indica `"source": "fallback"`

## Siguiente sesión (mañana o próxima)

### Prioridad 1: Resolver conectividad
1. Verificar VPC connector en Cloud Run
2. Revisar organization policies
3. Probar region alternativa (us-east1)
4. Agregar endpoint `/debug/connectivity` para validación
5. Una vez resuelto: volver a usar secret en lugar de variable directa

### Prioridad 2: Optimizaciones (post-conectividad)
1. Migrar runner a Responses API (eliminar warnings deprecation)
2. Agregar logging estructurado (JSON) en runner
3. Cache de respuestas Abu en runner para sesión
4. Panel de trazas en frontend mostrando tool calls

### Prioridad 3: Producción
1. Actualizar `cloud-run-urls.txt` con URLs finales
2. Actualizar frontend Next.js con URLs correctas
3. Tests de integración completos (con LLM real)
4. Monitoring y alertas

## Archivos clave modificados/creados

```
docs/
  Orchestrator_Design_and_Operations.md          [NUEVO]
  Lilly_OpenAI_Connection_Troubleshooting.md     [NUEVO]
  AI_Oracle_Progress_Report_7.md                 [NUEVO - este archivo]

scripts/
  create_orchestrator_assistant.py               [NUEVO]
  run_orchestrated_query.py                      [NUEVO]

lilly_engine/
  core/llm.py                                    [MODIFICADO - timeout]
  test_context_manager.py                        [MODIFICADO - cleanup]
  data/memory.json                               [RESETEADO]

.env                                             [USADO - no commitear]
```

## Comandos útiles para continuidad

```powershell
# Crear/actualizar Assistant
python scripts/create_orchestrator_assistant.py

# Ejecutar query orquestada
$env:USER_QUESTION = "Tu pregunta aquí"
python scripts/run_orchestrated_query.py

# Verificar logs Lilly
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=lilly-engine" --limit=20

# Verificar configuración de red
gcloud run services describe lilly-engine --region=us-central1 --format="value(spec.template.metadata.annotations)"

# Probar endpoint debug (después de agregarlo)
curl https://lilly-engine-503488473965.us-central1.run.app/debug/connectivity

# Tests
pytest -q lilly_engine/test_*.py abu_engine/test_openapi_schema.py
```

## Conclusión

El sistema orquestador está **completo y operativo**. La arquitectura modular funciona correctamente: Abu provee cálculos deterministas, el Assistant coordina las llamadas inteligentemente, y Lilly está lista para generar interpretaciones semánticas ricas.

El único bloqueante es **conectividad de red Cloud Run → OpenAI**, que es un problema de infraestructura GCP, no de código. Una vez resuelto (mañana), el sistema estará listo para producción con interpretaciones LLM completas.

Todo el código, tests y documentación están en orden. El proyecto avanzó significativamente hacia la arquitectura final escalable y mantenible.

---
**Fecha**: 2025-11-10  
**Autor**: Copilot Agent  
**Próximo paso**: Resolver conectividad Cloud Run (ver troubleshooting doc)
