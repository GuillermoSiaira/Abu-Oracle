# Sistema de Perfil de Usuario – Guía Rápida

## ✅ Implementado (2025-11-03)

### Características

1. **Selector de Ciudades Inteligente**
   - Autocomplete con búsqueda en tiempo real
   - Base de datos de 58 ciudades principales (España, LATAM, USA, Europa, Asia)
   - Muestra coordenadas geográficas automáticamente
   - Endpoint: `GET /api/cities/search?q=madrid`

2. **Perfil Completo del Usuario**
   - Nombre
   - Lugar de nacimiento (ciudad, país) → coordenadas automáticas
   - Lugar de residencia actual (opcional)
   - Fecha y hora de nacimiento

3. **Persistencia Automática**
   - Los datos se guardan en `localStorage`
   - Se cargan automáticamente al abrir cualquier página
   - Botón "Borrar datos guardados" disponible

4. **Integración en Páginas**

#### `/positions` - Tabla de Posiciones Detalladas
- Formulario completo con todos los datos
- Header personalizado con nombre y ubicaciones
- Cálculos usan las coordenadas del lugar de nacimiento

#### `/interpret` - Interpretación Astrológica
- Header compacto con datos del usuario
- Botón "Editar perfil" en esquina
- **Interpretación personalizada**: Lilly recibe `user_name` y `birth_location`
- **Forecast multi-ubicación**: Automáticamente compara natal + residencia
  - Línea azul: Lugar de nacimiento
  - Línea naranja: Lugar de residencia (si es diferente)
  - Botón para agregar más ciudades al comparador

## 🎯 Cómo Usar

### Primera Vez
1. Ir a `/positions` o `/interpret`
2. Llenar el formulario:
   - Nombre (opcional pero recomendado)
   - **Lugar de nacimiento** (requerido): escribir ciudad y seleccionar de lista
   - Lugar de residencia (opcional): para comparaciones de forecast
   - Fecha y hora de nacimiento
3. Click "Calcular Posiciones" o esperar carga automática
4. ✅ Los datos quedan guardados

### Visitas Posteriores
- Los datos se cargan automáticamente
- Puedes editar haciendo click en "Editar perfil" o "Borrar datos guardados"

## 🔍 Detalles Técnicos

### Componente `CitySelector`
```tsx
import CitySelector, { CityData } from '@/components/CitySelector'

const [city, setCity] = useState<CityData | null>(null)

<CitySelector
  label="Lugar de nacimiento"
  value={city}
  onChange={setCity}
  placeholder="Buscar ciudad..."
  required
/>
```

**Props**:
- `value`: `CityData | null` - Ciudad seleccionada
- `onChange`: `(city: CityData | null) => void` - Callback al seleccionar
- `label`: string (opcional) - Etiqueta del campo
- `placeholder`: string (opcional) - Texto de ayuda
- `required`: boolean (opcional) - Campo obligatorio

**Tipo `CityData`**:
```typescript
{
  city: string       // "Buenos Aires"
  country: string    // "Argentina"
  lat: number        // -34.6037
  lon: number        // -58.3816
}
```

### Endpoint Backend
```
GET /api/cities/search?q=<query>
```

**Parámetros**:
- `q`: String de búsqueda (mínimo 2 caracteres)

**Respuesta**:
```json
[
  {"city": "Madrid", "country": "España", "lat": 40.4168, "lon": -3.7038},
  {"city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816}
]
```

### Modelo `UserProfile`
```typescript
{
  name: string
  birthCity: CityData | null
  residenceCity: CityData | null
  birthDate: string      // "1990-07-05"
  birthTime: string      // "12:00"
}
```

Guardado en: `localStorage.getItem('userProfile')`

## 🌟 Beneficios

1. **Eliminamos lat/lon manuales**: Ya no hay que buscar coordenadas en Google
2. **Contexto personalizado**: Lilly puede mencionar tu nombre y ubicación en las interpretaciones
3. **Comparaciones automáticas**: El forecast compara tu ciudad natal vs residencia sin pasos extra
4. **Una sola vez**: Los datos se guardan y reutilizan en todas las páginas
5. **Base para futuro**: Preparado para guardar múltiples perfiles, exportar/importar, etc.

## 📋 Próximos Pasos

1. **Agregar más ciudades** a `abu_engine/data/cities.json` (actualmente 58)
2. **Múltiples perfiles**: Guardar charts de familia/amigos
3. **Exportar/Importar**: JSON o QR code para compartir
4. **Cloud sync**: Opcional guardar en servidor con cuenta
5. **Geocoding API**: Buscar cualquier ciudad del mundo (no solo las 58 actuales)

---

**Documentación completa**: `docs/Extended_Calculations_Roadmap.md`  
**Changelog**: `CHANGELOG.md`
