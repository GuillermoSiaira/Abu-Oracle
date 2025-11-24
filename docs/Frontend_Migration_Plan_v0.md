# Plan de Migración Frontend: ai-oracle-v0-repo → next_app

**Fecha:** 15 de noviembre de 2025  
**Branch objetivo:** `frontend-migration-v0`  
**Repositorios involucrados:**
- **Origen:** `ai-oracle-v0-repo` (playground de v0.dev)
- **Destino:** `ai-oracle/next_app/` (frontend de producción)

---

## 🎯 OBJETIVO

Migrar la UI/UX avanzada creada por v0.dev en el repo `ai-oracle-v0-repo` hacia el frontend de producción en `next_app/`, conectándola al backend real (Abu Engine + Lilly Engine) desplegado en Cloud Run.

---

## 📊 ARQUITECTURA IDENTIFICADA

### **ai-oracle-v0-repo** (Origen - UI avanzada)

**Componentes estables:**
- ✅ `ZodiacWheel` - Rueda zodiacal SVG completa con doble orientación
- ✅ `ResultsDisplay` - Sistema de tabs con planetas, casas, aspectos, profecciones, lotes
- ✅ `BirthDataPanel` - Formulario unificado de datos natales
- ✅ `ChartTabs` - Tabs modulares (Carta Natal, Técnicas Persas, Interpretación, Maestro JSON)
- ✅ `InterpretationTab` - Generación de interpretación + display narrativa + Maestro JSON
- ✅ `MaestroTab` - Visualización JSON completo para inspección
- ✅ `ChatPanel` - Panel lateral conversacional (placeholder)

**Store global:**
- Zustand con estado centralizado: `birthData`, `abuData`, `lillyData`, `wheelOrientation`, etc.

**Servicios tipados:**
- `services/abu.ts` → `getChartExtended()` (GET `/api/astro/chart/extended`)
- `services/lilly.ts` → `interpretMaestro()` (POST `/api/ai/interpret`)
- Mock data completo como fallback

**Diseño:**
- Dark theme con paleta persa (dorado `#D4AF37`, púrpura, índigo)
- Tipografía: DM Serif Display + Inter
- shadcn/ui (Radix UI + CVA)
- Tailwind CSS v4

---

### **ai-oracle/next_app/** (Destino - Estado actual)

**Estructura fragmentada:**
- Rutas separadas: `/chart`, `/forecast`, `/interpret`, `/positions`
- Sin tabs integrados ni navegación cohesiva

**Componentes básicos:**
- `ChartWheel` (rueda básica, menos completa)
- `LillyPanel` (maneja legacy + Maestro, pero sin tabs)
- `MapWithMarkers`, `AbuRankingPanel`, `CitySelector` (específicos de `/forecast`)

**Clientes existentes pero subutilizados:**
- `clients/abu.ts` y `clients/lilly.ts` bien implementados
- Componentes usan fetch directo en lugar de clientes

**Sin store global:**
- Estado local por página, sin persistencia

---

## 🔍 GAPS IDENTIFICADOS

| **Aspecto** | **v0-repo (avanzado)** | **next_app/ (básico)** | **Acción requerida** |
|-------------|------------------------|------------------------|----------------------|
| Organización UI | Tabs modulares | Rutas separadas | Migrar ChartTabs + sub-componentes |
| Store global | Zustand centralizado | Estado local | Crear lib/store.ts |
| Rueda zodiacal | Completa (orientación dual) | Básica | Migrar ZodiacWheel completo |
| Interpretación | Tab dedicado + Maestro JSON | Solo LillyPanel simple | Migrar InterpretationTab |
| Diseño | Paleta persa, DM Serif | Básico | Actualizar layout y tipografía |
| Servicios | abu.ts/lilly.ts usados | Fetch directo | Refactorizar para usar clientes |
| Maestro JSON | Tab de inspección | No visible | Migrar MaestroTab |
| Chat | Panel lateral | No existe | Migrar ChatPanel (opcional) |

---

## 📋 PLAN DE MIGRACIÓN (6 FASES)

### **FASE 1: PREPARACIÓN** ✅ Completada
- Auditoría completa de ambos repositorios
- Identificación de componentes y gaps
- Diseño del plan de migración

---

### **FASE 2: INSTALACIÓN DE DEPENDENCIAS**

**Nuevas dependencias necesarias:**

