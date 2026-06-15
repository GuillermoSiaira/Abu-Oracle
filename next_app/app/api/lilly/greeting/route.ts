/**
 * GET /api/lilly/greeting
 *
 * Lightweight endpoint — no LLM call, no context block.
 * Tells the frontend whether the user is new (Estado A) or returning (Estado B)
 * so OracleChat can show the correct entry nav state without calling Anthropic.
 *
 * Response: { isNewUser: boolean, lastTopic: string | null }
 *
 * Errors: always returns 200 with { isNewUser: true, lastTopic: null } —
 * never blocks the app loading by throwing.
 */

import { NextResponse } from 'next/server';
import { getUserIdFromRequest } from '@/lib/get-user-id';
import { getRecentHistory } from '@/lib/chat-memory';

export const dynamic = 'force-dynamic';

const FALLBACK = { isNewUser: true, lastTopic: null };

export async function GET(req: Request): Promise<NextResponse> {
  try {
    const { searchParams } = new URL(req.url);
    const isDemo = searchParams.get('isDemo') === 'true';

    // If it's a demo chart, do not load the logged-in user's memory
    if (isDemo) {
      return NextResponse.json(FALLBACK);
    }

    const userId = await getUserIdFromRequest(req);

    // Unauthenticated — treat as new user (dev local / public access)
    if (!userId) {
      return NextResponse.json(FALLBACK);
    }

    const memory = await getRecentHistory(userId);
    const isNewUser = memory.exchanges.length === 0 && !memory.summary;

    // TODO: añadir lastTopic al schema de summary en Fase futura.
    // El resumen actual es texto libre; extraer un campo estructurado
    // requiere actualizar summarizeIfNeeded() para guardar lastTopic.
    const lastTopic: string | null = null;

    return NextResponse.json({ isNewUser, lastTopic });
  } catch {
    // Non-fatal — fall back gracefully so the app never blocks on this
    return NextResponse.json(FALLBACK);
  }
}
