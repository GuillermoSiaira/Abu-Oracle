# MU-C01 — Mundana Tab: Calendario del Año + Cielo Ahora

**Fecha:** 2026-05-08  
**Track:** Mundana  
**Prioridad:** Alta — el tab actualmente muestra vacío cuando no hay configs estadísticas  
**Independiente de:** QA-C01, FI-C01, KG-C03

---

## Objetivo

Reescribir `MundanaTab` para que siempre muestre contenido útil, organizado en tres secciones:

1. **Cielo Ahora** — posiciones planetarias actuales, siempre visible
2. **Calendario del Año** — próximos eventos mundanos de los siguientes 12 meses, siempre visible
3. **Configuraciones Destacadas** — solo cuando hay configs estadísticamente significativas (contenido actual)

---

## Backend: nuevo endpoint `GET /api/mundana/calendar`

### Archivo: `abu_engine/routers/mundana.py` (agregar endpoint)

```python
@router.get("/api/mundana/calendar")
async def mundana_calendar(
    months: int = Query(default=12, ge=1, le=24),
    _: str = Depends(verify_token),
):
    """
    Retorna:
    - current_sky: posiciones planetarias actuales + configs activas
    - calendar: lista cronológica de eventos mundanos próximos (eclipses,
      Mercurio retrógrado, ingresos de planetas lentos, configs validadas, stelliums)
    """
    from core.mundana import get_current_sky, get_upcoming_configurations
    from core.mundana_calendar import build_mundana_calendar
    import swisseph as swe
    from datetime import datetime, timezone

    now     = datetime.now(timezone.utc)
    jd_now  = swe.julday(now.year, now.month, now.day,
                          now.hour + now.minute/60 + now.second/3600)

    current = get_current_sky()
    calendar_events = build_mundana_calendar(jd_now, months_ahead=months)

    return {
        "current_sky": current,
        "calendar":    calendar_events,
    }
```

---

### Archivo a crear: `abu_engine/core/mundana_calendar.py`

