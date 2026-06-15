// ──────────────────────────────────────────────────────────────────────────────
// context-builder.ts — Context Builder canónico de Abu Oracle
//
// Produce el contextBlock estructurado que recibe Lilly en cada interacción.
// Reemplaza buildBaseContext() (lilly-prompt.ts) y los contextBlocks ad-hoc
// de cada route. La migración de routes es el PASO 4 (instrucción separada).
//
// Fuentes de datos:
//   NatalContext      ← abuData (response de /analyze) + birthData opcional
//   BiographicalTimeline ← response de /api/astro/biography
//   ActiveContext     ← estado UI en el momento del evento
// ──────────────────────────────────────────────────────────────────────────────

// ── Helpers internos ─────────────────────────────────────────────────────────

const _SIGNS = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
];

const _RULERS: Record<string, string> = {
  Aries: "Mars",    Taurus: "Venus",   Gemini: "Mercury", Cancer: "Moon",
  Leo: "Sun",       Virgo: "Mercury",  Libra: "Venus",    Scorpio: "Mars",
  Sagittarius: "Jupiter", Capricorn: "Saturn", Aquarius: "Saturn", Pisces: "Jupiter",
};

function _getSign(lon: number): string {
  return _SIGNS[Math.floor(((lon % 360) + 360) % 360 / 30)];
}

/** Reconstruye longitud eclíptica desde signo + grado en signo. */
function _lonFromSignDeg(sign: string, deg: number): number {
  const idx = _SIGNS.indexOf(sign);
  return (idx < 0 ? 0 : idx) * 30 + deg;
}

const _PHASE_NAMES = [
  "Nueva", "Creciente Cóncava", "Cuarto Creciente", "Creciente Gibosa",
  "Llena", "Menguante Gibosa", "Cuarto Menguante", "Menguante Cóncava",
];

/** Devuelve nombre y porcentaje de la fase lunar natal (elongación Sol→Luna). */
function _natalLunarPhase(planets: NatalContext["planets"]): { name: string; pct: string } | null {
  const sun  = planets.find(p => p.name === "Sun");
  const moon = planets.find(p => p.name === "Moon");
  if (!sun || !moon) return null;
  const sunLon  = _lonFromSignDeg(sun.sign, sun.deg);
  const moonLon = _lonFromSignDeg(moon.sign, moon.deg);
  const elongation = ((moonLon - sunLon) % 360 + 360) % 360;
  const phaseIdx   = Math.floor((elongation / 360) * 8) % 8;
  const pct        = (elongation / 360 * 100).toFixed(1);
  return { name: _PHASE_NAMES[phaseIdx], pct };
}

/**
 * Detecta convergencia temporal: profección + firdaria + tránsito lento activo
 * cierran en una ventana de 30 días.
 * Devuelve el bloque de texto para Lilly, o null si no hay convergencia.
 */
function _detectConvergence(timeline: BiographicalTimeline, lang: string): string | null {
  const activeProf = timeline.profections.find(p => p.is_active);
  const activeFird = timeline.firdaria.find(f => f.is_active);
  if (!activeProf || !activeFird) return null;

  const profEnd  = new Date(activeProf.date_end).getTime();
  const firdEnd  = new Date(activeFird.date_end).getTime();
  const diff = Math.abs(profEnd - firdEnd) / (1000 * 60 * 60 * 24);
  if (diff > 30) return null;

  const activeSlowTransits = timeline.transits_window.filter(
    t => t.is_active && (t.speed_class === "slow" || !t.speed_class)
  );
  if (activeSlowTransits.length === 0) return null;

  const windowStart = new Date(Math.min(profEnd, firdEnd)).toISOString().slice(0, 10);
  const windowEnd   = new Date(Math.max(profEnd, firdEnd)).toISOString().slice(0, 10);
  const transitDesc = activeSlowTransits
    .slice(0, 2)
    .map(t => `${localizePlanet(t.transit_planet, lang)} ${t.aspect} ${localizePlanet(t.natal_planet, lang)}`)
    .join(", ");

  const activeIdx = timeline.profections.findIndex(p => p.is_active);
  const nextProf  = timeline.profections[activeIdx + 1];
  const nextHouse = nextProf ? `Casa ${nextProf.house}` : "nueva casa";

  const lines = [
    "VENTANA DE CONVERGENCIA",
    `${windowStart} — ${windowEnd}`,
    `Cambio de profección a ${nextHouse} · Cierre Firdaria ${localizePlanet(activeFird.minor_planet, lang)}/${localizePlanet(activeFird.major_planet, lang)} · ${transitDesc}`,
    "Tres técnicas convergen en este período.",
  ];
  return lines.join("\n");
}

