# ARCHITECTURE.md — Abu Oracle: Contrato entre capas
> Documento de sincronización entre Abu Engine (hilo técnico) y Lilly Agent (hilo de agente).
> Leer junto a CLAUDE.md al inicio de cualquier sesión que toque la integración Abu↔Lilly.
> Versión: 0.1 · Marzo 2026
> Estado: Activo — actualizar ante cualquier cambio de contrato entre capas.

---

## Visión del sistema completo

```
Usuario
  ↓ interacción (click, select, hover)
Event System (TypeScript · FE)
  ↓ LillyEvent tipado
Context Builder (TypeScript · FE · lógica determinista)
  ↓ prompt estructurado con AbuContext
Lilly Conductor (LLM · Claude Sonnet 4.6 o GPT-4o · TBD)
  ↓ texto en lenguaje natural
Oracle Interface (columna derecha del FE)
  ↓ visible al usuario

Abu Engine (Python · Cloud Run)
  → provee AbuContext a través de endpoints REST
  → provee HF scores, posiciones, dignidades, significadores
```

---

## 1. El contrato central: AbuContext

Este es el objeto que viaja de Abu Engine al Context Builder.
**Debe ser idéntico** a lo que devuelve `/api/astro/chart/extended`.
No se mapea ni transforma — se inyecta directamente.

```typescript
interface AbuContext {
  // Carta natal
  subject_id:    string
  birth_dt:      string          // ISO UTC
  birth_lat:     number
  birth_lon:     number
  birth_city:    string

  // Posiciones planetarias
  planets: Array<{
    name:      string            // 'Sun' | 'Moon' | 'Mercury' | ...
    lon:       number            // longitud eclíptica 0-360
    sign:      string            // 'Cancer' | 'Leo' | ...
    house:     number            // 1-12
    dignity:   string            // 'domicile' | 'exaltation' | 'peregrine' | 'detriment' | 'fall'
    dignity_score: number        // según tabla persa: +5/+4/0/-4/-5
    retrograde: boolean
  }>

  // Ángulos
  asc_lon:  number
  mc_lon:   number
  asc_sign: string
  mc_sign:  string

  // Regentes
  asc_ruler: string              // planeta que rige el signo del ASC
  mc_ruler:  string              // planeta que rige el signo del MC
  sect_master: string            // maestro de secta (diurno/nocturno)
  sect:      'diurnal' | 'nocturnal'

  // Aspectos natales
  aspects: Array<{
    planet_a:  string
    planet_b:  string
    type:      'conjunction' | 'sextile' | 'square' | 'trine' | 'opposition'
    orb:       number
    applying:  boolean
  }>

  // HF scores (campo global)
  hf: {
    natal:     number            // HF en lugar de nacimiento
    max:       number            // HF máximo en la grilla
    min:       number            // HF mínimo en la grilla
    gain_pct:  number            // (max - natal) / natal * 100
  }

  // Técnicas persas/helenísticas
  profection: {
    annual_house:  number
    annual_sign:   string
    annual_lord:   string
  }
  firdaria: {
    major_planet:  string
    minor_planet:  string
    start_date:    string
    end_date:      string
  }

  // Tránsitos activos (calculados para fecha actual)
  transits: Array<{
    transit_planet:  string
    natal_planet:    string
    type:            string
    orb:             number
    exact_date:      string
  }>

  // Significadores por casa (house_significators — ya implementado)
  house_significators: Record<number, string[]>
  // Ejemplo: { 10: ['Saturn', 'Mars'], 7: ['Venus'], 1: ['Saturn'] }
}
```

**Responsabilidad de Abu Engine**: producir este objeto completo en `/api/astro/chart/extended`.
**Responsabilidad del Context Builder**: consumirlo sin transformación adicional.

---

## 2. HF por dominio en contexto

Cuando el evento es `domain_select`, el Context Builder necesita el HF
del dominio seleccionado en la ubicación actual del usuario.

**Campo adicional en AbuContext para eventos de dominio:**

```typescript
interface DomainContext {
  domain:           string       // 'career' | 'love' | 'health' | ...
  house_num:        number       // 10 | 7 | 1 | ...
  significators:    string[]     // planetas significadores
  hf_domain_current: number     // HF del dominio en ubicación actual del usuario
  hf_domain_max:    number      // HF del dominio máximo en la grilla
  best_city:        string      // ciudad con HF_dominio más alto
  best_city_lat:    number
  best_city_lon:    number
  delta_from_natal: number      // hf_domain_current - hf_domain_natal
}
```