```python
"""
mundana_calendar.py

Genera una lista cronológica de eventos mundanos para los próximos N meses.

Tipos de evento:
  - eclipse_solar
  - eclipse_lunar
  - mercury_retrograde   (estación retrógrada)
  - mercury_direct       (estación directa)
  - planet_ingress       (Júpiter o Saturno entra en nuevo signo)
  - configuration        (configs estadísticamente validadas — JS, MS)
  - stellium             (≥4 planetas en mismo signo)
"""

import swisseph as swe
from datetime import datetime, timezone, timedelta
from typing import Optional

SIGNS_ES = [
    "Aries","Tauro","Géminis","Cáncer","Leo","Virgo",
    "Libra","Escorpio","Sagitario","Capricornio","Acuario","Piscis",
]

PLANET_SYMBOLS = {
    swe.SUN: "☉",  swe.MOON: "☽",   swe.MERCURY: "☿",
    swe.VENUS: "♀", swe.MARS: "♂",   swe.JUPITER: "♃",
    swe.SATURN: "♄", swe.URANUS: "♅", swe.NEPTUNE: "♆",
    swe.PLUTO: "♇",
}

PLANET_NAMES_ES = {
    swe.SUN: "Sol",  swe.MOON: "Luna",    swe.MERCURY: "Mercurio",
    swe.VENUS: "Venus", swe.MARS: "Marte", swe.JUPITER: "Júpiter",
    swe.SATURN: "Saturno", swe.URANUS: "Urano",
    swe.NEPTUNE: "Neptuno", swe.PLUTO: "Plutón",
}


def _jd_to_iso(jd: float) -> str:
    """Convierte Julian Day a string ISO 8601 (fecha únicamente)."""
    y, m, d, _ = swe.revjul(jd)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _get_sign(lon: float) -> str:
    return SIGNS_ES[int(lon // 30) % 12]


def _planet_lon(planet_id: int, jd: float) -> float:
    result, _ = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return result[0]


def _planet_speed(planet_id: int, jd: float) -> float:
    """Velocidad longitudinal en grados/día. Negativo = retrógrado."""
    result, _ = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return result[3]


# ── Eclipses ──────────────────────────────────────────────────────────────────

def _collect_eclipses(jd_start: float, jd_end: float) -> list[dict]:
    events = []
    jd = jd_start

    # Eclipses solares
    while jd < jd_end:
        retval, tret = swe.sol_eclipse_when_glob(jd + 1, swe.FLG_SWIEPH, 0)
        if retval < 0 or tret[0] <= 0 or tret[0] >= jd_end:
            break
        lon, _ = swe.calc_ut(tret[0], swe.SUN, swe.FLG_SWIEPH)
        sign = _get_sign(lon[0])
        eclipse_type = (
            "Total" if retval & 4 else
            "Anular" if retval & 2 else
            "Híbrido" if retval & 8 else "Parcial"
        )
        events.append({
            "type":         "eclipse_solar",
            "date":         _jd_to_iso(tret[0]),
            "jd":           tret[0],
            "description":  f"Eclipse Solar {eclipse_type} · {sign}",
            "significance": "high",
            "icon":         "☉🌑",
            "details":      { "eclipse_type": eclipse_type, "sign": sign },
        })
        jd = tret[0] + 10

    # Eclipses lunares
    jd = jd_start
    while jd < jd_end:
        retval, tret = swe.lun_eclipse_when(jd + 1, swe.FLG_SWIEPH, 0)
        if retval < 0 or tret[0] <= 0 or tret[0] >= jd_end:
            break
        lon, _ = swe.calc_ut(tret[0], swe.MOON, swe.FLG_SWIEPH)
        sign = _get_sign(lon[0])
        eclipse_type = (
            "Total"    if retval & 4  else
            "Parcial"  if retval & 16 else "Penumbral"
        )
        events.append({
            "type":         "eclipse_lunar",
            "date":         _jd_to_iso(tret[0]),
            "jd":           tret[0],
            "description":  f"Eclipse Lunar {eclipse_type} · {sign}",
            "significance": "high" if eclipse_type == "Total" else "medium",
            "icon":         "☽🌑",
            "details":      { "eclipse_type": eclipse_type, "sign": sign },
        })
        jd = tret[0] + 10

    return events


# ── Mercurio retrógrado ───────────────────────────────────────────────────────

def _collect_mercury_stations(jd_start: float, jd_end: float) -> list[dict]:
    """
    Escanea cada 5 días buscando cambio de signo en la velocidad de Mercurio.
    Cuando speed cruza 0 → bisección para encontrar el momento exacto.
    """
    events = []
    step   = 5.0
    jd     = jd_start
    prev_speed = _planet_speed(swe.MERCURY, jd)

    while jd < jd_end:
        jd += step
        curr_speed = _planet_speed(swe.MERCURY, jd)

        if prev_speed * curr_speed < 0:
            # Cambio de signo: bisección
            lo, hi = jd - step, jd
            for _ in range(20):
                mid = (lo + hi) / 2
                if _planet_speed(swe.MERCURY, mid) * prev_speed < 0:
                    hi = mid
                else:
                    lo = mid
            exact_jd = (lo + hi) / 2
            lon = _planet_lon(swe.MERCURY, exact_jd)
            sign = _get_sign(lon)
            is_rx = curr_speed < 0

            events.append({
                "type":         "mercury_retrograde" if is_rx else "mercury_direct",
                "date":         _jd_to_iso(exact_jd),
                "jd":           exact_jd,
                "description":  f"Mercurio {'retrógrado' if is_rx else 'directo'} en {sign}",
                "significance": "medium",
                "icon":         "☿℞" if is_rx else "☿D",
                "details":      { "sign": sign, "retrograde": is_rx },
            })

        prev_speed = curr_speed

    return events


# ── Ingresos de Júpiter y Saturno ─────────────────────────────────────────────

def _collect_planet_ingresses(jd_start: float, jd_end: float) -> list[dict]:
    events = []
    outer_planets = [
        (swe.JUPITER, "Júpiter", "♃"),
        (swe.SATURN,  "Saturno", "♄"),
    ]

    for planet_id, name, symbol in outer_planets:
        step = 10.0
        jd   = jd_start
        prev_sign = _get_sign(_planet_lon(planet_id, jd))

        while jd < jd_end:
            jd += step
            curr_lon  = _planet_lon(planet_id, jd)
            curr_sign = _get_sign(curr_lon)

            if curr_sign != prev_sign:
                # Bisección para ingreso exacto
                lo, hi = jd - step, jd
                for _ in range(20):
                    mid = (lo + hi) / 2
                    if _get_sign(_planet_lon(planet_id, mid)) == prev_sign:
                        lo = mid
                    else:
                        hi = mid
                exact_jd = (lo + hi) / 2

                events.append({
                    "type":         "planet_ingress",
                    "date":         _jd_to_iso(exact_jd),
                    "jd":           exact_jd,
                    "description":  f"{name} ingresa en {curr_sign}",
                    "significance": "high" if planet_id == swe.SATURN else "medium",
                    "icon":         symbol,
                    "details":      { "planet": name, "sign": curr_sign, "from_sign": prev_sign },
                })
                prev_sign = curr_sign

    return events


# ── Configuraciones validadas (JS, MS) ───────────────────────────────────────

def _collect_validated_configs(jd_start: float, jd_end: float) -> list[dict]:
    """
    Reutiliza get_upcoming_configurations() del módulo mundana.
    Solo incluye configs con p_value < 0.1 (umbral relajado para calendario).
    """
    try:
        from core.mundana import get_upcoming_configurations
        days = int(jd_end - jd_start)
        configs = get_upcoming_configurations(days_ahead=days)
        events = []
        for c in configs:
            if c.get("p_value") is None or c["p_value"] > 0.1:
                continue
            events.append({
                "type":         "configuration",
                "date":         c.get("exact_date", "")[:10],
                "jd":           jd_start,  # aproximado — no crítico para sort
                "description":  c.get("description", c.get("type", "Configuración")),
                "significance": c.get("significance", "medium"),
                "icon":         "⚡",
                "details":      c,
            })
        return events
    except Exception:
        return []


# ── Entry point ───────────────────────────────────────────────────────────────

def build_mundana_calendar(jd_start: float, months_ahead: int = 12) -> list[dict]:
    """
    Compila y ordena todos los eventos mundanos para los próximos N meses.
    Retorna lista ordenada por fecha ascendente.
    """
    jd_end = jd_start + months_ahead * 30.44  # aproximación días/mes

    all_events: list[dict] = []
    all_events += _collect_eclipses(jd_start, jd_end)
    all_events += _collect_mercury_stations(jd_start, jd_end)
    all_events += _collect_planet_ingresses(jd_start, jd_end)
    all_events += _collect_validated_configs(jd_start, jd_end)

    # Ordenar por fecha
    all_events.sort(key=lambda e: e.get("date", "9999"))

    # Limpiar campo interno jd del output
    for e in all_events:
        e.pop("jd", None)

    return all_events
```

