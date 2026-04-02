# Cálculos Astrológicos Detallados – Roadmap

## Objetivo
Replicar la funcionalidad de losarcanos.com: tablas detalladas de posiciones planetarias, dignidades, puntos matemáticos y tránsitos.

## ✅ Implementado (2025-11-03)

### 1. Planetas Extendidos
- ✅ Agregados Urano, Neptuno, Plutón a `chart_json()`
- ✅ Ahora se calculan 10 cuerpos celestes principales

### 2. Módulo `extended_calc.py`
Nuevo módulo con cálculos astrológicos avanzados:

#### Dignidades Esenciales
- ✅ `calculate_dignity()`: Evalúa domicilio, exaltación, caída, exilio, peregrino
- ✅ Tablas de regencias (modernas y tradicionales)
- ✅ Sistema de puntuación (+5 domicilio, +4 exaltación, -5 exilio, -4 caída)

#### Posiciones Detalladas
- ✅ `format_position()`: Formato tradicional "15°32' Aries"
- ✅ `calculate_detailed_positions()`: Tabla completa con:
  - Longitud eclíptica exacta
  - Signo zodiacal
  - Grado dentro del signo (0-30°)
  - Formato legible
  - Estado de dignidad

#### Nodos Lunares
- ✅ `get_lunar_nodes()`: Cálculo aproximado de Nodo Norte y Sur
- ⚠️ Implementación simplificada (nodo medio)
- 🔲 Pendiente: Integrar Swiss Ephemeris para nodo verdadero

#### Partes Arábicas
- ✅ `calculate_part_of_fortune()`: Parte de la Fortuna (Pars Fortunae)
- Formula día: ASC + Luna - Sol
- Formula noche: ASC + Sol - Luna
- ⚠️ Requiere Ascendente calculado (ver pendientes)

### 3. Nuevo Endpoint `/api/astro/chart-detailed`
Retorna JSON extendido con:
```json
{
  "datetime": "2026-07-05T12:00:00+00:00",
  "location": {"lat": -34.6, "lon": -58.4},
  "planets": [
    {
      "name": "Sun",
      "longitude": 103.1234,
      "sign": "Cancer",
      "degree_in_sign": 13.12,
      "formatted": "13°07' Cancer",
      "house": null,
      "dignity": {
        "domicile": false,
        "exaltation": false,
        "detriment": false,
        "fall": false,
        "peregrine": true,
        "score": 0
      }
    }
  ],
  "aspects": [...],
  "arabic_parts": {
    "part_of_fortune": {
      "longitude": 245.67,
      "sign": "Sagittarius",
      "formatted": "25°40' Sagittarius"
    }
  },
  "lunar_nodes": {
    "north_node": {...},
    "south_node": {...}
  }
}
```

### 4. Base de Datos de Ciudades
- ✅ `abu_engine/data/cities.json` con 58 ciudades principales
- ✅ Endpoint `/api/cities/search?q=query` con búsqueda typeahead
- ✅ Cobertura: España, LATAM, USA, Europa, Asia, Australia

### 5. Sistema de Perfil de Usuario
- ✅ **CitySelector Component**: Autocomplete con búsqueda en tiempo real, debounce 300ms
- ✅ **UserProfile Model**: `{ name, birthCity, residenceCity, birthDate, birthTime }`
- ✅ **localStorage Persistence**: Datos guardados automáticamente entre sesiones
- ✅ **Integrado en páginas**:
  - `/positions`: Formulario completo, header personalizado con datos
  - `/interpret`: Header con nombre y ubicaciones, forecast multi-ciudad (natal + residencia automático)
- ✅ **Context para Lilly**: Interpretaciones reciben `user_name` y `birth_location` para respuestas personalizadas
- ✅ **UX**: Botón "Borrar datos guardados", validación de campos requeridos

### 6. Frontend: Tabla de Posiciones (`/positions`)
- ✅ Tabla completa con dignidades coloreadas (verde=favorable, rojo=desfavorable)
- ✅ Nodos lunares en cards separados
- ✅ Partes arábicas con advertencias cuando faltan datos (ASC)
- ✅ Tabla de aspectos con badges de colores por tipo

## 🔲 Pendientes Críticos

### 1. Sistema de Casas (ALTA PRIORIDAD)
**Problema actual**: `house: null` en todas las posiciones

**Necesitamos**:
- Calcular cúspides de las 12 casas
- Sistema Placidus o Koch
- Ascendente (ASC), Medio Cielo (MC), Descendente (DSC), Fondo del Cielo (IC)

**Opciones**:
1. **Implementar con Skyfield**: Complicado, Skyfield no incluye casas nativamente
2. **Integrar Swiss Ephemeris (pyswisseph)**: ✅ RECOMENDADO
   ```python
   pip install pyswisseph
   ```
   - Cálculo preciso de casas Placidus, Koch, etc.
   - Nodos verdaderos
   - Puntos matemáticos adicionales

**Plan**:
- Crear `core/houses_swiss.py`
- Instalar `pyswisseph` en `requirements.txt`
- Agregar función `calculate_houses_placidus(lat, lon, datetime) -> List[float]`
- Integrar en `chart_json()` y `get_chart_detailed()`

### 2. Más Puntos Matemáticos
**Pendiente**:
- ✅ Parte de la Fortuna (implementado, pero requiere ASC)
- 🔲 Parte del Espíritu
- 🔲 Lilith (Luna Negra)
- 🔲 Quirón
- 🔲 Vertex
- 🔲 Parte del Karma (Nodo Sur)

**Prioridad**: MEDIA (después de casas)

