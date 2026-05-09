# KG-C02 — NetworkX Chart Graph Builder (Fase 1 del KG)

**Fecha:** 2026-05-05  
**Track:** Knowledge Graph  
**Prioridad:** Alta — núcleo de la Fase 1 del GraphRAG (in-memory, sin persistencia)  
**Independiente de:** KG-C01, BV-C01 — implementar en paralelo

---

## Objetivo

Construir la carta natal como un `NetworkX DiGraph` en memoria al momento de interpretación.
Hacer traversal del subgrafo relevante para los planetas clave activos. Serializar ese subgrafo
a texto estructurado para pasarlo a Lilly como hechos afirmados, no como inferencias.

Esto es la **Condición B** del experimento A/B: en vez del JSON plano de la carta, Lilly
recibe el subgrafo instanciado con las relaciones de Capa 3 ya computadas.

**Referencia arquitectónica:** `docs/theory/GRAPHRAG_KG_VISION.md` § Fase 1 y § 2.

---

## Archivo a crear: `abu_engine/core/chart_graph.py`

### Dependencias

```python
# requirements.txt ya tiene networkx — verificar. Si no:
# agregar: networkx>=3.3
import networkx as nx
from typing import Optional
```

### Función 1: `build_chart_graph`

```python
def build_chart_graph(abu_json: dict) -> nx.DiGraph:
    """
    Construye un DiGraph de la carta natal desde el JSON de /analyze.
    
    Capas implementadas:
      Capa 1 — Entidades: planetas, signos, casas, lotes
      Capa 2 — Relaciones estáticas: ocupa, aspecto, rige (domicilio/exaltación)
      Capa 3 — Relaciones derivadas: señor_ASC, señor_MC, señor_del_año,
                firdaria_mayor, firdaria_menor, señor_Fortuna, señor_Espíritu
    
    Args:
        abu_json: respuesta completa del endpoint /analyze de Abu Engine.
                  Campos esperados: chart.planets, chart.houses, derived.profections,
                  derived.firdaria, derived.lots, chart.aspects (si existe).
    
    Returns:
        nx.DiGraph con nodos tipados y aristas etiquetadas.
    """
```

#### Construcción del grafo

**Nodos de planetas** (desde `abu_json["chart"]["planets"]`):

```python
for p in planets:
    G.add_node(p["name"], 
               type="planet",
               sign=p["sign"],
               house=p["house"],
               degree=p["degree"],
               dignity=p.get("dignity", "peregrine"),
               retrograde=p.get("retrograde", False),
               longitude=p.get("longitude", 0.0))
```

Planetas esperados: `Sol, Luna, Mercurio, Venus, Marte, Júpiter, Saturno, Urano, Neptuno, Plutón`

**Nodos de casas** (desde `abu_json["chart"]["houses"]`):

```python
for h in houses:
    G.add_node(f"Casa{h['house']}", 
               type="house",
               sign=h["sign"],
               cusp_degree=h.get("degree", 0.0))
```

**Aristas `ocupa`** (planeta → casa):

```python
G.add_edge(planet_name, f"Casa{planet_house}", 
           relation="ocupa",
           degree=planet_degree)
```

**Aristas `aspecto`** (planeta ↔ planeta):

Si `abu_json["chart"].get("aspects")` existe, iterar:
```python
G.add_edge(a["planet_a"], a["planet_b"],
           relation="aspecto",
           type=a["type"],       # "trine", "square", "conjunction", etc.
           orb=a["orb"],
           applying=a.get("applying", False))
# también la dirección inversa (arista bidireccional):
G.add_edge(a["planet_b"], a["planet_a"],
           relation="aspecto",
           type=a["type"],
           orb=a["orb"],
           applying=a.get("applying", False))
```

Si no existe `aspects` en el JSON, omitir silenciosamente (no lanzar error).

**Capa 2 — Dignidades (aristas `rige`):**

Tabla de domicilios tradicionales (7 planetas, sin transpersonales):
```python
DOMICILIOS = {
    "Sol":     ["Leo"],
    "Luna":    ["Cancer"],
    "Mercurio":["Géminis", "Virgo"],
    "Venus":   ["Tauro", "Libra"],
    "Marte":   ["Aries", "Escorpio"],
    "Júpiter": ["Sagitario", "Piscis"],
    "Saturno": ["Capricornio", "Acuario"],
}
```

Para cada entrada, agregar nodo de signo y arista:
```python
G.add_node(sign_name, type="sign")
G.add_edge(planet_name, sign_name,
           relation="rige",
           type="domicilio",
           tradition="hellenistic")
```

**Capa 3 — Relaciones derivadas:**