function _getDegInSign(lon: number): number {
  return ((lon % 360) + 360) % 360 % 30;
}

/** Convierte el objeto de dignidad del backend (flags booleanos o campo kind) a string lowercase. */
function _dignityStr(d: any): string {
  if (!d) return "peregrine";
  if (typeof d === "string") return d.toLowerCase();
  if (d.kind)        return (d.kind as string).toLowerCase();
  if (d.domicile)    return "domicile";
  if (d.exaltation)  return "exaltation";
  if (d.detriment)   return "detriment";
  if (d.fall)        return "fall";
  return "peregrine";
}

/** Capitaliza primera letra para display. */
function _cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const _PLANETS_ES: Record<string, string> = {
  Sun: "Sol", Moon: "Luna", Mercury: "Mercurio", Venus: "Venus", Mars: "Marte",
  Jupiter: "Júpiter", Saturn: "Saturno", Uranus: "Urano", Neptune: "Neptuno", Pluto: "Plutón",
  "North Node": "Nodo Norte", "South Node": "Nodo Sur"
};
const _PLANETS_PT: Record<string, string> = {
  Sun: "Sol", Moon: "Lua", Mercury: "Mercúrio", Venus: "Vênus", Mars: "Marte",
  Jupiter: "Júpiter", Saturn: "Saturno", Uranus: "Urano", Neptune: "Netuno", Pluto: "Plutão",
  "North Node": "Nodo Norte", "South Node": "Nodo Sul"
};
const _PLANETS_FR: Record<string, string> = {
  Sun: "Soleil", Moon: "Lune", Mercury: "Mercure", Venus: "Vénus", Mars: "Mars",
  Jupiter: "Jupiter", Saturn: "Saturne", Uranus: "Uranus", Neptune: "Neptune", Pluto: "Pluton",
  "North Node": "Nœud Nord", "South Node": "Nœud Sud"
};

export function localizePlanet(name: string, lang: string): string {
  if (name === "ASC" || name === "MC" || name === "—" || !name) return name;
  if (lang === "es") return _PLANETS_ES[name] ?? name;
  if (lang === "pt") return _PLANETS_PT[name] ?? name;
  if (lang === "fr") return _PLANETS_FR[name] ?? name;
  return name;
}

/** Mapea el nivel de densidad a una etiqueta legible. */
function _densityLabel(density: string, lang: string): string {
  const labels: Record<string, Record<string, string>> = {
    high:   { es: "Alta", en: "High", pt: "Alta", fr: "Haute" },
    medium: { es: "Media", en: "Medium", pt: "Média", fr: "Moyenne" },
    low:    { es: "Baja", en: "Low", pt: "Baixa", fr: "Faible" },
  };
  const d = density.toLowerCase();
  return labels[d]?.[lang] ?? labels.medium[lang];
}

// ── Interfaces exportadas ─────────────────────────────────────────────────────

export interface PlanetPosition {
  name:          string
  sign:          string
  /** Grado dentro del signo (0–30) */
  deg:           number
  house:         number
  /** Dignidad esencial como string lowercase: "domicile" | "exaltation" | "detriment" | "fall" | "peregrine" */
  dignity:       string
  dignity_score: number
  retrograde:    boolean
}

export interface NatalContext {
  subject_name:  string
  birth_dt:      string
  birth_city:    string
  house_system:  string
  sect:          string
  sect_master:   string
  asc: {
    sign:         string
    deg:          number
    lord:         string
    lord_dignity: string
  }
  mc: {
    sign:         string
    deg:          number
    lord:         string
    lord_dignity: string
  }
  /** Siempre === asc.sign — ancla explícita para evitar confusión con la casa profectada */
  house_1_sign:  string
  planets:       PlanetPosition[]
  aspects: Array<{
    planet_a: string
    planet_b: string
    type:     string
    orb:      number
    applying: boolean
  }>
  lots: {
    fortuna: { sign: string; deg: number; house: number; lord: string }
    spirit:  { sign: string; deg: number; house: number; lord: string }
  }
  house_significators: Record<number, string[]>
}

