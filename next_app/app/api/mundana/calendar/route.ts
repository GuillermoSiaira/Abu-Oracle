import { NextRequest, NextResponse } from 'next/server';
import { getAbuAuthHeaders } from '@/lib/abu-auth';

const ABU =
  process.env.ABU_ENGINE_URL ??
  process.env.NEXT_PUBLIC_ABU_URL ??
  process.env.NEXT_PUBLIC_ABU_API_URL ??
  'http://localhost:8000';

export async function GET(req: NextRequest) {
  const months = req.nextUrl.searchParams.get('months') ?? '12';
  const headers = await getAbuAuthHeaders().catch(() => ({} as Record<string, string>));
  const res = await fetch(`${ABU}/api/mundana/calendar?months=${encodeURIComponent(months)}`, {
    headers,
    cache: 'no-store',
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
