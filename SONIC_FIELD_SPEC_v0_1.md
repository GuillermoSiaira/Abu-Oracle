# SONIC_FIELD_SPEC.md — Abu Oracle: Módulo de Síntesis Musical por Resonancia Astrológica
> Documento fundacional · v0.1 · Marzo 2026
> Estado: Active Draft
> Nodo Obsidian: `sonic_field/SONIC_FIELD_SPEC`
> Links: `[[HF_V6_RESULTS]]` · `[[AXIOMATICS_OF_HEAVENS_v0_4]]` · `[[ARCHITECTURE]]`

---

## 0. Fundamento doctrinal

La tradición pitagórica postuló que los cuerpos celestes producen frecuencias proporcionales a sus velocidades y distancias orbitales — la *musica universalis*. Hans Cousto (1978, *The Cosmic Octave*) formalizó ese mapeo en frecuencias audibles via ley de octavas: cualquier frecuencia astronómica puede trasladarse al rango audible duplicándola repetidamente hasta entrar en 20–20,000 Hz.

Abu Oracle extiende este principio con tres diferencias estructurales respecto a cualquier implementación previa:

1. **Dignidad esencial como timbre** — un planeta en domicilio suena distinto a uno en detrimento. La calidad sonora no es arbitraria: refleja el estado doctrinal del planeta según la tradición helenístico-persa.
2. **Angularidad como amplitud** — la fuerza de un planeta según su proximidad a ASC/MC/DESC/IC modula su volumen en la mezcla. Un planeta angular domina el campo sonoro como domina la carta.
3. **HF como campo sonoro espacial** — el Harmony Field geográfico tiene una dimensión auditiva: el gradiente escalar del campo se traduce en tensión/resolución armónica mientras el usuario navega el mapa.

Esto no es música de fondo. Es una representación sensorial paralela del mismo sistema de cómputo que genera el mapa y la interpretación de Lilly.

---

## 1. Arquitectura del módulo

### 1.1 Decisión arquitectónica: frontend-only, Capa 1

**El módulo vive íntegramente en el frontend (Next.js).**

Razones:
- Cero cambios en abu-engine, cero nuevos endpoints, cero Cloud Run
- El AbuContext ya expone todos los datos necesarios (posiciones, dignidades, angularidad, aspectos, tránsitos)
- Tone.js (síntesis Web Audio) opera en el browser sin latencia de red
- Desplegable en días, no semanas

Stack de síntesis:
- **Tone.js** — librería de síntesis y scheduling para Web Audio API
- **@tonejs/midi** — opcional, para exportación MIDI futura

### 1.2 Tres capas — diseño completo, implementación por fases

```
Capa 1 — Firma Sonora Natal        [ESTA SEMANA — MVP]
Capa 2 — Dinámica por Tránsito     [siguiente iteración]
Capa 3 — HF como Paisaje Sonoro    [iteración posterior]
```

---

## 2. Capa 1 — Firma Sonora Natal

### 2.1 Concepto

Cada carta natal produce una pieza generativa única e irrepetible. No un tema prediseñado — una textura procedural de síntesis aditiva donde cada planeta es una voz independiente. La superposición de todas las voces es la "firma sonora" de esa carta.

Ningún otro usuario tiene la misma firma. Dos cartas con el mismo Sol en Leo suenan distinto si difieren en la dignidad de Venus o en la angularidad de Saturno.

### 2.2 Mapeo de parámetros astrológicos → síntesis

#### Frecuencia base por planeta (tabla Cousto / octava audible)

Estas son las frecuencias planetarias canónicas derivadas de períodos orbitales, trasladadas al rango audible:

| Planeta   | Frecuencia base (Hz) | Nota aproximada |
|-----------|---------------------|-----------------|
| Sol       | 126.22              | B2              |
| Luna      | 210.42              | G#3 / Ab3       |
| Mercurio  | 141.27              | C#3 / Db3       |
| Venus     | 221.23              | A3              |
| Marte     | 144.72              | D3              |
| Júpiter   | 183.58              | F#3 / Gb3       |
| Saturno   | 147.85              | D3              |
| Urano     | 207.36              | G#3 / Ab3       |
| Neptuno   | 211.44              | G#3 / Ab3       |
| Plutón    | 140.25              | C#3 / Db3       |

