# BV-C01 — Blind Validation Analyzer + Doctrinal Claim Evaluator

**Fecha:** 2026-05-05  
**Track:** Blind Validation / Research Publication  
**Prioridad:** Media — necesario para el paper pero no bloquea KG  
**Prerequisito:** BUG-10 fix ya completado (ver `specs/done/BUG10_bv_alias_leak.md`)  
**Independiente de:** KG-C01, KG-C02 — implementar en paralelo

---

## Objetivo

Dos herramientas de análisis para el corpus de experimentos de validación ciega:

1. **`bv_analyzer.py`** — Lee todos los experimentos completados, produce tabla resumen
   y CSV para análisis estadístico. Foundation del paper.

2. **`doctrinal_evaluator.py`** — Extrae afirmaciones de Capa 3 del texto de Lilly y las
   verifica contra los datos de Abu Engine. Produce un score de precisión doctrinal.

Estas dos herramientas juntas permiten producir la tabla central del paper BV:
| BV_ID | Score (0-5) | Precision doctrinal | Dominio | Tradición |

---

## Archivo 1: `scripts/blind_validation/bv_analyzer.py`

### CLI

```bash
python scripts/blind_validation/bv_analyzer.py
# lee data/blind_validation/BV_index.json
# lee data/blind_validation/BV_NNN_*.md
# escribe analysis/blind_validation_summary.md (tabla)
# escribe analysis/blind_validation_data.csv  (datos crudos)
```

### Estructura del código

```python
#!/usr/bin/env python3
"""
bv_analyzer.py — Analiza el corpus de experimentos de validación ciega.

Lee: data/blind_validation/BV_index.json
     data/blind_validation/BV_NNN_*.md
Escribe:
     analysis/blind_validation_summary.md
     analysis/blind_validation_data.csv
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT      = Path(__file__).resolve().parents[2]
INDEX_PATH     = REPO_ROOT / "data" / "blind_validation" / "BV_index.json"
BV_DATA_DIR    = REPO_ROOT / "data" / "blind_validation"
ANALYSIS_DIR   = REPO_ROOT / "analysis"
SUMMARY_PATH   = ANALYSIS_DIR / "blind_validation_summary.md"
CSV_PATH       = ANALYSIS_DIR / "blind_validation_data.csv"
```

### Función: `parse_bv_markdown`

```python
def parse_bv_markdown(md_path: Path) -> dict:
    """
    Extrae campos clave del markdown de un experimento BV.
    
    Campos que intenta extraer:
      - score (int 0-5): buscar patrón "Score: N/5" o "Score: N" en el texto
      - tradition (str): buscar "Tradición: X" o "tradition: X"
      - doctrinal_accuracy (float|None): buscar "Precisión doctrinal: N.NN" si existe
      - evaluator_notes (str): primer párrafo de la sección "## Verificación del operador"
      - lilly_response_length (int): len de la sección de respuesta de Lilly
      - has_verification (bool): si la sección de verificación fue completada
    
    Returns dict with those fields (None if not found).
    """
    text = md_path.read_text(encoding="utf-8")
    
    result: dict = {
        "score":                 None,
        "tradition":             None,
        "doctrinal_accuracy":    None,
        "evaluator_notes":       None,
        "lilly_response_length": 0,
        "has_verification":      False,
    }
    
    # Score: buscar "Score: N/5" o "Score: N" o "**Score:** N"
    score_match = re.search(r'[Ss]core[:\s*]+(\d)', text)
    if score_match:
        result["score"] = int(score_match.group(1))
    
    # Tradition
    trad_match = re.search(r'[Tt]radic[ió]n[:\s*]+([A-Za-záéíóú]+)', text)
    if trad_match:
        result["tradition"] = trad_match.group(1).lower()
    
    # Precisión doctrinal (si fue calculada por doctrinal_evaluator)
    prec_match = re.search(r'[Pp]recisi[oó]n\s+doctrinal[:\s*]+([0-9.]+)', text)
    if prec_match:
        result["doctrinal_accuracy"] = float(prec_match.group(1))
    
    # Sección de verificación del operador
    verif_match = re.search(
        r'##\s+Verificaci[oó]n del operador\s*\n+([\s\S]+?)(?:\n##|\Z)', text
    )
    if verif_match:
        verif_text = verif_match.group(1).strip()
        result["has_verification"] = len(verif_text) > 30  # no vacía
        result["evaluator_notes"]  = verif_text[:300]      # primeros 300 chars
    
    # Longitud de respuesta de Lilly
    lilly_match = re.search(
        r'##\s+Respuesta de Lilly\s*\n+([\s\S]+?)(?:\n##|\Z)', text
    )
    if lilly_match:
        result["lilly_response_length"] = len(lilly_match.group(1).strip())
    
    return result
```

