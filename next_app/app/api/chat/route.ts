import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    // 1. Extraer TODO el payload (ahora incluye context y session_id)
    const body = await req.json();
    const { messages, context, session_id } = body;
    
    // Obtenemos el último mensaje del usuario
    const lastMessage = messages?.[messages.length - 1]?.content ?? "";

    // 2. Apuntar al contenedor correcto
    const BACKEND_URL = "http://lilly_swarm:8001";

    // 3. Llamada a Lilly (Python) PASANDO EL CONTEXTO
    const upstream = await fetch(`${BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: lastMessage,
        session_id: session_id || "default-session",
        context: context || null // <--- EL DATO CRUCIAL
      }),
    });

    if (!upstream.ok) {
      const txt = await upstream.text();
      return NextResponse.json({ error: txt }, { status: 500 });
    }

    // 4. Obtener respuesta de Lilly
    const data = await upstream.json();
    
    // Normalizar respuesta
    const textResponse = data.response || JSON.stringify(data);

    // 5. Devolver JSON simple (Compatible con tu await res.json() del frontend)
    return NextResponse.json({ response: textResponse });

  } catch (err: any) {
    console.error("🔴 Error route.ts:", err);
    return NextResponse.json({ error: "Internal error" }, { status: 500 });
  }
}