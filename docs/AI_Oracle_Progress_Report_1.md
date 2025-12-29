# AI Oracle - Progress Report 1

## Endpoints Implementados

### Abu Engine (`abu_engine/main.py`)

#### 1. `/api/astro/forecast` (GET)
- **Función:** Calcula una serie temporal de scores astrológicos entre dos fechas, detecta picos y valles.
- **Parámetros:** `birthDate`, `lat`, `lon`, `start`, `end`, `step`, `horizon`.
- **Respuesta:**
  ```json
  {
    "timeseries": [{"t": "2026-01-01", "F": 0.23}, ...],
    "peaks": [{"t": "2026-08-12", "F": 0.89, "kind": "peak"}, ...]
  }
  ```
- **Estado:** Implementado y funcional.

#### 2. `/api/astro/chart` (GET)
- **Función:** Calcula la carta astral para una fecha y ubicación, devuelve posiciones planetarias y aspectos.
- **Parámetros:** `date`, `lat`, `lon`.
- **Respuesta:**
  ```json
  {
    "datetime": "...",
    "location": {"lat":..,"lon":..},
    "planets": [{"name":"Sun","lon":103.12,"sign":"Cancer","house":null}, ...],
    "aspects": [{"a":"Sun","b":"Mars","type":"square","orb":1.2,"angle":90}]
  }
  ```
- **Estado:** Implementado y funcional.

#### 3. `/api/astro/life-cycles` (GET)
- **Función:** Detecta ciclos mayores de planetas lentos (retornos, oposiciones, cuadraturas) desde la fecha de nacimiento.
- **Parámetros:** `birthDate` (ISO).
- **Respuesta:**
  ```json
  {
    "astro_data": {
      "events": [
        {"cycle": "Saturn Return", "planet": "Saturn", "angle": 0, "approx": "2007-07-15"},
        ...
      ]
    },
    "interpretation": {
      "headline": "Madurez, responsabilidad y nuevos comienzos.",
      "narrative": "Palabras clave: disciplina, cambio, crecimiento. Tono: introspectivo",
      "actions": ["Reflexiona sobre: disciplina", "Reflexiona sobre: cambio", "Reflexiona sobre: crecimiento"],
      "astro_metadata": {"events": 1, "matched_cycle": "Saturn Return", "tone": "introspectivo"}
    }
  }
  ```
- **Estado:** Implementado, integrado con Lilly Engine para interpretación automática.

### Lilly Engine (`lilly_engine/main.py`)

#### 1. `/api/ai/interpret` (POST)
- **Función:** Recibe datos astrológicos (de Abu) y genera una interpretación basada en arquetipos definidos en `archetypes.json`.
- **Entrada:** JSON con claves como `events`, `planets`, `aspects`, `timeseries`, `peaks`.
- **Respuesta:**
  ```json
  {
    "headline": "Madurez, responsabilidad y nuevos comienzos.",
    "narrative": "Palabras clave: disciplina, cambio, crecimiento. Tono: introspectivo",
    "actions": ["Reflexiona sobre: disciplina", "Reflexiona sobre: cambio", "Reflexiona sobre: crecimiento"],
    "astro_metadata": {"events": 1, "matched_cycle": "Saturn Return", "tone": "introspectivo"}
  }
  ```
- **Estado:** Implementado, responde con datos dummy o arquetipos según coincidencia.

### Estado General
- Todos los endpoints principales están implementados y funcionales.
- La integración entre Abu y Lilly está activa vía HTTP POST.
- Las respuestas de interpretación se personalizan según los arquetipos definidos.
- El sistema está listo para pruebas de integración y ampliación de lógica interpretativa.
