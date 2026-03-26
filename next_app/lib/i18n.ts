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
  // TechnicalPanel guide sections
  tpReadingNow: string;
  tpNoSelection: string;
  tpYearLord: string;
  tpActivatedHouse: string;
  tpExplore: string;
  // Persian Techniques tab
  persianSect: string;
  persianSectDiurnal: string;
  persianSectNocturnal: string;
  persianSectDetailDiurnal: string;
  persianSectDetailNocturnal: string;
  persianProfection: string;
  persianHouseActivated: string;
  persianHouseLabel: string;
  persianCuspSign: string;
  persianAnnualLord: string;
  persianNoData: string;
  persianFirdaria: string;
  persianLastPeriod: string;
  persianOutOfCycle: string;
  persianMajorPeriod: string;
  persianSubPeriod: string;
  persianStart: string;
  persianEnd: string;
  persianLunarTransits: string;
  persianMoonPosition: string;
  persianNoLunar: string;
  persianCycles: string;
  persianNoEvents: string;
  // Arabic Parts / Lots
  persianLotsTitle: string;
  persianLotFortuna: string;
  persianLotSpirit: string;
  persianLotLord: string;
  persianCyclesUpcoming: string;
  persianCyclesRecent: string;
  persianTooltipSect: string;
  persianTooltipProfection: string;
  persianTooltipFirdaria: string;
  persianTooltipLots: string;
  persianTooltipLunar: string;
  persianTooltipCycles: string;
  persianLunarDialTitle: string;
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
  // Demo page
  demoPageTitle: string;
  demoPageSubtitle: string;
  demoLoading: string;
}> = {
  es: {
    tabChart: "Carta Natal",
    tabPersian: "Técnicas Persas",
    tabTransits: "Tránsitos",
    tabRelocation: "Mapa HF",
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
    lillyCtaDemo: "Ver el motor en acción",
    demoPageTitle: "Cartas de referencia",
    demoPageSubtitle: "10 sujetos con datos verificados (Rodden AA/A/B). Carta calculada on-demand.",
    demoLoading: "Calculando carta…",
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
    tpReadingNow: "LEYENDO AHORA",
    tpNoSelection: "Sin selección",
    tpYearLord: "SEÑOR DEL AÑO",
    tpActivatedHouse: "Casa activada",
    tpExplore: "EXPLORAR",
    persianSect: "Secta",
    persianSectDiurnal: "Carta diurna",
    persianSectNocturnal: "Carta nocturna",
    persianSectDetailDiurnal: "El Sol está sobre el horizonte. Júpiter y el Sol actúan como benéficos principales; Saturno como maléfico moderado.",
    persianSectDetailNocturnal: "El Sol está bajo el horizonte. Venus y la Luna actúan como benéficos principales; Marte como maléfico moderado.",
    persianProfection: "Profección anual",
    persianHouseActivated: "Casa activada",
    persianHouseLabel: "Casa",
    persianCuspSign: "Signo de la cúspide",
    persianAnnualLord: "Señor del año",
    persianNoData: "Sin datos.",
    persianFirdaria: "Firdaria",
    persianLastPeriod: "último período registrado",
    persianOutOfCycle: "Fuera del ciclo de 75 años.",
    persianMajorPeriod: "Período mayor",
    persianSubPeriod: "Sub-período",
    persianStart: "Inicio",
    persianEnd: "Fin",
    persianLunarTransits: "Tránsitos lunares",
    persianMoonPosition: "Posición lunar",
    persianNoLunar: "Sin datos lunares.",
    persianCycles: "Ciclos planetarios",
    persianNoEvents: "Sin eventos.",
    persianLotsTitle: "Partes Arábicas",
    persianLotFortuna: "Parte de Fortuna",
    persianLotSpirit: "Parte del Espíritu",
    persianLotLord: "Señor",
    persianCyclesUpcoming: "Próximos",
    persianCyclesRecent: "Recientes",
    persianTooltipSect: "La carta es diurna si el Sol está sobre el horizonte al nacer, nocturna si está bajo él. Define qué planetas benéficos y maléficos actúan con más fuerza.",
    persianTooltipProfection: "Técnica helenística que activa una casa distinta cada año de vida. La casa activa y su señor gobiernan los temas del año.",
    persianTooltipFirdaria: "Sistema persa de períodos planetarios. Cada planeta gobierna un período de años con su propia calidad e intensidad.",
    persianTooltipLots: "Puntos matemáticos calculados desde las posiciones de Sol, Luna y ASC. Revelan áreas específicas de la vida.",
    persianTooltipLunar: "Posición actual de la Luna y sus aspectos a la carta natal. El pulso diario del campo.",
    persianTooltipCycles: "Retornos y oposiciones de planetas lentos — momentos de cierre y apertura de ciclos de largo plazo.",
    persianLunarDialTitle: "Fase Lunar",
  },
  en: {
    tabChart: "Birth Chart",
    tabPersian: "Persian Techniques",
    tabTransits: "Transits",
    tabRelocation: "HF Map",
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
    lillyCtaDemo: "See the engine in action",
    demoPageTitle: "Reference charts",
    demoPageSubtitle: "10 subjects with verified data (Rodden AA/A/B). Chart computed on-demand.",
    demoLoading: "Computing chart…",
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
    tpReadingNow: "READING NOW",
    tpNoSelection: "No selection",
    tpYearLord: "YEAR LORD",
    tpActivatedHouse: "Activated house",
    tpExplore: "EXPLORE",
    persianSect: "Sect",
    persianSectDiurnal: "Diurnal chart",
    persianSectNocturnal: "Nocturnal chart",
    persianSectDetailDiurnal: "The Sun is above the horizon. Jupiter and the Sun act as primary benefics; Saturn as moderate malefic.",
    persianSectDetailNocturnal: "The Sun is below the horizon. Venus and the Moon act as primary benefics; Mars as moderate malefic.",
    persianProfection: "Annual profection",
    persianHouseActivated: "Activated house",
    persianHouseLabel: "House",
    persianCuspSign: "Cusp sign",
    persianAnnualLord: "Annual lord",
    persianNoData: "No data.",
    persianFirdaria: "Firdaria",
    persianLastPeriod: "last recorded period",
    persianOutOfCycle: "Outside the 75-year cycle.",
    persianMajorPeriod: "Major period",
    persianSubPeriod: "Sub-period",
    persianStart: "Start",
    persianEnd: "End",
    persianLunarTransits: "Lunar transits",
    persianMoonPosition: "Moon position",
    persianNoLunar: "No lunar data.",
    persianCycles: "Planetary cycles",
    persianNoEvents: "No events.",
    persianLotsTitle: "Arabic Parts",
    persianLotFortuna: "Part of Fortune",
    persianLotSpirit: "Part of Spirit",
    persianLotLord: "Lord",
    persianCyclesUpcoming: "Upcoming",
    persianCyclesRecent: "Recent",
    persianTooltipSect: "The chart is diurnal if the Sun is above the horizon at birth, nocturnal if below. Defines which benefic and malefic planets act with greater force.",
    persianTooltipProfection: "Hellenistic technique that activates a different house each year of life. The active house and its lord govern the themes of the year.",
    persianTooltipFirdaria: "Persian system of planetary periods. Each planet governs a period of years with its own quality and intensity.",
    persianTooltipLots: "Mathematical points calculated from the positions of Sun, Moon and ASC. Reveal specific areas of life.",
    persianTooltipLunar: "Current Moon position and its aspects to the natal chart. The daily pulse of the field.",
    persianTooltipCycles: "Returns and oppositions of slow planets — moments of closure and opening of long-term cycles.",
    persianLunarDialTitle: "Lunar Phase",
  },
  pt: {
    tabChart: "Carta Natal",
    tabPersian: "Técnicas Persas",
    tabTransits: "Trânsitos",
    tabRelocation: "Mapa HF",
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
    lillyCtaDemo: "Ver o motor em ação",
    demoPageTitle: "Cartas de referência",
    demoPageSubtitle: "10 sujeitos com dados verificados (Rodden AA/A/B). Carta calculada sob demanda.",
    demoLoading: "Calculando carta…",
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
    tpReadingNow: "LENDO AGORA",
    tpNoSelection: "Sem seleção",
    tpYearLord: "SENHOR DO ANO",
    tpActivatedHouse: "Casa ativada",
    tpExplore: "EXPLORAR",
    persianSect: "Seita",
    persianSectDiurnal: "Carta diurna",
    persianSectNocturnal: "Carta noturna",
    persianSectDetailDiurnal: "O Sol está acima do horizonte. Júpiter e o Sol atuam como benéficos principais; Saturno como maléfico moderado.",
    persianSectDetailNocturnal: "O Sol está abaixo do horizonte. Vênus e a Lua atuam como benéficos principais; Marte como maléfico moderado.",
    persianProfection: "Profeção anual",
    persianHouseActivated: "Casa ativada",
    persianHouseLabel: "Casa",
    persianCuspSign: "Signo da cúspide",
    persianAnnualLord: "Senhor do ano",
    persianNoData: "Sem dados.",
    persianFirdaria: "Firdaria",
    persianLastPeriod: "último período registrado",
    persianOutOfCycle: "Fora do ciclo de 75 anos.",
    persianMajorPeriod: "Período maior",
    persianSubPeriod: "Sub-período",
    persianStart: "Início",
    persianEnd: "Fim",
    persianLunarTransits: "Trânsitos lunares",
    persianMoonPosition: "Posição lunar",
    persianNoLunar: "Sem dados lunares.",
    persianCycles: "Ciclos planetários",
    persianNoEvents: "Sem eventos.",
    persianLotsTitle: "Partes Arábicas",
    persianLotFortuna: "Parte da Fortuna",
    persianLotSpirit: "Parte do Espírito",
    persianLotLord: "Senhor",
    persianCyclesUpcoming: "Próximos",
    persianCyclesRecent: "Recentes",
    persianTooltipSect: "O tema é diurno se o Sol está acima do horizonte no nascimento, noturno se está abaixo. Define quais planetas benéficos e maléficos atuam com mais força.",
    persianTooltipProfection: "Técnica helenística que ativa uma casa diferente a cada ano de vida. A casa ativa e seu senhor governam os temas do ano.",
    persianTooltipFirdaria: "Sistema persa de períodos planetários. Cada planeta governa um período de anos com sua própria qualidade e intensidade.",
    persianTooltipLots: "Pontos matemáticos calculados a partir das posições do Sol, Lua e ASC. Revelam áreas específicas da vida.",
    persianTooltipLunar: "Posição atual da Lua e seus aspectos com a carta natal. O pulso diário do campo.",
    persianTooltipCycles: "Retornos e oposições de planetas lentos — momentos de fechamento e abertura de ciclos de longo prazo.",
    persianLunarDialTitle: "Fase Lunar",
  },
  fr: {
    tabChart: "Thème Natal",
    tabPersian: "Techniques Persanes",
    tabTransits: "Transits",
    tabRelocation: "Carte HF",
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
    lillyCtaDemo: "Voir le moteur en action",
    demoPageTitle: "Thèmes de référence",
    demoPageSubtitle: "10 sujets avec données vérifiées (Rodden AA/A/B). Thème calculé à la demande.",
    demoLoading: "Calcul du thème…",
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
    tpReadingNow: "EN LECTURE",
    tpNoSelection: "Aucune sélection",
    tpYearLord: "SEIGNEUR DE L'ANNÉE",
    tpActivatedHouse: "Maison activée",
    tpExplore: "EXPLORER",
    persianSect: "Secte",
    persianSectDiurnal: "Thème diurne",
    persianSectNocturnal: "Thème nocturne",
    persianSectDetailDiurnal: "Le Soleil est au-dessus de l'horizon. Jupiter et le Soleil agissent comme bénéfiques principaux ; Saturne comme maléfique modéré.",
    persianSectDetailNocturnal: "Le Soleil est sous l'horizon. Vénus et la Lune agissent comme bénéfiques principaux ; Mars comme maléfique modéré.",
    persianProfection: "Profection annuelle",
    persianHouseActivated: "Maison activée",
    persianHouseLabel: "Maison",
    persianCuspSign: "Signe de la cuspide",
    persianAnnualLord: "Seigneur annuel",
    persianNoData: "Pas de données.",
    persianFirdaria: "Firdaria",
    persianLastPeriod: "dernière période enregistrée",
    persianOutOfCycle: "Hors du cycle de 75 ans.",
    persianMajorPeriod: "Période majeure",
    persianSubPeriod: "Sous-période",
    persianStart: "Début",
    persianEnd: "Fin",
    persianLunarTransits: "Transits lunaires",
    persianMoonPosition: "Position lunaire",
    persianNoLunar: "Pas de données lunaires.",
    persianCycles: "Cycles planétaires",
    persianNoEvents: "Aucun événement.",
    persianLotsTitle: "Parties Arabes",
    persianLotFortuna: "Partie de Fortune",
    persianLotSpirit: "Partie de l'Esprit",
    persianLotLord: "Seigneur",
    persianCyclesUpcoming: "À venir",
    persianCyclesRecent: "Récents",
    persianTooltipSect: "Le thème est diurne si le Soleil est au-dessus de l'horizon à la naissance, nocturne si en dessous. Définit quels planètes bénéfiques et maléfiques agissent avec plus de force.",
    persianTooltipProfection: "Technique hellénistique activant une maison différente chaque année de vie. La maison active et son seigneur gouvernent les thèmes de l'année.",
    persianTooltipFirdaria: "Système perse de périodes planétaires. Chaque planète gouverne une période d'années avec sa propre qualité et intensité.",
    persianTooltipLots: "Points mathématiques calculés depuis les positions du Soleil, de la Lune et de l'ASC. Révèlent des domaines spécifiques de la vie.",
    persianTooltipLunar: "Position actuelle de la Lune et ses aspects avec le thème natal. Le pouls quotidien du champ.",
    persianTooltipCycles: "Retours et oppositions des planètes lentes — moments de fermeture et d'ouverture de cycles à long terme.",
    persianLunarDialTitle: "Phase Lunaire",
  },
};