### 3. Tránsitos
**Objetivo**: Comparar carta natal vs posiciones actuales o futuras

**Endpoint nuevo**: `GET /api/astro/transits`
```
Params:
  - birthDate: fecha natal
  - birthLat, birthLon: coordenadas natales
  - transitDate: fecha a comparar (default: ahora)

Returns:
  - natal_planets: posiciones natales
  - transit_planets: posiciones en transitDate
  - aspects_to_natal: aspectos entre tránsitos y natal
  - interpretation: llamada a Lilly con eventos significativos
```

**Prioridad**: ALTA (después de casas)

### 4. Progresiones Secundarias
**Objetivo**: Calcular carta progresada (1 día = 1 año)

**Endpoint nuevo**: `GET /api/astro/progressions`
```
Params:
  - birthDate
  - currentAge (en años)

Returns:
  - progressed_planets: posiciones progresadas
  - aspects_to_natal
```

**Prioridad**: MEDIA

### 5. UI: Tabla de Posiciones (Frontend)
**Objetivo**: Mostrar tabla estilo losarcanos.com

**Componente nuevo**: `components/PositionsTable.tsx`
```tsx
<PositionsTable 
  planets={detailedChart.planets}
  aspects={detailedChart.aspects}
  arabicParts={detailedChart.arabic_parts}
  lunarNodes={detailedChart.lunar_nodes}
/>
```

**Layout**:
```
┌─────────────────────────────────────────────────┐
│ Planeta  │ Posición    │ Casa │ Dignidad       │
├─────────────────────────────────────────────────┤
│ ☉ Sol    │ 13°07' ♋   │  10  │ Peregrino      │
│ ☽ Luna   │ 25°40' ♐   │   4  │ Exilio         │
│ ☿ Mercur │  3°15' ♌   │  11  │ Peregrino      │
│ ...      │ ...         │ ...  │ ...            │
└─────────────────────────────────────────────────┘
```

**Prioridad**: ALTA (para validar cálculos visualmente)

### 6. Aspectos Menores
Actualmente solo calculamos:
- Conjunción (0°)
- Sextil (60°)
- Cuadratura (90°)
- Trígono (120°)
- Oposición (180°)

**Pendiente**:
- Semi-sextil (30°)
- Semi-cuadratura (45°)
- Sesqui-cuadratura (135°)
- Quincuncio (150°)

**Prioridad**: BAJA

## 📋 Plan de Implementación (Próximos Pasos)

### Fase 1: Casas y Ascendente (AHORA)
1. Instalar `pyswisseph`
2. Crear `core/houses_swiss.py` con funciones:
   - `calculate_houses_placidus()`
   - `calculate_ascendant()`
   - `calculate_mc()`
3. Actualizar `chart_json()` para incluir `houses: List[HouseCusp]`
4. Actualizar `get_chart_detailed()` para asignar casas a planetas
5. Recalcular Parte de la Fortuna con ASC real

### Fase 2: Tránsitos (DESPUÉS DE FASE 1)
1. Crear endpoint `/api/astro/transits`
2. Calcular aspectos entre natal y tránsitos
3. Integrar con Lilly para interpretación de tránsitos activos
4. UI: Página `/transits` con tabla comparativa

### Fase 3: UI – Tabla de Posiciones
1. Crear `PositionsTable.tsx` con Tailwind
2. Integrar en `/chart` y `/interpret`
3. Agregar tooltips explicativos para dignidades

### Fase 4: Más Puntos y Progresiones
1. Agregar Lilith, Quirón, Vertex
2. Implementar progresiones secundarias
3. UI: Selector de fecha para tránsitos futuros

## 🎯 Resultado Final Esperado

Una vez completado, tendremos:

✅ **Carta Natal Completa**:
- 10 planetas + Nodos + Lilith + Quirón + Parte de Fortuna
- 12 casas con Ascendente y MC
- Dignidades esenciales calculadas
- Tabla de aspectos mayor y menores

✅ **Tránsitos en Tiempo Real**:
- Comparar cualquier fecha vs carta natal
- Aspectos activos (exactos y aplicativos)
- Interpretación automática vía Lilly

✅ **Progresiones**:
- Carta progresada por edad
- Aspectos progresión-natal

✅ **UI Profesional**:
- Rueda visual + Tabla de posiciones
- Exportar PDF o imagen
- Compartir enlace a carta

## 📚 Referencias

- **Swiss Ephemeris**: https://www.astro.com/swisseph/
- **pyswisseph**: https://pypi.org/project/pyswisseph/
- **Cálculo de casas**: https://www.astro.com/swisseph/swisseph.htm#_Toc19107869
- **Dignidades**: Libro "The Real Astrology" – John Frawley

## Notas Técnicas

### Limitaciones Actuales
- Nodos: aproximación por nodo medio (error ~1-2°)
- Parte de Fortuna: placeholder ASC=0° hasta implementar casas
- Sin casas: todos los planetas reportan `house: null`

### Dependencias a Agregar
```txt
# abu_engine/requirements.txt
pyswisseph==2.10.3.1
```

### Ejemplo de Uso
```python
# Después de Fase 1
from core.houses_swiss import calculate_houses_placidus

houses = calculate_houses_placidus(lat=-34.6, lon=-58.4, dt=datetime.now())
# houses = [0.0, 30.5, 58.2, 90.0, ...] (12 cúspides en longitud eclíptica)
```

---

**Última actualización**: 2025-11-03  
**Estado**: Fase 0 completada (cálculos básicos extendidos), listo para Fase 1 (casas)