Desde `abu_json["derived"]` si existe el campo:

```python
derived = abu_json.get("derived", {})

# ASC lord
asc_lord = abu_json["chart"]["houses"][0].get("lord")  # o extraer de derived
if asc_lord:
    G.add_edge(asc_lord, "Casa1", relation="señor_ASC")

# MC lord
mc_lord = abu_json["chart"]["houses"][9].get("lord")   # casa 10 = índice 9
if mc_lord:
    G.add_edge(mc_lord, "Casa10", relation="señor_MC")

# Profección activa
prof = next((p for p in derived.get("profections", []) if p.get("is_active")), None)
if prof and prof.get("lord"):
    G.add_edge(prof["lord"], f"Casa{prof['house']}",
               relation="señor_del_año",
               house=prof["house"],
               sign=prof["sign"],
               date_end=prof.get("date_end", ""))

# Firdaria activa
fird = next((f for f in derived.get("firdaria", []) if f.get("is_active")), None)
if fird:
    G.add_edge(fird["major_planet"], "firdaria_node",
               relation="firdaria_mayor",
               date_end=fird.get("date_end", ""))
    if fird.get("minor_planet") and fird["minor_planet"] != fird["major_planet"]:
        G.add_edge(fird["minor_planet"], "firdaria_node",
                   relation="firdaria_menor",
                   date_end=fird.get("date_end", ""))

# Lotes
lots = derived.get("lots", {})
for lot_key, lot_data in lots.items():
    lot_lord = lot_data.get("lord")
    if lot_lord:
        G.add_edge(lot_lord, f"Lote_{lot_key}",
                   relation=f"señor_{lot_key}",
                   lot_sign=lot_data.get("sign", ""),
                   lot_house=lot_data.get("house", 0))
```

**Nota sobre `lord` de ASC/MC:** Si el JSON de /analyze no incluye `lord` en los datos
de casas, derivarlo desde la tabla `DOMICILIOS` usando el signo de la cúspide:

```python
def _sign_lord(sign: str) -> Optional[str]:
    for planet, signs in DOMICILIOS.items():
        if sign in signs:
            return planet
    return None
```

---

### Función 2: `get_key_planets`

```python
def get_key_planets(G: nx.DiGraph, derived: dict) -> list[str]:
    """
    Retorna lista de planetas clave para el contexto activo del nativo.
    Son los planetas cuyas relaciones de Capa 3 Lilly necesita conocer.
    
    Orden de prioridad (sin duplicados):
      1. Señor del año (profección activa)
      2. Firdaria mayor
      3. Firdaria menor
      4. Señor ASC
      5. Señor MC
      6. Señor de Fortuna
      7. Señor de Espíritu
    """
    key = []
    
    # Helper: primer nodo con arista de tipo 'relation' saliente
    def _lord_of(relation: str) -> Optional[str]:
        for u, v, d in G.edges(data=True):
            if d.get("relation") == relation:
                return u
        return None
    
    prof    = next((p for p in derived.get("profections", []) if p.get("is_active")), None)
    fird    = next((f for f in derived.get("firdaria",    []) if f.get("is_active")), None)
    
    candidates = [
        prof["lord"] if prof else None,
        fird["major_planet"] if fird else None,
        fird["minor_planet"] if fird and fird.get("minor_planet") else None,
        _lord_of("señor_ASC"),
        _lord_of("señor_MC"),
        _lord_of("señor_fortuna"),
        _lord_of("señor_spirit"),
    ]
    
    seen = set()
    for c in candidates:
        if c and c not in seen and G.has_node(c):
            key.append(c)
            seen.add(c)
    
    return key
```

---

### Función 3: `serialize_subgraph`

