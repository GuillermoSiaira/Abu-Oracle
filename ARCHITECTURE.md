# ARCHITECTURE.md — Abu Oracle: Contrato entre capas
> Documento de sincronización entre Abu Engine (hilo técnico) y Lilly Agent (hilo de agente).
> Leer junto a CLAUDE.md al inicio de cualquier sesión que toque la integración Abu↔Lilly.
> Versión: 0.2 · Marzo 2026
> Estado: Activo — actualizar ante cualquier cambio de contrato entre capas.

---

## Visión del sistema completo

```
Usuario
  ↓ interacción (click, select, hover)
Event System (TypeScript · FE)
  ↓ LillyEvent tipado
Route Handler ad-hoc (TypeScript · Next.js API Routes)  ← Context Builder centralizado pendiente (Fase 9)
  ↓ contextBlock estructurado + LILLY_SYSTEM_PROMPT
Lilly Conductor (Claude Sonnet 4.6 · confirmado en producción)
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

  // Significadores por casa (house_significators — implementado)
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

### Estado actual de disponibilidad de datos (post Fase 8.11)

| Campo | Disponible en domain_select | Observación |
|---|---|---|
| `significators` | ✅ | Derivados client-side con `deriveSignificators()` |
| `hf_domain_current` | ❌ | Fetch del campo de dominio llega después del event |
| `hf_domain_max` | ❌ | Ídem |
| `best_city` | ❌ | `data.rankings[0]` es global, no por dominio |

**Decisión vigente**: campos no disponibles se omiten del contextBlock (no se envían como `null` ni `"—"`). Lilly interpreta mejor la ausencia que un placeholder engañoso.

### `deriveSignificators()` — implementación client-side

```typescript
function deriveSignificators(
  houseNum: number,
  planets: Array<{ name: string; house: number }>,
  houseCusps: Array<{ house: number; start: number }>
): string[] {
  const SIGN_LORDS: Record<string, string> = {
    Aries: 'Mars', Taurus: 'Venus', Gemini: 'Mercury', Cancer: 'Moon',
    Leo: 'Sun', Virgo: 'Mercury', Libra: 'Venus', Scorpio: 'Mars',
    Sagittarius: 'Jupiter', Capricorn: 'Saturn', Aquarius: 'Saturn',
    Pisces: 'Jupiter'
  };
  const SIGNS = [
    'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
    'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
  ];
  const cusp = houseCusps.find(h => h.house === houseNum);
  const cuspSign = cusp ? SIGNS[Math.floor(cusp.start / 30) % 12] : null;
  const lord = cuspSign ? SIGN_LORDS[cuspSign] : null;
  const occupants = planets.filter(p => p.house === houseNum).map(p => p.name);
  const result = lord ? [lord, ...occupants.filter(p => p !== lord)] : occupants;
  return result;
}
```

### Coordenada actual del usuario
**Decisión: Opción C** — el campo "Ciudad de residencia actual" del Home
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
  | 'click_transit'      // ✅ implementado Fase 8.11
  | 'date_change'
  | 'domain_select'      // ✅ implementado Fase 8.10
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
// click_planet (pendiente)
{ planet_name: string, lon: number, sign: string, house: number }

// click_aspect (pendiente)
{ planet_a: string, planet_b: string, type: string, orb: number }

// click_house (pendiente)
{ house_num: number, cusp_sign: string, house_lord: string }

// click_transit ✅ implementado
{
  transit_planet: string
  transit_sign:   string
  transit_deg:    number
  aspects: Array<{ natal_planet: string, aspect: string, orb: number, applying: boolean }>
  transit_date:   string
  subject_name:   string
  lang:           string
}

// date_change (pendiente)
{ new_date: string, active_transits: Transit[] }

// domain_select ✅ implementado
{
  domain:       string
  house_num:    number
  subject_name: string
  significators: string[]
  hf_current:   null          // no disponible en este momento del flujo
  hf_max:       null          // ídem
  best_city:    null          // ídem
  lang:         string
  sr_year?:     number        // solo para Solar Return
}

// city_hover / city_select (pendiente)
{ city_name: string, country: string, lat: number, lon: number, hf_score: number }
```

---

## 4. Routes de Lilly implementadas (Context Builder ad-hoc)

> El Context Builder centralizado (ARCHITECTURE.md §4 original) está pendiente para Fase 9.
> Actualmente cada route construye su propio contextBlock.
> **Regla de contextBlock**: omitir líneas con valores null — no usar "—" ni placeholders.

| Route | Event | Estado | max_tokens |
|---|---|---|---|
| `/api/lilly/screen-open` | `screen_open` | ✅ Fase 8.10 | 512 |
| `/api/lilly/technique` | `click_technique` | ✅ Fase 8.10 | 512 |
| `/api/lilly/domain` | `domain_select` (natal) | ✅ Fase 8.11 | 1024 |
| `/api/lilly/solar-return` | `domain_select` (SR) | ✅ Fase 8.11 | 1024 |
| `/api/lilly/transit` | `click_transit` | ✅ Fase 8.11 | 1024 |
| `/api/lilly/planet` | `click_planet` | ✅ Fase 8.6 | 512 |
| `/api/lilly/city` | `city_select` | ✅ Fase 8.7 | 768 |
| `/api/lilly/chat` | input libre usuario | ✅ existente | 1024 |

