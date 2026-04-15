# MUNDANA_MODULE_SPEC.md
# Especificación completa — Módulo Astrología Mundana + Automatización RRSS
> Para Claude Code. Leer CLAUDE.md y ARCHITECTURE.md antes de ejecutar cualquier tarea.
> Fecha: 2026-04-15 · Target: 18 de abril (Luna nueva Aries, stellium 7 planetas)
> Workflow invariante: diagnóstico → diff → confirmación → commit. Un archivo a la vez.

---

## CONTEXTO

Abu Oracle es un motor astrológico computacional con:
- Abu Engine (Python/FastAPI) en Cloud Run
- Next.js frontend en Cloud Run (app.abu-oracle.com)
- Lilly: agente Claude Sonnet 4.6 con doctrina helenística-persa
- Swiss Ephemeris DE440s + Moshier para fechas históricas

El módulo mundana aplica la misma doctrina de Abu Mashar
a eventos colectivos en lugar de cartas natales individuales.
La hipótesis H_mundana_A está confirmada: conjunciones Júpiter-Saturno
correlacionan con clusters de eventos históricos con p=5×10⁻⁶,
densidad 4.3x baseline (corpus: 23.636 eventos, año 8-2069).

---

## PRIMERA TAREA URGENTE — Fix routing modelos

**Antes de cualquier otra cosa**, corregir selectModel.ts:

```
Archivo: next_app/lib/selectModel.ts
Cambio: todas las rutas → 'claude-sonnet-4-6' sin excepción
Haiku queda reservado para MILP por usuario (feature futura)
```

Pasos:
1. Leer contenido actual de selectModel.ts
2. Cambiar todas las rutas a claude-sonnet-4-6
3. tsc --noEmit exit 0
4. git add next_app/lib/selectModel.ts
5. git commit -m "fix(routing): todas las rutas → Sonnet, Haiku reservado MILP"
6. gcloud builds submit --config=cloudbuild-nextjs.yaml --project=abu-oracle

NO continuar hasta que el deploy confirme SUCCESS.

---

## FASE 1 — Backend: Abu Engine endpoints mundana

### 1.1 Script de configuraciones planetarias

**Archivo nuevo:** `scripts/mundana/sky_calculator.py`

Funciones requeridas:

```python
def get_current_sky() -> dict:
    """
    Calcula posiciones planetarias actuales.
    Retorna: {
        'date': ISO string,
        'planets': {'jupiter': lon, 'saturn': lon, 'mars': lon, ...},
        'active_configurations': [
            {
                'type': 'conjunction_JS' | 'opposition_MS' | 'stellium',
                'planets': [...],
                'orb': float,
                'exact_date': ISO string,
                'p_value': float,  # del corpus
                'density_ratio': float,  # vs baseline
                'significance': 'high' | 'medium' | 'low'
            }
        ]
    }
    """

def get_upcoming_configurations(days_ahead: int = 90) -> list:
    """
    Calcula configuraciones planetarias próximas.
    Filtra por umbral estadístico: p_value < 0.05 AND density > 2.0x
    Ordena por significancia descendente.
    Retorna lista de configuraciones con fecha exacta.
    """

def get_historical_context(config_type: str, orb: float = 8.0) -> dict:
    """
    Busca en data/mundana/eventos_raw.jsonl eventos ocurridos
    en ventanas ±30 días de configuraciones similares.
    Retorna: {
        'sample_events': [...],  # 3-5 eventos representativos
        'density_ratio': float,
        'p_value': float
    }
    """
```

Usar `scripts/mundana/ephemeris_historical.py` (ya existe, Moshier).
NO modificar abu_engine/ en este paso.

### 1.2 Endpoint Abu Engine

**Archivo nuevo:** `abu_engine/routers/mundana.py`

