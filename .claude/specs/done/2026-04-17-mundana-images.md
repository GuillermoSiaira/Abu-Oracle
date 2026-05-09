# Spec: Imágenes en posts Mundana + Product Showcase HF Map

**Estado:** ACTIVO  
**Fecha:** 2026-04-17  
**Objetivo:** Agregar imágenes generadas programáticamente a los posts del pipeline Mundana
(Bluesky automático + Twitter draft) y crear un script standalone de product showcase
usando el HF map de figuras históricas para impulsar tráfico a app.abu-oracle.com.

**Contexto del proyecto:**
- Pipeline mundana: `scripts/mundana/` — Cloud Run Job diario, ya publicando en Bluesky (texto)
- HF maps disponibles como GeoJSON: `next_app/public/geojson/{slug}_domains.geojson`
- Rankings top-20: `next_app/public/rankings/` (verificar si existen antes de leer)
- Sujetos demo disponibles: einstein, freud, jung, tesla, gandhi, frida, picasso, vangogh, borges, bowie
- Abu Engine corriendo en local: `http://localhost:8000`

---

## TAREA 1 — Módulo de generación de imágenes

**Archivo nuevo:** `scripts/mundana/image_generator.py`

### Función 1: `generate_sky_diagram(config: dict) -> bytes`

Genera un diagrama circular de la configuración planetaria mundana.

**Input:** objeto `config` del pipeline (campos relevantes: `planet_a`, `planet_b`,
`config_type`, `exact_date`, `current_longitude_a`, `current_longitude_b`)

**Output:** PNG en bytes (300×300px, DPI 150)

**Estilo visual:**
- Fondo negro `#0a0a0f`
- Proyección polar (matplotlib `projection='polar'`)
- 12 sectores de 30° para los signos zodiacales, bordes en `#2a2a3a`
- Labels de signos con símbolos Unicode en gris tenue `#4a4a6a`: ♈♉♊♋♌♍♎♏♐♑♒♓
- Planetas como puntos coloreados en sus longitudes eclípticas, símbolo Unicode encima:
  - Sol ☉ `#fbbf24`, Luna ☽ `#e2e8f0`, Mercurio ☿ `#94a3b8`, Venus ♀ `#f9a8d4`
  - Marte ♂ `#ef4444`, Júpiter ♃ `#fb923c`, Saturno ♄ `#a78bfa`
  - Urano ⛢ `#67e8f9`, Neptuno ♆ `#818cf8`, Plutón ♇ `#6b7280`
- Línea de aspecto entre `planet_a` y `planet_b`, color por `config_type`:
  - `conjunction_*` → blanco `#ffffff` alpha 0.8
  - `opposition_*` → rojo tenue `#ef4444` alpha 0.6
  - `square_*` → naranja `#f97316` alpha 0.6
  - `trine_*` → verde `#4ade80` alpha 0.6
- Texto central inferior: `config_type` formateado (ej: "Conjunción ♃♄") en 9px gris claro
- Fecha debajo en 8px gris tenue
- Sin ejes, sin ticks, sin frame — solo el círculo

**Nota técnica:** Las longitudes eclípticas van de 0° a 360°. En proyección polar de matplotlib,
0° está a la derecha y avanza en sentido antihorario. Convertir: `theta = (90 - lon) % 360`
para que Aries (0°) quede arriba, como es convencional en astrología.

---

### Función 2: `generate_hf_map_image(subject_slug: str, domain: str = 'global') -> bytes`

Genera imagen del Harmony Field de un sujeto para una plataforma social.

**Input:** slug del sujeto (ej: `'einstein'`), dominio HF (ej: `'global'`, `'h10'`, `'h07'`)

**Output:** PNG en bytes (800×400px — landscape 2:1, ideal para Twitter/Bluesky)

**Fuente de datos:**
- Leer `next_app/public/geojson/{subject_slug}_domains.geojson`
- Campo HF a usar: si `domain == 'global'` → `hf_global`; si no → `hf_{domain}`
- Si el campo no existe en el GeoJSON, hacer fallback a `hf_global` con warning
- Si el archivo no existe: lanzar `FileNotFoundError(f"GeoJSON not found for {subject_slug}")`

