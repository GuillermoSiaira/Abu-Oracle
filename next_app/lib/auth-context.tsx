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