#### Modulación por longitud eclíptica natal

La posición del planeta en el zodíaco (0°–360°) modula la frecuencia base en ±1 semitono (±5.9%):

```
freq_natal = freq_base * (1 + (lon_natal / 360) * 0.059 * 2 - 0.059)
```

Esto garantiza que dos cartas con el mismo planeta produzcan frecuencias ligeramente distintas según la posición exacta.

#### Tipo de oscilador según dignidad esencial (timbre)

| Dignidad         | Oscilador Tone.js | Carácter sonoro                        |
|------------------|-------------------|----------------------------------------|
| Domicilio        | `Synth` sine      | Puro, sostenido, consonante            |
| Exaltación       | `Synth` triangle  | Brillante, claro, ligeramente más rico |
| Peregrino        | `Synth` sawtooth  | Neutro, abierto, sin carácter fijo     |
| Detrimento       | `AMSynth`         | Modulación de amplitud, fricción       |
| Caída            | `FMSynth`         | Modulación de frecuencia, disonancia   |

#### Amplitud por angularidad (volumen en la mezcla)

La angularidad del planeta — su proximidad a ASC, MC, DESC, IC — ya está calculada en el motor como score 0–1. Se usa directamente como volumen (gain):

```
volume_db = -30 + (angularity_score * 24)
# Rango: -30 dB (cadente) → -6 dB (angular)
```

Un planeta angular ocupa el primer plano sonoro. Un planeta cadente es casi inaudible — presente en la textura pero no dominante.

#### Aspectos natales como intervalos armónicos

Los aspectos entre planetas crean relaciones de frecuencia:

| Aspecto     | Relación armónica | Efecto perceptual        |
|-------------|-------------------|--------------------------|
| Conjunción  | Unísono (1:1)     | Fusión, refuerzo         |
| Trígono     | Quinta justa      | Consonancia, apertura    |
| Sextil      | Tercera mayor     | Consonancia suave        |
| Cuadratura  | Segunda menor     | Disonancia activa        |
| Oposición   | Tritono (±)       | Tensión máxima           |

Implementación: cuando dos planetas forman aspecto natal, sus frecuencias se ajustan mutuamente para aproximarse a la relación armónica del aspecto, ponderada por el orb (orb=0° → relación exacta, orb=8° → ajuste mínimo).

#### Fase lunar natal como envolvente global

La fase lunar natal (0°–360° de separación Sol-Luna) determina el carácter global de la envolvente:

| Fase             | Separación | Envolvente ADSR — Attack | Carácter          |
|------------------|------------|--------------------------|-------------------|
| Nueva (0–45°)    | Oscuridad  | Largo (3s), fade lento   | Introspectivo     |
| Creciente        | 45–135°    | Medio (1.5s)             | Emergente         |
| Llena (135–225°) | Máxima luz | Corto (0.5s), sustain    | Pleno, abierto    |
| Menguante        | 225–315°   | Medio (1.5s), decay      | Reflexivo         |
| Balsámica        | 315–360°   | Largo (4s), muy suave    | Disolución        |

Para la carta de Guillermo (Luna Nueva 1.8%): attack=3s, sustain muy largo, volumen general moderado — textura introspectiva y continua.

### 2.3 Estructura de datos — input del componente

El componente `SonicField` consume directamente el AbuContext ya disponible en el frontend. No requiere ningún nuevo endpoint.

```typescript
interface SonicFieldInput {
  planets: Array<{
    name: string
    lon: number               // 0–360, longitud eclíptica natal
    dignity_traditional: string  // 'domicile' | 'exaltation' | 'peregrine' | 'detriment' | 'fall'
    angularity_score?: number    // 0–1, si disponible; default 0.3
    house: number
  }>
  aspects: Array<{
    planet_a: string
    planet_b: string
    type: 'conjunction' | 'sextile' | 'square' | 'trine' | 'opposition'
    orb: number
  }>
  moon_phase_deg: number    // separación Sol-Luna en grados (0–360)
  subject_name: string
}
```