export interface BiographicalTimeline {
  profections: Array<{
    year_of_life: number
    house:        number
    sign:         string
    lord:         string
    lord_dignity: string
    date_start:   string
    date_end:     string
    is_active:    boolean
  }>
  firdaria: Array<{
    major_planet: string
    minor_planet: string
    date_start:   string
    date_end:     string
    is_active:    boolean
  }>
  transits_window: Array<{
    transit_planet: string
    natal_planet:   string
    aspect:         string
    exact_date:     string
    ingress_date:   string
    egress_date:    string
    is_active:      boolean
    speed_class?:   string
    transit_lon?:   number
  }>
}

export interface MundanaEvent {
  name:                string
  is_active:           boolean
  historical_density:  'high' | 'medium' | 'low'
  description:         string
  historical_context?: string
  exact_date?:         string
  days_to_exact?:      number
  transit_planets?:    string[]
}

export interface ActiveContext {
  current_date:     string
  /** Fecha local del usuario (YYYY-MM-DD), derivada de utcOffsetHours si se provee. */
  user_local_date?: string
  active_tab:       string
  active_domain:    string | null
  active_city: {
    name:     string
    lat:      number
    lon:      number
    hf_score: number
  } | null
  last_event_type: string
  trigger_data:    Record<string, unknown>
}

// ── formatLunarContext ────────────────────────────────────────────────────────

/** Marca temporal relativa a hoy. Pasado se marca EXPLÍCITO para que el modelo
 *  no hable de un tránsito ya ocurrido como si fuera futuro. Server-side: Date.now() es UTC. */
const daysUntil = (isoStr: string): string => {
  if (!isoStr) return '';
  try {
    const target = new Date(isoStr.length === 10 ? `${isoStr}T00:00:00Z` : isoStr);
    const diff = Math.round((target.getTime() - Date.now()) / 86_400_000);
    if (diff < 0) {
      const ago = -diff;
      return ago === 1 ? ' · YA OCURRIÓ (ayer)' : ` · YA OCURRIÓ (hace ${ago} días)`;
    }
    if (diff === 0) return ' · hoy';
    if (diff === 1) return ' · mañana';
    return ` · en ${diff} días`;
  } catch { return ''; }
};

/** Convierte una diferencia de días en unidades humanas (días, meses, ~años). */
const _humanDeltaRaw = (diffDays: number): string => {
  const abs = Math.abs(diffDays);
  if (abs < 45) return `${abs} días`;
  if (abs < 730) return `${Math.round(abs / 30)} meses`;
  return `~${Math.round(abs / 365)} años`;
};

/** Formatea fechas con humanDelta indicando futuro/pasado. */
const humanDelta = (isoStr: string): string => {
  if (!isoStr) return '';
  try {
    const target = new Date(isoStr.length === 10 ? `${isoStr}T00:00:00Z` : isoStr);
    const diff = Math.round((target.getTime() - Date.now()) / 86_400_000);
    if (diff === 0) return 'hoy';
    if (diff === 1) return 'mañana';
    if (diff < 0) return `hace ${_humanDeltaRaw(diff)}`;
    return `en ${_humanDeltaRaw(diff)}`;
  } catch { return ''; }
};

/** Determina el estado temporal de un tránsito o paso en ventana. */
const transitTemporal = (ingress: string, egress: string, exact: string): string => {
  if (!exact) return '';
  const iStr = ingress || exact;
  const eStr = egress || exact;
  try {
    const tStart = new Date(iStr.length === 10 ? `${iStr}T00:00:00Z` : iStr).getTime();
    const tEnd = new Date(eStr.length === 10 ? `${eStr}T00:00:00Z` : eStr).getTime();
    const now = Date.now();
    const dEnd = Math.round((tEnd - now) / 86_400_000);
    const dStart = Math.round((tStart - now) / 86_400_000);

    if (dEnd < 0) {
      return ` · YA OCURRIÓ (${humanDelta(exact)}) [usar PASADO]`;
    }
    if (dStart <= 0 && dEnd >= 0) {
      return ` · EN CURSO (exacto: ${exact}) [usar PRESENTE]`;
    }
    return ` · COMIENZA ${humanDelta(iStr)} (exacto: ${exact}) [usar FUTURO]`;
  } catch { return ''; }
};