### Plantilla contextBlock — click_transit

```
El usuario seleccionó SATURNO en tránsito — actualmente en Aries 3.3°.
Aspectos activos de este tránsito:
- Trígono a Mercurio natal (orb 2.11°, aplicante)
Fecha de tránsito: 16/03/2026
Sujeto: Guillermo Siaira
Idioma de respuesta: es
```

### Plantilla contextBlock — domain_select

```
El usuario activó el dominio CARRERA — Casa 10.
Sujeto: Guillermo Siaira
Significadores de la casa: Mars, Neptune
Idioma de respuesta: es
```

### Plantilla contextBlock — domain_select Solar Return

```
El usuario activó el dominio CARRERA — Casa 10 en el contexto del Retorno Solar 2026.
Sujeto: Guillermo Siaira
Significadores de la casa: Mars, Neptune
Idioma de respuesta: es
```

---

## 5. El system prompt de Lilly

Implementado en `next_app/lib/lilly-prompt.ts` como `LILLY_SYSTEM_PROMPT`.

Secciones activas:
- Identidad y voz (William Lilly · siglo XXI)
- Restricciones absolutas (no predicciones como certezas, no diagnósticos)
- Marco doctrinal (Abu Mashar, helenístico, persa medieval)
- **JEEVA/SAREERA PRINCIPLE** (Jyotish · Bhagat)
- **HARMONY FIELD — QUÉ ES Y CÓMO INTERPRETARLO** ✅ agregado Fase 8.11

El HF está definido en el system prompt con fórmula, valores, Delta HF,
interpretación doctrinal y referencia a validación empírica (527 eventos, Cohen's d≈0.44).
Lilly no dice que no tiene información sobre el HF.

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

## 7. Decisiones — estado actualizado

| # | Decisión | Estado | Resolución |
|---|---|---|---|
| 1 | Modelo LLM del Conductor | ✅ Resuelto | Claude Sonnet 4.6 — en producción |
| 2 | Chunking Christian Astrology para RAG | ⏳ Pendiente | Fase 9+ |
| 3 | Event System FE — emisores por pantalla | ✅ Parcial | `click_transit`, `domain_select`, `screen_open`, `technique` implementados |
| 4 | Context Builder — implementación completa | ⏳ Pendiente Fase 9 | Routes ad-hoc como solución provisional |
| 5 | Caché de AbuContext por sesión | ⏳ Pendiente | Sin implementar |
| 6 | `click_planet` handler + route | ✅ Resuelto | Fase 8.6 — `natal-chart-tab.tsx` + `/api/lilly/planet` |
| 7 | `city_select` handler + route | ✅ Resuelto | Fase 8.7 — `relocation-tab.tsx` + `/api/lilly/city` |

---

## 8. Lo que ya está listo en Abu Engine

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

## 9. Fixes técnicos aplicados — registro

| Fix | Archivo | Fase | Descripción |
|---|---|---|---|
| Infinite loop tránsitos | `transits-tab.tsx` | 8.11 | `useState` para estabilizar `effectiveTransitDate` |
| HF en system prompt | `lilly-prompt.ts` | 8.11 | Sección HARMONY FIELD completa |
| Significadores dominio | caller de `lilly/domain` | 8.11 | `deriveSignificators()` client-side |
| contextBlock limpio | `lilly/domain/route.ts` | 8.11 | Omitir líneas null, no usar "—" |
| SR integrado con Lilly | `relocation-tab.tsx` | 8.11 | `LifeDomainSelector` dispara evento Lilly |
| SR route | `lilly/solar-return/route.ts` | 8.11 | Nueva route con `sr_year` en contextBlock |
| click_transit | `transits-tab.tsx` + `transit/route.ts` | 8.11 | Handler + route completos |
| max_tokens transit | `transit/route.ts` | 8.11 | 512 → 1024 para grupos multi-aspecto |

---

## 10. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| v0.1 | 2026-03-13 | Documento inicial. AbuContext schema, LillyEvent contrato, Context Builder plantillas, decisiones pendientes. |
| v0.2 | 2026-03-16 | Routes ad-hoc implementadas. Event System parcial. `deriveSignificators()`. Fix infinite loop tránsitos. HF en system prompt. SR integrado. Decisiones 1 y 3 resueltas. Tabla de fixes técnicos. |

---

*Abu Oracle Project — ARCHITECTURE.md v0.2*
*Mantener actualizado ante cualquier cambio de contrato entre capas.*
*Ambos hilos (Abu Engine y Lilly) deben leer este archivo al inicio de sesiones de integración.*