**Nota sobre angularity_score**: el AbuContext actual no expone este campo directamente. Como aproximación para Capa 1, se calcula client-side usando la distancia del planeta al ASC/MC más cercano:

```typescript
function estimateAngularity(planet_lon: number, asc_lon: number, mc_lon: number): number {
  const angles = [asc_lon, mc_lon, (asc_lon + 180) % 360, (mc_lon + 180) % 360]
  const minDist = Math.min(...angles.map(a => Math.abs(((planet_lon - a + 180) % 360) - 180)))
  return Math.max(0, 1 - minDist / 45) // máxima fuerza a 0°, cero a 45°
}
```

### 2.4 Componente React — estructura

```
next_app/components/sonic/
├── SonicField.tsx          # componente principal, orquesta todo
├── useSonicEngine.ts       # hook — inicializa Tone.js, calcula parámetros
├── planetSynths.ts         # crea y retorna los Synth por planeta
├── sonicMapping.ts         # tablas de mapeo (frecuencias, osciladores, etc.)
└── SonicControls.tsx       # botón play/pause/volumen (UI mínima)
```

### 2.5 UX de integración

- Botón "♪" discreto en la interfaz existente (esquina del panel natal o del header)
- Al activar: fade-in suave de 3s, la firma sonora comienza a reproducirse en loop generativo
- Al desactivar: fade-out 2s
- Control de volumen global (slider)
- Texto de una línea: "Tu firma sonora natal · [nombre del sujeto]"
- No interrumpe ni depende de ninguna otra interacción de la app

---

## 3. Capa 2 — Dinámica por Tránsito (diseño)

### 3.1 Concepto

La firma natal es el estado base. Cuando un tránsito significativo está activo, introduce una voz adicional que modula la textura. El usuario no necesita leer el tránsito para percibirlo — lo escucha.

### 3.2 Mapeo

Cada tránsito activo agrega:
- Una nueva frecuencia basada en la posición actual del planeta en tránsito (efémero, no natal)
- Volumen proporcional a la importancia del tránsito: aspecto exacto → máximo, orb amplio → mínimo
- Tipo de modulación según el aspecto en tránsito:
  - Trígono/Sextil: nueva voz consonante que se fusiona con la firma
  - Cuadratura/Oposición: nueva voz disonante que crea tensión con la firma
  - Conjunción: refuerzo de la voz natal del planeta afectado (amplitud aumentada)

### 3.3 Input adicional necesario

```typescript
interface TransitLayer {
  active_transits: Array<{
    transit_planet: string
    transit_lon: number       // posición actual del planeta (fecha hoy)
    natal_planet: string
    type: string
    orb: number
  }>
}
```

Este dato ya está disponible en el AbuContext (`transits[]`). Solo necesita ser pasado al engine sonoro.

### 3.4 Estado de implementación

**Diseñado. Pendiente de implementación post-Capa 1.**

---

## 4. Capa 3 — HF como Paisaje Sonoro (diseño)

### 4.1 Concepto

El Harmony Field geográfico ya es un campo escalar sobre 9,425 puntos de la Tierra. Ese campo tiene gradientes — zonas de HF alto, zonas de HF bajo, transiciones. Traducido a audio: mientras el usuario navega el mapa de relocalización, el paisaje sonoro cambia según el HF de la región que está explorando.

### 4.2 Mapeo HF → parámetros sonoros

| HF score (normalizado 0–1) | Efecto sonoro                                    |
|----------------------------|--------------------------------------------------|
| 0.8 – 1.0 (HF muy alto)    | Resolución completa — todos los intervalos consonantes, reverb amplio |
| 0.5 – 0.8 (HF alto)        | Consonancia dominante, leve tensión de fondo     |
| 0.3 – 0.5 (HF medio)       | Balance tensión/resolución                        |
| 0.1 – 0.3 (HF bajo)        | Disonancia dominante, filtro paso-bajo aplicado  |
| 0.0 – 0.1 (HF mínimo)      | Tensión máxima, intervalos de tritono, reverb seco |