/**
 * Formatea datos del endpoint /api/astro/lunar para inyección en contextBlock.
 * Omite líneas cuyos valores sean null/undefined — never injects empty fields.
 */
export function formatLunarContext(lunarData: any): string {
  if (!lunarData) return '';
  const lines: string[] = [];

  const fmtDate = (iso: string): string => (iso ?? '').slice(0, 10);
  const fmtHouse = (sign: string, house: number | null | undefined): string =>
    house ? `${sign} · Casa ${house} natal` : sign;

  const phase = lunarData.phase;
  if (phase?.name) {
    lines.push(
      `Fase lunar actual: ${phase.name} (${Number(phase.pct ?? 0).toFixed(0)}% del ciclo)`
    );
  }

  const nm = lunarData.next_new_moon;
  if (nm?.dt && nm?.sign) {
    lines.push(`Próxima Luna Nueva: ${fmtDate(nm.dt)} · ${fmtHouse(nm.sign, nm.natal_house)}${daysUntil(nm.dt)}`);
  }

  const fm = lunarData.next_full_moon;
  if (fm?.dt && fm?.sign) {
    lines.push(`Próxima Luna Llena: ${fmtDate(fm.dt)} · ${fmtHouse(fm.sign, fm.natal_house)}${daysUntil(fm.dt)}`);
  }

  const se = lunarData.next_solar_eclipse;
  if (se?.dt && se?.sign) {
    lines.push(
      `Próximo Eclipse Solar: ${fmtDate(se.dt)} · ${se.type} · ${fmtHouse(se.sign, se.natal_house)}${daysUntil(se.dt)}`
    );
  }

  const le = lunarData.next_lunar_eclipse;
  if (le?.dt && le?.sign) {
    lines.push(
      `Próximo Eclipse Lunar: ${fmtDate(le.dt)} · ${le.type} · ${fmtHouse(le.sign, le.natal_house)}${daysUntil(le.dt)}`
    );
  }

  return lines.join('\n');
}

/**
 * Formatea el contexto de Astrología Mundana (Cielo Colectivo).
 */
export function formatMundanaContext(events: MundanaEvent[], lang: string): string {
  if (!events || events.length === 0) return "";
  const lines: string[] = [];

  const active = events.filter(e => e.is_active);
  const upcoming = events.filter(e => !e.is_active);

  if (active.length > 0) {
    lines.push("CONFIGURACIONES COLECTIVAS ACTIVAS");
    for (const e of active) {
      const density = _densityLabel(e.historical_density, lang);
      lines.push(`- ${e.name} (Densidad histórica: ${density})`);
      lines.push(`  Interpretación: ${e.description}`);
      if (e.historical_context) lines.push(`  Contexto: ${e.historical_context}`);
    }
    lines.push("");
  }

  if (upcoming.length > 0) {
    lines.push("CONFIGURACIONES COLECTIVAS PRÓXIMAS (90 días)");
    for (const e of upcoming) {
      const dateStr = e.exact_date ? ` · exacto: ${e.exact_date}` : "";
      const daysStr = e.days_to_exact != null ? ` (en ${e.days_to_exact} días)` : "";
      lines.push(`- ${e.name}${dateStr}${daysStr}`);
      lines.push(`  Potencial: ${e.description}`);
    }
  }

  return lines.join("\n");
}

// ── buildNatalContext ─────────────────────────────────────────────────────────

/**
 * Construye NatalContext desde el objeto abuData (response de /analyze).
 * birthData opcional para enriquecer con birth_dt y birth_city que no
 * están en el response del analyze pero sí en el store del frontend.
 */
