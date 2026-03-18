import { firebaseAuth, isFirebaseConfigured } from "@/lib/firebase";

export async function getAbuAuthHeaders(
  baseHeaders?: HeadersInit
): Promise<Record<string, string>> {
  const headers = new Headers(baseHeaders);

  if (isFirebaseConfigured && firebaseAuth) {
    try {
      await firebaseAuth.authStateReady();
      const token = await firebaseAuth.currentUser?.getIdToken();
      if (token) headers.set("Authorization", `Bearer ${token}`);
    } catch {
      // Token refresh falló: dejamos pasar la request sin Authorization.
      // Abu Engine responderá 401 y la UI/guard gestionará la sesión.
    }
  }

  return Object.fromEntries(headers.entries());
}
