# Session A — Bio Event Scraper

## Objetivo
Construir un scraper que extraiga **eventos biográficos fechados** de fuentes públicas (Wikipedia, Wikidata, biografías online) para los sujetos del dataset astrológico. Los eventos alimentarán el optimizador de pesos del Harmony Field (HF v4).

## Contexto mínimo
- Proyecto: AI Oracle — motor astrológico + interpretador LLM.
- Dataset: 4,650 sujetos con datos natales en `data/processed/embeddings_v2/` y `data/processed/rankings_v3/`.
- 10 sujetos demo con campos HF pre-calculados en `output/demo/`.
- 3 sujetos gold standard con eventos manuales en `data/gold_standard/`.

## Sujetos prioritarios (13)

### Gold Standard (ya tienen eventos manuales — ampliar)
| ID | Slug | Nombre | Nacimiento |
|----|------|--------|------------|
| GS_001 | jung | Carl Gustav Jung | 1875-07-26 |
| GS_002 | tesla | Nikola Tesla | 1856-07-10 |
| GS_003 | turing | Alan Turing | — |

### Demo pack (necesitan eventos desde cero)
| ID | Slug | Nombre | Nacimiento |
|----|------|--------|------------|
| 308660 | einstein | Albert Einstein | 1879-03-14 |
| 12145 | borges | Jorge Luis Borges | 1899-08-24 |
| 35255 | frida | Frida Kahlo | 1907-07-06 |
| 76835 | picasso | Pablo Picasso | 1881-10-25 |
| 317785 | vangogh | Vincent Van Gogh | 1853-03-30 |
| 337730 | freud | Sigmund Freud | 1856-05-06 |
| 61360 | gandhi | Mohandas Gandhi | 1869-10-02 |
| 232650 | bowie | David Bowie | 1947-01-08 |

## Schema de salida (RESPETAR)
Cada sujeto produce un JSON siguiendo el schema de `data/gold_standard/GS_001_JUNG.json`:

```json
{
  "meta": {
    "id": "308660",
    "name": "Albert Einstein",
    "source_origin": "Wikipedia",
    "schema_version": "1.2"
  },
  "biographical_events": [
    {
      "date": "1905-06-30",
      "event_type": "professional_milestone",
      "location": { "city": "Bern", "country": "Switzerland", "lat": 46.95, "lon": 7.45 },
      "description": "Publicación del artículo sobre relatividad especial.",
      "valence": "positive",
      "validation_target": {
        "axiom_id": null,
        "label": "Logro profesional"
      },
      "confidence": "high"
    }
  ]
}
```

### Campos obligatorios por evento
| Campo | Tipo | Notas |
|-------|------|-------|
| `date` | `YYYY-MM-DD` | Si solo se conoce el año, usar `YYYY-01-01` y `confidence: "low"` |
| `event_type` | string enum | Ver tabla abajo |
| `description` | string | 1–2 frases en español |
| `valence` | `"positive"` \| `"negative"` \| `"neutral"` | Valoración cualitativa del evento |
| `confidence` | `"high"` \| `"medium"` \| `"low"` | Certeza de la fecha |

### Campos opcionales
| Campo | Tipo | Notas |
|-------|------|-------|
| `location` | `{city, country, lat, lon}` | Donde ocurrió el evento (importante para relocation) |
| `validation_target` | `{axiom_id, label}` | Para gold standard; puede ser `null` |

### Event types permitidos
```
death, birth_child, marriage, divorce, relocation,
professional_milestone, award, publication, exhibition,
health_critical, psychological_crisis, accident,
political_event, arrest, exile, legal,
artistic_creation, discovery, invention,
financial_crisis, financial_success,
relationship_start, relationship_end,
education_start, education_end,
military_service, retirement
```

## Arquitectura del scraper (Híbrida: SPARQL + LLM)

Dos fuentes complementarias. Wikidata da datos limpios gratis; el LLM extrae el grueso de eventos interesantes del texto narrativo de Wikipedia.

### Fuente 1: Wikidata SPARQL (datos estructurados, sin LLM)
- Endpoint: `https://query.wikidata.org/sparql`
- Propiedades útiles: P569 (nacimiento), P570 (muerte), P26 (cónyuge→matrimonio), P40 (hijos), P166 (premios), P69 (educación), P108 (empleador), P551 (residencia), P585 (fecha del evento), P276 (lugar), P625 (coordenadas).
- Devuelve: fechas exactas, coordenadas, labels. Cubre ~30-40% de eventos típicos (muerte, matrimonio, premios, educación).
- Costo: $0.