export function buildNatalContext(
  abuData: any,
  birthData?: { birthDate?: string | null; city?: string | null; userName?: string | null; utcOffset?: number | null } | null,
): NatalContext {
  const planets: any[] = abuData?.chart?.planets ?? [];
  const housesObj       = abuData?.chart?.houses ?? {};
  const ascLon: number  = housesObj?.asc ?? 0;
  const mcLon:  number  = housesObj?.mc  ?? 0;
  const cusps:  any[]   = housesObj?.houses ?? [];

  // ── Planeta helper ───────────────────────────────────────────────────────
  function _findPlanet(name: string): any {
    return planets.find((p: any) => p.name === name);
  }
  function _planetDignity(name: string): string {
    return _dignityStr(_findPlanet(name)?.dignity);
  }

  // ── Ángulos ──────────────────────────────────────────────────────────────
  const ascSign = _getSign(ascLon);
  const ascLord = _RULERS[ascSign] ?? "—";

  const mcSign = _getSign(mcLon);
  const mcLord = _RULERS[mcSign] ?? "—";

  // ── Planetas mapeados ────────────────────────────────────────────────────
  const mappedPlanets: PlanetPosition[] = planets.map((p: any) => {
    const lon = p.longitude ?? p.lon ?? 0;
    return {
      name:          p.name ?? "?",
      sign:          p.sign || _getSign(lon),
      deg:           _getDegInSign(lon),
      house:         p.house ?? 0,
      dignity:       _dignityStr(p.dignity),
      dignity_score: p.dignity_score ?? 0,
      retrograde:    p.retrograde ?? false,
    };
  });

  // ── Aspectos (orbe < 3°) — si el response los incluye ───────────────────
  const rawAspects: any[] = abuData?.chart?.aspects ?? [];
  const filteredAspects = rawAspects
    .filter((a: any) => (a.orb ?? 99) < 3.0)
    .map((a: any) => ({
      planet_a: a.planet_a ?? a.planet1 ?? "",
      planet_b: a.planet_b ?? a.planet2 ?? "",
      type:     a.type ?? a.aspect ?? "",
      orb:      a.orb ?? 0,
      applying: a.applying ?? false,
    }));

  // ── Partes Arábicas ──────────────────────────────────────────────────────
  const lots: any[] = abuData?.derived?.lots ?? [];
  const _findLot = (names: string[]) => lots.find(
    (l: any) => names.some(n => (l.name ?? "").toLowerCase() === n.toLowerCase())
  );
  const fortunaRaw = _findLot(["fortuna", "Fortuna", "Fortune"]);
  const spiritRaw  = _findLot(["spirit", "Spirit", "Espíritu", "Espiritu"]);

  const _lotObj = (raw: any) => ({
    sign:  raw?.sign  ?? "—",
    deg:   raw?.degree ?? 0,
    house: raw?.house ?? 0,
    lord:  raw?.lord  ?? "—",
  });

  // ── Sect ─────────────────────────────────────────────────────────────────
  const sect = abuData?.derived?.sect ?? "unknown";
  const sectMaster = sect === "nocturnal" ? "Moon" : sect === "diurnal" ? "Sun" : "—";

  return {
    subject_name:  birthData?.userName || abuData?.person?.name || "Anónimo",
    birth_dt: (() => {
      const rawDt = birthData?.birthDate ?? abuData?.subject?.birth_dt ?? "";
      if (!rawDt) return rawDt;
      try {
        const utcMs    = new Date(rawDt).getTime();
        const offsetMs = (birthData?.utcOffset ?? 0) * 60 * 60 * 1000;
        const local    = new Date(utcMs + offsetMs);
        const dd  = String(local.getUTCDate()).padStart(2, '0');
        const mm  = String(local.getUTCMonth() + 1).padStart(2, '0');
        const yyyy = local.getUTCFullYear();
        const hh  = String(local.getUTCHours()).padStart(2, '0');
        const min = String(local.getUTCMinutes()).padStart(2, '0');
        return `${dd}/${mm}/${yyyy} ${hh}:${min}`;
      } catch {
        return rawDt;
      }
    })(),
    birth_city:    birthData?.city ?? abuData?.subject?.birth_city ?? "",
    house_system:  abuData?.chart?.house_system ?? "placidus",
    sect,
    sect_master:   sectMaster,
    asc: {
      sign:         ascSign,
      deg:          _getDegInSign(ascLon),
      lord:         ascLord,
      lord_dignity: _planetDignity(ascLord),
    },
    mc: {
      sign:         mcSign,
      deg:          _getDegInSign(mcLon),
      lord:         mcLord,
      lord_dignity: _planetDignity(mcLord),
    },
    house_1_sign: ascSign,
    planets:      mappedPlanets,
    aspects:      filteredAspects,
    lots: {
      fortuna: _lotObj(fortunaRaw),
      spirit:  _lotObj(spiritRaw),
    },
    house_significators: abuData?.derived?.house_significators ?? {},
  };
}