### Función: `load_all_experiments`

```python
def load_all_experiments() -> list[dict]:
    """Carga todos los experimentos desde index + markdowns."""
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"BV index not found: {INDEX_PATH}")
    
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    experiments = index if isinstance(index, list) else index.get("experiments", [])
    
    results = []
    for exp in experiments:
        bv_id  = exp.get("id", "BV_???")
        alias  = exp.get("alias", "unknown")
        status = exp.get("status", "unknown")
        
        # buscar el markdown correspondiente
        md_files = list(BV_DATA_DIR.glob(f"{bv_id}_*.md"))
        if not md_files:
            # fallback: buscar por alias
            slug = alias.lower().replace(" ", "_").replace("-", "_")
            md_files = list(BV_DATA_DIR.glob(f"*{slug}*.md"))
        
        parsed = parse_bv_markdown(md_files[0]) if md_files else {}
        
        results.append({
            "id":                    bv_id,
            "alias":                 alias,
            "status":                status,
            "score":                 parsed.get("score"),
            "tradition":             parsed.get("tradition"),
            "doctrinal_accuracy":    parsed.get("doctrinal_accuracy"),
            "has_verification":      parsed.get("has_verification", False),
            "lilly_response_length": parsed.get("lilly_response_length", 0),
            "evaluator_notes":       parsed.get("evaluator_notes", ""),
        })
    
    return results
```

### Función: `write_summary_md`

```python
def write_summary_md(experiments: list[dict]) -> None:
    """Escribe analysis/blind_validation_summary.md con tabla de resultados."""
    ANALYSIS_DIR.mkdir(exist_ok=True)
    
    completed = [e for e in experiments if e["status"] == "completed"]
    pending   = [e for e in experiments if e["status"] != "completed"]
    
    # Estadísticas básicas
    scores = [e["score"] for e in completed if e["score"] is not None]
    mean_score = sum(scores) / len(scores) if scores else None
    
    prec_vals = [e["doctrinal_accuracy"] for e in completed 
                 if e["doctrinal_accuracy"] is not None]
    mean_prec = sum(prec_vals) / len(prec_vals) if prec_vals else None
    
    lines = [
        "# Blind Validation — Summary",
        f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        f"**Completed experiments:** {len(completed)} / {len(experiments)}",
        f"**Mean score (0-5):** {mean_score:.2f}" if mean_score else "**Mean score:** N/A",
        f"**Mean doctrinal accuracy:** {mean_prec:.2%}" if mean_prec else "**Mean doctrinal accuracy:** not yet computed",
        "",
        "## Results",
        "",
        "| ID | Alias | Score | Tradition | Doctrinal Acc | Notes |",
        "|---|---|---|---|---|---|",
    ]
    
    for e in completed:
        score_str = f"{e['score']}/5" if e["score"] is not None else "—"
        prec_str  = f"{e['doctrinal_accuracy']:.0%}" if e["doctrinal_accuracy"] is not None else "—"
        notes     = (e["evaluator_notes"] or "")[:80].replace("\n", " ")
        lines.append(
            f"| {e['id']} | {e['alias']} | {score_str} | {e['tradition'] or '—'} | {prec_str} | {notes} |"
        )
    
    if pending:
        lines += ["", "## Pending", ""]
        for e in pending:
            lines.append(f"- {e['id']} — {e['alias']} ({e['status']})")
    
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[bv_analyzer] Summary: {SUMMARY_PATH}")
```

### Función: `write_csv`

