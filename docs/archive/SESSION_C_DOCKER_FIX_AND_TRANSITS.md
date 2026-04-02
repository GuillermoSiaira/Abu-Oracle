# Session Log — Sesión 10 (Claude Sonnet 4.6)
**Fecha:** 2026-03-12
**Branch:** `integration/docker-rebuild`
**Estado al entrar:** Contenedores levantados, autocomplete ciudad roto, Ascendente incorrecto.

---

## Contexto heredado de sesión anterior (Opus 4.6)
- Session 9 completada: Cross-validation LOSO HF v4 (26/26 folds)
- Pending: #7 narrativas Lilly, rebuild Docker
- Último rebuild había roto el autocomplete de ciudad

---

## Trabajos realizados

### 1. Fix Docker networking — Autocomplete de ciudades
**Problema:** `NEXT_PUBLIC_ABU_URL=http://abu_engine:8000` se bakea en el bundle. El browser no resuelve hostnames Docker internos.
**Solución:**
- Nuevo proxy: `next_app/app/api/cities/search/route.ts` (server-side → Abu interno)
- `CityAutocomplete` ahora usa `/api/cities/search` (URL relativa)
- `docker-compose.yml`: build arg `NEXT_PUBLIC_ABU_URL=http://localhost:8000`, runtime `ABU_ENGINE_URL=http://abu_engine:8000`
- `Dockerfile` next_app: `ENV NODE_OPTIONS=--max_old_space_size=2048` (previene OOM kill en npm build)

### 2. Ciudades: 60 → 144,563
- Regenerado `abu_engine/data/cities.json` desde `data/external/worldcities.csv`
- `main.py`: cache en memoria al startup, búsqueda prioriza starts-with antes de contains
- `relocation.py`: corregido `CITIES_PATH` que apuntaba fuera del container, migrado de CSV a JSON

### 3. BirthDataPanel — Upgrade del formulario
Nuevos campos:
- **Nombre**: persiste en `localStorage` con clave `ai-oracle-profile-v1` (sobrevive clearAll)
- **Huso horario (UTC offset)**: input numérico con default = browser timezone
- **Ciudad de residencia actual**: segundo autocomplete, pre-poblado con ciudad natal
- **Proyección futura** (toggle): ciudad objetivo + fecha objetivo

`buildISODate(localDate, offsetHours)` convierte local → UTC matemáticamente antes de enviar.

### 4. Bug crítico: Ascendente/MC incorrectos
**Causa raíz:** `houses_swiss.py` en `swe.julday()` usaba `dt.hour/minute` directamente sin convertir a UTC primero. Si el datetime tenía timezone offset, se ignoraba.
**Fix:** `dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo is not None else dt`
**Verificado:** con `1978-07-06T00:15:00Z` → ASC Acuario 26.9° ✅ (referencia: Acuario 26°52')

### 5. TransitsTab — Reescrito completo
Antes: solo posición lunar + aspectos lunares.
Ahora:
- Fetch a `POST /api/astro/transits/with-natal` (todos los planetas)
- Agrupado por planeta transitante (orden: Plutón → Luna)
- Colores por tipo de aspecto (conjunción=ámbar, trígono=verde, cuadratura=naranja, oposición=rojo)
- Badge aplicante (verde) / separante (gris)
- Orbe < 1° resaltado en ámbar como "exacto"

### 6. Zustand store — userName
- `userName: string` con clave de persistencia separada `ai-oracle-profile-v1`
- `setUserName(name)` guarda en localStorage y en estado
- `clearAll()` preserva el nombre intencionalmente

---

## Estado de builds al cerrar ventana
- `abu_engine`: rebuild en progreso (pip install ~90% completado)
- `next_app`: pendiente rebuild con `--no-cache`

## Comando para próxima sesión (ejecutar primero)
```bash
# Esperar que termine abu_engine si sigue corriendo, luego:
docker ps  # verificar abu_engine está UP
docker-compose build --no-cache next_app && docker-compose up -d next_app
```

---

## Pendientes para próxima sesión

### Verificación inmediata
- [ ] Confirmar ASC Acuario 26° en el form actualizado (cabio de birth-data-panel + houses_swiss)
- [ ] Confirmar que relocalización ya no falla con Error 500
- [ ] Ver TransitsTab con datos reales en browser

### Features por implementar
1. **Módulo Pronóstico** (próxima tarea grande):
   - Timeline de tránsitos lentos (Júp/Sat/Ura/Nep/Plu) vs natales
   - Para cada tránsito: fecha inicio, fecha exacta (orb=0), fecha fin
   - Superponer curva HF weighted sobre el timeline
   - Necesita: nuevo endpoint en Abu o usar forecast + transits combinados
   - Referencia de diseño: archivo "Pronostico General 2026" (Grupo Venus)

2. **Rueda zodiacal con tránsitos** (overlay):
   - Anillo exterior en `zodiac-wheel.tsx` con posiciones actuales
   - Líneas de aspecto entre natales y tránsitos
   - Necesita: datos de `chart-detailed` para fecha actual

3. **Narrativas personales con Lilly** (Tarea #7)
4. **Cacheo HF** (Tarea #11)
5. **Sustento científico** — expandir `HF_THEORETICAL_FRAMEWORK.md`

---

## Archivos modificados en esta sesión
```
abu_engine/data/cities.json              — regenerado (144K ciudades)
abu_engine/main.py                       — cities cache en memoria al startup
abu_engine/services/relocation.py        — CITIES_PATH + _load_cities() JSON
abu_engine/core/houses_swiss.py          — FIX timezone en swe.julday()
next_app/app/api/cities/search/route.ts  — NUEVO: proxy server-side
next_app/components/city-autocomplete.tsx — URL relativa + label/placeholder props
next_app/components/birth-data-panel.tsx  — nombre + UTC offset + residencia + futuro
next_app/components/transits-tab.tsx      — reescrito completo
next_app/lib/types.ts                     — BirthData expandido
next_app/lib/store.ts                     — userName + PROFILE_KEY
next_app/Dockerfile                       — NODE_OPTIONS=--max_old_space_size=2048
docker-compose.yml                        — separación ABU_ENGINE_URL vs NEXT_PUBLIC_ABU_URL
```
