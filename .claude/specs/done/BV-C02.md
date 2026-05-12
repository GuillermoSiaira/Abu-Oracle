# BV-C02 — Alias opaco obligatorio en Blind Validation

**Fecha:** 2026-05-11  
**Track:** Blind Validation / Seguridad del protocolo  
**Prioridad:** Alta — bloqueante para iniciar nuevas sesiones BV  
**Independiente de:** todos los specs activos  
**Archivos Python:** solo `scripts/blind_validation/` y `data/blind_validation/`  

---

## Problema

`run_blind_validation.py` tiene un bug de identidad que compromete la validez
del experimento de carta ciega:

### Bug 1 — Alias no opaco llega al LLM

```python
# CÓDIGO ACTUAL (línea ~130):
alias = args.alias if args.alias != "Mr. X" else _opaque
```

Si el operador pasa `--alias "Jung"`, el alias "Jung" entra al contexto:

```
╔══ CARTA NATAL — Jung ══╗
```

El modelo sabe inmediatamente que está leyendo la carta de Jung.
**El experimento queda invalidado antes de comenzar.**

### Bug 2 — Filename contiene el alias slug

```python
slug = _slug(alias)             # "jung" si alias = "Jung"
bv_filename = f"{bv_id}_{slug}.md"  # "BV_002_jung.md"
```

El nombre del archivo en disco identifica al sujeto.
**Ya ocurrió:** `data/blind_validation/BV_001_trump.md` existe en el repo.

### Bug 3 — stdout puede filtrar alias

```python
print(f"[BV] Iniciando experimento {bv_id} — alias: {alias}", flush=True)
```

Si `alias = "Trump"`, el log identifica al sujeto.

---

## Fix requerido

### Regla central

> El alias opaco (`NTV-{hash[:4].upper()}`) es el **único identificador**
> que el LLM ve, que aparece en filenames, y que se imprime en stdout.
> El `--label` humano (opcional) es **exclusivamente interno**: solo en `BV_index.json`.

### Cambio 1 — Parámetro `--alias` → `--label`

```python
# ANTES:
p.add_argument("--alias", default="Mr. X", help="Alias operativo (no revela identidad)")

# DESPUÉS:
p.add_argument(
    "--label",
    default=None,
    help="Etiqueta interna opcional (ej: 'Caso Libra 1946'). "
         "NUNCA se pasa al LLM ni aparece en filenames. "
         "Solo se guarda en BV_index.json como campo 'label'.",
)
```

**Backward compatibility:** si alguien aún pasa `--alias`, ignorar silenciosamente
(o agregar `p.add_argument("--alias", ...)` como alias deprecado que se descarta).

### Cambio 2 — Alias opaco siempre, sin condición

```python
# ANTES:
_hash_input = f"{args.date}{args.time}{args.lat}{args.lon}"
_opaque = "NTV-" + hashlib.sha256(_hash_input.encode()).hexdigest()[:4].upper()
alias = args.alias if args.alias != "Mr. X" else _opaque

# DESPUÉS:
_hash_input = f"{args.date}{args.time}{args.lat}{args.lon}"
opaque_id = "NTV-" + hashlib.sha256(_hash_input.encode()).hexdigest()[:4].upper()
# opaque_id es el único alias que circula externamente
```

Variable renombrada de `alias` a `opaque_id` en todo el archivo para dejar
claro que es el identificador opaco.

### Cambio 3 — Filename siempre usa opaque_id

```python
# ANTES:
slug = _slug(alias)
bv_filename = f"{bv_id}_{slug}.md"

# DESPUÉS:
bv_filename = f"{bv_id}_{opaque_id}.md"   # ej: "BV_002_NTV-206B.md"
obs_filename = f"{bv_id}_{opaque_id}.md"
```

### Cambio 4 — `_build_doctrinal_context` usa opaque_id

```python
# ANTES (header del contextBlock):
return f"""╔══ CARTA NATAL — {alias} ══╗

# DESPUÉS:
return f"""╔══ CARTA NATAL — {opaque_id} ══╗
```

El LLM recibe `NTV-206B` como referencia del sujeto. Sin nombre, sin label.

### Cambio 5 — Stdout nunca imprime label

```python
# ANTES:
print(f"[BV] Iniciando experimento {bv_id} — alias: {alias}", flush=True)

# DESPUÉS:
print(f"[BV] Iniciando experimento {bv_id} — id: {opaque_id}", flush=True)
```

Todos los prints usan `opaque_id`, nunca el label.

### Cambio 6 — `BV_index.json`: separar opaque_id de label

```python
# ANTES en _update_index:
data.append({
    "id": bv_id,
    "alias": alias,
    "subject_real": args.subject_real,
    ...
})

# DESPUÉS:
entry = {
    "id":           bv_id,
    "opaque_id":    opaque_id,      # ← antes "alias", ahora separado
    "subject_real": args.subject_real,
    ...
}
if args.label:                       # ← solo si se pasó --label
    entry["label"] = args.label      # interno, no circula
data.append(entry)
```

### Cambio 7 — Filtrar campos identificatorios del chart antes del LLM

En `_build_doctrinal_context`, antes de extraer datos, limpiar el dict:

```python
def _strip_identifying_fields(chart: dict) -> dict:
    """Elimina cualquier campo que pueda identificar al nativo antes de pasarlo al LLM."""
    import copy
    clean = copy.deepcopy(chart)
    
    # Campos de nivel raíz que pueden contener nombre o ciudad
    for field in ("name", "person", "subject_name", "birth_city", "city",
                  "birth_place", "location", "userName"):
        clean.pop(field, None)
    
    # También limpiar dentro de subcampos conocidos
    for subchart_key in ("chart", "derived", "extended"):
        subdict = clean.get(subchart_key, {})
        if isinstance(subdict, dict):
            for field in ("name", "person", "subject_name", "birth_city", "city"):
                subdict.pop(field, None)
    
    return clean

def _build_doctrinal_context(chart: dict, opaque_id: str) -> str:
    clean_chart = _strip_identifying_fields(chart)
    # resto del código usa clean_chart, no chart
    planets = clean_chart.get("chart", {}).get("planets", [])
    ...
```

