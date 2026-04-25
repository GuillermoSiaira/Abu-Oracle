---
name: MUNDANA_H_A_RESULTADOS
description: Resultados hipótesis H_mundana_A + estado completo Fase 12 — módulo mundana + publisher autónomo
tipo: resultado
version: 2026-04-17
estado: ✅ confirmada + en producción
tags: [mundana, H_mundana_A, publisher, cloud-run, bluesky, lilly]
---

# H_mundana_A — Resultados + Fase 12

**Fecha confirmación hipótesis:** 2026-04-05  
**Estado Fase 12:** ✅ En producción (Cloud Run Job desde 2026-04-17)  
**Commit principal:** ff295f5, 3570f9d, 98b65f4 · deploy commit: producción 2026-04-17

**Anclaje axiomático**: [[AXIOMATICS_v0_4#11. Principio de Estratificación de Niveles Operativos]] — la mundana es el **nivel colectivo** del campo, distinto del nivel individual del nativo.

**Hipótesis formal**: [[HIPOTESIS_REGISTRO#H_mundana_A — Conjunciones de ciclo largo como marcadores epocales|H_mundana_A]]

**Doctrina fuente**: Abu Mashar al-Balkhi (787–886), *De Magnis Coniunctionibus*. Tradición persa medieval — ciclos largos como historiografía celeste (ver [[AXIOMATICS_v0_4#Axioma 4.3]] y [[AXIOMATICS_v0_3]]).

---

## Hipótesis H_mundana_A — Confirmada

> Existen configuraciones planetarias de ciclo largo (conjunciones J-S, oposiciones
> M-S) cuya densidad de eventos históricos en torno a su fecha exacta es
> estadísticamente distinguible del ruido de fondo.

### Resultados estadísticos (corpus: 23.636 eventos, año 8–2069)

| Configuración | p-value | r (rank-biserial) | Densidad | Veredicto |
|---|---|---|---|---|
| Conjunción Júpiter-Saturno | 5×10⁻⁶ | +0.204 | 4.3× baseline | ✅ Robusta |
| Oposición Marte-Saturno | 0.016 | +0.056 | 1.6× baseline | ✅ Señal real |

**Hallazgo clave J-S:** 8.67 eventos/ventana vs 2.02 baseline.
Confirma doctrina Abu Mashar — conjunciones J-S como eje predictivo mundano.

**Limitación:** corpus sesgado siglo XIX-XX (68% eventos).
Réplica estratificada por siglo es el siguiente paso para fortalecer el claim.

### Implicación de producto
La señal justificó implementar el módulo mundana completo en Abu Oracle
(Fase 12). Feature live en producción desde 2026-04-15 (app) / 2026-04-17 (publisher).

---

## Fase 12 — Módulo Mundana + Publisher Autónomo

**3 archivos nuevos (backend) · 2 archivos nuevos (frontend) · Pipeline Cloud Run**

### Backend — Abu Engine

**`abu_engine/core/mundana.py`** — módulo cálculo mundano:
- `get_current_sky()` → posiciones + configuraciones activas ahora
- `get_upcoming_configurations(days_ahead)` → bisección para fecha exacta
- `get_historical_context(config_type)` → corpus en ventanas similares
- Detección stellium: ≥4 planetas en 30°, incluye Neptuno
- Tipos: `conjunction_JS`, `conjunction_MS`, `opposition_MS`, `conjunction_MJ`, `opposition_MJ`

**`abu_engine/routers/mundana.py`** — 3 endpoints:
```
GET /api/mundana/sky       → configuraciones activas
GET /api/mundana/forecast  → próximas (days=90)
GET /api/mundana/history   → contexto histórico por tipo
```

### Frontend — Next.js

**`next_app/components/mundana-tab.tsx`** — pestaña "Mundana":
- Fetch sky + forecast automáticos
- Tarjetas activas clickeables (esmeralda=alta, ámbar=media)
- p_value + density_ratio por configuración
- Botón "Lilly interpreta" → evento `mundana_config`
- Timeline de próximas configuraciones

**Integración:** `MundanaTab` en `chart-tabs.tsx` (grid-cols-6 con tab "Mundana"),
routing `mundana_config` en `OracleChat.tsx`, route `next_app/app/api/lilly/mundana/route.ts`
(max_tokens 2048, funciona con o sin carta natal).

**`next_app/components/transits-tab.tsx`** — sección "Contexto Mundano":
- Fetch lazy sky al montar
- Tarjetas compactas antes del Gantt de tránsitos

### Publisher Pipeline Autónomo

**Ubicación:** `scripts/mundana/`

| Módulo | Función |
|---|---|
| `publication_filter.py` | Cooldown 3d + umbrales (p≤0.05, density≥2.0, days_to_exact≤7) |
| `content_generator.py` | `generate_post(config, platform, history)` → Claude Sonnet 4.6 |
| `main_publisher.py` | Entry point: filter → generate → publish → registry |
| `onchain_registry.py` | SHA-256 + backup local + GCS upload |
| `publishers/bluesky_publisher.py` | AT Protocol createRecord (auto) |
| `publishers/twitter_publisher.py` | Borrador + email Resend |
| `publishers/farcaster_publisher.py` | Neynar API (pendiente activación FID) |

**Plataformas:**
- Bluesky: automático ✅
- Twitter: borrador + email Resend 🟡
- Farcaster: pendiente pago FID ⏳

### Producción (Cloud Run)

```
Cloud Run Job: mundana-publisher (us-central1)
Cloud Scheduler: mundana-publisher-daily — 08:00 UTC
Imagen: gcr.io/abu-oracle/mundana-publisher:latest
GCS cooldown: gs://abu-oracle-predictions/state/last_published.json
GCS registry: gs://abu-oracle-predictions/predictions/
```

**Secrets en GCP Secret Manager:**
`anthropic-api-key`, `bluesky-handle`, `bluesky-password`, `resend-api-key`

**Para actualizar imagen:**
```bash
gcloud builds submit --config=cloudbuild-mundana-job.yaml --project=abu-oracle .
```

### Validación end-to-end (local, 2026-04-15)

```
filter → stellium Aries 5 planetas (sig=high)
       → farcaster 317 chars ✓
       → twitter borrador en data/mundana/drafts/ ✓
       → SHA-256 registry ✓
```

---

## Referencias cruzadas

### Doctrina y axiomática
- [[AXIOMATICS_v0_4]] — Axioma 11: estratificación niveles individual/colectivo
- [[AXIOMATICS_OF_HEAVENS_v0_4]] — redirect raíz con tabla de axiomas
- [[AXIOMATICS_v0_3]] — versión previa: Abu Mashar y campo de relocalización (referencia histórica)
- [[AXIOM_0_MECANISMO]] — ontología del campo continuo: mundana opera sobre $\phi(t)$ sin requerir $\pi_{natal}$

### Hipótesis
- [[HIPOTESIS_REGISTRO]] — H_mundana_A como hipótesis formal del registro

### Engineering
- [[MUNDANA_PHASE12]] — arquitectura completa: backend, frontend, publisher, Cloud Run
- [[ARCHITECTURE]] — cómo mundana encaja en el sistema Abu↔Lilly

### Validación y publicación
- [[HF_EXPERIMENT_LOG]] — metodología de correlación con corpus histórico
- [[ANTHROPIC_STRATEGY]] — publisher autónomo + corpus mundano como caso publicable
- [[grant_proposal_ResearchHub]] — paper FinOps incluye costos publisher mundana

### Costos y ops
- [[finops_milp]] — costos del publisher (1 llamada Sonnet 4.6/día)
- [[COST_OPTIMIZATION]] — modelo de costos publisher dentro del presupuesto API

### Código fuente
- `abu_engine/core/mundana.py` — detección configuraciones J-S, M-S, M-J + stellium
- `abu_engine/routers/mundana.py` — endpoints `/api/mundana/{sky,forecast,history}`
- `scripts/mundana/` — pipeline publisher completo
- `cloudbuild-mundana-job.yaml` — configuración Cloud Build