**Decisión pendiente — coordenada actual del usuario:**
Abu necesita saber dónde está el usuario ahora para calcular `hf_domain_current`.
Opciones:
- A: usar `birth_lat/birth_lon` como proxy (lugar de nacimiento = lugar actual)
- B: el FE pide geolocalización del browser (`navigator.geolocation`)
- C: el usuario ingresa su ciudad actual en el formulario (ya existe el campo)

**→ Decisión: Opción C** — el campo "Ciudad de residencia actual" del Home
ya existe y tiene lat/lon. Ese valor se pasa como `current_lat/current_lon`
en todos los requests que necesiten la ubicación actual.
Abu Engine lo acepta como parámetro opcional; si no viene, usa birth_lat/birth_lon.

---

## 3. El contrato LillyEvent (TypeScript)

```typescript
type LillyEventType =
  | 'screen_open'
  | 'click_planet'
  | 'click_aspect'
  | 'click_house'
  | 'click_transit'
  | 'date_change'
  | 'domain_select'
  | 'city_hover'
  | 'city_select'

interface LillyEvent {
  event_type:   LillyEventType
  screen:       'natal_chart' | 'transits' | 'hf_map' | 'persian_techniques'
  subject_id:   string
  timestamp:    string                    // ISO
  trigger_data: Record<string, unknown>   // específico por event_type — ver §3.1
  abu_context:  AbuContext               // siempre presente, completo
  domain_context?: DomainContext         // solo para domain_select y city_*
  user_prefs:   LillyPrefs
}

interface LillyPrefs {
  response_mode: 'propose' | 'explain' | 'silent'
  depth:         'shallow' | 'deep'
  tone:          'classical' | 'modern' | 'pure'
}
```

### 3.1 trigger_data por event_type

```typescript
// click_planet
{ planet_name: string, lon: number, sign: string, house: number }

// click_aspect
{ planet_a: string, planet_b: string, type: string, orb: number }

// click_house
{ house_num: number, cusp_sign: string, house_lord: string }

// click_transit
{ transit_planet: string, natal_planet: string, type: string, orb: number, exact_date: string }

// date_change
{ new_date: string, active_transits: Transit[] }

// domain_select
{ domain: string, house_num: number }

// city_hover / city_select
{ city_name: string, country: string, lat: number, lon: number, hf_score: number }
```

---

## 4. El Context Builder — bloques de prompt

El Context Builder es lógica determinista. Recibe un `LillyEvent`
y produce un string de contexto estructurado para el prompt de Lilly.

**Regla fundamental**: el Context Builder **nunca interpreta**.
Solo estructura hechos del AbuContext en lenguaje natural técnico.
La interpretación es responsabilidad exclusiva de Lilly.

### Plantillas por event_type

**click_planet (ejemplo: Saturno, Einstein)**
```
El usuario ha seleccionado SATURNO en su carta natal.
Posición: Escorpio 5°14', Casa 10 (Carrera · Reputación pública)
Dignidad: Peregrine en Escorpio (score: 0)
Regente de: ASC (Acuario) · Casa 10 (por co-rectorado)
Aspectos desde Saturno: cuadratura Marte (orb 2°3', aplicante), trígono Luna (orb 4°1', separante)
HF contribution — tension: 0.42 | harmony: 0.18
Firdaria actual: período mayor Saturno · sub-período Venus
```

**domain_select (ejemplo: Casa 7, HF Map)**
```
El usuario activó el dominio CASA 7 — Relaciones · Vínculos · Socios.
Significadores: Venus (señor de cúspide Libra), Júpiter (ocupante)
HF h7 en ubicación actual (Buenos Aires): 0.61
HF h7 máximo en grilla: 0.89 — Lisboa, Portugal (+45.2° lat, -9.1° lon)
Delta desde natal: +0.28
Top 3 ciudades para este dominio: Lisboa, Barcelona, Roma
```