```python
# Endpoints requeridos:

GET /api/mundana/sky
# Retorna cielo actual + configuraciones activas
# Respuesta: current_sky dict completo

GET /api/mundana/forecast?days=90
# Retorna configuraciones próximas filtradas por significancia
# Respuesta: lista ordenada de configuraciones

GET /api/mundana/history?config_type=conjunction_JS&limit=5
# Retorna eventos históricos similares del corpus
# Respuesta: eventos representativos con contexto
```

Registrar el router en `abu_engine/main.py`:
```python
from routers import mundana
app.include_router(mundana.router, prefix="/api/mundana")
```

Verificar con test manual antes de continuar.

### 1.3 Route Lilly mundana

**Archivo nuevo:** `next_app/app/api/lilly/mundana/route.ts`

Patrón: igual que las otras routes Lilly existentes.

Context block para Lilly:
```
Configuración mundana activa: {tipo} — exactitud {fecha}.
Contexto histórico: en {N} ventanas similares desde el año {X},
la densidad de eventos fue {ratio}x el baseline (p={p_value}).
Eventos representativos: {lista}.
Planetas involucrados: {lista}.
Idioma de respuesta: {lang}
```

Modelo: claude-sonnet-4-6 (no negociable para rutas doctrinales).
max_tokens: 2048 (interpretación mundana es compleja).
Cachear LILLY_SYSTEM_PROMPT con cache_control: ephemeral.

---

## FASE 2 — Frontend: Tab Cielo Hoy

### 2.1 Componente MundanaTab

**Archivo nuevo:** `next_app/components/mundana-tab.tsx`

Estructura del componente:

```
MundanaTab
├── CieloActual
│   ├── ConfiguracionesActivas (cards con badge de significancia)
│   └── OracleInterface → dispara evento Lilly mundana
├── PronosticoProximo (próximas 90 días)
│   ├── TimelineConfiguraciones (ordenadas por fecha)
│   └── FiltroSignificancia (alta/media/todas)
└── ContextoHistorico
    └── EventosRepresentativos (del corpus)
```

Diseño: misma estética que el resto del app.
- Fondo: #0d1117
- Cards con borde rgba(255,255,255,0.08)
- Acentos ámbar #f5a623
- Verde #00ff88 para configuraciones de alta significancia
- Fuentes: mismas que el app (Cormorant Garamond, Courier Prime)

### 2.2 Integración en el dashboard

**Archivo a modificar:** `next_app/components/dashboard-layout.tsx`
(o el componente que maneja los tabs principales)

Agregar tab "Cielo Hoy" al mismo nivel que Carta Natal,
Técnicas Persas, Tránsitos, Mapa HF.

### 2.3 Integración en Tránsitos

**Archivo a modificar:** `next_app/components/transits-tab.tsx`

Agregar sección "Contexto Mundano" al pie del tab de Tránsitos.
Mostrar si hay configuraciones mundanas activas que amplifican
o contextualizan los tránsitos personales del nativo.
Lilly puede comentar ambas capas simultáneamente cuando
el usuario hace click en un tránsito personal.

### 2.4 Acceso desde Home

**Archivo a modificar:** `next_app/app/page.tsx`

Agregar opción "Astrología Mundana" en el home post-login,
al mismo nivel que "Mi carta" y "Analizar otra persona".
El usuario puede entrar directamente sin tener carta cargada.

---

## FASE 3 — Agente publicador autónomo

### 3.1 Filtro de publicación

**Archivo nuevo:** `scripts/mundana/publication_filter.py`

Criterios para publicar:
```python
PUBLICATION_THRESHOLDS = {
    'p_value_max': 0.05,        # señal estadísticamente significativa
    'density_ratio_min': 2.0,   # al menos 2x el baseline
    'days_to_exact_max': 7,     # dentro de la ventana relevante
    'min_days_between_posts': 3 # no publicar más de una vez cada 3 días
}
```

Lógica:
1. Calcular configuraciones próximas 7 días
2. Filtrar por umbrales
3. Si hay configuración → generar contenido
4. Si no → no publicar (el silencio es doctrinalmente correcto)