```python
def write_csv(experiments: list[dict]) -> None:
    """Escribe analysis/blind_validation_data.csv para análisis estadístico."""
    ANALYSIS_DIR.mkdir(exist_ok=True)
    fields = ["id", "alias", "status", "score", "tradition",
              "doctrinal_accuracy", "has_verification", "lilly_response_length"]
    
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(experiments)
    
    print(f"[bv_analyzer] CSV: {CSV_PATH}")
```

### Entry point

```python
if __name__ == "__main__":
    exps = load_all_experiments()
    write_summary_md(exps)
    write_csv(exps)
    
    completed = [e for e in exps if e["status"] == "completed"]
    print(f"[bv_analyzer] Done — {len(completed)} completed, {len(exps)-len(completed)} pending")
```

---

## Archivo 2: `scripts/blind_validation/doctrinal_evaluator.py`

### Propósito

Dado el texto de respuesta de Lilly y el JSON de Abu Engine, extrae afirmaciones de Capa 3
y las verifica automáticamente. Produce un score de precisión doctrinal.

### Afirmaciones verificables automáticamente

Las afirmaciones de Capa 3 más comunes que Lilly hace:

| Patrón textual | Qué verificar | Fuente de verdad |
|---|---|---|
| "X es el señor del año" / "X rige este año" | ¿Es X el señor de la profección activa? | `derived.profections[is_active].lord` |
| "X es el señor de la firdaria" / "período de X" | ¿Es X el mayor de firdaria activa? | `derived.firdaria[is_active].major_planet` |
| "X se encuentra en detrimento" / "X en caída" | ¿Coincide con la tabla de dignidades? | tabla `ESSENTIAL_DIGNITIES` |
| "la Parte de Fortuna está en Casa N" / "en signo Z" | ¿Coincide con `derived.lots.fortuna`? | `derived.lots.fortuna.house/sign` |
| "X ocupa la Casa N" | ¿Coincide con posición del planeta? | `chart.planets[X].house` |

### Estructura del código

```python
#!/usr/bin/env python3
"""
doctrinal_evaluator.py — Evalúa precisión doctrinal de respuestas de Lilly.

Extrae afirmaciones de Capa 3 del texto y las verifica contra abu_json.
"""
from __future__ import annotations

import re
from typing import Optional

# ── Tabla de dignidades esenciales (7 planetas tradicionales) ──────────────
ESSENTIAL_DIGNITIES = {
    "Sol":      {"domicilio": ["Leo"],     "exaltacion": ["Aries"],
                 "detrimento": ["Acuario"], "caida": ["Libra"]},
    "Luna":     {"domicilio": ["Cáncer"],  "exaltacion": ["Tauro"],
                 "detrimento": ["Capricornio"], "caida": ["Escorpio"]},
    "Mercurio": {"domicilio": ["Géminis","Virgo"], "exaltacion": ["Virgo"],
                 "detrimento": ["Sagitario","Piscis"], "caida": ["Piscis"]},
    "Venus":    {"domicilio": ["Tauro","Libra"], "exaltacion": ["Piscis"],
                 "detrimento": ["Aries","Escorpio"], "caida": ["Virgo"]},
    "Marte":    {"domicilio": ["Aries","Escorpio"], "exaltacion": ["Capricornio"],
                 "detrimento": ["Tauro","Libra"], "caida": ["Cáncer"]},
    "Júpiter":  {"domicilio": ["Sagitario","Piscis"], "exaltacion": ["Cáncer"],
                 "detrimento": ["Géminis","Virgo"], "caida": ["Capricornio"]},
    "Saturno":  {"domicilio": ["Capricornio","Acuario"], "exaltacion": ["Libra"],
                 "detrimento": ["Cáncer","Leo"], "caida": ["Aries"]},
}

# Nombres de planetas en español (para regex)
_PLANET_NAMES = list(ESSENTIAL_DIGNITIES.keys()) + ["Urano", "Neptuno", "Plutón"]
_PLANET_PATTERN = "|".join(_PLANET_NAMES)
```

### Función: `extract_doctrinal_claims`

