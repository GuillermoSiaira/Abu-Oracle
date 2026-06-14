import { NextResponse } from 'next/server';
import { getAdminDb } from './firebase-admin';
import { getUserIdFromRequest } from './get-user-id';
import { DAILY_LIMIT, FREE_TIER_LIMIT } from './usage-limiter';

export type AccessPlan = 'free' | 'genesis' | 'monthly' | 'annual' | null;
export type LlmProvider = 'anthropic' | 'gemini';

export interface AccessContext {
  userId: string | null;
  plan: AccessPlan;
  paying: boolean;
  allowed: boolean;
  provider: LlmProvider;
  limitType?: 'free_lifetime' | 'daily';
}

const PAID_PLANS: Array<Exclude<AccessPlan, 'free' | null>> = [
  'genesis',
  'monthly',
  'annual',
];

function normalizePlan(data: FirebaseFirestore.DocumentData | undefined): AccessPlan {
  const rawPlan = data?.plan;
  if (rawPlan === 'genesis' || rawPlan === 'monthly' || rawPlan === 'annual') {
    return rawPlan;
  }
  if (data?.payment_verified === true) return 'genesis';
  return 'free';
}

export async function getAccessContext(req: Request): Promise<AccessContext> {
  const userId = await getUserIdFromRequest(req).catch(() => null);

  if (!userId) {
    return {
      userId: null,
      plan: null,
      paying: false,
      allowed: true,
      provider: 'gemini',
    };
  }

  const operatorUid = process.env.OPERATOR_UID;
  if (operatorUid && userId === operatorUid) {
    let providerChoice: LlmProvider | undefined;

    // Operator can choose provider. Precedence: query param > body > env > default.
    try {
      const url = new URL(req.url);
      const queryProvider = url.searchParams.get('provider');
      if (queryProvider === 'anthropic' || queryProvider === 'gemini') {
        providerChoice = queryProvider;
      }
    } catch (e) { /* ignore URL parsing errors */ }

    if (!providerChoice) {
      try {
        const body = await req.clone().json();
        if (body.providerChoice === 'anthropic' || body.providerChoice === 'gemini') {
          providerChoice = body.providerChoice;
        }
      } catch (e) { /* ignore body parsing errors */ }
    }

    const envProvider = process.env.LILLY_OPERATOR_PROVIDER;
    const provider: LlmProvider =
      providerChoice ||
      (envProvider === 'anthropic' || envProvider === 'gemini' ? envProvider : 'gemini');

    return {
      userId,
      plan: 'genesis',
      paying: true,
      allowed: true,
      provider,
    };
  }

  const db = getAdminDb();
  const userRef = db.collection('users').doc(userId);
  const snap = await userRef.get().catch(() => null);
  const plan = normalizePlan(snap?.data());
  const paying = PAID_PLANS.includes(plan as Exclude<AccessPlan, 'free' | null>);

  if (paying) {
    const today = new Date().toISOString().slice(0, 10);
    const usageRef = userRef.collection('usage').doc('daily');

    const result = await db.runTransaction(async (tx) => {
      const usageSnap = await tx.get(usageRef);
      const usageData = usageSnap.data() ?? {};
      const currentCount = usageData.date === today ? (usageData.lilly_calls ?? 0) : 0;

      if (currentCount >= DAILY_LIMIT) {
        return { allowed: false, limitType: 'daily' as const };
      }

      tx.set(usageRef, { date: today, lilly_calls: currentCount + 1 }, { merge: true });
      return { allowed: true };
    }).catch((err) => {
      console.error('[access-context] daily usage check failed:', err);
      return { allowed: true };
    });

    return {
      userId,
      plan,
      paying: true,
      provider: 'gemini',
      ...result,
    };
  }

  const freeRef = userRef.collection('usage').doc('free_tier');
  const result = await db.runTransaction(async (tx) => {
    const freeSnap = await tx.get(freeRef);
    const freeData = freeSnap.data() ?? {};
    const count = freeData.lilly_calls ?? freeData.calls ?? 0;

    if (count >= FREE_TIER_LIMIT) {
      return { allowed: false, limitType: 'free_lifetime' as const };
    }

    tx.set(freeRef, { lilly_calls: count + 1, calls: count + 1 }, { merge: true });
    return { allowed: true };
  }).catch((err) => {
    console.error('[access-context] free tier usage check failed:', err);
    return { allowed: true };
  });

  return {
    userId,
    plan,
    paying: false,
    provider: 'gemini',
    ...result,
  };
}

export function rateLimitResponse(ctx: AccessContext): Response {
  const message = ctx.limitType === 'free_lifetime'
    ? `Has usado tus ${FREE_TIER_LIMIT} consultas gratuitas. Hazte miembro Genesis para acceso ilimitado.`
    : `Limite diario alcanzado (${DAILY_LIMIT} consultas). Se restablece manana.`;

  return NextResponse.json({ error: message, response: message }, { status: 429 });
}
