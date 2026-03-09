  // next_app/lib/store.ts

  import { create } from "zustand"
  import type {
    AbuAnalyzeResponse,
    LillyResponse,
    ChatMessage,
    BirthData
  } from "./types"

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

    onboardingStage: OnboardingStage
    onboardingData: OnboardingData

    setBirthData: (data: BirthData) => void
    setAbuData: (data: AbuAnalyzeResponse | null) => void
    setLillyData: (data: LillyResponse | null) => void
    setIsLoading: (value: boolean) => void
    setError: (message: string | null) => void
    setIncludeTransits: (value: boolean) => void
    addChatMessage: (msg: ChatMessage) => void
    clearAll: () => void

    setOnboardingStage: (stage: OnboardingStage) => void
    updateOnboardingData: (partial: Partial<OnboardingData>) => void
    resetOnboarding: () => void
  }

  // ======================================================
  //  PERSISTENCIA
  // ======================================================

  const STORAGE_KEY = "ai-oracle-store-v1"

  function loadPersisted() {
    if (typeof window === "undefined") return {}

    try {
      const raw = window.localStorage.getItem(STORAGE_KEY)
      if (!raw) return {}

      const parsed = JSON.parse(raw) as {
        abuData?: AbuAnalyzeResponse | null
        lillyData?: LillyResponse | null
        chatHistory?: ChatMessage[]
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
      }
    } catch (e) {
      console.error("[Store] Error leyendo localStorage:", e)
      return {}
    }
  }

  function persistSelected(state: AppState) {
    if (typeof window === "undefined") return

    const payload = {
      abuData: state.abuData,
      lillyData: state.lillyData,
      chatHistory: state.chatHistory,
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
      birthData: null,
      abuData: (persisted as any).abuData ?? null,
      lillyData: (persisted as any).lillyData ?? null,
      chatHistory: (persisted as any).chatHistory ?? [],
      isLoading: false,
      error: null,

      includeTransits: true,

      // ---- Estado de onboarding ----
      onboardingStage: "idle",
      onboardingData: {},

      // ---------------------------------------------------
      // MUTADORES PRINCIPALES
      // ---------------------------------------------------

      setBirthData: (data) => set({ birthData: data }),

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

      addChatMessage: (msg) =>
        set((state) => {
          const newHistory = [...state.chatHistory, msg]
          const next: AppState = { ...state, chatHistory: newHistory }
          persistSelected(next)
          return { chatHistory: newHistory }
        }),

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
        }

        set({
          birthData: null,
          abuData: null,
          lillyData: null,
          chatHistory: [],
          isLoading: false,
          error: null,
          includeTransits: true,
          onboardingStage: "idle",
          onboardingData: {},
        })
      },
    }
  })
