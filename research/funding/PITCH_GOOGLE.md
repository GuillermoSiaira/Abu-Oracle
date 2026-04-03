# Pitch — Google Research Credits

> Programa: Google Research Credits (cloud.google.com/edu/researchers)
> Sin afiliación académica requerida. Formulario directo.
> Ángulo: GCP user activo + investigación de optimización de LLM.

---

## Contexto del programa

Google Research Credits ofrece hasta $5,000-10,000 USD en créditos de GCP para
investigadores que usen Google Cloud en proyectos de investigación. No requiere
afiliación académica. El sistema ya corre en Cloud Run — el caso es directo.

---

## Descripción del proyecto (para el formulario)

**Título:** Optimal LLM Model Selection in Multi-Plan SaaS: A Mixed Integer
Linear Programming Approach with Empirical Calibration

**Una línea:** Formulamos y resolvemos el problema de selección óptima de modelo
LLM en un SaaS con múltiples planes de suscripción, usando datos empíricos de
un sistema en producción desplegado en Google Cloud Run.

**Descripción técnica:**

Abu Oracle es un sistema de interpretación astrológica basado en agentes LLM
(Claude Sonnet 4.6 / Haiku 4.5) desplegado en Google Cloud Run. El sistema opera
11 rutas LLM distintas, cada una con diferentes requisitos de calidad y costo.

El problema central: dado un mix de usuarios con planes de suscripción distintos
(Genesis/Annual/Monthly), un conjunto de rutas LLM con costos variables, y un
rate limit compartido de Anthropic (Tier 2: 1,000 RPM / 450,000 TPM), ¿qué
modelo y max_tokens asignar a cada ruta × plan para maximizar el margen total
sujeto a restricciones de calidad mínima?

Formulamos esto como un MILP con variables discretas (elección de modelo) y
continuas (max_tokens por ruta). El simulador de carga muestra que una política
greedy derivada del MILP convierte un margen negativo de −$6.76/hora en
+$11.24/hora bajo carga de 500 usuarios simultáneos.

**Infraestructura GCP usada:**
- Cloud Run: abu-oracle-app (Next.js) + abu-engine (Python/FastAPI)
- Cloud Build: CI/CD pipeline (cloudbuild-app.yaml + cloudbuild-engine.yaml)
- Firestore: memoria longitudinal por usuario
- Artifact Registry: imágenes Docker

---

## Uso de los créditos

| Componente | Uso actual/mes | Con créditos |
|-----------|----------------|-------------|
| Cloud Run (app + engine) | ~$50-80 | Sin cambio — estabilidad operativa |
| Cloud Build (deploys) | ~$5-10 | Sin cambio |
| Firestore | ~$5-10 | Sin cambio |
| **Nuevo con créditos** | — | Vertex AI para calibración del MILP |
| **Nuevo con créditos** | — | BigQuery para análisis de logs de producción |
| **Nuevo con créditos** | — | Cloud Run jobs para Fase A-2 y re-runs del simulador |

**Total solicitado:** $5,000 USD en créditos GCP (12 meses)

---

## Resultados esperados

1. Dataset público de distribución de tokens por tipo de request LLM en producción
2. Paper enviado a MLSys o SIGMOD sobre optimización de costos multi-plan
3. Código del simulador y MILP publicado como open source en GitHub
4. Benchmark de políticas de selección de modelo (static vs greedy vs MILP exacto)

---

## Por qué Google

El sistema ya está en Google Cloud. Los datos de producción (Cloud Run logs,
Firestore) son la fuente primaria de calibración del MILP. Ampliar la capacidad
de Cloud Run y agregar BigQuery para análisis de logs es la extensión natural
del trabajo existente.

Además, los resultados tienen valor directo para el ecosistema de Google:
Gemini tiene la misma estructura de pricing (input/output/cache) y los mismos
problemas de rate limit. El MILP es agnóstico al proveedor de LLM.

---

## Equipo

Guillermo Siaira — desarrollador independiente
- Sistema completo (backend Python, frontend Next.js, infraestructura GCP)
- Investigación estadística (HF field, correlación con eventos biográficos)
- Modelado matemático (MILP, simulación de carga)

guillermosiaira@gmail.com · app.abu-oracle.com
