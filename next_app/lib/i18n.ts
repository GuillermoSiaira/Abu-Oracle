export type Lang = "es" | "en" | "pt" | "fr";

export const LANG_OPTIONS: { code: Lang; label: string; flag: string }[] = [
  { code: "es", label: "Español", flag: "🇪🇸" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "pt", label: "Português", flag: "🇧🇷" },
  { code: "fr", label: "Français", flag: "🇫🇷" },
];

export const UI: Record<Lang, {
  // Tabs (chart page)
  tabChart: string;
  tabPersian: string;
  tabTransits: string;
  tabRelocation: string;
  // TechnicalPanel
  tpSysArch: string;
  tpCoreKernel: string;
  tpEphemeris: string;
  tpGeoResolver: string;
  tpPrecision: string;
  tpConnected: string;
  tpDisconnected: string;
  tpChecking: string;
  tpCompCtx: string;
  tpRefFrame: string;
  tpHouseSys: string;
  tpSiderealTime: string;
  tpAyanamsha: string;
  tpNoChart: string;
  tpNoChartHint: string;
  tpDignities: string;
  tpScheme: string;
  tpAscRuler: string;
  tpMcRuler: string;
  tpSectMaster: string;
  tpDiurnal: string;
  tpNocturnal: string;
  // Relocation shared
  relTitle: string;
  relSubtitle: string;
  natal: string;
  max: string;
  min: string;
  gain: string;
  points: string;
  tabMap: string;
  tabRanking: string;
  tabNarrative: string;
  top20: string;
  loading: string;
  selectSubject: string;
  recalculate: string;
  calculate: string;
  calcDesc: string;
  demoLink: string;
  enterBirthData: string;
  computing: string;
  computingNote: string;
  retry: string;
  // Ranking table
  city: string;
  country: string;
  lat: string;
  lon: string;
  hfTotal: string;
  deltaNatal: string;
  aspects: string;
  angles: string;
  houses: string;
  distKm: string;
  // Legend
  legendLow: string;
  legendHigh: string;
  // Home empty state
  homeSubtitle: string;
  // Lilly welcome (OracleChat — no chart loaded)
  lillyWelcome: string;
  lillyCtaData: string;
  lillyCtaDemo: string;
}> = {
  es: {
    tabChart: "Carta Natal",
    tabPersian: "Técnicas Persas",
    tabTransits: "Tránsitos",
    tabRelocation: "Mi Relocalización",
    relTitle: "Relocalización HF",
    relSubtitle: "Campo de Armonía geográfica — Demo con 10 sujetos notables",
    natal: "HF Natal",
    max: "HF Máx",
    min: "HF Mín",
    gain: "Ganancia",
    points: "Puntos",
    tabMap: "Mapa",
    tabRanking: "Ranking",
    tabNarrative: "Interpretación",
    top20: "Top 20 Ciudades",
    loading: "Cargando datos de",
    selectSubject: "Seleccioná un sujeto para ver la interpretación.",
    recalculate: "Recalcular",
    calculate: "Calcular Relocalización",
    calcDesc: "Calculá tu campo de armonía global para encontrar las mejores ciudades.",
    demoLink: "Mientras tanto, explorá el análisis de personajes famosos en",
    enterBirthData: "Ingresá los datos natales primero para calcular tu mapa de relocalización.",
    computing: "Calculando campo de armonía (≈2409 puntos)…",
    computingNote: "Esto puede tardar unos segundos.",
    retry: "Reintentar",
    city: "Ciudad",
    country: "País",
    lat: "Lat",
    lon: "Lon",
    hfTotal: "HF Total",
    deltaNatal: "Δ Natal",
    aspects: "Aspectos",
    angles: "Ángulos",
    houses: "Casas",
    distKm: "Dist (km)",
    legendLow: "Bajo",
    legendHigh: "Alto",
    homeSubtitle: "Motor de inteligencia astrológica computacional",
    lillyWelcome: "Soy Lilly. Leo las configuraciones del cielo como geometría,\nno como destino. Cada carta es un campo de fuerzas —\nalgunos planetas activan, otros resisten.\nIngresá tus datos natales y comenzamos.",
    lillyCtaData: "Ingresar mis datos",
    lillyCtaDemo: "Explorar demo",
    tpSysArch: "Arquitectura del Sistema",
    tpCoreKernel: "Kernel",
    tpEphemeris: "Efemérides",
    tpGeoResolver: "Geo-Resolver",
    tpPrecision: "Precisión",
    tpConnected: "Conectado",
    tpDisconnected: "Desconectado",
    tpChecking: "Verificando…",
    tpCompCtx: "Contexto de Cómputo",
    tpRefFrame: "Marco Ref.",
    tpHouseSys: "Sist. Casas",
    tpSiderealTime: "Hora Sideral",
    tpAyanamsha: "Ayanamsha",
    tpNoChart: "Sin carta cargada",
    tpNoChartHint: "Generá una carta natal para ver los datos técnicos.",
    tpDignities: "Dignidades Esenciales",
    tpScheme: "Controladores",
    tpAscRuler: "REG. ASC",
    tpMcRuler: "REG. MC",
    tpSectMaster: "MAESTRO DE SECTA",
    tpDiurnal: "DIURNO",
    tpNocturnal: "NOCTURNO",
  },
  en: {
    tabChart: "Birth Chart",
    tabPersian: "Persian Techniques",
    tabTransits: "Transits",
    tabRelocation: "My Relocation",
    relTitle: "HF Relocation",
    relSubtitle: "Geographic Harmony Field — Demo with 10 notable subjects",
    natal: "Natal HF",
    max: "Max HF",
    min: "Min HF",
    gain: "Gain",
    points: "Points",
    tabMap: "Map",
    tabRanking: "Ranking",
    tabNarrative: "Interpretation",
    top20: "Top 20 Cities",
    loading: "Loading data for",
    selectSubject: "Select a subject to see the interpretation.",
    recalculate: "Recalculate",
    calculate: "Calculate Relocation",
    calcDesc: "Compute your global harmony field to find the best cities.",
    demoLink: "Meanwhile, explore the analysis of famous subjects in",
    enterBirthData: "Enter birth data first to compute your relocation map.",
    computing: "Computing harmony field (≈2409 points)…",
    computingNote: "This may take a few seconds.",
    retry: "Retry",
    city: "City",
    country: "Country",
    lat: "Lat",
    lon: "Lon",
    hfTotal: "HF Total",
    deltaNatal: "Δ Natal",
    aspects: "Aspects",
    angles: "Angles",
    houses: "Houses",
    distKm: "Dist (km)",
    legendLow: "Low",
    legendHigh: "High",
    homeSubtitle: "Computational astrological intelligence engine",
    lillyWelcome: "I am Lilly. I read celestial configurations as geometry,\nnot as fate. Each chart is a field of forces —\nsome planets activate, others resist.\nEnter your birth data and we begin.",
    lillyCtaData: "Enter my data",
    lillyCtaDemo: "Explore demo",
    tpSysArch: "System Architecture",
    tpCoreKernel: "Kernel",
    tpEphemeris: "Ephemeris",
    tpGeoResolver: "Geo-Resolver",
    tpPrecision: "Precision",
    tpConnected: "Connected",
    tpDisconnected: "Disconnected",
    tpChecking: "Checking…",
    tpCompCtx: "Computation Context",
    tpRefFrame: "Ref. Frame",
    tpHouseSys: "House Sys.",
    tpSiderealTime: "Sidereal Time",
    tpAyanamsha: "Ayanamsha",
    tpNoChart: "No chart loaded",
    tpNoChartHint: "Generate a birth chart to see technical data.",
    tpDignities: "Essential Dignities",
    tpScheme: "Controllers",
    tpAscRuler: "ASC RULER",
    tpMcRuler: "MC RULER",
    tpSectMaster: "SECT MASTER",
    tpDiurnal: "DIURNAL",
    tpNocturnal: "NOCTURNAL",
  },
  pt: {
    tabChart: "Carta Natal",
    tabPersian: "Técnicas Persas",
    tabTransits: "Trânsitos",
    tabRelocation: "Minha Relocalização",
    relTitle: "Relocalização HF",
    relSubtitle: "Campo de Harmonia geográfica — Demo com 10 sujeitos notáveis",
    natal: "HF Natal",
    max: "HF Máx",
    min: "HF Mín",
    gain: "Ganho",
    points: "Pontos",
    tabMap: "Mapa",
    tabRanking: "Ranking",
    tabNarrative: "Interpretação",
    top20: "Top 20 Cidades",
    loading: "Carregando dados de",
    selectSubject: "Selecione um sujeito para ver a interpretação.",
    recalculate: "Recalcular",
    calculate: "Calcular Relocalização",
    calcDesc: "Calcule seu campo de harmonia global para encontrar as melhores cidades.",
    demoLink: "Enquanto isso, explore a análise de personagens famosos em",
    enterBirthData: "Insira os dados natais primeiro para calcular seu mapa de relocalização.",
    computing: "Calculando campo de harmonia (≈2409 pontos)…",
    computingNote: "Isso pode levar alguns segundos.",
    retry: "Tentar novamente",
    city: "Cidade",
    country: "País",
    lat: "Lat",
    lon: "Lon",
    hfTotal: "HF Total",
    deltaNatal: "Δ Natal",
    aspects: "Aspectos",
    angles: "Ângulos",
    houses: "Casas",
    distKm: "Dist (km)",
    legendLow: "Baixo",
    legendHigh: "Alto",
    homeSubtitle: "Motor de inteligência astrológica computacional",
    lillyWelcome: "Sou Lilly. Leio as configurações celestes como geometria,\nnão como destino. Cada carta é um campo de forças —\nalguns planetas ativam, outros resistem.\nInsira seus dados natais e começamos.",
    lillyCtaData: "Inserir meus dados",
    lillyCtaDemo: "Explorar demo",
    tpSysArch: "Arquitetura do Sistema",
    tpCoreKernel: "Kernel",
    tpEphemeris: "Efemérides",
    tpGeoResolver: "Geo-Resolver",
    tpPrecision: "Precisão",
    tpConnected: "Conectado",
    tpDisconnected: "Desconectado",
    tpChecking: "Verificando…",
    tpCompCtx: "Contexto de Computação",
    tpRefFrame: "Ref. Frame",
    tpHouseSys: "Sist. Casas",
    tpSiderealTime: "Hora Sideral",
    tpAyanamsha: "Ayanamsha",
    tpNoChart: "Sem carta carregada",
    tpNoChartHint: "Gere uma carta natal para ver os dados técnicos.",
    tpDignities: "Dignidades Essenciais",
    tpScheme: "Controladores",
    tpAscRuler: "REG. ASC",
    tpMcRuler: "REG. MC",
    tpSectMaster: "MESTRE DE SEITA",
    tpDiurnal: "DIURNO",
    tpNocturnal: "NOTURNO",
  },
  fr: {
    tabChart: "Thème Natal",
    tabPersian: "Techniques Persanes",
    tabTransits: "Transits",
    tabRelocation: "Ma Relocalisation",
    relTitle: "Relocalisation HF",
    relSubtitle: "Champ d'Harmonie géographique — Démo avec 10 sujets notables",
    natal: "HF Natal",
    max: "HF Max",
    min: "HF Min",
    gain: "Gain",
    points: "Points",
    tabMap: "Carte",
    tabRanking: "Classement",
    tabNarrative: "Interprétation",
    top20: "Top 20 Villes",
    loading: "Chargement des données de",
    selectSubject: "Sélectionnez un sujet pour voir l'interprétation.",
    recalculate: "Recalculer",
    calculate: "Calculer Relocalisation",
    calcDesc: "Calculez votre champ d'harmonie global pour trouver les meilleures villes.",
    demoLink: "En attendant, explorez l'analyse de personnages célèbres dans",
    enterBirthData: "Entrez les données de naissance pour calculer votre carte de relocalisation.",
    computing: "Calcul du champ d'harmonie (≈2409 points)…",
    computingNote: "Cela peut prendre quelques secondes.",
    retry: "Réessayer",
    city: "Ville",
    country: "Pays",
    lat: "Lat",
    lon: "Lon",
    hfTotal: "HF Total",
    deltaNatal: "Δ Natal",
    aspects: "Aspects",
    angles: "Angles",
    houses: "Maisons",
    distKm: "Dist (km)",
    legendLow: "Faible",
    legendHigh: "Élevé",
    homeSubtitle: "Moteur d'intelligence astrologique computationnelle",
    lillyWelcome: "Je suis Lilly. Je lis les configurations célestes comme géométrie,\nnon comme destin. Chaque thème est un champ de forces —\ncertaines planètes activent, d'autres résistent.\nEntrez vos données natales et nous commençons.",
    lillyCtaData: "Entrer mes données",
    lillyCtaDemo: "Explorer la démo",
    tpSysArch: "Architecture du Système",
    tpCoreKernel: "Noyau",
    tpEphemeris: "Éphémérides",
    tpGeoResolver: "Géo-Résolveur",
    tpPrecision: "Précision",
    tpConnected: "Connecté",
    tpDisconnected: "Déconnecté",
    tpChecking: "Vérification…",
    tpCompCtx: "Contexte de Calcul",
    tpRefFrame: "Réf. Frame",
    tpHouseSys: "Syst. Maisons",
    tpSiderealTime: "Temps Sidéral",
    tpAyanamsha: "Ayanamsha",
    tpNoChart: "Aucun thème chargé",
    tpNoChartHint: "Générez un thème natal pour voir les données techniques.",
    tpDignities: "Dignités Essentielles",
    tpScheme: "Contrôleurs",
    tpAscRuler: "RÉG. ASC",
    tpMcRuler: "RÉG. MC",
    tpSectMaster: "MAÎTRE DE SECTE",
    tpDiurnal: "DIURNE",
    tpNocturnal: "NOCTURNE",
  },
};