```json
{
  "zustand": "^4.5.0",
  "@radix-ui/react-tabs": "^1.0.4",
  "@radix-ui/react-switch": "^1.0.3",
  "@radix-ui/react-alert-dialog": "^1.0.5",
  "class-variance-authority": "^0.7.0",
  "clsx": "^2.1.0",
  "tailwind-merge": "^2.2.0"
}
```

**Comandos:**
```bash
cd next_app
npm install zustand @radix-ui/react-tabs @radix-ui/react-switch @radix-ui/react-alert-dialog class-variance-authority clsx tailwind-merge
npx shadcn-ui@latest init
```

**Configuración shadcn/ui:**
- Estilo: Default
- Color base: Slate
- CSS variables: Sí
- Importar componentes en `components/ui/`

---

### **FASE 3: MIGRACIÓN DE COMPONENTES UI**

#### **3.1 - Migrar lib/store.ts y lib/types.ts**

**Archivos a crear:**
- `next_app/lib/store.ts` → Store Zustand con estado global
- `next_app/lib/types.ts` → Tipos centralizados

**Estructura del store:**
```typescript
interface AppState {
  // Birth data
  birthData: BirthData | null
  setBirthData: (data: BirthData) => void

  // Abu data (chart + extended)
  abuData: AbuResponse | null
  setAbuData: (data: AbuResponse) => void
  abuLoading: boolean
  abuError: string | null

  // Lilly data (maestro + narrative)
  lillyData: LillyResponse | null
  setLillyData: (data: LillyResponse) => void
  lillyLoading: boolean
  lillyError: string | null

  // Chat
  chatHistory: ChatMessage[]
  addChatMessage: (message: ChatMessage) => void

  // Settings
  wheelOrientation: 'aries-top' | 'asc-top'
  setWheelOrientation: (orientation: 'aries-top' | 'asc-top') => void
  includeTransits: boolean
  setIncludeTransits: (include: boolean) => void
}
```

**Integración con tipos existentes:**
- Alinear con `types/contracts.ts`
- Reutilizar interfaces existentes
- No duplicar definiciones

---

#### **3.2 - Actualizar services/ con clientes v0**

**Archivos a actualizar:**
- `next_app/services/abu.ts` (migrar desde `clients/abu.ts` + v0)
- `next_app/services/lilly.ts` (migrar desde `clients/lilly.ts` + v0)

**Mejoras a aplicar:**
1. Usar base URLs de env (`NEXT_PUBLIC_ABU_URL`, `NEXT_PUBLIC_LILLY_URL`)
2. Añadir mock data completo como fallback
3. Logging para debugging
4. Error handling robusto

**Contrato garantizado:**
- ✅ `getChartExtended()` → GET `/api/astro/chart/extended?birthDate=...&lat=...&lon=...`
- ✅ `interpretMaestro()` → POST `/api/ai/interpret` con body `{ birthDate, lat, lon, language, include_narrative }`

**Mock data locations:**
- `services/abu.ts` → `MOCK_ABU_RESPONSE`
- `services/lilly.ts` → Mock dentro de `interpretMaestro()` catch block

---

#### **3.3 - Migrar componentes shadcn/ui**

**Componentes base a instalar:**
```bash
npx shadcn-ui@latest add card
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add switch
npx shadcn-ui@latest add alert
```

**Ubicación:** `next_app/components/ui/`

**Validación:**
- Todos los componentes UI deben usar Radix UI
- Consistencia con paleta de colores
- Soporte para dark mode

---

#### **3.4 - Migrar ZodiacWheel completo**

**Archivo origen:** `ai-oracle-v0-repo/components/zodiac-wheel.tsx`  
**Archivo destino:** `next_app/components/zodiac-wheel.tsx`

**Características a migrar:**
- ✅ Rueda SVG de 600x600px
- ✅ 12 signos zodiacales con símbolos dorados
- ✅ Posiciones planetarias con colores específicos
- ✅ Líneas de aspectos entre planetas
- ✅ Divisiones de casas (12 líneas radiales)
- ✅ Ángulos principales (ASC, MC, DSC, IC)
- ✅ **Doble orientación:**
  - `orientation="aries"` → Aries arriba (0° en top)
  - `orientation="ascendant"` → Ascendente arriba (AC a las 9 en punto)

