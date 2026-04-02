# Abu Oracle Orchestrator – Diseño y Operación

## 1. Propósito
Extender el sistema AI Oracle con un orquestador externo (Abu Oracle) que coordina llamadas a los microservicios Abu (cálculo astrológico) y Lilly (interpretación semántica) usando la API de OpenAI (Assistant con function tools). Mantiene los servicios desacoplados y permite evolución independiente sin alterar contratos REST.

## 2. Rol de cada componente
| Componente | Rol | LLM Directo | Notas |
|------------|-----|-------------|-------|
| Abu Engine | Cálculo astronómico determinista (cartas, forecast, solar return, optimización) | NO | Ephemeris local, CPU-bound |
| Lilly Engine | Construcción de prompt semántico + llamada al LLM + fallback | SÍ | Devuelve JSON: headline, narrative, actions, astro_metadata |
| Orquestador (Assistant + runner) | Decide qué datos pedir y en qué orden, no interpreta profundo | Parcial (usa modelo para razonar sobre qué función llamar) | Funciones mapean a endpoints externos |
| OpenAI LLM | Modelo hospedado en OpenAI | N/A | No vive en nuestros contenedores |

## 3. Flujo de alto nivel
1. Usuario envía pregunta → runner crea Thread & Run en Assistant.
2. Assistant analiza instrucciones y produce `tool_calls` (function calls).
3. Runner recibe `requires_action` → ejecuta cada tool_call invocando Abu/Lilly (HTTP Cloud Run) y envía las respuestas como `tool_outputs`.
4. Assistant recibe outputs, decide si necesita más funciones o responde.
5. Respuesta final: JSON con `{ headline, narrative, actions[], astro_metadata{ source } }`.

## 4. Motivación arquitectónica
- Mantener a Lilly como único lugar de semántica y control de estilo narrativo.
- Evitar duplicar prompts en múltiples sitios.
- Orquestación flexible: el Assistant puede decidir subconjuntos (solo chart + interpretación) o flujos completos (forecast + life-cycles + interpretación) según la pregunta.
- Baja latencia adicional: el orquestador agrega sólo razonamiento y secuenciación (< ~400–800 ms típico) frente al cálculo astro + LLM.

## 5. Endpoints orquestados (funciones)
```
get_chart -> GET /api/astro/chart
get_forecast -> GET /api/astro/forecast
get_life_cycles -> GET /api/astro/life-cycles
get_solar_return -> GET /api/astro/solar-return
optimize_sr_locations -> POST /api/rs/optimize
interpret_astrological_data -> POST /api/ai/interpret (Lilly)
```
Cada función devuelve JSON. La última (interpret) genera la narrativa final.

## 6. Scripts añadidos
- `scripts/create_orchestrator_assistant.py`: Crea/actualiza Assistant con tools función. Carga `.env` internamente (sin dependencias extra) y usa `gpt-4o-mini` para bajo costo.
- `scripts/run_orchestrated_query.py`: Ejecuta un ciclo completo, maneja `requires_action` y hace HTTP a Cloud Run.

## 7. Archivos de especificación
- `docs/openai_actions/abu_openapi_actions.yaml`
- `docs/openai_actions/lilly_openapi_actions.yaml`
Preparados para futura carga en UI si aparece la sección Actions. Actualmente la UI de tu cuenta no la expone.

## 8. Variables de entorno relevantes
```
OPENAI_API_KEY=...        # Acceso al LLM y Assistant
OPENAI_ASSISTANT_ID=...   # ID del orquestador creado por script
ABU_URL=...               # Base URL (Cloud Run) Abu
LILLY_URL=...             # Base URL (Cloud Run) Lilly
LILLY_MODEL=gpt-4o-mini   # Modelo usado por Lilly internamente
USE_ASSISTANTS=true       # Bandera futura para modo Assistants
```
Si `ABU_URL`/`LILLY_URL` no se definen, se usan defaults hardcodeados en el runner (las URLs actuales de Cloud Run).

## 9. Estrategia de llamadas
- Heurística inicial: la pregunta se envía y el Assistant decide. Si no llama a ninguna función y responde vacía, endurecer instrucciones.
- Política recomendada: Siempre llamar primero `get_chart` antes de `interpret_astrological_data` para garantizar contexto mínimo.
- `optimize_sr_locations` encapsula un batch interno de evaluaciones; no se fragmenta en múltiples tool calls.

## 10. Prompt del Assistant (actual)
```
Eres Abu Oracle, un orquestador astrológico. Obtén datos (chart, forecast, life-cycles, solar-return, optimize) y luego solicita interpretación a Lilly. Devuelve SIEMPRE JSON final válido con las claves: headline, narrative, actions, astro_metadata. Si falta información llama a las funciones necesarias. No inventes datos planetarios; siempre recupéralos por funciones. Idioma por defecto: español.
```
### Próximo endurecimiento (plan)
Agregar: “Nunca generes interpretación final sin haber llamado al menos a get_chart. Si la pregunta menciona año futuro, considera solar-return u optimize_sr_locations. Para dudas sobre evolución anual usa forecast.”

## 11. Consideraciones de calidad
- Tests del repo: todos PASS (15). Ajuste menor en test de contexto para limpiar estado previo.
- No se tocaron contratos de endpoints.
- Riesgo operativo: mínimos cambios confinados a carpeta `scripts/` y `docs/`.
- Deprecation warnings: El SDK indica migrar a Responses API. Plan: crear versión runner `run_orchestrated_query_responses.py` a futuro.

## 12. Troubleshooting rápido
| Síntoma | Causa probable | Acción |
|---------|----------------|--------|
| Assistant no llama funciones | Instrucciones suaves | Endurecer prompt, regenerar Assistant |
| 404 en endpoint | URL Cloud Run cambiada | Actualizar ABU_URL / LILLY_URL en .env |
| Interpretación fallback | Falta OPENAI_API_KEY o error de modelo | Verificar variable y modelo disponible |
| Demora excesiva | Forecast/optimize con rangos grandes | Ajustar parámetros (step/horizon o target_year) |

## 13. Evolución futura
- Migrar a Responses API (unifica tool calls y reduce warnings).
- Añadir trazas estructuradas (logging JSON en runner) para telemetría.
- Cache de respuestas de observación (chart/forecast) en el runner para evitar recalcular dentro de una misma sesión.
- Integración frontend: panel que muestre secuencia de tool calls realizada.

## 14. Seguridad
- Secrets sólo en `.env` local y Secret Manager en Cloud Run.
- Ningún script imprime la API key.
- Fallback narrativo evita exponer estructura interna del prompt.

## 15. Uso rápido (PowerShell)
```powershell
# Crear / actualizar Assistant
D:/projects/AI_Oracle/venv/Scripts/python.exe scripts/create_orchestrator_assistant.py
# Ejecutar pregunta
$env:USER_QUESTION = "¿Qué oportunidades clave tengo en 2026?"
D:/projects/AI_Oracle/venv/Scripts/python.exe scripts/run_orchestrated_query.py
```

## 16. Resumen ejecutivo
El orquestador externo agrega una capa ligera de decisión sin modificar servicios actuales. Lilly sigue siendo la fuente semántica. Abu provee cálculos deterministas. El Assistant como orquestador reduce acoplamiento, facilita ampliación funcional y prepara el terreno para instrumentación avanzada y multi-modalidad futura.

---
Última actualización: 2025-11-10