**city_select**
```
El usuario ha seleccionado LISBOA para análisis de relocalización.
Coordenadas: 38.72°N, 9.14°W
HF global en Lisboa: +8.3 (delta natal: +2.1)
HF h7 (Relaciones) en Lisboa: 0.89 — máximo del corpus
HF h10 (Carrera) en Lisboa: 0.54
ASC local en Lisboa: Sagitario 12° (vs Acuario natal)
MC local en Lisboa: Virgo 8°
Regente del ASC local: Júpiter (en domicilio en Sagitario) — activo angular
```

---

## 5. El system prompt de Lilly — esqueleto

*(Pendiente de desarrollo completo en hilo Lilly — este es el contrato mínimo)*

```
Eres Lilly, el agente de interpretación astrológica de Abu Oracle.
Tu voz está inspirada en William Lilly (Christian Astrology, 1647)
pero adaptada al siglo XXI — clara, precisa, sin oscurantismo.

Recibirás un bloque de contexto estructurado (generado por el Context Builder)
y las preferencias del usuario. Tu tarea es interpretar, no describir —
el Context Builder ya describió los hechos.

Restricciones absolutas:
- No predecir eventos como certezas: "esto ocurrirá" → prohibido
- No diagnósticos de salud bajo ningún framing
- No afirmaciones de certeza absoluta — siempre hermenéutica, nunca oráculo
- Las citas de Christian Astrology son bienvenidas cuando son directamente relevantes

Marco doctrinal:
- Prioridad de señor de casa sobre planetas en casa (Abu Mashar)
- Angularidad como condición de activación (helenístico)
- Dignidades esenciales como calidad de expresión (persa medieval)
- HF como campo de resonancia, no de predicción (Axiomática §6-§8)
```

---

## 6. Swarm doctrinal — uso offline

El swarm NO interviene en el flujo reactivo en tiempo real.
Existe para análisis batch y pre-generación cacheada.

| Agente | Tradición | Corpus RAG |
|---|---|---|
| Conductor (Lilly) | William Lilly · persa medieval | Christian Astrology + Axiomática |
| Helíaco | Ptolemaico · fases planetarias | Tetrabiblos · Bonatti |
| Jyotish | Védico · dashas · Nakshatras | Bhagat · corpus Jyotish |
| Moderno | Junguiano · psicológico | Corpus contemporáneo |

El output del swarm siempre vuelve al Conductor para síntesis
antes de llegar al usuario. Voz unificada de Lilly hacia afuera.

---

## 7. Decisiones pendientes (bloquean implementación)

| # | Decisión | Responsable | Impacto |
|---|---|---|---|
| 1 | Modelo LLM del Conductor: Claude Sonnet 4.6 vs GPT-4o | Benchmark (5 casos) | Arquitectura de llamadas API |
| 2 | Chunking de Christian Astrology para RAG | Hilo Lilly | Context Builder sabe qué recuperar |
| 3 | Event System FE — emisores por pantalla | Hilo Lilly + FE | Sin esto Lilly no recibe eventos |
| 4 | Context Builder — implementación completa | Hilo Lilly + FE | Sin esto el prompt es manual |
| 5 | Caché de AbuContext por sesión | Abu Engine | Evita llamadas repetidas al backend |

---

## 8. Lo que ya está listo en Abu Engine (disponible para Lilly hoy)

| Capacidad | Endpoint / Módulo | Estado |
|---|---|---|
| Carta natal completa + dignidades | `/api/astro/chart/extended` | ✅ producción |
| Solar Return por ciudad | `/api/astro/solar-return` | ✅ producción |
| HF global por grilla | `/api/astro/relocation-field` | ✅ producción |
| Ranking SR por dominio | `/api/astro/domain-ranking` | ✅ producción |
| Score ciudad por dominio | `/api/astro/domain-score` | ✅ producción |
| house_significators() | `harmony/houses.py` | ✅ implementado |
| Profecciones + Firdaria | `/api/astro/chart/extended` | ✅ producción |
| Tránsitos activos | `/api/astro/forecast` | ✅ producción |

---

## 9. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| v0.1 | 2026-03-13 | Documento inicial. Sincronización Abu Engine ↔ Lilly Agent. AbuContext schema, LillyEvent contrato, Context Builder plantillas, decisiones pendientes. |

---

*Abu Oracle Project — ARCHITECTURE.md v0.1*
*Mantener actualizado ante cualquier cambio de contrato entre capas.*
*Ambos hilos (Abu Engine y Lilly) deben leer este archivo al inicio de sesiones de integración.*