### 4.3 Implementación técnica

- El HF score de la ubicación actual del cursor en el mapa se expone vía MapLibre (evento `mousemove` sobre la capa de heatmap)
- Ese score se pasa al engine sonoro como parámetro de mezcla en tiempo real
- Transición suave (crossfade 500ms) para evitar saltos abruptos al mover el cursor

### 4.4 Por qué esta capa es disruptiva

No existe ningún sistema de astrocartografía, astrología computacional ni visualización de datos astronómicos que haya implementado un campo escalar geográfico con dimensión auditiva dinámica. La Capa 3 es genuinamente nueva como concepto producto.

Potencial de demostración: la secuencia "Einstein's chart → navegar el mapa → escuchar cómo cambia el sonido mientras se mueve sobre Europa vs. América" es el tipo de demo que no requiere explicación. Se entiende en 10 segundos.

### 4.5 Estado de implementación

**Diseñado. Pendiente de implementación post-Capa 2.**

---

## 5. Roadmap de implementación

```
Semana actual
  └── [CC] Capa 1 MVP
        ├── Instalar Tone.js en next_app
        ├── sonicMapping.ts — tablas de frecuencias, osciladores, envolventes
        ├── useSonicEngine.ts — hook principal
        ├── SonicField.tsx — componente con play/pause
        └── Integración en natal-chart-tab.tsx (botón ♪)

Siguiente iteración
  └── [CC] Capa 2 — transit layer sobre el engine existente

Iteración posterior
  └── [CC] Capa 3 — HF score como parámetro de mezcla vía MapLibre
```

---

## 6. Nodos Obsidian recomendados

```
obsidian_vault/sonic_field/
├── SONIC_FIELD_SPEC.md          ← este documento
├── sonic_capa1_natal.md         ← notas de implementación Capa 1
├── sonic_capa2_transitos.md     ← diseño Capa 2
├── sonic_capa3_hf_paisaje.md    ← diseño Capa 3
└── sonic_referencias.md         ← Cousto, Kepler, Pitágoras, antecedentes

Links cruzados sugeridos:
[[HF_V6_RESULTS]] ← Capa 3 usa el mismo campo escalar
[[AXIOMATICS_OF_HEAVENS_v0_4#Axioma 8]] ← especificidad de dominio aplica al sonido
[[ARCHITECTURE]] ← AbuContext como fuente de datos del engine sonoro
[[HF_EXPERIMENT_LOG]] ← Cohen's d del campo que Capa 3 sonoriza
```

---

## 7. Decisiones abiertas

| # | Decisión | Estado |
|---|----------|--------|
| D1 | Exportación MIDI de la firma natal | Pendiente — evaluar demanda |
| D2 | Firma sonora como track descargable (MP3) | Pendiente — requiere backend o renderizado offline |
| D3 | Modo "solo planeta" — escuchar un planeta individual al clickearlo | Pendiente — natural extensión del click_planet existente |
| D4 | Ajuste fino de la tabla Cousto por feedback de oído | Abierto — Guillermo como quality gate sonoro |

---

## 8. Criterio de calidad

El juez de calidad de este módulo es el mismo que el resto del proyecto: **el oído de Guillermo como usuario**.

Luna en domicilio en Cáncer Casa 5 es el quality gate sonoro. Si la firma de una carta con ese stellium no suena a algo que ese oído reconoce como coherente, las tablas de mapeo se ajustan. Ningún parámetro de síntesis es doctrinal — son todos ajustables. Lo que es doctrinal es el principio: dignidad → timbre, angularidad → volumen, aspecto → intervalo.

---

*Abu Oracle Project — SONIC_FIELD_SPEC.md v0.1*
*Documento fundacional del módulo de síntesis musical por resonancia astrológica.*
*Mantener sincronizado con ARCHITECTURE.md y con los nodos Obsidian correspondientes.*
