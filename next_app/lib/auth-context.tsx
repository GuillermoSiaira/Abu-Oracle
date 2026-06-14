"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  User,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
} from "firebase/auth";
import { firebaseAuth, isFirebaseConfigured } from "@/lib/firebase";
import { useAppStore } from "@/lib/store";

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
  isConfigured: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!firebaseAuth || !isFirebaseConfigured) {
      setLoading(false);
      return;
    }

    const unsub = onAuthStateChanged(firebaseAuth, (nextUser) => {
      setUser(nextUser);
      setLoading(false);
    });

    return () => unsub();
  }, []);

  // Carga el plan del usuario (users/{uid}.plan en Firestore) al autenticarse.
  // Sin esto, userPlan queda null → isPro=false → la proyección futura muestra
  // upsell incluso a usuarios pagos. Default conservador: null (free tier) hasta
  // que la respuesta confirme el plan — nunca otorga "pro" sin verificar.
  const setUserPlan = useAppStore((s) => s.setUserPlan);
  useEffect(() => {
    if (!user) {
      setUserPlan(null);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const token = await user.getIdToken();
        const res = await fetch("/api/user/plan", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = (await res.json()) as { plan?: string | null };
        if (!cancelled) setUserPlan(data.plan ?? null);
      } catch {
        // Non-fatal: el plan queda null (free tier). El gating reactivo de la API
        // sigue protegiendo el backend si el usuario intenta exceder su cuota.
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [user, setUserPlan]);

  const login = useCallback(async (email: string, password: string) => {
    if (!firebaseAuth || !isFirebaseConfigured) {
      throw new Error("Firebase no está configurado en el frontend.");
    }
    await signInWithEmailAndPassword(firebaseAuth, email, password);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    if (!firebaseAuth || !isFirebaseConfigured) {
      throw new Error("Firebase no está configurado en el frontend.");
    }
    await createUserWithEmailAndPassword(firebaseAuth, email, password);
  }, []);

  const logout = useCallback(async () => {
    if (!firebaseAuth || !isFirebaseConfigured) return;
    await signOut(firebaseAuth);
  }, []);

  const getIdToken = useCallback(async () => {
    if (!firebaseAuth || !isFirebaseConfigured || !firebaseAuth.currentUser) {
      return null;
    }
    return firebaseAuth.currentUser.getIdToken();
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      register,
      logout,
      getIdToken,
      isConfigured: isFirebaseConfigured,
    }),
    [user, loading, login, register, logout, getIdToken]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
