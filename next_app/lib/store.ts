  // next_app/lib/store.ts

  import { create } from "zustand"
  import type {
    AbuAnalyzeResponse,
    LillyResponse,
    ChatMessage,
    BirthData
  } from "./types"
  import type { BiographicalTimeline } from "./context-builder"

  // ======================================================
  //  ONBOARDING TYPES
  // ======================================================

  export type OnboardingStage =
    | "idle"
    | "ask_name"
    | "ask_birthdate"
    | "ask_time"
    | "ask_birthplace"
    | "ask_residence"
    | "ask_relocation"
    | "completed"

  export interface OnboardingData {
    name?: string
    birthDate?: string
    birthTime?: string
    birthPlaceText?: string
    residenceText?: string
    relocationPreference?: string
  }

  export type ChartTabKey = "chart" | "persian" | "transits" | "relocation" | "sky"

  // ======================================================
  //  APP STATE
  // ======================================================

  interface AppState {
    birthData: BirthData | null
    abuData: AbuAnalyzeResponse | null
    lillyData: LillyResponse | null
    chatHistory: ChatMessage[]
    isLoading: boolean
    error: string | null

    includeTransits: boolean
    transitDate: string | null
    lang: "es" | "en" | "pt" | "fr"
    chartTab: ChartTabKey
    chartSidebarExpanded: boolean
    chartTab: ChartTabKey

    userName: string
    isDemo: boolean
    pendingLillyEvent: Record<string, any> | null
    lastLillyEvent: { type: string; label: string } | null
    lillySuggestions: Array<{ type: string; target: string; label: string }> | null
    timeline: BiographicalTimeline | null

    onboardingStage: OnboardingStage
    onboardingData: OnboardingData

    setBirthData: (data: BirthData) => void
    setAbuData: (data: AbuAnalyzeResponse | null) => void
    setLillyData: (data: LillyResponse | null) => void
    setIsLoading: (value: boolean) => void
    setError: (message: string | null) => void
    setIncludeTransits: (value: boolean) => void
    setTransitDate: (date: string | null) => void
    setLang: (lang: "es" | "en" | "pt" | "fr") => void
    setChartTab: (tab: ChartTabKey) => void
    setChartSidebarExpanded: (expanded: boolean) => void
    setChartTab: (tab: ChartTabKey) => void
    addChatMessage: (msg: ChatMessage) => void
    setUserName: (name: string) => void
    setIsDemo: (value: boolean) => void
    setPendingLillyEvent: (event: Record<string, any> | null) => void
    setLastLillyEvent: (evt: { type: string; label: string } | null) => void
    setLillySuggestions: (s: Array<{ type: string; target: string; label: string }> | null) => void
    setTimeline: (t: BiographicalTimeline | null) => void
    clearAll: () => void

    setOnboardingStage: (stage: OnboardingStage) => void
    updateOnboardingData: (partial: Partial<OnboardingData>) => void
    resetOnboarding: () => void
  }

  // ======================================================
  //  PERSISTENCIA
  // ======================================================

  const STORAGE_KEY = "ai-oracle-store-v1"
  const PROFILE_KEY = "ai-oracle-profile-v1"
  const CHART_SIDEBAR_KEY = "chartSidebarExpanded"

  function loadPersisted() {
    if (typeof window === "undefined") return {}

    try {
      const raw = window.localStorage.getItem(STORAGE_KEY)
      if (!raw) return {}

      const parsed = JSON.parse(raw) as {
        abuData?: AbuAnalyzeResponse | null
        lillyData?: LillyResponse | null
        chatHistory?: ChatMessage[]
        birthData?: BirthData | null
      }

      const chatHistory: ChatMessage[] = Array.isArray(parsed.chatHistory)
        ? parsed.chatHistory.map((m: any) => ({
            ...m,
            timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
          }))
        : []

      return {
        abuData: parsed.abuData ?? null,
        lillyData: parsed.lillyData ?? null,
        chatHistory,
        birthData: parsed.birthData ?? null,
      }
    } catch (e) {
      console.error("[Store] Error leyendo localStorage:", e)
      return {}
    }
  }

  function loadChartSidebarExpanded(): boolean {
    if (typeof window === "undefined") return true
    return window.localStorage.getItem(CHART_SIDEBAR_KEY) !== "false"
  }

  function loadUserName(): string {
    if (typeof window === "undefined") return ""
    try {
      const raw = window.localStorage.getItem(PROFILE_KEY)
      if (!raw) return ""
      return JSON.parse(raw)?.name ?? ""
    } catch {
      return ""
    }
  }

  function saveUserName(name: string) {
    if (typeof window === "undefined") return
    try {
      window.localStorage.setItem(PROFILE_KEY, JSON.stringify({ name }))
    } catch (e) {
      console.error("[Store] Error guardando perfil:", e)
    }
  }

  function persistSelected(state: AppState) {
    if (typeof window === "undefined") return

    const payload = {
      abuData: state.abuData,
      lillyData: state.lillyData,
      chatHistory: state.chatHistory,
      birthData: state.birthData,
      lang: state.lang,
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    } catch (e) {
      console.error("[Store] Error escribiendo localStorage:", e)
    }
  }

  // ======================================================
  //  STORE
  // ======================================================

  export const useAppStore = create<AppState>((set, get) => {
    const persisted = loadPersisted()

    return {
      // ---- Estado base ----
      birthData: (persisted as any).birthData ?? null,
      abuData: (persisted as any).abuData ?? null,
      lillyData: (persisted as any).lillyData ?? null,
      chatHistory: (persisted as any).chatHistory ?? [],
      isLoading: false,
      error: null,

      includeTransits: true,
      transitDate: null,
      lang: (persisted as any).lang ?? "es",
      chartTab: "persian",
      chartSidebarExpanded: loadChartSidebarExpanded(),
      chartTab: "persian",

      userName: loadUserName(),
      isDemo: false,
      pendingLillyEvent: null,
      lastLillyEvent: null,
      lillySuggestions: null,
      timeline: null,

      // ---- Estado de onboarding ----
      onboardingStage: "idle",
      onboardingData: {},

      // ---------------------------------------------------
      // MUTADORES PRINCIPALES
      // ---------------------------------------------------

      setBirthData: (data) =>
        set((state) => {
          const next: AppState = { ...state, birthData: data }
          persistSelected(next)
          return { birthData: data }
        }),

      setAbuData: (data) =>
        set((state) => {
          const next: AppState = { ...state, abuData: data }
          persistSelected(next)
          return { abuData: data }
        }),

      setLillyData: (data) =>
        set((state) => {
          const next: AppState = { ...state, lillyData: data }
          persistSelected(next)
          return { lillyData: data }
        }),

      setIsLoading: (value) => set({ isLoading: value }),

      setError: (message) => set({ error: message }),

      setIncludeTransits: (value) => set({ includeTransits: value }),

      setTransitDate: (date) => set({ transitDate: date }),

      setLang: (lang) => set({ lang }),
      setChartTab: (tab) => set({ chartTab: tab }),
      setChartSidebarExpanded: (expanded) => {
        if (typeof window !== "undefined") {
          window.localStorage.setItem(CHART_SIDEBAR_KEY, String(expanded))
        }
        set({ chartSidebarExpanded: expanded })
      },
      setChartTab: (tab) => set({ chartTab: tab }),

      addChatMessage: (msg) =>
        set((state) => {
          const newHistory = [...state.chatHistory, msg]
          const next: AppState = { ...state, chatHistory: newHistory }
          persistSelected(next)
          return { chatHistory: newHistory }
        }),

      setUserName: (name) => {
        saveUserName(name)
        set({ userName: name })
      },

      setIsDemo: (value) => set({ isDemo: value }),

      setPendingLillyEvent: (event) => set({ pendingLillyEvent: event }),

      setLastLillyEvent: (evt) => set({ lastLillyEvent: evt }),

      setLillySuggestions: (s) => set({ lillySuggestions: s }),

      setTimeline: (t) => set({ timeline: t }),

      // ---------------------------------------------------
      // ONBOARDING MUTATORS
      // ---------------------------------------------------

      setOnboardingStage: (stage: OnboardingStage) =>
        set({ onboardingStage: stage }),

      updateOnboardingData: (partial) =>
        set((state) => ({
          onboardingData: { ...state.onboardingData, ...partial },
        })),

      resetOnboarding: () =>
        set({
          onboardingStage: "idle",
          onboardingData: {},
        }),

      // ---------------------------------------------------
      // CLEAR ALL
      // ---------------------------------------------------

      clearAll: () => {
        if (typeof window !== "undefined") {
          window.localStorage.removeItem(STORAGE_KEY)
          // PROFILE_KEY (userName) se preserva intencionalmente
        }

        set({
          birthData: null,
          abuData: null,
          lillyData: null,
          chatHistory: [],
          isLoading: false,
          error: null,
          includeTransits: true,
          isDemo: false,
          onboardingStage: "idle",
          onboardingData: {},
          chartTab: "persian",
          chartSidebarExpanded: true,
          chartTab: "persian",
          // userName se preserva
        })
      },
    }
  })