// ── buildActiveContext ────────────────────────────────────────────────────────

export function buildActiveContext(params: {
  currentDate:     string
  activeTab:       string
  activeDomain:    string | null
  activeCity:      { name: string; lat: number; lon: number; hf_score: number } | null
  lastEventType:   string
  triggerData:     Record<string, unknown>
  /** UTC offset en horas del usuario (ej: -3 para Buenos Aires). Usado para mostrar fecha local. */
  utcOffsetHours?: number
}): ActiveContext {
  let userLocalDate: string | undefined;
  if (params.utcOffsetHours != null) {
    try {
      const localMs = Date.now() + params.utcOffsetHours * 3_600_000;
      userLocalDate = new Date(localMs).toISOString().slice(0, 10);
    } catch { /* no-op */ }
  }
  return {
    current_date:     params.currentDate,
    user_local_date:  userLocalDate,
    active_tab:       params.activeTab,
    active_domain:    params.activeDomain,
    active_city:      params.activeCity,
    last_event_type:  params.lastEventType,
    trigger_data:     params.triggerData,
  };
}

// ── assembleContextBlock ──────────────────────────────────────────────────────

/**
 * Produce el string que va al system prompt (o como user context block) de Lilly.
 * lang está disponible para extensión futura (secciones localizadas).
 * memoryContext: string pre-formateado de chat-memory.formatMemoryForPrompt() — opcional.
 */