---

## Frontend: reescritura de `MundanaTab`

### Estructura de tres secciones

```tsx
// next_app/components/mundana-tab.tsx — reescritura completa

export function MundanaTab() {
  // Estado
  const [calendarData, setCalendarData] = useState<MundanaCalendarResponse | null>(null);
  const [loading, setLoading] = useState(true);
  
  const { lang, abuData, birthData, setPendingLillyEvent } = useAppStore();
  const t = UI[lang] ?? UI.es;

  // Fetch único al montar (o cuando cambia el sujeto)
  useEffect(() => {
    setLoading(true);
    const url = new URL(`${ABU_BASE_URL}/api/mundana/calendar`);
    url.searchParams.set('months', '12');
    
    getAbuAuthHeaders()
      .then(headers => fetch(url.toString(), { headers }))
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setCalendarData(data); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 space-y-6">
      {/* ── SECCIÓN 1: Cielo Ahora ── */}
      <CieloAhoraSection data={calendarData?.current_sky} loading={loading} lang={lang} />

      {/* ── SECCIÓN 2: Calendario del Año ── */}
      <CalendarioSection events={calendarData?.calendar ?? []} loading={loading} lang={lang} />

      {/* ── SECCIÓN 3: Configuraciones Destacadas (condicional) ── */}
      {(calendarData?.current_sky?.active_configurations?.length ?? 0) > 0 && (
        <ConfiguracionesSection
          configs={calendarData!.current_sky.active_configurations}
          lang={lang}
          onConfigClick={(c) => setPendingLillyEvent({ type: 'mundana_config', payload: { config: c, lang } })}
        />
      )}
    </div>
  );
}
```

---

### Subcomponente: `CieloAhoraSection`

Muestra posiciones planetarias actuales en una grilla 2×5.