**Props interface:**
```typescript
interface ZodiacWheelProps {
  planets: Planet[]
  houses?: {
    houses?: House[]
    asc?: number | null
    mc?: number | null
  }
  birthData?: {
    name?: string
    date?: string
    location?: string
    lat?: number
    lon?: number
  }
  sunSign?: string
  moonSign?: string
  ascendantSign?: string
  orientation?: "aries" | "ascendant"
}
```

**Cálculo de rotación:**
```typescript
const rotationOffset = useMemo(() => {
  if (orientation === "ascendant" && houses?.asc !== undefined) {
    return houses.asc - 90
  }
  return 0
}, [orientation, houses?.asc])
```

**Reemplazo de componente:**
- `ChartWheel.tsx` → deprecar (mantener como backup)
- `zodiac-wheel.tsx` → nuevo componente principal

---

### **FASE 4: INTEGRACIÓN CON BACKEND REAL**

#### **4.1 - Conectar BirthDataPanel con abu.getChartExtended()**

```typescript
import { getChartExtended } from '@/services/abu'
import { useAppStore } from '@/lib/store'

const { setAbuData, setAbuLoading, setAbuError } = useAppStore()

const handleCalculate = async () => {
  setAbuLoading(true)
  try {
    const response = await getChartExtended({
      birthDate: '1990-01-01T12:00:00Z',
      lat: -34.6,
      lon: -58.3
    })
    setAbuData(response)
  } catch (error) {
    setAbuError(error.message)
  } finally {
    setAbuLoading(false)
  }
}
```

#### **4.2 - Conectar InterpretationTab con lilly.interpretMaestro()**

```typescript
import { interpretMaestro } from '@/services/lilly'
import { useAppStore } from '@/lib/store'

const { birthData, setLillyData, setLillyLoading } = useAppStore()

const handleInterpret = async () => {
  setLillyLoading(true)
  try {
    const response = await interpretMaestro({
      birthDate: birthData.date,
      lat: birthData.lat,
      lon: birthData.lon,
      language: 'es',
      includeNarrative: true
    })
    setLillyData(response)
  } catch (error) {
    setLillyError(error.message)
  } finally {
    setLillyLoading(false)
  }
}
```

#### **4.3 - Eliminar fetch directo**

**Archivos a refactorizar:**
- `app/chart/page.tsx` → usar `getChartExtended()`
- `app/interpret/page.tsx` → usar `interpretMaestro()`
- Cualquier componente con fetch manual

---

### **FASE 5: SISTEMA DE TABS Y PÁGINA PRINCIPAL**

#### **5.1 - Crear página principal unificada**

**Archivo:** `next_app/app/page.tsx`

**Estructura:**
```tsx
<main>
  <header>
    <h1>Abu — Astrología Persa</h1>
  </header>

  <BirthDataPanel />

  <ChartTabs />

  <ChatPanel /> {/* opcional */}
</main>
```

#### **5.2 - Migrar ChartTabs y sub-componentes**

**Componentes a crear:**
- `components/chart-tabs.tsx` → Contenedor principal
- `components/natal-chart-tab.tsx` → ZodiacWheel + PositionsTable + HousesTable
- `components/persian-techniques-tab.tsx` → Profections, Lots, Lunar Mansion, Fixed Stars
- `components/interpretation-tab.tsx` → Botón "Generar" + Narrative + Maestro JSON
- `components/maestro-tab.tsx` → JSON completo en `<pre>`

**Tabs a implementar:**
1. Carta Natal
2. Técnicas Persas
3. Interpretación
4. Análisis Maestro (JSON)
5. Tránsitos (opcional, si `includeTransits: true`)

---

### **FASE 6: LIMPIEZA Y VALIDACIÓN**

#### **6.1 - Deprecar rutas antiguas**

**Mantener:**
- `/forecast` → Solar return (no hay equivalente en v0)

**Consolidar:**
- `/chart` → redirect a `/` (tabs)
- `/positions` → redirect a `/` (tabs)
- `/interpret` → redirect a `/` (tabs)

**Actualizar Navigation:**
```tsx
<Link href="/">Carta Natal</Link>
<Link href="/forecast">Revolución Solar</Link>
```

#### **6.2 - Actualizar layout con tipografía**

```typescript
import { DM_Serif_Display, Inter } from 'next/font/google'

const dmSerif = DM_Serif_Display({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-serif'
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans'
})

// En <html>:
<html className={`${dmSerif.variable} ${inter.variable} dark`}>
```

