---
name: MUNDANA_PHASE12
description: Arquitectura completa Fase 12 — módulo mundana Abu Engine + publisher RRSS autónomo
tipo: engineering
version: 2026-04-17
estado: ✅ en producción — Cloud Run Job activo
tags: [mundana, publisher, cloud-run, bluesky, lilly, fase12, anthropic-vertex]
---

# Fase 12 — Módulo Mundana + Publisher Autónomo

> Completado: sesión 2026-04-15 (Day 1-2 código) + 2026-04-17 (deploy producción).
> Commits principales: `eb74e02`, `1996290`, `26a6c6b`, `3e770b2`, `98b65f4`, `ff295f5`, `3570f9d`.

**Anclaje doctrinal**: implementación del **nivel colectivo** del campo según [[AXIOMATICS_v0_4#11. Principio de Estratificación de Niveles Operativos]] (Axioma 11.5). Justificada empíricamente por [[HIPOTESIS_REGISTRO#H_mundana_A — Conjunciones de ciclo largo como marcadores epocales|H_mundana_A]] confirmada en [[MUNDANA_H_A_RESULTADOS]].

**Fundamento histórico**: Abu Mashar al-Balkhi, *De Magnis Coniunctionibus* (siglo IX) — la doctrina persa de las grandes conjunciones como marcadores de épocas históricas.

---

## Day 1 — Backend + Lilly mundana

### Migración AnthropicVertex

**`next_app/lib/anthropic-client.ts`** — factory AnthropicVertex:
```ts
import { AnthropicVertex } from '@anthropic-ai/vertex-sdk';
export function getAnthropicClient() {
  return new AnthropicVertex({ projectId: 'abu-oracle', region: 'us-east5' });
}
```
Cloud Run usa ADC — sin `ANTHROPIC_API_KEY`. **10 routes Lilly migradas** de `new Anthropic({ apiKey })` a `getAnthropicClient()`.

**`next_app/lib/selectModel.ts`** — routing revisado: todas las routes → `claude-sonnet-4-6`.
Haiku reservado para MILP optimizer (Fase E). Ramas Haiku eliminadas de `technique` y `city`.

### Abu Engine — módulo mundana

**`abu_engine/core/mundana.py`:**
- `get_current_sky()` → posiciones + configuraciones activas
- `get_upcoming_configurations(days_ahead)` → bisección para fecha exacta
- `get_historical_context(config_type)` → corpus en ventanas similares
- Detección stellium: ≥4 planetas en 30°, incluye Neptuno
- Tipos configuración: `conjunction_JS`, `conjunction_MS`, `opposition_MS`, `conjunction_MJ`, `opposition_MJ`

**`abu_engine/routers/mundana.py`** — router FastAPI:
```
GET /api/mundana/sky       → configuraciones activas
GET /api/mundana/forecast  → próximas (days=90)
GET /api/mundana/history   → contexto histórico por tipo
```
Registrado en `abu_engine/main.py` via `include_router(mundana_router)`.

### Lilly mundana

**`next_app/app/api/lilly/mundana/route.ts`:**
- Evento `mundana_config` → interpreta cielo colectivo
- Funciona con o sin carta natal del usuario
- `max_tokens: 2048`
- Migrado a AnthropicVertex

---

## Day 2 — Frontend MundanaTab

### `next_app/components/mundana-tab.tsx`

- Fetch `/api/mundana/sky` + `/api/mundana/forecast?days=90` al montar
- Tarjetas activas clickeables: badges (esmeralda=alta, ámbar=media)
- p_value + density_ratio por configuración
- Botón "Lilly interpreta" → `setPendingLillyEvent({ type: 'mundana_config', payload: config })`
- Timeline de próximas configuraciones

**Integración en el sistema:**
- `ChartTabKey` incluye `'mundana'`
- `chart-tabs.tsx` → grid-cols-6, tab con ícono `Orbit`
- `OracleChat.tsx` → routing `mundana_config` → `/api/lilly/mundana`
- `TechnicalPanel.tsx` → label en `deriveLabel`
- 15 keys i18n nuevas en `lib/i18n.ts`

### `next_app/components/transits-tab.tsx` — Contexto Mundano

Sección compacta insertada antes del Gantt de tránsitos:
- Fetch lazy `/api/mundana/sky` al montar el tab
- Tarjetas compactas de configuraciones activas

---

## Day 3 — Publisher Pipeline Autónomo

### Estructura `scripts/mundana/`

```
scripts/mundana/
├── main_publisher.py          # Entry point Cloud Run Job
├── publication_filter.py      # Cooldown + umbrales
├── content_generator.py       # Claude Sonnet 4.6
├── onchain_registry.py        # SHA-256 + GCS
├── sky_calculator.py          # Módulo mundana local
├── Dockerfile
├── requirements-mundana.txt
├── cloudbuild-mundana-job.yaml
└── publishers/
    ├── __init__.py            # dispatch publish_all()
    ├── bluesky_publisher.py   # AT Protocol ✅ auto
    ├── twitter_publisher.py   # borrador + Resend 🟡
    ├── farcaster_publisher.py # Neynar API ⏳ pendiente
    └── reddit_publisher.py    # ❌ pendiente
```

### `publication_filter.py`

- `should_publish()`: cooldown 3d + umbrales (p≤0.05, density≥2.0, days_to_exact≤7)
- Excepción stellium: pasa sin p_value si `significance='high'`
- `get_best_configuration()`: prioridad activa+alta > próxima+alta > activa+media

### `content_generator.py`

- `generate_post(config, platform, history)` → Claude Sonnet 4.6
- Voz Lilly doctrinal
- Límites: farcaster 320 · twitter hilo `[TWEET]` · bluesky 300 · instagram 2200

### `onchain_registry.py`

- SHA-256 del contenido publicado
- Backup local: `data/mundana/registry/`
- Upload GCS: `gs://abu-oracle-predictions/predictions/`

---

## Producción

### Cloud Run Job + Scheduler

```
Job: mundana-publisher (us-central1)
Scheduler: mundana-publisher-daily — 08:00 UTC todos los días
Imagen: gcr.io/abu-oracle/mundana-publisher:latest
```

### Variables de entorno (Cloud Run Job)

| Variable | Valor | Descripción |
|---|---|---|
| `DRY_RUN` | `false` | Publicar real |
| `PLATFORMS` | `bluesky,twitter` | CSV de plataformas activas |
| `GCS_BUCKET` | `abu-oracle-predictions` | Cooldown + registry |

### Secrets (GCP Secret Manager)

| Secret | Uso |
|---|---|
| `anthropic-api-key` | Claude Sonnet 4.6 para generación |
| `bluesky-handle` | @abuoracle.bsky.social |
| `bluesky-password` | AT Protocol auth |
| `resend-api-key` | Email borrador Twitter |

### Para actualizar imagen

```bash
gcloud builds submit --config=cloudbuild-mundana-job.yaml --project=abu-oracle .
```

---

## Estado cuentas RRSS (2026-04-17)

| Plataforma | Cuenta | Estado |
|---|---|---|
| Bluesky | @abuoracle.bsky.social | ✅ Automático — primer post publicado |
| Twitter/X | — | 🟡 Borrador + email Resend operativo |
| Farcaster | Cuenta Warpcast (sin activar) | ⏳ Pago FID ~$5-10 → Neynar signer |
| Reddit | — | ❌ Pendiente |
| Instagram/Facebook/TikTok | — | 🟡 Draft semi-auto listo |

### Próximos pasos RRSS

1. Farcaster — pagar FID → neynar.com → `NEYNAR_API_KEY` + `FARCASTER_SIGNER_UUID` → gcloud secrets
2. Reddit — cuenta → `reddit.com/prefs/apps` → 5 secrets → gcloud secrets
3. Multilingüismo — `lang` param en `generate_post()` + `LANGUAGES` env var (EN/ES/FR/PT)

---

## Validación end-to-end (local, 2026-04-15)

```
filter → stellium Aries 5 planetas (sig=high) → farcaster 317 chars ✓
       → twitter borrador en data/mundana/drafts/ ✓
       → SHA-256 registry ✓
```

---

## Referencias cruzadas

### Doctrina (justificación axiomática)
- [[AXIOMATICS_v0_4]] — Axioma 11: estratificación niveles operativos
- [[AXIOMATICS_OF_HEAVENS_v0_4]] — redirect raíz con tabla de axiomas
- [[AXIOMATICS_v0_3]] — Abu Mashar y campo histórico (referencia previa)

### Validación empírica
- [[MUNDANA_H_A_RESULTADOS]] — hipótesis confirmada que justifica la feature
- [[HIPOTESIS_REGISTRO]] — H_mundana_A formalizada
- [[HF_EXPERIMENT_LOG]] — metodología de correlación

### Engineering del sistema
- [[ARCHITECTURE]] — integración con Abu↔Lilly, Event System, Context Builder
- [[CONTEXT_QUALITY_FIXES]] — calidad del contexto que recibe Lilly mundana

### Costos y estrategia
- [[finops_milp]] — impacto en costos (1 llamada Sonnet/día por post)
- [[COST_OPTIMIZATION]] — modelo de costos del publisher
- [[ANTHROPIC_STRATEGY]] — publisher autónomo como caso publicable
- [[grant_proposal_ResearchHub]] — paper FinOps con caso publisher

### Código fuente
- `abu_engine/core/mundana.py` — módulo cálculo
- `abu_engine/routers/mundana.py` — endpoints FastAPI
- `next_app/components/mundana-tab.tsx` — UI
- `next_app/app/api/lilly/mundana/route.ts` — interpretación Lilly
- `scripts/mundana/` — código fuente pipeline publisher