### Fuente 2: Wikipedia + GPT-4o-mini (texto narrativo → eventos estructurados)
- Wikipedia REST API: `https://en.wikipedia.org/api/rest_v1/page/html/{title}` (o `es.wikipedia.org` si el artículo en español es más completo).
- Bajar texto completo del artículo, limpiar HTML → texto plano.
- Enviar a **GPT-4o-mini** con un prompt de extracción que devuelve JSON directamente.
- Costo estimado: ~$0.003/sujeto → ~$0.04 total para 13 sujetos.

#### Prompt de extracción LLM
```
Sistema: Eres un extractor de eventos biográficos. Dado el texto de un artículo de Wikipedia,
extrae todos los eventos fechados relevantes. Devuelve SOLO un JSON array.

Cada evento debe tener:
- date: "YYYY-MM-DD" (si solo se conoce el año, usar "YYYY-01-01")
- event_type: uno de [death, birth_child, marriage, divorce, relocation,
  professional_milestone, award, publication, exhibition, health_critical,
  psychological_crisis, accident, political_event, arrest, exile, legal,
  artistic_creation, discovery, invention, financial_crisis, financial_success,
  relationship_start, relationship_end, education_start, education_end,
  military_service, retirement]
- description: 1-2 frases en español describiendo el evento
- valence: "positive" | "negative" | "neutral"
- confidence: "high" si la fecha exacta aparece en el texto,
  "medium" si se infiere del contexto, "low" si solo se conoce el año
- location: {city, country} si se menciona en el texto (omitir si no)

No incluyas el nacimiento del sujeto. Prioriza eventos con fechas precisas.
Devuelve entre 8 y 25 eventos, cubriendo distintas etapas de la vida.

Usuario: Artículo sobre {nombre_sujeto}:
{texto_wikipedia}
```

### Módulos a crear
```
scripts/
  bio_scraper/
    __init__.py
    wikidata.py      # SPARQL queries → eventos estructurados
    wikipedia.py     # Descarga y limpieza de artículos Wikipedia
    llm_extractor.py # Envía texto a GPT-4o-mini, parsea JSON response
    geocoder.py      # Agrega lat/lon a eventos con city+country (Wikidata o Nominatim)
    models.py        # dataclass BioEvent (mirrors JSON schema)
    pipeline.py      # Orquestador: wikidata → wikipedia+LLM → merge → dedup → geocode → output
    subjects.py      # Lista de sujetos con Wikidata Q-IDs y Wikipedia titles
```

### Pipeline
1. Resolver Wikidata Q-ID del sujeto (por nombre + fecha nacimiento).
2. **Paso SPARQL**: query Wikidata → eventos estructurados con fecha, lugar, coordenadas.
3. **Paso LLM**: descargar artículo Wikipedia → limpiar HTML → enviar a GPT-4o-mini → parsear JSON de eventos.
4. **Merge + dedup**: unir ambas fuentes. Misma fecha ±7 días + mismo tipo = mismo evento (priorizar el de mayor confidence).
5. **Geocoding**: para eventos con city+country pero sin lat/lon, resolver coordenadas vía Wikidata o Nominatim.
6. **Validar schema**: verificar que cada evento cumple el schema obligatorio.
7. **Exportar** JSON final al schema definido.

### Configuración LLM
- Usar `OPENAI_API_KEY` del env (ya existe para Lilly Engine).
- Modelo: `gpt-4o-mini` (barato, rápido, suficiente para extracción estructurada).
- `temperature: 0.1` (queremos extracción determinista, no creatividad).
- `response_format: { type: "json_object" }` (forzar JSON válido).
- Retry: 1 reintento con backoff si falla la llamada.

### Output
```
data/biographical_events/
  308660_einstein.json
  12145_borges.json
  ...
  GS_001_JUNG.json  (ampliado con eventos de Wikipedia)
```

### Criterios de calidad
- Mínimo 5 eventos por sujeto, ideal 10-20.
- Al menos 50% con `confidence: "high"` (fecha exacta conocida).
- Al menos 30% con `location` (para validar relocation HF).
- Eventos deben cubrir distintas etapas de vida (no solo muerte y nacimiento).

## Dependencias
```
pip install requests sparqlwrapper beautifulsoup4 lxml openai
```
- `requests`, `bs4`: ya existen en el proyecto (ver `astro_dataset/cartanatal/scraper.py`).
- `openai`: ya instalado para lilly_engine. Usar el mismo `OPENAI_API_KEY` del env.
- Costo total estimado para 13 sujetos: < $0.05 USD.

## Validación
- Correr el pipeline para los 13 sujetos prioritarios.
- Comparar eventos extraídos de Jung con `data/gold_standard/GS_001_JUNG.json` (debe incluir los 3 eventos manuales).
- Generar un resumen: sujeto, n_eventos, n_high_confidence, n_con_location.

## NO hacer en esta sesión
- No modificar el motor HF ni la fórmula.
- No tocar el frontend.
- No tocar abu_engine ni lilly_engine.
- Solo crear el scraper y generar los JSONs.