#### **6.3 - Configurar Tailwind con paleta persa**

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#D4AF37', // Dorado
        secondary: '#8B5CF6', // Púrpura
        accent: '#6366F1', // Índigo
      },
      fontFamily: {
        serif: ['var(--font-serif)'],
        sans: ['var(--font-sans)']
      }
    }
  }
}
```

#### **6.4 - Testing funcional**

**Checklist de validación:**
- [ ] Ingresar datos natales → carta calculada correctamente
- [ ] Click "Generar Interpretación" → narrativa + Maestro JSON visible
- [ ] Cambiar orientación rueda → actualización visual funcional
- [ ] Navegar entre tabs → datos correctos en todos
- [ ] `/forecast` → funciona sin cambios
- [ ] Store persiste datos al navegar
- [ ] Mock data funciona si backend no disponible

---

## ⚠️ RESTRICCIONES CRÍTICAS

### **NO MODIFICAR:**
❌ `abu_engine/` → Backend intacto  
❌ `lilly_engine/` → Backend intacto  
❌ Endpoints existentes → Contratos garantizados  
❌ `types/contracts.ts` → Interfaces validadas  

### **SÍ MODIFICAR:**
✅ `next_app/` completo  
✅ Componentes UI  
✅ Store y estado  
✅ Layout y diseño  
✅ Servicios frontend  

---

## 🚀 ESTRATEGIA DE IMPLEMENTACIÓN

### **Branch workflow:**
1. Crear branch: `git checkout -b frontend-migration-v0`
2. Implementar en iteraciones (Fase 2 → 3 → 4 → 5 → 6)
3. Commit frecuente con mensajes descriptivos
4. PR para merge a `backend-improvements` al finalizar

### **Commits sugeridos:**
- `feat: add Zustand store and centralized types`
- `feat: migrate abu/lilly services with v0 improvements`
- `feat: add shadcn/ui base components`
- `feat: migrate complete ZodiacWheel with dual orientation`
- `feat: create unified chart tabs system`
- `feat: integrate interpretation tab with Maestro JSON`
- `chore: deprecate old routes and update navigation`

### **Testing iterativo:**
- Validar cada fase antes de continuar
- Mantener `/forecast` funcional en todo momento
- Probar con backend real (Cloud Run) y con mocks

---

## 📦 RESULTADO ESPERADO

**Al finalizar la migración:**

1. ✅ **Página principal unificada** (`/`) con:
   - Form de datos natales
   - Tabs: Carta Natal | Técnicas Persas | Interpretación | Maestro JSON
   - Rueda zodiacal completa con orientación dual
   - Interpretación narrativa + JSON visible

2. ✅ **Store global Zustand** compartiendo:
   - `birthData`, `abuData`, `lillyData`
   - Estados de carga/error
   - Configuración UI (orientación, tránsitos)

3. ✅ **Servicios centralizados** usando clientes tipados

4. ✅ **Diseño refinado** con paleta persa y DM Serif Display

5. ✅ **Ruta `/forecast`** intacta para solar return

6. ✅ **Listo para deploy en Vercel**

---

## 📊 MÉTRICAS DE ÉXITO

| **Métrica** | **Objetivo** |
|-------------|--------------|
| Componentes migrados | 15+ componentes de v0 |
| Reducción de fetch directo | 100% usan servicios |
| Store centralizado | 1 único store Zustand |
| Rutas consolidadas | De 4 rutas a 2 (/  + /forecast) |
| Tabs implementados | 4 tabs funcionales |
| Orientación de rueda | 2 modos (Aries / ASC) |
| Maestro JSON visible | Sí (tab dedicado) |
| Backend modificado | 0 cambios |
| Contratos rotos | 0 |

---

## 🔗 REFERENCIAS

- **v0-repo docs:** `ai-oracle-v0-repo/docs_v0/Abu_Interface_Implementation.md`
- **Contratos API:** `docs/API_Examples.md`, `docs/Solar_Return_API.md`
- **Copilot Instructions:** `.github/copilot-instructions.md`
- **Maestro Schema:** `docs/JSON_Maestro_Schema.md`

---

**Estado:** 📝 Plan documentado  
**Próximo paso:** Crear branch `frontend-migration-v0` e iniciar Fase 2