```python
def serialize_subgraph(G: nx.DiGraph, key_planets: list[str]) -> str:
    """
    Serializa el subgrafo relevante a texto estructurado para Lilly.
    
    Formato de salida (compatible con _buildDerivedRelationsBlock en context-builder.ts):
    
        SEÑORÍOS ACTIVOS (KG)
        Jupiter [Exaltation · Cáncer 3.4° · Casa 1]
          → señor_ASC → Casa 1 (Cáncer)
          → firdaria_mayor · período completo hasta 2028-04-05
          → trine → Sol (2.1°) ↑
        Sol [Domicilio · Leo 21.3° · Casa 2]
          → señor_del_año → Casa 2 (Leo) · hasta 2026-07-05
    
    Si key_planets está vacío, retorna string vacío.
    """
    if not key_planets:
        return ""
    
    lines = ["SEÑORÍOS ACTIVOS (KG)"]
    
    for planet in key_planets:
        if not G.has_node(planet):
            continue
        
        node = G.nodes[planet]
        dignity   = node.get("dignity", "peregrine").capitalize()
        sign      = node.get("sign", "?")
        deg       = node.get("degree", 0.0)
        house     = node.get("house", 0)
        retrograde = " ℞" if node.get("retrograde") else ""
        
        lines.append(f"{planet} [{dignity} · {sign} {deg:.1f}° · Casa {house}{retrograde}]")
        
        # Capa 3 — relaciones derivadas salientes
        for _, target, edge in G.out_edges(planet, data=True):
            rel = edge.get("relation", "")
            
            if rel == "señor_ASC":
                target_sign = G.nodes.get(target, {}).get("sign", "")
                lines.append(f"  → señor_ASC → {target} ({target_sign})")
            
            elif rel == "señor_MC":
                target_sign = G.nodes.get(target, {}).get("sign", "")
                lines.append(f"  → señor_MC → {target} ({target_sign})")
            
            elif rel == "señor_del_año":
                date_end = edge.get("date_end", "?")
                target_sign = edge.get("sign", "")
                lines.append(f"  → señor_del_año → {target} ({target_sign}) · hasta {date_end}")
            
            elif rel == "firdaria_mayor":
                date_end = edge.get("date_end", "?")
                lines.append(f"  → firdaria_mayor · período hasta {date_end}")
            
            elif rel == "firdaria_menor":
                date_end = edge.get("date_end", "?")
                lines.append(f"  → firdaria_menor · hasta {date_end}")
            
            elif rel.startswith("señor_"):
                lot_name = rel.replace("señor_", "")
                lot_sign = edge.get("lot_sign", "")
                lot_house = edge.get("lot_house", 0)
                lines.append(f"  → {rel} → [{lot_sign} · Casa {lot_house}]")
        
        # Aspectos (top 3 por orbe)
        aspects = [
            (target, edge) 
            for _, target, edge in G.out_edges(planet, data=True) 
            if edge.get("relation") == "aspecto"
        ]
        aspects.sort(key=lambda x: x[1].get("orb", 99))
        
        for target, edge in aspects[:3]:
            aspect_type = edge.get("type", "")
            orb         = edge.get("orb", 0.0)
            app_marker  = " ↑" if edge.get("applying") else ""
            lines.append(f"  → {aspect_type} → {target} ({orb:.1f}°{app_marker})")
    
    return "\n".join(lines)
```

---

## Archivo a crear: `abu_engine/tests/test_chart_graph.py`

```python
"""Tests para chart_graph.py usando carta de prueba (Einstein o Guillermo)."""
import pytest
from abu_engine.core.chart_graph import build_chart_graph, get_key_planets, serialize_subgraph

# Carta mínima de prueba (estructura similar al JSON de /analyze)
SAMPLE_CHART_JSON = {
    "chart": {
        "planets": [
            {"name": "Sol",     "sign": "Piscis",    "house": 12, "degree": 12.3, "longitude": 342.3},
            {"name": "Júpiter", "sign": "Cáncer",    "house": 1,  "degree": 3.4,  "longitude": 93.4,
             "dignity": "exaltation"},
            {"name": "Saturno", "sign": "Leo",       "house": 4,  "degree": 18.2, "longitude": 138.2,
             "dignity": "detriment"},
        ],
        "houses": [
            {"house": 1,  "sign": "Cáncer",     "degree": 1.2},
            {"house": 10, "sign": "Aries",      "degree": 5.6},
        ],
        "aspects": [
            {"planet_a": "Sol", "planet_b": "Júpiter", "type": "sextile", "orb": 2.1, "applying": True},
        ]
    },
    "derived": {
        "profections": [{"house": 12, "sign": "Piscis", "lord": "Júpiter", "is_active": True,
                         "date_end": "2026-07-05"}],
        "firdaria": [{"major_planet": "Sol", "minor_planet": "Júpiter", "is_active": True,
                      "date_end": "2026-04-05"}],
        "lots": {
            "fortuna": {"sign": "Sagitario", "house": 6, "degree": 14.2, "lord": "Júpiter"},
        }
    }
}

def test_build_chart_graph_nodes():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    assert G.has_node("Sol")
    assert G.has_node("Júpiter")
    assert G.has_node("Casa1")

def test_build_chart_graph_ocupa_edges():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    assert G.has_edge("Sol", "Casa12")
    assert G.has_edge("Júpiter", "Casa1")

def test_build_chart_graph_layer3_profection():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    # Júpiter es señor del año (profección Casa 12 = Piscis → señor Júpiter)
    prof_edges = [(u, v, d) for u, v, d in G.edges(data=True) 
                  if d.get("relation") == "señor_del_año"]
    assert len(prof_edges) >= 1
    assert any(u == "Júpiter" for u, v, d in prof_edges)

def test_get_key_planets():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    key = get_key_planets(G, SAMPLE_CHART_JSON["derived"])
    # Júpiter debe aparecer (es señor del año + firdaria menor + señor Fortuna)
    assert "Júpiter" in key
    # Sol debe aparecer (firdaria mayor)
    assert "Sol" in key

def test_serialize_subgraph_not_empty():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    key = get_key_planets(G, SAMPLE_CHART_JSON["derived"])
    text = serialize_subgraph(G, key)
    assert "SEÑORÍOS ACTIVOS" in text
    assert "Júpiter" in text
    assert "señor_del_año" in text

def test_serialize_subgraph_empty_key():
    G = build_chart_graph(SAMPLE_CHART_JSON)
    assert serialize_subgraph(G, []) == ""
```