```tsx
function CieloAhoraSection({ data, loading, lang }: { data: any; loading: boolean; lang: string }) {
  if (loading) return <div className="h-24 rounded-md bg-slate-800/60 animate-pulse" />;

  const planets = data?.planets ?? [];

  return (
    <div>
      <h3 className="text-[11px] font-semibold tracking-widest uppercase text-amber-400/70 mb-3">
        Cielo Ahora
      </h3>
      <div className="grid grid-cols-2 gap-1.5">
        {planets.map((p: any) => (
          <div key={p.name}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-slate-800/40 border border-slate-700/30">
            <span className="text-[13px] font-mono text-slate-300 w-5 shrink-0 text-center">
              {PLANET_SYMBOLS[p.name] ?? p.name[0]}
            </span>
            <span className="text-[11px] text-slate-400 shrink-0 w-[70px] truncate">{p.name}</span>
            <span className="text-[11px] text-slate-300 font-mono ml-auto">
              {p.sign} {p.degree?.toFixed(1)}°
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### Subcomponente: `CalendarioSection`

Lista cronológica con indicador visual de significancia.

```tsx
const SIGNIFICANCE_STYLES: Record<string, string> = {
  high:   'border-l-amber-400/80  bg-amber-400/5',
  medium: 'border-l-slate-500/60  bg-slate-800/30',
  low:    'border-l-slate-700/40  bg-slate-800/20',
};

const EVENT_TYPE_LABELS: Record<string, Record<string, string>> = {
  eclipse_solar:      { es: 'Eclipse Solar',    en: 'Solar Eclipse',   pt: 'Eclipse Solar',  fr: 'Éclipse Solaire'  },
  eclipse_lunar:      { es: 'Eclipse Lunar',    en: 'Lunar Eclipse',   pt: 'Eclipse Lunar',  fr: 'Éclipse Lunaire'  },
  mercury_retrograde: { es: 'Mercurio Rx',      en: 'Mercury Rx',      pt: 'Mercúrio Rx',    fr: 'Mercure Rx'       },
  mercury_direct:     { es: 'Mercurio Directo', en: 'Mercury Direct',  pt: 'Mercúrio Direto',fr: 'Mercure Direct'   },
  planet_ingress:     { es: 'Ingreso',          en: 'Ingress',         pt: 'Ingresso',        fr: 'Entrée'          },
  configuration:      { es: 'Configuración',    en: 'Configuration',   pt: 'Configuração',    fr: 'Configuration'   },
};