```python
def extract_doctrinal_claims(response_text: str) -> list[dict]:
    """
    Extrae afirmaciones de Capa 3 del texto de Lilly.
    
    Returns list of dicts: { "type": str, "planet": str, "claim": str, "raw": str }
    """
    claims = []
    text   = response_text
    
    # Patrón 1: señor del año / señor del período
    for m in re.finditer(
        rf'({_PLANET_PATTERN})\s+(?:es\s+)?(?:el\s+)?señor\s+del\s+año',
        text, re.IGNORECASE
    ):
        claims.append({"type": "señor_del_año", "planet": _normalize(m.group(1)), "raw": m.group(0)})
    
    # Patrón 2: firdaria / fardaria / período planetario
    for m in re.finditer(
        rf'(?:período|firdaria|fardaria)\s+(?:de\s+|mayor\s+de\s+)?({_PLANET_PATTERN})',
        text, re.IGNORECASE
    ):
        claims.append({"type": "firdaria_mayor", "planet": _normalize(m.group(1)), "raw": m.group(0)})
    
    # Patrón 3: dignidades (X en detrimento/caída/domicilio/exaltación)
    for m in re.finditer(
        rf'({_PLANET_PATTERN})\s+(?:se\s+encuentra\s+)?(?:en\s+)?(detrimento|caída|domicilio|exaltación)',
        text, re.IGNORECASE
    ):
        claims.append({
            "type":    "dignidad",
            "planet":  _normalize(m.group(1)),
            "dignity": m.group(2).lower(),
            "raw":     m.group(0)
        })
    
    # Patrón 4: Parte de Fortuna en Casa N
    for m in re.finditer(
        r'(?:Parte\s+de\s+)?Fortuna\s+(?:está\s+)?en\s+Casa\s+(\d+)',
        text, re.IGNORECASE
    ):
        claims.append({"type": "fortuna_house", "house": int(m.group(1)), "raw": m.group(0)})
    
    # Patrón 5: X ocupa la Casa N (solo para planetas nombrados)
    for m in re.finditer(
        rf'({_PLANET_PATTERN})\s+(?:ocupa|está\s+en)\s+(?:la\s+)?Casa\s+(\d+)',
        text, re.IGNORECASE
    ):
        claims.append({
            "type":   "ocupa_casa",
            "planet": _normalize(m.group(1)),
            "house":  int(m.group(2)),
            "raw":    m.group(0)
        })
    
    return claims


def _normalize(planet_str: str) -> str:
    """Normaliza nombre de planeta (capitalización)."""
    mapping = {name.lower(): name for name in _PLANET_NAMES}
    return mapping.get(planet_str.lower(), planet_str)
```

### Función: `verify_claims`