**Estilo visual:**
- Fondo negro `#0a0a0f`
- Scatter plot lat/lon, tamaño de punto `s=6`, sin bordes (`linewidths=0`)
- Colormap `RdYlGn` (rojo=HF bajo, verde=HF alto), normalizado al rango del dataset
- Alpha `0.7` para los puntos
- Sin ejes, sin frame, sin título — mapa limpio
- Watermark en esquina inferior derecha: texto `abu-oracle.com` en gris muy tenue `#2a2a3a`,
  fontsize 8, `transform=ax.transAxes`, `ha='right'`, `va='bottom'`
- `plt.tight_layout(pad=0)` para eliminar márgenes

**Nota:** `matplotlib` sin backend de display requiere `matplotlib.use('Agg')` al inicio del módulo.

---

## TAREA 2 — Integrar imagen en el pipeline Mundana

### 2a — Modificar `scripts/mundana/content_generator.py`

- Importar `generate_sky_diagram` desde `image_generator`
- Al final de `generate_post()`, después de generar el texto:
  ```python
  try:
      image_bytes = generate_sky_diagram(config)
      image_alt = f"{config.get('config_type', 'configuración')} — {config.get('exact_date', '')}"
  except Exception as e:
      print(f"[WARNING] No se pudo generar imagen: {e}")
      image_bytes = None
      image_alt = None
  ```
- Agregar `image_bytes` e `image_alt` al dict de retorno

### 2b — Modificar `scripts/mundana/publishers/bluesky_publisher.py`

Agregar soporte para imagen en el post de Bluesky.

**Nueva función privada:**
```python
def _upload_blob(session_token: str, image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """Sube imagen a Bluesky y devuelve el blob ref."""
    response = requests.post(
        "https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
        headers={
            "Content-Type": mime_type,
            "Authorization": f"Bearer {session_token}"
        },
        data=image_bytes,
        timeout=30
    )
    response.raise_for_status()
    return response.json()["blob"]
```

**En la función de publicación**, si `content.get("image_bytes")`:
1. Llamar `_upload_blob()` → obtener `blob_ref`
2. Agregar `embed` al record:
   ```python
   "embed": {
       "$type": "app.bsky.embed.images",
       "images": [{"image": blob_ref, "alt": content.get("image_alt", "")}]
   }
   ```
3. Si falla el upload: loggear warning, publicar de todas formas sin imagen (no bloquear)

### 2c — Modificar `scripts/mundana/publishers/twitter_publisher.py`

Si `content.get("image_bytes")`:
- Guardar PNG: `data/mundana/drafts/{timestamp}_{config_type}.png`
- En el cuerpo del email de draft (Resend), agregar sección:
  ```html
  <hr>
  <p><strong>📎 Imagen generada:</strong></p>
  <p><code>{ruta_imagen}</code></p>
  <p style="color:#888">Adjuntar esta imagen al tweet.</p>
  ```
- No intentar adjuntar binarios al email — solo indicar ruta local

---

## TAREA 3 — Script standalone Product Showcase

**Archivo nuevo:** `scripts/mundana/showcase_publisher.py`

Script ejecutable manualmente para publicar HF map de figuras históricas.

**CLI:**
```bash
python scripts/mundana/showcase_publisher.py \
  --subject einstein \
  --domain h10 \
  --platform bluesky \
  --lang es
```

**Parámetros:**
- `--subject`: slug del sujeto (requerido)
- `--domain`: dominio HF, default `global`
- `--platform`: `bluesky` | `twitter` | `all`, default `bluesky`
- `--lang`: `es` | `en`, default `es`
- `--dry-run`: genera imagen y texto pero no publica

**Flujo:**
1. Llamar `generate_hf_map_image(subject, domain)` → `image_bytes`
2. Leer ranking top-3 si existe en `next_app/public/rankings/{subject}_top20.json`
   (campo a buscar: array de objetos con `city` y `hf_score` o `score`)