### 3.2 Generador de contenido

**Archivo nuevo:** `scripts/mundana/content_generator.py`

```python
def generate_post(config: dict, platform: str) -> dict:
    """
    Genera contenido adaptado por plataforma.
    
    platform: 'farcaster' | 'twitter' | 'instagram' | 
              'facebook' | 'tiktok' | 'bluesky'
    
    Retorna: {
        'text': str,
        'hashtags': list,
        'image_prompt': str,  # para generar imagen si aplica
        'thread': list,       # para Twitter/X (hilos)
    }
    """
```

Llamar a Claude API (claude-sonnet-4-6) con system prompt de Lilly
y context block mundano. Lilly redacta en su voz doctrinal.

Límites por plataforma:
- Farcaster: 320 chars
- Twitter/X: 280 chars (o hilo de 3-5 tweets)
- Instagram: caption larga + hashtags
- Facebook: post completo, más extenso
- TikTok: script para video corto (30-60 seg)
- Bluesky: 300 chars

### 3.3 Publicadores por plataforma

**Archivo nuevo:** `scripts/mundana/publishers/`

```
publishers/
├── __init__.py
├── base_publisher.py      # clase abstracta
├── farcaster_publisher.py # Neynar API (gratuito, prioritario)
├── twitter_publisher.py   # supervisión manual en etapa inicial
├── instagram_publisher.py # Meta Graph API
├── facebook_publisher.py  # Meta Graph API
├── bluesky_publisher.py   # AT Protocol (gratuito)
└── tiktok_publisher.py    # TikTok API
```

**Farcaster (prioritario):**
```python
# Neynar API — gratuito hasta 1000 casts/mes
import requests

NEYNAR_API_KEY = os.environ['NEYNAR_API_KEY']
FARCASTER_SIGNER_UUID = os.environ['FARCASTER_SIGNER_UUID']

def publish_farcaster(text: str) -> dict:
    response = requests.post(
        'https://api.neynar.com/v2/farcaster/cast',
        headers={'api_key': NEYNAR_API_KEY},
        json={'signer_uuid': FARCASTER_SIGNER_UUID, 'text': text}
    )
    return response.json()
```

**Twitter/X (supervisión manual en Fase 1):**
```python
# En lugar de publicar directamente, guardar borrador
# y enviar mail via Resend para aprobación manual

def publish_twitter(text: str) -> dict:
    # Guardar en GCS como borrador
    save_draft_to_gcs(text, platform='twitter')
    # Enviar mail de aprobación
    send_approval_email(text, platform='twitter')
    return {'status': 'pending_approval', 'text': text}
```

**Instagram y Facebook:**
```python
# Meta Graph API — requiere Facebook App con permisos
# pages_manage_posts, instagram_content_publish
# Token de larga duración (60 días, renovar automáticamente)
```

**Bluesky:**
```python
# AT Protocol — gratuito, sin límites estrictos
from atproto import Client

def publish_bluesky(text: str) -> dict:
    client = Client()
    client.login(os.environ['BLUESKY_HANDLE'], 
                 os.environ['BLUESKY_PASSWORD'])
    return client.send_post(text=text)
```

**TikTok:**
```python
# TikTok Content Posting API
# Genera script de texto que el operador narra
# En Fase 1: guardar script + enviar mail para producción manual
```

### 3.4 Registro on-chain

**Archivo nuevo:** `scripts/mundana/onchain_registry.py`

```python
def register_prediction(content: str, config: dict) -> dict:
    """
    Registra pronóstico on-chain para reputación verificable.
    
    1. Genera hash SHA-256 del contenido + timestamp
    2. Escribe en contrato en Arbitrum (Safe wallet existente)
    3. Retorna tx_hash para verificación pública
    
    Safe wallet: 0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82
    """
```

En Fase 1: guardar hash en GCS con timestamp.
El registro on-chain real es Fase 2 (requiere contrato).