function CalendarioSection({ events, loading, lang }: { events: any[]; loading: boolean; lang: string }) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1,2,3,4].map(i => (
          <div key={i} className="h-10 rounded bg-slate-800/50 animate-pulse"
            style={{ opacity: 1 - i * 0.18 }} />
        ))}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <p className="text-[11px] text-slate-600 italic py-2">
        No hay eventos destacados en los próximos 12 meses.
      </p>
    );
  }

  // Agrupar por mes
  const byMonth: Record<string, any[]> = {};
  for (const ev of events) {
    const month = ev.date?.slice(0, 7) ?? 'unknown';
    if (!byMonth[month]) byMonth[month] = [];
    byMonth[month].push(ev);
  }

  return (
    <div>
      <h3 className="text-[11px] font-semibold tracking-widest uppercase text-slate-500 mb-3">
        Próximos 12 meses
      </h3>
      <div className="space-y-4">
        {Object.entries(byMonth).map(([month, monthEvents]) => (
          <div key={month}>
            {/* Header de mes */}
            <div className="text-[10px] text-slate-600 font-mono uppercase tracking-widest mb-1.5 pl-1">
              {new Date(month + '-01').toLocaleDateString(
                lang === 'en' ? 'en-US' : lang === 'pt' ? 'pt-BR' : lang === 'fr' ? 'fr-FR' : 'es-ES',
                { month: 'long', year: 'numeric' }
              )}
            </div>
            {/* Eventos del mes */}
            <div className="space-y-1">
              {monthEvents.map((ev, i) => (
                <div key={i}
                  className={`flex items-center gap-3 px-3 py-2 rounded border-l-2
                    ${SIGNIFICANCE_STYLES[ev.significance] ?? SIGNIFICANCE_STYLES.low}`}>
                  <span className="text-[13px] shrink-0 w-6 text-center font-mono">
                    {ev.icon}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-[11px] text-slate-300 truncate">{ev.description}</div>
                    <div className="text-[10px] text-slate-600 font-mono">
                      {EVENT_TYPE_LABELS[ev.type]?.[lang] ?? EVENT_TYPE_LABELS[ev.type]?.es ?? ev.type}
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-600 font-mono shrink-0">
                    {ev.date?.slice(5)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### Subcomponente: `ConfiguracionesSection`

Mueve el contenido actual de MundanaTab (configs estadísticas) aquí sin cambios de lógica.
Solo se renderiza cuando `configs.length > 0`.

```tsx
function ConfiguracionesSection({ configs, lang, onConfigClick }: {
  configs: any[];
  lang: string;
  onConfigClick: (c: any) => void;
}) {
  return (
    <div className="pt-4 border-t border-slate-800/60">
      <h3 className="text-[11px] font-semibold tracking-widest uppercase text-amber-400/70 mb-3">
        Configuraciones Estadísticas Activas
      </h3>
      {/* ... mismas tarjetas que el MundanaTab actual ... */}
    </div>
  );
}
```

---

## TypeScript: tipos

```typescript
// Agregar en next_app/lib/types.ts o inline en mundana-tab.tsx

interface MundanaCalendarResponse {
  current_sky: {
    timestamp: string;
    planets?: Array<{ name: string; sign: string; degree: number; symbol: string }>;
    active_configurations: any[];
  };
  calendar: Array<{
    type: string;
    date: string;
    description: string;
    significance: 'high' | 'medium' | 'low';
    icon: string;
    details: Record<string, unknown>;
  }>;
}
```

---

## Proxy Next.js

Agregar en `next_app/app/api/mundana/calendar/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getAbuAuthHeaders } from '@/lib/abu-auth';

const ABU = process.env.ABU_ENGINE_URL ?? process.env.NEXT_PUBLIC_ABU_URL ?? 'http://localhost:8000';

export async function GET(req: NextRequest) {
  const months = req.nextUrl.searchParams.get('months') ?? '12';
  const headers = await getAbuAuthHeaders().catch(() => ({} as Record<string, string>));
  const res = await fetch(`${ABU}/api/mundana/calendar?months=${months}`, { headers });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
```

---

## Tests

```bash
# Verificar que el endpoint responde
curl "http://localhost:8000/api/mundana/calendar?months=6" \
  -H "Authorization: Bearer $TEST_TOKEN" | python -m json.tool | head -60

# Debe retornar current_sky.planets + calendar con ≥1 evento
```

---

## Criterios de aceptación

- [ ] `GET /api/mundana/calendar` responde con `current_sky` + `calendar` (array no vacío para 12 meses)
- [ ] `calendar` incluye al menos eclipses y estaciones de Mercurio Rx para los próximos 12 meses
- [ ] Ingresos de Júpiter/Saturno aparecen si ocurren en la ventana
- [ ] MundanaTab siempre muestra contenido (Sección 1 + Sección 2 independientemente de configs estadísticas)
- [ ] Sección 3 solo se muestra cuando `active_configurations.length > 0`
- [ ] Eventos agrupados por mes con header de mes legible
- [ ] Border izquierdo amber para eventos `high`, gris para `medium`
- [ ] `npx tsc --noEmit` sin errores nuevos

---

## Deploy

Este spec requiere deploy de **ambos servicios**:

```bash
# Abu Engine (nuevo módulo mundana_calendar.py + endpoint)
gcloud builds submit --config=cloudbuild-engine.yaml --project=abu-oracle .

# Next.js app (MundanaTab reescrito + proxy route)
gcloud builds submit --config=cloudbuild-app.yaml --project=abu-oracle .
```

---

## Commit sugerido

```
feat(mundana): calendar tab — always-on sky view + year events (MU-C01)

- core/mundana_calendar.py: eclipses, Mercury Rx, planet ingresses, validated configs
- routers/mundana.py: GET /api/mundana/calendar?months=N
- app/api/mundana/calendar/route.ts: Next.js proxy
- components/mundana-tab.tsx: 3-section rewrite
  - Section 1: current planetary positions (always visible)
  - Section 2: chronological year calendar grouped by month
  - Section 3: statistical configurations (conditional)
```
