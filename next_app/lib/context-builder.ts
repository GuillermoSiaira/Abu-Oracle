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
  }>
}

export interface ActiveContext {
  current_date:    string
  active_tab:      string
  active_domain:   string | null
  active_city: {
    name:     string
    lat:      number
    lon:      number
    hf_score: number
  } | null
  last_event_type: string
  trigger_data:    Record<string, unknown>
}

// ── buildNatalContext ─────────────────────────────────────────────────────────

/**
 * Construye NatalContext desde el objeto abuData (response de /analyze).
 * birthData opcional para enriquecer con birth_dt y birth_city que no
 * están en el response del analyze pero sí en el store del frontend.
 */
export function buildNatalContext(
  abuData: any,
  birthData?: { birthDate?: string | null; city?: string | null; userName?: string | null } | null,
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
    birth_dt:      birthData?.birthDate ?? abuData?.subject?.birth_dt ?? "",
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
  currentDate:   string
  activeTab:     string
  activeDomain:  string | null
  activeCity:    { name: string; lat: number; lon: number; hf_score: number } | null
  lastEventType: string
  triggerData:   Record<string, unknown>
}): ActiveContext {
  return {
    current_date:    params.currentDate,
    active_tab:      params.activeTab,
    active_domain:   params.activeDomain,
    active_city:     params.activeCity,
    last_event_type: params.lastEventType,
    trigger_data:    params.triggerData,
  };
}

// ── assembleContextBlock ──────────────────────────────────────────────────────

/**
 * Produce el string que va al system prompt (o como user context block) de Lilly.
 * lang está disponible para extensión futura (secciones localizadas).
 */
export function assembleContextBlock(
  natal:    NatalContext,
  timeline: BiographicalTimeline,
  active:   ActiveContext,
  _lang:    string,
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
    `ASC: ${natal.asc.sign} ${natal.asc.deg.toFixed(1)}° · Señor: ${natal.asc.lord} (${_cap(natal.asc.lord_dignity)})`
  );
  lines.push(
    `MC:  ${natal.mc.sign} ${natal.mc.deg.toFixed(1)}°  · Señor: ${natal.mc.lord} (${_cap(natal.mc.lord_dignity)})`
  );
  lines.push(`Casa 1 = ${natal.house_1_sign} — ancla de identidad.`);
  lines.push("");

  // Secta
  lines.push("SECTA");
  lines.push(`Carta ${natal.sect} · Maestro de secta: ${natal.sect_master}`);
  lines.push("");

  // Planetas
  lines.push("PLANETAS");
  for (const p of natal.planets) {
    const retro = p.retrograde ? " ℞" : "";
    lines.push(
      `${p.name} · ${p.sign} ${p.deg.toFixed(1)}° · Casa ${p.house} · ${_cap(p.dignity)}${retro}`
    );
  }
  lines.push("");

  // Aspectos natales (solo si el endpoint los devuelve)
  if (natal.aspects.length > 0) {
    lines.push("ASPECTOS NATALES (orbe < 3°)");
    for (const a of natal.aspects) {
      const app = a.applying ? " ↑" : "";
      lines.push(`${a.planet_a} ${a.type} ${a.planet_b} · orbe ${a.orb.toFixed(1)}°${app}`);
    }
    lines.push("");
  }

  // Partes Arábicas
  lines.push("PARTES ARÁBICAS");
  const f = natal.lots.fortuna;
  const s = natal.lots.spirit;
  if (f.sign !== "—") {
    lines.push(`Fortuna: ${f.sign} ${f.deg.toFixed(1)}° · Casa ${f.house} · Señor: ${f.lord}`);
  }
  if (s.sign !== "—") {
    lines.push(`Espíritu: ${s.sign} ${s.deg.toFixed(1)}° · Casa ${s.house} · Señor: ${s.lord}`);
  }
  lines.push("");

  // ╔══ LÍNEA DE TIEMPO ══════════════════════════════════════════════════════╗
  lines.push(SEP);
  lines.push("LÍNEA DE TIEMPO");
  lines.push(SEP);
  lines.push("");

  // Profección activa
  const activeProf = timeline.profections.find(p => p.is_active);
  if (activeProf) {
    lines.push("PROFECCIÓN ACTIVA");
    lines.push(`Año ${activeProf.year_of_life} · ${activeProf.date_start} → ${activeProf.date_end}`);
    lines.push(
      `Casa ${activeProf.house} (${activeProf.sign}) · Señor del año: ${activeProf.lord} · Dignidad: ${_cap(activeProf.lord_dignity)}`
    );

    const activeIdx = timeline.profections.findIndex(p => p.is_active);
    const nextProf  = timeline.profections[activeIdx + 1];
    if (nextProf) {
      lines.push("");
      lines.push("PROFECCIÓN SIGUIENTE");
      lines.push(`Casa ${nextProf.house} (${nextProf.sign}) · Señor: ${nextProf.lord} · desde ${nextProf.date_start}`);
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
    lines.push(`Mayor: ${activeFird.major_planet} · activa desde ${majorStart}`);
    lines.push(
      `Menor activa: ${activeFird.minor_planet} · ${activeFird.date_start} → ${activeFird.date_end}`
    );

    const activeIdx = timeline.firdaria.findIndex(f => f.is_active);
    const nextFird  = timeline.firdaria[activeIdx + 1];
    if (nextFird) {
      lines.push(`Siguiente menor: ${nextFird.minor_planet} · desde ${nextFird.date_start}`);
    }
    lines.push("");
  }

  // Tránsitos significativos
  if (timeline.transits_window.length > 0) {
    lines.push("TRÁNSITOS SIGNIFICATIVOS ±18 meses");
    for (const t of timeline.transits_window) {
      const active = t.is_active ? " [activo]" : "";
      lines.push(
        `- ${t.transit_planet} ${t.aspect} ${t.natal_planet} natal [exacto: ${t.exact_date}]${active}`
      );
    }
    lines.push("");
  }

  // ╔══ CONTEXTO ACTIVO ══════════════════════════════════════════════════════╗
  lines.push(SEP);
  lines.push(`CONTEXTO ACTIVO — ${active.current_date}`);
  lines.push(SEP);
  lines.push(`Vista: ${active.active_tab}`);
  lines.push(`Trigger: ${active.last_event_type}`);

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

  return lines.join("\n");
}