### 3.5 Cloud Run Job (scheduler)

**Archivo nuevo:** `cloudbuild-mundana-job.yaml`

```yaml
# Cloud Run Job — cron diario 08:00 UTC
# gcloud run jobs create mundana-publisher \
#   --image gcr.io/abu-oracle/mundana-publisher \
#   --schedule "0 8 * * *" \
#   --region us-central1

steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/abu-oracle/mundana-publisher', 
         '-f', 'scripts/mundana/Dockerfile', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/abu-oracle/mundana-publisher']
```

**Archivo nuevo:** `scripts/mundana/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY scripts/mundana/ ./mundana/
COPY requirements-mundana.txt .
RUN pip install -r requirements-mundana.txt
CMD ["python", "mundana/main_publisher.py"]
```

**Archivo nuevo:** `scripts/mundana/main_publisher.py`

```python
# Entry point del job
from publication_filter import should_publish
from content_generator import generate_post
from publishers import publish_all
from onchain_registry import register_prediction

def main():
    if not should_publish():
        print("No hay configuraciones que superen el umbral. No se publica.")
        return
    
    config = get_best_configuration()
    
    for platform in ['farcaster', 'bluesky', 'twitter', 'instagram', 'facebook']:
        content = generate_post(config, platform)
        result = publish_all(platform, content)
        register_prediction(content['text'], config)
        log_result(platform, result)

if __name__ == '__main__':
    main()
```

---

## VARIABLES DE ENTORNO REQUERIDAS

Agregar en Cloud Run y en `.env.local`:

```bash
# Ya existentes
OPERATOR_UID=xJhOVmVFRUXoRBRGK6mJWyMeZOu1
ANTHROPIC_API_KEY=...
FIREBASE_SERVICE_ACCOUNT_JSON=...

# Nuevas para mundana publisher
NEYNAR_API_KEY=...              # Farcaster — obtener en neynar.com
FARCASTER_SIGNER_UUID=...       # Farcaster — del dashboard Neynar
BLUESKY_HANDLE=...              # ej: abuoracle.bsky.social
BLUESKY_PASSWORD=...            # app password de Bluesky
META_PAGE_ID=...                # Facebook Page ID
META_ACCESS_TOKEN=...           # Token largo plazo Meta Graph API
INSTAGRAM_ACCOUNT_ID=...        # Instagram Business Account ID
RESEND_API_KEY=...              # Ya existe — para mails de aprobación
```

---

## ORDEN DE EJECUCIÓN

```
DÍA 1 (hoy):
  □ Fix selectModel.ts → deploy
  □ sky_calculator.py
  □ abu_engine/routers/mundana.py
  □ Route /api/lilly/mundana

DÍA 2:
  □ MundanaTab component
  □ Integración tabs dashboard
  □ Integración Tránsitos
  □ Acceso desde Home
  □ Deploy completo

DÍA 3 (antes del 18):
  □ publication_filter.py
  □ content_generator.py
  □ publishers/ (Farcaster + Bluesky primero)
  □ main_publisher.py
  □ Test completo del pipeline
  □ Cloud Run Job configurado
  □ Primer post publicado manualmente para validar
```

---

## ARCHIVOS PROTEGIDOS — NUNCA MODIFICAR

- `abu_engine/core/life_cycles.py`
- `abu_engine/harmony/field_v3.py`
- `abu_engine/harmony/angularity.py`
- `abu_engine/harmony/houses.py`

---

## CONVENCIONES

- Un archivo a la vez
- tsc --noEmit exit 0 entre pasos TypeScript
- python -m pytest abu_engine/tests/ entre pasos Python
- Commits atómicos con mensaje descriptivo
- Deploy solo con: `gcloud builds submit --config=cloudbuild-*.yaml`
- NO modificar abu_engine/ sin confirmar con el operador primero
- Lilly siempre en claude-sonnet-4-6 (sin excepción)
