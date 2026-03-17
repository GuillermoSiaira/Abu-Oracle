"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const { user, loading, login, register, isConfigured } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nextPath = searchParams.get("next") || "/chart";

  useEffect(() => {
    if (!loading && user) {
      router.replace(nextPath);
    }
  }, [loading, user, router, nextPath]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(email.trim(), password);
      }
      router.replace(nextPath);
    } catch (err: any) {
      setError(err?.message || "No se pudo autenticar.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!isConfigured) {
    return (
      <main className="h-full flex items-center justify-center px-6">
        <div className="max-w-md w-full rounded-xl border border-amber-400/30 bg-[#080808] p-6 text-slate-300 space-y-3">
          <h1 className="text-lg text-amber-400">Firebase no configurado</h1>
          <p className="text-sm text-slate-400">
            Faltan variables públicas: <code>NEXT_PUBLIC_FIREBASE_API_KEY</code>, <code>NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN</code>, <code>NEXT_PUBLIC_FIREBASE_PROJECT_ID</code>.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="h-full flex items-center justify-center px-6">
      <div className="max-w-md w-full rounded-xl border border-slate-700 bg-[#080808] p-6 space-y-5">
        <h1 className="text-2xl font-semibold text-slate-100">
          {mode === "login" ? "Iniciar sesión" : "Crear cuenta"}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs text-slate-400">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs text-slate-400">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
            />
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-amber-600 hover:bg-amber-500 disabled:opacity-60 px-4 py-2 text-sm font-semibold text-white"
          >
            {submitting
              ? "Procesando…"
              : mode === "login"
              ? "Entrar"
              : "Registrarme"}
          </button>
        </form>

        <button
          type="button"
          onClick={() => setMode((m) => (m === "login" ? "register" : "login"))}
          className="text-xs text-amber-400 hover:text-amber-300"
        >
          {mode === "login"
            ? "¿No tenés cuenta? Crear cuenta"
            : "¿Ya tenés cuenta? Iniciar sesión"}
        </button>
      </div>
    </main>
  );
}