```python
def verify_claims(claims: list[dict], abu_json: dict) -> list[dict]:
    """
    Verifica cada afirmación contra los datos de Abu Engine.
    
    Returns list de afirmaciones enriquecidas con campos:
      - "verified": bool | None (None = no verificable automáticamente)
      - "ground_truth": str — la respuesta correcta según Abu Engine
    """
    derived  = abu_json.get("derived", {})
    planets  = {p["name"]: p for p in abu_json.get("chart", {}).get("planets", [])}
    
    # Profección activa
    active_prof = next(
        (p for p in derived.get("profections", []) if p.get("is_active")), None
    )
    
    # Firdaria activa
    active_fird = next(
        (f for f in derived.get("firdaria", []) if f.get("is_active")), None
    )
    
    # Lote de Fortuna
    fortuna = derived.get("lots", {}).get("fortuna")
    
    results = []
    for claim in claims:
        c = dict(claim)
        c["verified"]     = None
        c["ground_truth"] = "N/A"
        
        if claim["type"] == "señor_del_año" and active_prof:
            truth = active_prof.get("lord", "?")
            c["ground_truth"] = truth
            c["verified"]     = claim["planet"] == truth
        
        elif claim["type"] == "firdaria_mayor" and active_fird:
            truth = active_fird.get("major_planet", "?")
            c["ground_truth"] = truth
            c["verified"]     = claim["planet"] == truth
        
        elif claim["type"] == "dignidad":
            planet  = claim["planet"]
            dignity = claim["dignity"]
            if planet in ESSENTIAL_DIGNITIES and planet in planets:
                sign = planets[planet]["sign"]
                digs = ESSENTIAL_DIGNITIES[planet]
                if dignity == "domicilio":
                    c["verified"]     = sign in digs.get("domicilio", [])
                    c["ground_truth"] = ", ".join(digs.get("domicilio", []))
                elif dignity == "exaltación":
                    c["verified"]     = sign in digs.get("exaltacion", [])
                    c["ground_truth"] = ", ".join(digs.get("exaltacion", []))
                elif dignity == "detrimento":
                    c["verified"]     = sign in digs.get("detrimento", [])
                    c["ground_truth"] = ", ".join(digs.get("detrimento", []))
                elif dignity in ("caída", "caida"):
                    c["verified"]     = sign in digs.get("caida", [])
                    c["ground_truth"] = ", ".join(digs.get("caida", []))
        
        elif claim["type"] == "fortuna_house" and fortuna:
            truth = fortuna.get("house", "?")
            c["ground_truth"] = str(truth)
            c["verified"]     = claim["house"] == truth
        
        elif claim["type"] == "ocupa_casa":
            planet = claim["planet"]
            if planet in planets:
                truth = planets[planet].get("house", "?")
                c["ground_truth"] = str(truth)
                c["verified"]     = claim["house"] == truth
        
        results.append(c)
    
    return results


def compute_precision(verified_claims: list[dict]) -> Optional[float]:
    """
    Computa precisión doctrinal: n_correctas / n_verificables.
    Retorna None si no hay afirmaciones verificables.
    """
    verifiable = [c for c in verified_claims if c["verified"] is not None]
    if not verifiable:
        return None
    correct = sum(1 for c in verifiable if c["verified"])
    return correct / len(verifiable)


def evaluate_response(response_text: str, abu_json: dict) -> dict:
    """
    Pipeline completo: texto → claims → verificación → precision.
    
    Returns:
    {
      "total_claims":      int,
      "verifiable_claims": int,
      "correct_claims":    int,
      "precision":         float | None,
      "details":           list[dict]
    }
    """
    claims   = extract_doctrinal_claims(response_text)
    verified = verify_claims(claims, abu_json)
    prec     = compute_precision(verified)
    
    verifiable = [c for c in verified if c["verified"] is not None]
    correct    = [c for c in verifiable if c["verified"]]
    
    return {
        "total_claims":      len(claims),
        "verifiable_claims": len(verifiable),
        "correct_claims":    len(correct),
        "precision":         prec,
        "details":           verified,
    }
```

### CLI de `doctrinal_evaluator.py`

```python
if __name__ == "__main__":
    import sys, json
    
    if len(sys.argv) < 3:
        print("Usage: python doctrinal_evaluator.py <lilly_response.txt> <abu_json.json>")
        sys.exit(1)
    
    response_text = Path(sys.argv[1]).read_text(encoding="utf-8")
    abu_json      = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    
    result = evaluate_response(response_text, abu_json)
    
    print(f"Total claims extracted:  {result['total_claims']}")
    print(f"Verifiable:              {result['verifiable_claims']}")
    print(f"Correct:                 {result['correct_claims']}")
    if result["precision"] is not None:
        print(f"Doctrinal precision:     {result['precision']:.1%}")
    else:
        print("Doctrinal precision:     N/A (no verifiable claims found)")
    
    print("\nDetails:")
    for c in result["details"]:
        status = "✓" if c["verified"] is True else ("✗" if c["verified"] is False else "?")
        print(f"  [{status}] {c['type']}: {c.get('planet', '')} — GT: {c['ground_truth']}")
        print(f"       Raw: \"{c['raw']}\"")
```

---

## Tests rápidos