---

## Migración de BV_001 existente

BV_001 fue creado manualmente con el archivo `BV_001_trump.md`.
El hash correcto para los datos de BV_001 es `NTV-206B`
(verificado: `sha256("1946-06-1410:5440.7128-74.006")[:4].upper() == "206B"`).

### Acciones de migración (hacer como parte del commit):

**1. Renombrar archivos:**
```bash
# data/blind_validation/
mv data/blind_validation/BV_001_trump.md data/blind_validation/BV_001_NTV-206B.md

# obsidian_vault/ (mismo cambio para consistencia):
mv obsidian_vault/03_experimentos/BV_001_trump.md \
   obsidian_vault/03_experimentos/BV_001_NTV-206B.md
```

**2. Actualizar `data/blind_validation/BV_index.json`:**

Cambiar la entrada de BV_001:
```json
{
  "id": "BV_001",
  "opaque_id": "NTV-206B",
  "label": "Caso público — carta de referencia",
  "subject_real": "Donald Trump",
  "rodden": "AA",
  "birth_date": "1946-06-14",
  "birth_time": "10:54",
  "lat": 40.7128,
  "lon": -74.006,
  "experiment_date": "2026-04-03",
  "verifier": "Guillermo Siaira",
  "status": "completed",
  "score": {
    "dimensions_passed": 4,
    "dimensions_total": 5,
    "validates": true
  },
  "file": "BV_001_NTV-206B.md",
  "obsidian_file": "obsidian_vault/03_experimentos/BV_001_NTV-206B.md",
  "notes": "Primera carta ciega completada. Score: 4/5. Archivo renombrado en BV-C02."
}
```

**Nota:** el campo `"birth_place"` se elimina del índice — la ubicación ya está
representada por `lat`/`lon`. No hay dato biográfico en texto libre que identifique.

---

## Archivos a modificar

- `scripts/blind_validation/run_blind_validation.py` — cambios 1-7 descritos arriba
- `data/blind_validation/BV_index.json` — migración BV_001

## Archivos a renombrar

- `data/blind_validation/BV_001_trump.md` → `data/blind_validation/BV_001_NTV-206B.md`
- `obsidian_vault/03_experimentos/BV_001_trump.md` → `obsidian_vault/03_experimentos/BV_001_NTV-206B.md`

## Archivos a NO modificar

- `scripts/blind_validation/bv_analyzer.py` — no usa `alias` directamente, lee markdown
- `scripts/blind_validation/doctrinal_evaluator.py` — no usa alias, analiza contenido doctrinal
- Cualquier archivo de Abu Engine o Next.js

---

## Verificación manual post-implementación

Correr el script con un sujeto de prueba y verificar:

```bash
cd d:/projects/ai-oracle
python scripts/blind_validation/run_blind_validation.py \
    --date 1879-03-14 --time 11:30 \
    --lat 48.4 --lon 10.0 \
    --label "Test Einstein" \
    --subject-real "Albert Einstein" \
    --rodden AA \
    --abu-url http://localhost:8000
```

**Checklist:**
- [ ] stdout muestra `id: NTV-XXXX` nunca `label: Test Einstein`
- [ ] archivo creado es `BV_002_NTV-XXXX.md` (no `BV_002_test_einstein.md`)
- [ ] dentro del .md, el header dice `╔══ CARTA NATAL — NTV-XXXX ══╗`
- [ ] `BV_index.json` tiene `"opaque_id": "NTV-XXXX"` y `"label": "Test Einstein"` separados
- [ ] el campo `label` NO aparece en ningún print de stdout
- [ ] `data/blind_validation/BV_001_trump.md` no existe (renombrado)
- [ ] `data/blind_validation/BV_001_NTV-206B.md` existe

---

## Criterios de aceptación

- [ ] Pasar `--label "cualquier cosa"` no filtra ese texto al LLM
- [ ] El contextBlock que recibe el LLM contiene `NTV-XXXX`, nunca el label ni subject_real
- [ ] Los filenames siguen el patrón `{BV_ID}_{NTV-XXXX}.md` siempre
- [ ] BV_001 correctamente migrado a `NTV-206B`
- [ ] `BV_index.json` válido (JSON parseable, sin campos `alias` legacy)
- [ ] Script corre sin errores con los datos de prueba de Einstein

---

## Lo que NO hace este spec

- **NO** modifica el protocolo doctrinal de evaluación (bv_analyzer, doctrinal_evaluator)
- **NO** cambia la estructura de las fichas .md más allá del header del contextBlock
- **NO** toca Next.js ni Abu Engine
- **NO** cambia cómo se registra `subject_real` (sigue en el índice — es el registro interno válido)

---

## Commit sugerido

```
fix(blind-validation): alias opaco obligatorio — BUG-10 (BV-C02)

- run_blind_validation.py: opaque_id siempre NTV-{hash}, --alias → --label interno
- _build_doctrinal_context: recibe opaque_id, filtra campos identificatorios del chart
- BV_001_trump.md → BV_001_NTV-206B.md (data/ + obsidian_vault/)
- BV_index.json: "alias" → "opaque_id", "label" separado, migración BV_001

Closes BUG-10: el LLM nunca recibe nombre, city ni label del nativo.
```
