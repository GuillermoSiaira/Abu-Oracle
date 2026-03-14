import { NextRequest, NextResponse } from "next/server";

// Server-side proxy for city search.
// The browser calls /api/cities/search (same origin, always reachable).
// This handler forwards to Abu Engine using the internal Docker network URL.
const ABU_INTERNAL =
  process.env.ABU_ENGINE_URL ||
  process.env.NEXT_PUBLIC_ABU_URL ||
  "http://localhost:8000";

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") ?? "";

  try {
    const upstream = await fetch(
      `${ABU_INTERNAL}/api/cities/search?q=${encodeURIComponent(q)}`,
      { cache: "no-store" }
    );

    if (!upstream.ok) {
      return NextResponse.json([], { status: upstream.status });
    }

    const data = await upstream.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json([], { status: 502 });
  }
}