---

## Endpoint opcional para testing: `POST /api/astro/chart-graph`

Agregar en `abu_engine/main.py` (solo para verificación durante desarrollo):

```python
@app.post("/api/astro/chart-graph")
async def chart_graph_endpoint(request: Request):
    """
    Dev-only endpoint: recibe el JSON de /analyze y retorna el subgrafo serializado.
    Permite verificar el output antes de pasarlo a Lilly.
    """
    abu_json = await request.json()
    from core.chart_graph import build_chart_graph, get_key_planets, serialize_subgraph
    G   = build_chart_graph(abu_json)
    key = get_key_planets(G, abu_json.get("derived", {}))
    return {"key_planets": key, "subgraph": serialize_subgraph(G, key)}
```

Este endpoint NO requiere auth (solo dev) — si AUTH_ENABLED=true, marcar como excluido
del middleware de auth o protegerlo con el mismo patrón.

---

## Cómo correr los tests

```bash
cd d:/projects/ai-oracle
source .venv311/Scripts/activate
python -m pytest abu_engine/tests/test_chart_graph.py -v
```

Todos deben pasar. Si hay `ImportError` de networkx:
```bash
pip install networkx
```

---

## Criterios de aceptación

- [ ] `build_chart_graph` retorna un DiGraph con nodos para todos los planetas del JSON
- [ ] Aristas `ocupa` conectan cada planeta con su casa natal
- [ ] Aristas `aspecto` conectan pares de planetas (bidireccional)
- [ ] Aristas Capa 3 (señor_del_año, firdaria_mayor, señor_ASC, etc.) presentes cuando el campo existe en `derived`
- [ ] `serialize_subgraph` produce texto legible con el formato definido arriba
- [ ] `serialize_subgraph(G, [])` retorna `""` sin error
- [ ] Todos los tests de `test_chart_graph.py` pasan con `pytest -v`
- [ ] Si `aspects` no está en el JSON, no lanza excepción

---

## Lo que NO hace este spec

- **NO** persiste el grafo en base de datos (eso es Fase 3)
- **NO** modifica las rutas de Lilly para usar el subgrafo (eso es KG-C05)
- **NO** crea el endpoint `/api/astro/chart-graph` en producción (solo dev/test)
- **NO** implementa Urano/Neptuno/Plutón en la tabla de domicilios (no tienen en doctrina tradicional)

---

## Commit sugerido

```
feat(kg): NetworkX chart graph builder — Fase 1 GraphRAG (KG-C02)

- core/chart_graph.py: build_chart_graph(), get_key_planets(), serialize_subgraph()
- Capa 1: nodos planeta/casa/signo desde abu_json
- Capa 2: aristas ocupa, aspecto, rige (domicilios tradicionales 7 planetas)
- Capa 3: señor_del_año, firdaria_mayor/menor, señor_ASC/MC, señor_Fortuna/Espíritu
- tests/test_chart_graph.py: 6 tests, carta de prueba mínima
- main.py: dev endpoint POST /api/astro/chart-graph para inspección
```

---

## Referencias

- `docs/theory/GRAPHRAG_KG_VISION.md` — visión arquitectónica, Fase 1
- `docs/theory/KG_ONTOLOGY_SCHEMA.md` — schema completo Capas 1-3
- `docs/theory/KG_EXPERIMENT_PROTOCOL.md` — contexto del experimento
- `next_app/lib/context-builder.ts` → `_buildDerivedRelationsBlock()` — formato de output equivalente ya en producción
- `abu_engine/core/lots.py` — tabla SIGN_LORDS existente (puede reemplazar DOMICILIOS si coincide)
