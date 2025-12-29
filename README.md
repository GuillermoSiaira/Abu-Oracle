# AI Oracle

AI Oracle es una plataforma de astrología clásica persa que integra cálculo astronómico, análisis semántico determinístico y narrativa generada por LLM bajo un contrato estricto.

## Arquitectura

```
User Request
    ↓
Abu Engine (cálculos astronómicos + técnicas persas)
    → /api/astro/chart/extended
    ↓
Lilly Engine (ensamblaje semántico)
    → json_maestro.build_json_maestro()
    ↓ (si include_narrative=true)
Narrative Engine (GPT-4 con contrato estricto)
    → generate_narrative()
    ↓
Response: { maestro: {...}, narrative: "..." }
```

### Componentes principales

- **Abu Engine** (FastAPI, Python): Cálculos astronómicos, dignidades esenciales/accidentales, profecciones, fardars, lotes, mansiones lunares, estrellas fijas, solar return ranking
- **Lilly Engine** (FastAPI, Python): Ensamblaje del JSON Maestro (estructura semántica determinística) y generación de narrativa clásica vía GPT
- **Next.js Frontend** (React, TypeScript): Visualización interactiva de cartas, forecast y ciclos de vida

## Levantar el stack completo

```bash
docker compose up --build
```

## Servicios y puertos
- Abu Engine → http://localhost:8000
- Lilly Engine → http://localhost:8001
- Frontend → http://localhost:3000

## Endpoints principales

### Abu Engine
- `GET /api/astro/chart` - Carta natal básica
- `GET /api/astro/chart-detailed` - Carta con dignidades y nodos
- `GET /api/astro/chart/extended` - **Nuevo**: Bundle unificado con todos los cálculos persas
- `GET /api/astro/forecast` - Series temporales y picos
- `GET /api/astro/life-cycles` - Ciclos vitales (Saturn Return, etc.)
- `GET /api/astro/solar-return` - Retorno Solar para año y ubicación
- `GET /api/astro/solar-return/ranking` - Ranking de ciudades para RS
- `GET /api/astro/profections` - Profecciones anuales/mensuales
- `GET /api/astro/fardars` - Fardars (períodos mayores/subperíodos)
- `GET /api/astro/lots` - Lotes (Fortuna, Espíritu, etc.)
- `GET /api/astro/lunar-mansions` - Mansión lunar actual
- `GET /api/astro/fixed-stars` - Contactos con estrellas fijas

### Lilly Engine
- `POST /api/ai/interpret` - **Nuevo**: Interpreta datos astrológicos retornando JSON Maestro + narrativa opcional
  - Request: `{ birthDate, lat, lon, language, include_narrative? }`
  - Response: `{ maestro: {...}, narrative?: "..." }`

## JSON Maestro

El JSON Maestro es una estructura semántica de 10 secciones que organiza todos los datos astrológicos en un formato interpretable:

1. **metadata** - Modo (persian_cosmology), versión, contexto
2. **cosmology_context** - Principios clave del sistema persa
3. **year_overview** - Elemento del año, tono, Asc RS, Sol RS
4. **elemental_analysis** - Conteos elementales, dominancia, planetas angulares
5. **lord_of_year** - Señor del año (Ṣāḥib al-Sana), evaluación de candidatos
6. **angularity_and_dignities** - Planetas fuertes/débiles, combustión
7. **rs_natal_interplay** - Temas desbloqueados por RS–Natal overlay
8. **transits_contextualized** - Tránsitos mayores con timing
9. **monthly_windows** - Ventanas mensuales por profecciones
10. **critical_days** - Días críticos derivados de timing preciso

Ver [docs/JSON_Maestro_Schema.md](docs/JSON_Maestro_Schema.md) para schema completo.

## Modo intérprete con narrativa GPT

Lilly Engine genera narrativas en español, inglés o portugués usando GPT-4 bajo un contrato estricto:

**Contrato de narrativa:**
- Lee **SOLO** del JSON Maestro (sin inventar datos)
- **7 secciones fijas** en orden determinístico
- Sin conceptos modernos no-persas
- Sin predicciones de peligro o consejos psicológicos no fundamentados
- Tono español: sobrio, elegante, neutro-cultural

Variables de entorno relevantes:
- `OPENAI_API_KEY` (obligatoria para narrativa)
- `OPENAI_NARRATIVE_MODEL` (default: `gpt-4o-mini`)
- `ABU_BASE_URL` (para que Lilly llame a Abu Extended)

Ver [docs/Narrative_Engine_Guide.md](docs/Narrative_Engine_Guide.md) para detalles del prompt y estructura.

## Reportes de progreso
- [docs/AI_Oracle_Progress_Report_1.md](docs/AI_Oracle_Progress_Report_1.md)
- [docs/AI_Oracle_Progress_Report_2.md](docs/AI_Oracle_Progress_Report_2.md)
- [docs/AI_Oracle_Progress_Report_3.md](docs/AI_Oracle_Progress_Report_3.md)
- [docs/IGP_Sprint_B_Summary.md](docs/IGP_Sprint_B_Summary.md) ← **Nuevo: Cache, tests, estabilidad**

## Features recientes
- ✅ **IGP (Intelligent Geographic Prediction)**: Endpoint `/api/rs/optimize` para encontrar ubicaciones óptimas de Retorno Solar
- ✅ **Integration Tests**: 9 tests de integración validando contratos de API
- ✅ **Cache Layer**: Sistema de caché LRU para reducir cálculos redundantes
- ✅ **Multiprocessing**: Evaluación paralela de ciudades (8 workers)

## Despliegue
- Backends listos para Cloud Run
- Frontend listo para Vercel