export function assembleContextBlock(
  natal:    NatalContext,
  timeline: BiographicalTimeline,
  active:   ActiveContext,
  lang:     string,
  memoryContext?: string,
  lunarContext?:  string,
  mundanaContext?: string,
): string {
  const lines: string[] = [];
  const SEP = "═══════════════════════════════════════";

  // ╔══ CARTA NATAL ══════════════════════════════════════════════════════════╗
  lines.push(SEP);
  lines.push(`CARTA NATAL — ${natal.subject_name} · Carta ${natal.sect}`);
  lines.push(`Sistema de casas: ${natal.house_system}`);
  lines.push(SEP);
  lines.push(`Fecha de nacimiento: ${natal.birth_dt}  ·  ${natal.birth_city}`);
  lines.push("");

  // Ángulos
  lines.push("ÁNGULOS");
  lines.push(
    `ASC: ${natal.asc.sign} ${natal.asc.deg.toFixed(1)}° · Señor: ${localizePlanet(natal.asc.lord, lang)} (${_cap(natal.asc.lord_dignity)})`
  );
  lines.push(
    `MC:  ${natal.mc.sign} ${natal.mc.deg.toFixed(1)}°  · Señor: ${localizePlanet(natal.mc.lord, lang)} (${_cap(natal.mc.lord_dignity)})`
  );
  lines.push(`Casa 1 = ${natal.house_1_sign} — ancla de identidad.`);
  lines.push("");

  // Secta
  lines.push("SECTA");
  lines.push(`Carta ${natal.sect} · Maestro de secta: ${localizePlanet(natal.sect_master, lang)}`);
  lines.push("");

  // Planetas
  lines.push("PLANETAS");
  for (const p of natal.planets) {
    const retro = p.retrograde ? " ℞" : "";
    lines.push(
      `${localizePlanet(p.name, lang)} · ${p.sign} ${p.deg.toFixed(1)}° · Casa ${p.house} · ${_cap(p.dignity)}${retro}`
    );
  }
  lines.push("");

  // Fase lunar natal
  const lunarPhase = _natalLunarPhase(natal.planets);
  if (lunarPhase) {
    lines.push(`Fase lunar natal: ${lunarPhase.name} (${lunarPhase.pct}% del ciclo)`);
    lines.push("");
  }

  // Aspectos natales (solo si el endpoint los devuelve)
  if (natal.aspects.length > 0) {
    lines.push("ASPECTOS NATALES (orbe < 3°)");
    for (const a of natal.aspects) {
      const app = a.applying ? " ↑" : "";
      lines.push(`${localizePlanet(a.planet_a, lang)} ${a.type} ${localizePlanet(a.planet_b, lang)} · orbe ${a.orb.toFixed(1)}°${app}`);
    }
    lines.push("");
  }

  // Partes Arábicas
  lines.push("PARTES ARÁBICAS");
  const f = natal.lots.fortuna;
  const s = natal.lots.spirit;
  if (f.sign !== "—") {
    lines.push(`Fortuna: ${f.sign} ${f.deg.toFixed(1)}° · Casa ${f.house} · Señor: ${localizePlanet(f.lord, lang)}`);
  }
  if (s.sign !== "—") {
    lines.push(`Espíritu: ${s.sign} ${s.deg.toFixed(1)}° · Casa ${s.house} · Señor: ${localizePlanet(s.lord, lang)}`);
  }
  lines.push("");

  // ╔══ LÍNEA DE TIEMPO ══════════════════════════════════════════════════════╗
  lines.push(SEP);
  lines.push("LÍNEA DE TIEMPO");
  lines.push("Tránsitos marcados [usar PASADO] ya ocurrieron · [usar PRESENTE] están en curso · [usar FUTURO] aún no comienzan — respetá el tiempo verbal y la distancia indicada.");
  lines.push(SEP);
  lines.push("");

  // Profección activa
  const activeProf = timeline.profections.find(p => p.is_active);
  if (activeProf) {
    lines.push("PROFECCIÓN ACTIVA");
    lines.push(`Año ${activeProf.year_of_life} · ${activeProf.date_start} → ${activeProf.date_end}`);
    lines.push(
      `Casa ${activeProf.house} (${activeProf.sign}) · Señor del año: ${localizePlanet(activeProf.lord, lang)} · Dignidad: ${_cap(activeProf.lord_dignity)}`
    );

    const activeIdx = timeline.profections.findIndex(p => p.is_active);
    const nextProf  = timeline.profections[activeIdx + 1];
    if (nextProf) {
      lines.push("");
      lines.push("PROFECCIÓN SIGUIENTE");
      lines.push(`Casa ${nextProf.house} (${nextProf.sign}) · Señor: ${localizePlanet(nextProf.lord, lang)} · desde ${nextProf.date_start}`);
    }
    lines.push("");
  }

  // Firdaria
  const activeFird = timeline.firdaria.find(f => f.is_active);
  if (activeFird) {
    // Fecha de inicio del período mayor (primer sub-período con el mismo mayor)
    const majorStart =
      timeline.firdaria.find(f => f.major_planet === activeFird.major_planet)?.date_start
      ?? activeFird.date_start;

    lines.push("FIRDARIA");
    lines.push(`Mayor: ${localizePlanet(activeFird.major_planet, lang)} · activa desde ${majorStart}`);
    lines.push(
      `Menor activa: ${localizePlanet(activeFird.minor_planet, lang)} · ${activeFird.date_start} → ${activeFird.date_end}`
    );

    const activeIdx = timeline.firdaria.findIndex(f => f.is_active);
    const nextFird  = timeline.firdaria[activeIdx + 1];
    if (nextFird) {
      lines.push(`Siguiente menor: ${localizePlanet(nextFird.minor_planet, lang)} · desde ${nextFird.date_start}`);
    }
    lines.push("");
  }

  // Tránsitos significativos — agrupa los multi-paso para que Lilly no los ancle al primer paso
  if (timeline.transits_window.length > 0) {
    lines.push("TRÁNSITOS SIGNIFICATIVOS ±18 meses");

    // Agrupar por clave planeta_transit|aspecto|planeta_natal
    type TGroup = {
      transit_planet: string;
      aspect:         string;
      natal_planet:   string;
      passes: Array<{ exact_date: string; ingress_date: string; egress_date: string; is_active: boolean }>;
    };
    const groups = new Map<string, TGroup>();
    for (const t of timeline.transits_window) {
      const key = `${t.transit_planet}|${t.aspect}|${t.natal_planet}`;
      if (!groups.has(key)) {
        groups.set(key, {
          transit_planet: t.transit_planet,
          aspect:         t.aspect,
          natal_planet:   t.natal_planet,
          passes: [],
        });
      }
      groups.get(key)!.passes.push({
        exact_date:   t.exact_date,
        ingress_date: t.ingress_date,
        egress_date:  t.egress_date,
        is_active:    t.is_active,
      });
    }

    for (const g of Array.from(groups.values())) {
      const anyActive = g.passes.some(p => p.is_active);
      const activeTag = anyActive ? " [activo]" : "";
      if (g.passes.length === 1) {
        const p = g.passes[0];
        lines.push(
          `- ${localizePlanet(g.transit_planet, lang)} ${g.aspect} ${localizePlanet(g.natal_planet, lang)} natal${p.is_active ? " [activo]" : ""}${transitTemporal(p.ingress_date, p.egress_date, p.exact_date)}`
        );
      } else {
        // Tránsito multi-paso — muestra ventana completa + cada paso
        const first = g.passes[0].ingress_date || g.passes[0].exact_date;
        const last  = g.passes[g.passes.length - 1].egress_date || g.passes[g.passes.length - 1].exact_date;
        lines.push(
          `- ${localizePlanet(g.transit_planet, lang)} ${g.aspect} ${localizePlanet(g.natal_planet, lang)} natal · ${g.passes.length} pasos · ventana: ${first} → ${last}${activeTag}`
        );
        for (let i = 0; i < g.passes.length; i++) {
          const p = g.passes[i];
          lines.push(
            `  Paso ${i + 1}: ${p.exact_date}${p.is_active ? " [activo]" : ""}${transitTemporal(p.ingress_date, p.egress_date, p.exact_date)}`
          );
        }
      }
    }
    lines.push("");
  }

  // Ventana de convergencia (si aplica)
  const convergence = _detectConvergence(timeline, lang);
  if (convergence) {
    lines.push(convergence);
    lines.push("");
  }

  // ╔══ CIELO COLECTIVO (Mundana) ════════════════════════════════════════════╗
  if (mundanaContext) {
    lines.push(SEP);
    lines.push("CIELO COLECTIVO — ASTROLOGÍA MUNDANA");
    lines.push(SEP);
    lines.push(mundanaContext);
    lines.push("");
  }

  // ╔══ CIELO ACTUAL (fase lunar, lunaciones, eclipses) ══════════════════════╗
  if (lunarContext) {
    lines.push(SEP);
    lines.push("CIELO ACTUAL");
    lines.push(SEP);
    lines.push(lunarContext);
    lines.push("");
  }

  // ╔══ CONTEXTO ACTIVO ══════════════════════════════════════════════════════╗
  lines.push(SEP);
  lines.push(`CONTEXTO ACTIVO — ${active.current_date} (UTC)`);
  if (active.user_local_date) {
    lines.push(`Fecha local usuario: ${active.user_local_date}`);
  }
  lines.push(SEP);
  lines.push(`Vista: ${active.active_tab}`);
  lines.push(`Trigger: ${active.last_event_type}`);
  lines.push(`Idioma de respuesta: ${lang}`);

  // Campos del trigger_data (uno por línea, omitir nulos y vacíos)
  for (const [key, value] of Object.entries(active.trigger_data)) {
    if (value !== null && value !== undefined && value !== "") {
      lines.push(`${key}: ${value}`);
    }
  }

  if (active.active_domain) {
    lines.push(`Dominio activo: ${active.active_domain}`);
  }
  if (active.active_city) {
    const c = active.active_city;
    lines.push(`Ciudad activa: ${c.name} · HF: ${c.hf_score.toFixed(2)}`);
  }

  // ╔══ MEMORIA BIOGRÁFICA (si existe) ═══════════════════════════════════════╗
  if (memoryContext) {
    lines.push("");
    lines.push(memoryContext);
  }

  // ╔══ INSTRUCCIÓN FINAL DE IDIOMA ══════════════════════════════════════════╗
  // Al final del bloque — mayor peso sobre memoria y historial previo.
  lines.push("");
  lines.push(`RESPOND ONLY IN: ${lang.toUpperCase()}. This overrides any language used in previous conversation or biographical memory.`);

  return lines.join("\n");
}