```python
# test_doctrinal_evaluator.py
from scripts.blind_validation.doctrinal_evaluator import (
    extract_doctrinal_claims, verify_claims, compute_precision
)

SAMPLE_ABU = {
    "chart": {
        "planets": [
            {"name": "Sol",     "sign": "Piscis",  "house": 12, "degree": 12.3},
            {"name": "Júpiter", "sign": "Cáncer",  "house": 1,  "degree": 3.4},
            {"name": "Saturno", "sign": "Leo",     "house": 4,  "degree": 18.2},
        ]
    },
    "derived": {
        "profections": [{"house": 12, "sign": "Piscis", "lord": "Júpiter", "is_active": True}],
        "firdaria":    [{"major_planet": "Sol", "minor_planet": "Júpiter", "is_active": True}],
        "lots":        {"fortuna": {"sign": "Sagitario", "house": 6, "degree": 14.2}},
    }
}

def test_extract_señor_del_año():
    text = "Júpiter es el señor del año, dado que la profección recae en Casa 12."
    claims = extract_doctrinal_claims(text)
    assert any(c["type"] == "señor_del_año" and c["planet"] == "Júpiter" for c in claims)

def test_verify_señor_del_año_correct():
    claims = [{"type": "señor_del_año", "planet": "Júpiter", "raw": "..."}]
    result = verify_claims(claims, SAMPLE_ABU)
    assert result[0]["verified"] is True

def test_verify_señor_del_año_wrong():
    claims = [{"type": "señor_del_año", "planet": "Saturno", "raw": "..."}]
    result = verify_claims(claims, SAMPLE_ABU)
    assert result[0]["verified"] is False

def test_verify_dignidad_detrimento():
    # Saturno en Leo → detrimento (correcto)
    claims = [{"type": "dignidad", "planet": "Saturno", "dignity": "detrimento", "raw": "..."}]
    result = verify_claims(claims, SAMPLE_ABU)
    assert result[0]["verified"] is True

def test_compute_precision():
    verified = [
        {"verified": True},
        {"verified": True},
        {"verified": False},
        {"verified": None},  # no verificable
    ]
    assert abs(compute_precision(verified) - 2/3) < 0.01
```

---

## Cómo ejecutar

```bash
cd d:/projects/ai-oracle
source .venv311/Scripts/activate

# Analizar todos los experimentos existentes
python scripts/blind_validation/bv_analyzer.py

# Evaluar precisión doctrinal de un experimento
python scripts/blind_validation/doctrinal_evaluator.py \
    data/blind_validation/BV_001_mr_x.md \
    data/blind_validation/BV_001_abu_json.json
```

**Nota:** Si el JSON de Abu Engine no fue guardado durante el experimento, se puede
regenerar ejecutando `/analyze` con los datos natales del sujeto (disponibles en
`data/blind_validation/BV_index.json`).

---

## Criterios de aceptación

- [ ] `bv_analyzer.py` genera `analysis/blind_validation_summary.md` con tabla correcta para BV_001
- [ ] `bv_analyzer.py` genera `analysis/blind_validation_data.csv` con una fila por experimento
- [ ] `extract_doctrinal_claims` detecta al menos 3 tipos de afirmación (señor_año, firdaria, dignidad)
- [ ] `verify_claims` retorna `verified=True` para afirmaciones correctas, `False` para incorrectas
- [ ] `compute_precision` retorna `None` cuando no hay claims verificables (no lanza excepción)
- [ ] Todos los tests de `test_doctrinal_evaluator.py` pasan
- [ ] Script no requiere Abu Engine corriendo (solo lee JSON pre-generados)

---

## Lo que NO hace este spec

- **NO** modifica el pipeline de generación de experimentos (`run_blind_validation.py`)
- **NO** requiere Abu Engine corriendo para el análisis (solo lee archivos)
- **NO** implementa evaluación manual de afirmaciones complejas (multi-hop, contexto narrativo)
- **NO** modifica Firestore ni rutas de producción

---

## Commit sugerido

```
feat(bv): BV analyzer + doctrinal claim evaluator (BV-C01)

- scripts/blind_validation/bv_analyzer.py: reads BV index + markdowns,
  produces analysis/blind_validation_summary.md and _data.csv
- scripts/blind_validation/doctrinal_evaluator.py: regex extractor for
  Layer 3 claims (señor del año, firdaria, dignidades, lots, casa) +
  verifier against abu_json ground truth + precision score
- tests/test_doctrinal_evaluator.py: 5 unit tests
```

---

## Referencias

- `data/blind_validation/BV_index.json` — índice de experimentos
- `data/blind_validation/BV_001_*.md` — primer experimento completado (referencia de formato)
- `docs/theory/KG_EXPERIMENT_PROTOCOL.md` § Métricas — sección "Precisión doctrinal"
- `specs/done/BUG10_bv_alias_leak.md` — prerequisito completado
