# ABU_AGENT_MVP_IMPLEMENTATION_PLAN.md

## Introducción
Agente batch de investigación astrológica que ejecuta Abu (motor determinista) sobre una lista de sujetos, genera artefactos (ej. transits/timeline), los almacena en Storacha/IPFS y publica resultados estáticos en la web (Vercel). Enfoque API-first y reproducible.

### Objetivo del agente
- Automatizar cálculos astrológicos para múltiples sujetos en modo batch, sin interacción humana en runtime.
- Publicar artefactos resultantes en almacenamiento descentralizado y exponerlos vía web estática.

### Problema que resuelve
- Evita ejecuciones manuales ad-hoc y centraliza el pipeline de cálculo → almacenamiento → publicación.
- Proporciona trazabilidad (runs, artifacts) y separación de concerns (cálculo vs publicación).

### Alcance del MVP
**Hace:**
- Ejecuta Abu como servicio determinista (Cloud Run Job) para sujetos predefinidos.
- Calcula timeline biográfico y tránsitos según parámetros de entrada.
- Sube resultados a Storacha/IPFS y publica enlaces en Vercel.
- Opcional: invoca razonamiento LLM fuera de la ruta crítica.

**No hace:**
- Fine-tuning, RLHF o aprendizaje continuo.
- UI interactiva compleja; solo publicación estática/SSR ligera.
- Orquestación multi-agente avanzada; un pipeline secuencial basta.

## Arquitectura general

### Diagrama textual end-to-end
```
Usuario (UI Vercel) → Dispara Job (Scheduler) → Cloud Run Job (Pipeline)
  → Abu (Cloud Run service o contenedor batch) → Genera artifacts (JSON/CSV/HTML)
  → Sube a Storacha/IPFS → Guarda metadatos en DB (subjects, runs, artifacts)
  → Publica enlaces en Vercel (static/ISR) → Usuario consume resultados
```

### Separación de componentes
- **Motor determinista (Abu):** cálculo ephemeris/astrológico, contratos estables.
- **Pipeline batch:** orquesta fuentes, invoca Abu, persiste y publica.
- **Razonamiento (opcional):** llamada a LLM para enriquecer narrativa; no bloquea el pipeline.

### Actualización (2026-03-02)
- Endpoint de tránsitos fortalecido: cálculo de velocidad (directo/retro) y nuevo POST de conveniencia `/api/astro/transits/with-natal` que genera la carta natal y los tránsitos en un solo paso; opción `includeMinor` para aspectos menores.
- Casas robustas en latitudes altas: fallback automático a Whole Sign si Placidus falla o |lat|>66°, manteniendo 12 cúspides y trazabilidad en `house_system_used`.

## Recursos disponibles
- **GCP:** Cloud Run Jobs (pipeline), Cloud Run Services (Abu), Cloud Scheduler (disparos), Cloud Storage (opcional staging), Secret Manager (claves).
- **RunPod (opcional):** ejecución del job en pod dedicado si se requiere GPU/aislamiento.
- **Vercel:** hosting de la UI/SSR estática que consume artifacts publicados.
- **Storacha / IPFS:** almacenamiento descentralizado de artifacts finales.

## Modelo de datos (mínimo)
- **subjects**
  - `subject_id` (PK)
  - `name` (opcional/pseudónimo)
  - `birth_datetime_utc`
  - `lat`, `lon`
  - `metadata` (JSON: tags, notas)
- **runs**
  - `run_id` (PK)
  - `subject_id` (FK)
  - `started_at`, `ended_at`
  - `status` (queued/running/success/fail)
  - `params` (JSON: rango fechas, opciones)
  - `logs_uri` (Cloud Logging / file)
- **artifacts**
  - `artifact_id` (PK)
  - `run_id` (FK)
  - `type` (timeline, transits, report)
  - `uri` (Storacha/IPFS CID o gateway URL)
  - `checksum`
  - `created_at`

## Pipeline paso a paso
- **Paso 0: Setup y repositorios**
  - Repos: `ai-oracle` (Abu) + repo infra (IaC/CI) + repo UI (Vercel).
  - Variables en Secret Manager: keys de Storacha/IPFS, API Abu URL, etc.