// Celebrity descriptions for the /demo page — hardcoded, not in UI type
export const DEMO_DESCRIPTIONS: Record<string, Record<Lang, string>> = {
  einstein: {
    es: "Físico teórico. Relatividad especial y general.",
    en: "Theoretical physicist. Special and general relativity.",
    pt: "Físico teórico. Relatividade especial e geral.",
    fr: "Physicien théoricien. Relativités spéciale et générale.",
  },
  borges: {
    es: "Escritor argentino. Laberintos, espejos, infinitos.",
    en: "Argentine writer. Labyrinths, mirrors, infinities.",
    pt: "Escritor argentino. Labirintos, espelhos, infinitos.",
    fr: "Écrivain argentin. Labyrinthes, miroirs, infinis.",
  },
  frida: {
    es: "Pintora mexicana. Arte autobiográfico e identidad.",
    en: "Mexican painter. Autobiographical art and identity.",
    pt: "Pintora mexicana. Arte autobiográfica e identidade.",
    fr: "Peintre mexicaine. Art autobiographique et identité.",
  },
  picasso: {
    es: "Pintor español. Co-fundador del cubismo.",
    en: "Spanish painter. Co-founder of Cubism.",
    pt: "Pintor espanhol. Co-fundador do Cubismo.",
    fr: "Peintre espagnol. Co-fondateur du Cubisme.",
  },
  vangogh: {
    es: "Pintor neerlandés. Postimpresionismo y expresión emocional.",
    en: "Dutch painter. Post-impressionism and emotional expression.",
    pt: "Pintor neerlandês. Pós-impressionismo e expressão emocional.",
    fr: "Peintre néerlandais. Post-impressionnisme et expression émotionnelle.",
  },
  freud: {
    es: "Médico austríaco. Fundador del psicoanálisis.",
    en: "Austrian physician. Founder of psychoanalysis.",
    pt: "Médico austríaco. Fundador da psicanálise.",
    fr: "Médecin autrichien. Fondateur de la psychanalyse.",
  },
  jung: {
    es: "Psiquiatra suizo. Psicología analítica e inconsciente colectivo.",
    en: "Swiss psychiatrist. Analytical psychology and collective unconscious.",
    pt: "Psiquiatra suíço. Psicologia analítica e inconsciente coletivo.",
    fr: "Psychiatre suisse. Psychologie analytique et inconscient collectif.",
  },
  gandhi: {
    es: "Líder indio. Independencia y resistencia no violenta.",
    en: "Indian leader. Independence and nonviolent resistance.",
    pt: "Líder indiano. Independência e resistência não violenta.",
    fr: "Leader indien. Indépendance et résistance non violente.",
  },
  tesla: {
    es: "Inventor serbio-americano. Corriente alterna y electromagnetismo.",
    en: "Serbian-American inventor. Alternating current and electromagnetism.",
    pt: "Inventor sérvio-americano. Corrente alternada e eletromagnetismo.",
    fr: "Inventeur serbo-américain. Courant alternatif et électromagnétisme.",
  },
  bowie: {
    es: "Músico británico. Arte, alter egos y transformación.",
    en: "British musician. Art, alter egos and transformation.",
    pt: "Músico britânico. Arte, alter egos e transformação.",
    fr: "Musicien britannique. Art, alter egos et transformation.",
  },
};
