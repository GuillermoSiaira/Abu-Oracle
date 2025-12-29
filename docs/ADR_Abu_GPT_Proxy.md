# ADR-0001 · Abu Engine + GPT Proxy Conversacional
**Fecha:** 2025-11-04  
**Autor:** ChatGPT (asistente técnico)  
**Estado:** Aprobado

## 1) Decisiones cortas (Sí/No + Por qué)

**a) ¿Crear los cálculos en Abu Engine y exponerlos como endpoints mejora la performance de las respuestas del GPT?**  
**Sí.** Separar **cálculo** de **interpretación** reduce latencia y costo: el GPT recibe datos *ya procesados* (casas, dignidades, fardars, RS, etc.) y solo interpreta. Esto evita que el modelo “adivine”, disminuye tokens (menos texto y menos ambigüedad) y mejora consistencia (misma matemática siempre).

**b) ¿Elegimos la Opción 2 (Proxy conversacional propio en /abu) con la API de OpenAI Assistant?**  
**Sí.** Incrustar el chat como **UI nativa** nos da control total (perfiles, branding, permisos, A/B tests), mantiene una sola identidad visual y permite telemetría fina. Requiere un poco más de código, pero habilita una experiencia superior y medible.

---

## 2) Resumen ejecutivo
Migramos la capa LLM fuera del backend y la instalamos como **GPT personalizado ("Abu Interpreter")**.  
El frontend servirá un **chat nativo** (`/abu`) que habla con ese GPT mediante la **Assistants API**.  
El GPT, a su vez, llama **Actions** hacia **Abu Engine (FastAPI)** para obtener cálculos astronómicos persas de alta precisión.

**Beneficios clave**:  
- Menor latencia, menor costo por token, mayor coherencia.  
- Backend simplificado (solo cálculo/datos).  
- UX conversacional fluida con memoria y estilo consistente.  
- Observabilidad y control de la experiencia en nuestra propia UI.

---

## 3) Arquitectura objetivo

```mermaid
flowchart LR
  U[Usuario] -->|chat web /abu| FE[Next.js UI]
  FE -->|Assistants API| GPT[GPT "Abu Interpreter"]
  GPT -->|Actions REST| BE[Abu Engine (FastAPI)]
  BE --> EP[Ephemerides (Skyfield/Swiss) & DB]

  subgraph "Front-end"
    FE
  end

  subgraph "OpenAI (SaaS)"
    GPT
  end

  subgraph "Backend propio"
    BE
    EP
  end
```

**Roles**  
- **Abu Engine (FastAPI):** cálculo astronómico (casas, RS, fardars, mansiones, lotes, etc.).  
- **GPT Abu Interpreter:** conversación y interpretación con doctrina persa.  
- **Next.js (/abu):** contenedor del chat, session state, perfil de usuario, telemetría.

---

## 4) Endpoints mínimos (Abu Engine)

- `GET /api/astro/chart` → carta natal detallada (planetas, signos, **casas**, dignidades).  
- `GET /api/astro/transits?date=...` → aspectos a la natal (aplicación/separación, orbes).  
- `GET /api/astro/solar-return?year=...&lat=...&lon=...` → **RS** reubicada.  
- `GET /api/astro/profections?year=...` → regente anual/mensual.  
- `GET /api/astro/fardars` → períodos mayores/subperíodos activos.  
- `GET /api/astro/lots` → Fortuna, Espíritu, y lotes secundarios.  
- `GET /api/astro/lunar-mansions` → mansión lunar para fecha/hora.  
- `GET /api/astro/fixed-stars` → conjunciones relevantes por magnitud.

**Requisitos técnicos**  
- `pyswisseph` + efemérides Swiss para ASC/MC y casas.  
- Skyfield/DE440s para posiciones planetarias.  
- Configuración de orbes por planeta/aspecto (configurable).

---

## 5) Acciones (Actions) del GPT

Ejemplo de definición conceptual (equivalente OpenAPI/JSON Schema):

- **get_chart**: devuelve carta natal detallada.  
- **get_transits(date)**: devuelve aspectos de tránsitos a natal.  
- **get_solar_return(year, lat, lon, timezone?)**: calcula RS reubicada.  
- **get_profections(year)**, **get_fardars()**, **get_lots()**, **get_mansions(date)**, **get_fixed_stars()**.

El GPT **nunca interpreta sin datos**: primero llama a las Actions y **después** responde.

---

## 6) UX y seguridad
- UI nativa del chat (`/abu`): mejor control de flujos, perfil, y persistencia.  
- JWT y CORS para Actions. No exponer claves del GPT en el cliente.  
- Telemetría (duración, tokens, endpoints usados) para tuning de costos.

---

## 7) Roadmap resumido
1. Integrar casas (Swiss), RS y tránsitos en Abu Engine.  
2. Publicar endpoints mínimos y smoke tests.  
3. Crear GPT “Abu Interpreter” con doctrina persa + Actions.  
4. Implementar `/abu` con Assistants API y estado de sesión.  
5. Lanzar beta privada; medir latencia y costos; iterar prompts y datos.