- **Paso 1: DB y schema**
  - Provisionar DB ligera (Postgres/SQLite hosted) para `subjects`, `runs`, `artifacts`.
  - Migraciones iniciales.

- **Paso 2: Conector Abu**
  - Cliente HTTP hacia `Abu` (Cloud Run service) o contenedor local si el job incluye Abu.
  - Endpoints clave: `/api/astro/chart`, `/forecast`, `/life-cycles`, `/solar-return`, `/chart-detailed`.

- **Paso 3: Timeline biográfico**
  - Para cada `subject`, generar milestones (ej. ciclos, solar returns por año objetivo).
  - Guardar artifact (JSON/CSV) con metadata.

- **Paso 4: Cálculo de tránsitos**
  - Llamar endpoint de tránsitos (si disponible) o combinar chart natal + forecast/solar-return.
  - Generar artifact de tránsitos activos para el rango solicitado.

- **Paso 5: Subida a Storacha/IPFS**
  - Empaquetar artifacts (JSON/CSV/HTML). Subir y registrar CIDs.
  - Guardar en tabla `artifacts` con checksum y tipo.

- **Paso 6: (Opcional) Razonamiento con LLM**
  - Enriquecer con narrativa usando Lilly/LLM externo. Guardar como artifact separado (tipo `narrative`).

- **Paso 7: Publicación en web**
  - Vercel consume la tabla `artifacts` o un index JSON generado por el job.
  - ISR/SSG: páginas por `subject_id` con links a CIDs.

- **Paso 8: Automatización con Scheduler**
  - Cloud Scheduler → invoca Cloud Run Job (cron). Parametrizar rango de fechas/subjects.

## Proceso de ejecución (operativo)
- **Cloud Run Job:** imagen de pipeline (incluye cliente Abu y uploader Storacha). Se ejecuta con args/vars por run.
- **Disparo:** Cloud Scheduler (HTTP) o manual (gcloud). RunPod opcional para ejecutar la misma imagen.
- **Logging:** stdout/stderr a Cloud Logging; `run_id` en cada línea para correlación.
- **Errores y retries:** Cloud Run Job retries configurados (ej. 3). Subir estado `fail` en tabla `runs` y conservar logs URI.

## Memoria y aprendizaje
- Datos guardados: subjects, runs, artifacts, logs URI, CIDs.
- "Aprendizaje" en este MVP: cero fine-tuning. Solo persistencia de resultados y parámetros para reproducibilidad. No hay RL/ajuste de modelo.

## Seguridad
- Secrets en Secret Manager (keys Storacha/IPFS, Abu URLs si privadas).
- Claves de storage no se committean; inyección vía env en job.
- Separación de entornos: `dev/stage/prod` con proyectos GCP distintos o prefixes de recursos.

## Limitaciones actuales
- Sin UI interactiva completa; solo publicación estática.
- Sin fine-tuning ni memoria a largo plazo de LLM.
- Sistemas de casas experimentales no incluidos; se usa el core actual.

## Próximos hitos posibles
- Integrar LangGraph/agentes persistentes para orquestación condicional.
- Añadir endpoint de tránsitos dedicado si no existe en el core.
- Enriquecer publicación con visualizaciones (charts estáticos) renderizadas en el job.

## Checklist de despliegue (local → prod)
1) Build de imagen del pipeline (incluye cliente Abu + uploader Storacha). Montar `de440s.bsp` y tzdata.
2) Provisionar DB y correr migraciones (`subjects`, `runs`, `artifacts`).
3) Configurar Secret Manager: claves Storacha/IPFS, Abu URL, opcional API key.
4) Desplegar Abu (Cloud Run service) o usar instancia existente.
5) Desplegar Cloud Run Job del pipeline con vars: DB URL, Storacha keys, Abu URL.
6) Configurar Cloud Scheduler (cron) apuntando al Job con payload de subjects/rango.
7) Desplegar UI en Vercel apuntando al index de artifacts/CIDs.
8) Probar un run manual; verificar artifacts en Storacha/IPFS y página en Vercel.
9) Activar retries y alertas básicas (Cloud Monitoring) para fallos de Job.