3. Llamar `generate_showcase_caption(subject, domain, top3_cities, lang)` — nueva función
   en `content_generator.py`:
   - Prompt a Claude Sonnet 4.6:
     ```
     Eres Lilly, astrólogo del sistema Abu Oracle. Describe el mapa HF de {nombre_real}
     para el dominio "{dominio_label}" en máximo {limite} caracteres.
     Menciona las 3 mejores ciudades: {ciudades}.
     Cierra con una pregunta al lector sobre su propia carta.
     Tono: directo, doctrinal, sin emojis excesivos.
     Termina con: app.abu-oracle.com
     ```
   - `nombre_real`: mapear slug → nombre (dict hardcodeado: einstein→"Albert Einstein", etc.)
   - `dominio_label`: mapear h10→"Carrera", h07→"Amor", etc. (o "Campo Global")
   - Límites por plataforma: bluesky=280, twitter=220 (deja margen para URL), instagram=400
4. Publicar en la plataforma seleccionada via los publishers existentes
5. Loggear resultado con timestamp

**Nombres reales (dict en el script):**
```python
SUBJECT_NAMES = {
    "einstein": "Albert Einstein",
    "freud": "Sigmund Freud",
    "jung": "Carl Jung",
    "tesla": "Nikola Tesla",
    "gandhi": "Mahatma Gandhi",
    "frida": "Frida Kahlo",
    "picasso": "Pablo Picasso",
    "vangogh": "Vincent van Gogh",
    "borges": "Jorge Luis Borges",
    "bowie": "David Bowie",
}
```

---

## TAREA 4 — Dependencias y Docker

### `requirements-mundana.txt`

Agregar si no están:
```
matplotlib>=3.8.0
Pillow>=10.0.0
numpy>=1.26.0
```

### `scripts/mundana/Dockerfile`

Después del `apt-get` existente (o crearlo si no hay), agregar:
```dockerfile
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*
```

Verificar que `matplotlib.use('Agg')` esté al inicio de `image_generator.py`
(necesario en entornos headless sin display).

---

## TAREA 5 — Tests locales (ejecutar antes de deploy)

```bash
cd d:/projects/ai-oracle
source .venv311/Scripts/activate

# Test 1: sky diagram
python -c "
import sys; sys.path.insert(0, '.')
from scripts.mundana.image_generator import generate_sky_diagram
config = {
    'planet_a': 'Jupiter', 'planet_b': 'Saturn',
    'config_type': 'conjunction_JS', 'exact_date': '2026-05-15',
    'current_longitude_a': 45.2, 'current_longitude_b': 46.1
}
img = generate_sky_diagram(config)
open('test_sky_diagram.png', 'wb').write(img)
print('sky diagram OK —', len(img), 'bytes')
"

# Test 2: HF map
python -c "
import sys; sys.path.insert(0, '.')
from scripts.mundana.image_generator import generate_hf_map_image
img = generate_hf_map_image('einstein', 'h10')
open('test_hf_map.png', 'wb').write(img)
print('hf map OK —', len(img), 'bytes')
"

# Abrir las imágenes y verificar visualmente antes de continuar
```

Si los tests pasan y las imágenes se ven bien → proceder con Tareas 2 y 3.

---

## TAREA 6 — Deploy

Solo después de que los tests locales pasen:

```bash
cd d:/projects/ai-oracle
gcloud builds submit --config=cloudbuild-mundana-job.yaml --project=abu-oracle .
```

---

## Criterios de aceptación

- [ ] `test_sky_diagram.png` generado y visualmente correcto (diagrama circular, planetas visibles, línea de aspecto)
- [ ] `test_hf_map.png` generado y visualmente correcto (mapa mundo, colores warm/cool, watermark)
- [ ] Pipeline mundana completo con `DRY_RUN=true` no lanza errores
- [ ] Post en Bluesky (test manual) incluye imagen adjunta
- [ ] `showcase_publisher.py --subject einstein --domain h10 --dry-run` genera texto e imagen sin errores
- [ ] Docker build exitoso con las nuevas dependencias

---

## Notas para el implementador

- El módulo `image_generator.py` debe ser **importable sin side effects** — nada en el nivel de módulo
  que no sea `matplotlib.use('Agg')` e imports.
- No modificar `main_publisher.py` ni `publication_filter.py` — la integración va en `content_generator.py`.
- Los publishers existentes (bluesky, twitter) deben mantener retrocompatibilidad: si no viene
  `image_bytes` en el payload, deben funcionar exactamente igual que antes.
- Si hay dudas sobre el formato del GeoJSON, leer
  `next_app/public/geojson/einstein_domains.geojson` como referencia.
