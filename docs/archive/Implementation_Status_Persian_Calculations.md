# Implementación de Cálculos Persas - Resumen

## Estado Actual

### ✅ Módulos Creados (abu_engine/core/)

1. **dignities.py** - Dignidades y Debilidades Esenciales
   - Domicilio, Exaltación, Exilio, Caída
   - Puntajes por dignidad
   - Función `get_planet_dignity()` y `get_all_dignities()`

2. **houses_swiss.py** - Sistema de Casas con pyswisseph
   - Cálculo de ASC/MC/cúspides con Placidus
   - Asignación de planetas a casas
   - Conversión longitud → signo/grado
   - **Requiere:** pyswisseph instalado

3. **lots.py** - Lotes (Partes Árabigas)
   - Parte de Fortuna (diurna/nocturna)
   - Parte de Espíritu
   - Parte de Eros
   - Parte de Necesidad (Némesis)
   - Función `calculate_all_lots()`

4. **solar_conditions.py** - Condiciones Solares
   - Cazimi (< 17')
   - Combustión (< 8°)
   - Bajo rayos (< 17°)
   - Función `get_solar_condition()`

5. **profections.py** - Profecciones
   - Profección anual (regente del año)
   - Profección mensual (opcional)
   - Funciones `calculate_annual_profection()` y `calculate_monthly_profection()`

6. **fardars.py** - Fardars (Firdaria)
   - Períodos mayores y subperíodos
   - Secuencia diurna/nocturna
   - Funciones `calculate_fardars()` y `get_current_fardar()`

7. **transits.py** - Tránsitos
   - Aspectos natal vs. tránsito
   - Aplicativo/separativo
   - Filtros por orbe y planetas mayores
   - Función `calculate_transits()`

8. **lunar_mansions.py** - Mansiones Lunares
   - 28 mansiones (Manzil árabe)
   - Naturaleza (fortunate/unfortunate/mixed)
   - Función `get_lunar_mansion()`

9. **fixed_stars.py** - Estrellas Fijas
   - Catálogo de 10+ estrellas principales
   - Conjunciones con orbes por magnitud
   - Función `get_all_fixed_star_contacts()`

10. **solar_return.py** - Revolución Solar Reubicada
    - Búsqueda binaria del momento exacto
    - Cálculo de casas para ubicación específica
    - Función `calculate_solar_return()`
    - **Requiere:** pyswisseph instalado

11. **aspects.py** (expandido)
    - Aspectos mayores y menores
    - Funciones `calculate_aspect_type()` y `is_applying()`

---

### ✅ Endpoints Añadidos (main.py)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check para monitoreo |
| `/api/astro/profections` | GET | Profecciones anuales/mensuales |
| `/api/astro/fardars` | GET | Períodos de Fardars |
| `/api/astro/lots` | GET | Lotes (Fortuna, Espíritu, etc.) |
| `/api/astro/lunar-mansions` | GET | Mansión lunar actual |
| `/api/astro/fixed-stars` | GET | Conjunciones con estrellas fijas |
| `/api/astro/transits` | GET | Tránsitos natal vs. actual |

---

### ✅ Archivos Actualizados

- **abu_engine/requirements.txt** - Agregado `pyswisseph>=2.10.3.2`
- **abu_engine/core/aspects.py** - Agregadas funciones para tránsitos

---

## 🔧 Pendiente

### 1. Instalación de pyswisseph
**Estado:** En progreso (requiere Microsoft C++ Build Tools)

**Pasos:**
1. Instalar Microsoft C++ Build Tools en D: (en curso)
2. Reiniciar terminal
3. Ejecutar: `D:/projects/AI_Oracle/venv/Scripts/python.exe -m pip install pyswisseph`

### 2. Pruebas de Endpoints
- Probar cada endpoint con datos de ejemplo
- Validar formatos de salida según `persian_calculations.md`
- Ajustar orbes y parámetros configurables

### 3. Integración de Casas en `/api/astro/chart`
- Actualmente usa Skyfield (sin casas)
- Migrar a pyswisseph para casas Placidus
- Asignar planetas y lotes a casas

### 4. Mejorar `/api/astro/solar-return`
- Reemplazar implementación actual con `solar_return.py`
- Usar búsqueda binaria para precisión exacta
- Integrar casas con pyswisseph

### 5. Tests Unitarios
- Crear `abu_engine/tests/test_dignities.py`
- Crear `abu_engine/tests/test_houses_swiss.py`
- Crear `abu_engine/tests/test_lots.py`
- Crear `abu_engine/tests/test_profections.py`
- Crear `abu_engine/tests/test_fardars.py`

### 6. Docker y CI/CD
- Actualizar `Dockerfile` para incluir build tools (si necesario)
- Agregar volumen `sweph/` en `docker-compose.yml`
- Configurar healthchecks en Docker

---

## 📋 Esquema de Respuesta Completo

Según `persian_calculations.md`, el endpoint `/api/astro/chart` debería devolver:

```json
{
  "asc": "Gemini 14°",
  "mc": "Aquarius 22°",
  "houses": [{"num":1,"cusp":"Gem 14°"}, ...],
  "planets": [
    {
      "name":"Sun",
      "sign":"Gemini",
      "deg":21.2,
      "house":1,
      "dignity":{"kind":"domicile","score":+5},
      "solar_condition":{"state":"under_beams","distance_deg":12.3}
    }
  ],
  "aspects":[{"a":"Sun","b":"Saturn","type":"square","orb":3.2,"applying":true,"reception":"mutual"}],
  "lots":[{"name":"Fortuna","sign":"Leo","deg":18.1,"house":3}],
  "profections":{"year":41,"sign":"Cancer","lord":"Moon"},
  "fardars":[{"major":"Venus","start":"2024-01-01","end":"2028-12-31","sub":[...]}],
  "lunar_mansion":{"index":11,"name":"Al Zubrah","start":...,"end":...},
  "fixed_stars":[{"star":"Regulus","mag":1.4,"long":"Leo 29°","match":true,"orb":0.8}]
}
```

---

## 🎯 Próximos Pasos

1. **Terminar instalación de C++ Build Tools** (en curso)
2. **Instalar pyswisseph y validar**
3. **Probar endpoints uno por uno** con Postman/curl
4. **Refinar formatos de salida** según el esquema
5. **Agregar tests** para cada módulo
6. **Documentar** en `/docs` con ejemplos de uso

---

## 🚀 Valor Agregado

Con estos módulos, Abu Engine ahora puede:

✅ Calcular **casas reales** (Placidus, Koch, etc.)  
✅ Determinar **dignidades esenciales** (domicilio, exaltación, caída, exilio)  
✅ Calcular **lotes/partes** (Fortuna, Espíritu, Eros, Necesidad)  
✅ Identificar **condiciones solares** (cazimi, combustión, bajo rayos)  
✅ Generar **profecciones** (regente anual y mensual)  
✅ Calcular **fardars** (períodos planetarios persas)  
✅ Detectar **tránsitos** con aspectos aplicativos/separativos  
✅ Determinar **mansiones lunares** (Manzil árabe)  
✅ Encontrar **conjunciones con estrellas fijas** (Regulus, Spica, etc.)  
✅ Calcular **revoluciones solares reubicadas** con precisión exacta  

**Diferenciación clave:** Técnicas de astrología persa/medieval que casi ninguna app moderna ofrece.
